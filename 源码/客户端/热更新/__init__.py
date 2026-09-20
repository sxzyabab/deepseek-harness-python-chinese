import json,os,threading#JSON、路径与定时器
from ...依赖.schemastery import 自然数字段#配置字段
from .事件 import 插件事件帧,事件端点,热更新错误#再导出 SSE 帧、路径与本包错误

__all__=['名称','依赖','配置','应用','插件事件帧','事件端点','热更新错误']#仅中文公开名

名称='client-hmr'#Cordis 插件名（字面量）
依赖=['clientModules','webServer']#依赖客户端模块与 web 服务器
配置={#HMR 可校验配置
    'pollIntervalMs':自然数字段(最小=1,默认值=500),#至少 1 毫秒，默认 500
}#配置模式结束

def sse数据(帧):
    """把一帧序列化成 SSE data 行。"""
    return 'data: '+json.dumps(帧,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n\n'#标准 data 行加空行

def 应用(上下文,配置值):
    """挂上开发链：打包产物监视、rebuilt 上报，以及 SSE 通道。"""
    上下文.__hmr_stat_watchers__=0#不变量基线；双下划线属性走自由点访问
    轮询间隔毫秒=配置值['pollIntervalMs']#schemastery 校验后必有
    监视表={}#id → 监视状态
    连接集=set()#当前打开的 SSE 响应
    停止旗=threading.Event()#拆除旗

    def 再哈希(标识,监视,当前):
        """对一行重新 hash；hash 未变则保持静默。"""
        try:#rebuilt 会再 hash，缺文件按脏处理
            上下文.clientModules.rebuilt(标识)#上报可能的重建
        except FileNotFoundError:#文件暂时不在
            监视['dirty']=True#标脏，下次轮询再试
            return#先不更新基线
        except OSError as 错误:#其它磁盘错误
            上下文.日志.警告(错误)#记警告后仍更新基线
        监视['mtimeMs']=当前['mtimeMs']#记下本次 stat 时间
        监视['size']=当前['size']#记下本次大小
        监视['dirty']=False#本轮成功，清脏

    def 读状态(路径):
        """读磁盘 mtime 与 size。mtime 是纪元毫秒 int。"""
        信息=os.stat(路径)#同步 stat
        return {'mtimeMs':int(信息.st_mtime*1000),'size':信息.st_size}#毫秒时间与大小

    def 监视行(标识,路径):
        """开始监视一行的打包产物。"""
        try:#读当前 stat
            基线=读状态(路径)#同步 stat
        except FileNotFoundError:#文件还不在
            监视表[标识]={'path':路径,'mtimeMs':0,'size':0,'dirty':True}#先占位并标脏
            return#等下次轮询
        except OSError as 错误:#其它磁盘错误
            监视表[标识]={'path':路径,'mtimeMs':0,'size':0,'dirty':True}#先占位并标脏
            上下文.日志.警告(错误)#非缺失才警告
            return#等下次轮询
        监视={'path':路径,'mtimeMs':基线['mtimeMs'],'size':基线['size'],'dirty':False}#用当前 stat 做基线
        监视表[标识]=监视#登记监视
        再哈希(标识,监视,基线)#立刻对齐 hash 与图

    def 轮询监视():
        """一轮 stat 轮询。"""
        for 标识,监视 in list(监视表.items()):#逐行检查
            try:#读磁盘
                当前=读状态(监视['path'])#同步 stat
            except FileNotFoundError:#文件暂时不在
                监视['dirty']=True#标脏
                continue#本行下次再试
            except OSError as 错误:#其它磁盘错误
                监视['dirty']=True#标脏
                上下文.日志.警告(错误)#警告
                continue#本行下次再试
            if (not 监视['dirty']) and 当前['mtimeMs']==监视['mtimeMs'] and 当前['size']==监视['size']:#干净且未变
                continue#跳过
            再哈希(标识,监视,当前)#内容或脏标记变化则再 hash

    def 同步监视():
        """把监视集对当前图做 diff。图是跨线 dict，行是 dict。"""
        行表={}#id → 当前客户端打包路径
        图=上下文.clientModules.graph()#当前整图
        for 行 in 图['entries']:#遍历图中每一行
            路径=上下文.clientModules.clientPath(行['id'])#取该行客户端打包路径
            if 路径 is not None:#有路径才监视
                行表[行['id']]=路径#记下
        for 标识,监视 in list(监视表.items()):#丢掉图里没有或路径已变的监视
            if 标识 in 行表 and 行表[标识]==监视['path']:#路径仍匹配则保留
                continue#保留
            del 监视表[标识]#删除过期监视
        for 标识,路径 in 行表.items():#为尚无监视的行补上
            if 标识 not in 监视表:#新行
                监视行(标识,路径)#开始监视
        上下文.__hmr_stat_watchers__=len(监视表)#同步给不变量

    def 监视线程体():
        """按配置间隔轮询，直到拆除。"""
        while not 停止旗.wait(轮询间隔毫秒/1000):#按间隔休眠；stdlib Event.wait
            轮询监视()#一轮轮询

    def 连接(响应):
        """把一个 HTTP 响应升级为 SSE。响应是 webServer 对象。"""
        响应.writeHead(200,{#SSE 响应头
            'content-type':'text/event-stream',#事件流
            'cache-control':'no-cache',#禁止缓存
            'connection':'keep-alive',#保持连接
        })#结束响应头
        响应.write(': connected\n\n')#SSE 注释行
        图=上下文.clientModules.graph()#当前整图
        帧={'type':'graph','graph':图}#整图帧
        响应.write(sse数据(帧))#先推当前整图
        连接集.add(响应)#登记连接
        def 关闭(_事件=None):
            """关闭时从表删除。"""
            连接集.discard(响应)#删除
        响应.on('close',关闭)#关闭时从表删除

    def 路由处理(请求,响应):
        """对本端点的非 GET 保持 405 语义。请求是 webServer 对象。"""
        方法=请求.method#HTTP 方法
        if 方法!='GET' and 方法!='HEAD':#只允许读
            响应.writeHead(405)#方法不允许
            响应.end()#结束响应
            return#不升级为 SSE
        连接(响应)#升级为 SSE 并推图

    def 拆除监视():
        """停轮询并清表。"""
        停止旗.set()#停线程
        退订图()#取消图订阅
        监视表.clear()#丢掉监视表
        上下文.__hmr_stat_watchers__=0#拆除后归零

    def 拆除通道():
        """取消订阅、注销路由、拆掉连接。"""
        if 退订图广播 is not None:#有图广播
            退订图广播()#退订
        退订重建()#取消 rebuilt 订阅
        拆除路由()#注销路由
        for 响应 in list(连接集):#仍打开的连接
            响应.destroy()#拆掉
        连接集.clear()#清空连接集

    def 监视效应():
        """对齐图、开轮询，返回拆除器。"""
        同步监视()#先对齐已有图
        nonlocal 退订图,轮询线程#写入外层绑定
        退订图=上下文.clientModules.onGraphChanged(同步监视)#图变再对齐
        轮询线程=threading.Thread(target=监视线程体,daemon=True)#后台轮询
        轮询线程.start()#启动轮询
        return 拆除监视#拆除器
    退订图=None#图订阅拆除
    轮询线程=None#轮询线程
    上下文.副作用(监视效应,'client-hmr: bundle watches')#监视生命周期
    def 广播图():
        """图变更时广播 graph 帧。"""
        行=sse数据({'type':'graph','graph':上下文.clientModules.graph()})#帧
        for 响应 in list(连接集):#写给每个打开的 SSE
            响应.write(行)#写出

    def 通道效应():
        """登记路由与 graph/rebuilt 广播，返回拆除器。"""
        nonlocal 拆除路由,退订重建,退订图广播#写入外层绑定
        拆除路由=上下文.webServer.register({#注册精确路径
            'kind':'exact',#精确匹配
            'path':事件端点,#SSE 端点
            'handler':路由处理,#处理该路径
        })#结束路由注册
        def 广播重建(标识,修订):
            """某行重建时广播 rebuilt 帧。"""
            行=sse数据({'type':'rebuilt','id':标识,'rev':修订})#组装 rebuilt 帧
            for 响应 in list(连接集):#写给每个打开的 SSE
                响应.write(行)#写出
        退订图广播=上下文.clientModules.onGraphChanged(广播图)#图变广播
        退订重建=上下文.clientModules.onRebuilt(广播重建)#订阅重建
        return 拆除通道#拆除器
    拆除路由=None#路由拆除
    退订重建=None#重建订阅拆除
    退订图广播=None#图广播拆除
    上下文.副作用(通道效应,'client-hmr: /plugins/events channel')#通道生命周期

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
