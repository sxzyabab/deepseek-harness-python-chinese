'宿主侧：轮询每个图行的客户端包，变更经 clientModules.rebuilt 上报，并用 /plugins/events 把图和重建帧推给浏览器'
import os,threading#磁盘状态与轮询
from ...基础设施.通用工具 import 紧凑json编码,编码sse事件#SSE 数据行
from .事件 import 事件端点#系统端点
from . import 事件,异常,客户端#同目录模块。导入时执行它们的顶层

__all__=['名称','依赖','配置','应用','事件端点','事件','异常','客户端']#包根导出客户端这个模块，不转发里面的类

名称='client-hmr'#插件名
依赖=['clientModules','webServer']#客户端图与网页路由

class 热更新配置:
    '包状态轮询间隔。缺省 500 毫秒，至少 1，步长 1'
    @classmethod
    def 校验数据(类,数据=None):
        '没写 pollIntervalMs 时补 500。布尔值不是整数'
        if 数据 is None:#启动时没给配置
            数据={}#按默认
        if not isinstance(数据,dict):#必须是对象
            raise ValueError('热更新配置必须是对象')#拒绝
        if 'pollIntervalMs' in 数据:#写了间隔
            值=数据['pollIntervalMs']#原值
        else:#没写
            值=500#默认 500 毫秒
        if isinstance(值,bool) or not isinstance(值,int) or 值<1:#不是大于等于 1 的整数
            raise ValueError('pollIntervalMs 必须是大于等于 1 的整数')#拒绝
        return {'pollIntervalMs':值}#只留这个字段

def 系统错误码(错误):
    'Node 错误的 code。文件不存在对应 ENOENT'
    码=getattr(错误,'code',None)#错误对象上的 code
    if isinstance(码,str):#已经是字符串码
        return 码#原码
    if isinstance(错误,FileNotFoundError):#Python 打开或 stat 找不到文件
        return 'ENOENT'#与 Node 的 ENOENT 对齐
    return None#其它错误

def 读包状态(路径):
    '读可执行包的修改时间、状态变更时间和字节大小，单位是毫秒'
    信息=os.stat(路径)#同步 stat
    return {'mtimeMs':信息.st_mtime_ns/1000000,'ctimeMs':信息.st_ctime_ns/1000000,'size':信息.st_size}#毫秒时间与字节大小

def 状态相同(左,右):
    '上次公布之后，修改时间、状态变更时间和大小都没变'
    return 左['mtimeMs']==右['mtimeMs'] and 左['ctimeMs']==右['ctimeMs'] and 左['size']==右['size']#三项都相等

def 事件数据行(帧):
    '把一帧写成一条 SSE data 行'
    return 编码sse事件(紧凑json编码(帧))#data 行，以空行结尾

def 应用(上下文,配置值):
    '挂上包监视，以及图和重建帧的 SSE'
    轮询间隔毫秒=配置值['pollIntervalMs']#校验后一定有
    监视表={}#标识到监视状态
    监视锁=threading.RLock()#轮询线程和拆除要串起来；重建回调会重入
    停止旗=threading.Event()#拆掉之后不再轮询
    连接集=set()#当前打开的 SSE 响应
    连接锁=threading.Lock()#连接表。写出时不占着这把锁

    def 发布(标识,监视,当前):
        '上报一次重建。文件暂时不在就保持旧基线并标脏'
        try:#rebuilt 再读文件
            上下文.clientModules.rebuilt(标识)#只有这里把构建变更送进图
        except Exception as 错误:#缺文件或其它失败
            if 系统错误码(错误)=='ENOENT':#文件在读的时候没了
                监视['dirty']=True#下次轮询再试
                return#不改基线
            上下文.日志.警告(错误)#其它错误记下来，基线仍前进
        监视['mtimeMs']=当前['mtimeMs']#记下这次修改时间
        监视['ctimeMs']=当前['ctimeMs']#记下这次状态变更时间
        监视['size']=当前['size']#记下这次大小
        监视['dirty']=False#这轮成功

    def 轮询监视():
        '一轮 stat。调用方已持有监视锁'
        for 标识,监视 in list(监视表.items()):#快照，重建回调可以改表
            try:#读磁盘
                当前=读包状态(监视['path'])#当前状态
            except Exception as 错误:#读失败
                监视['dirty']=True#标脏
                if 系统错误码(错误)!='ENOENT':#不是文件暂时不在
                    上下文.日志.警告(错误)#记警告
                continue#下一行
            if (not 监视['dirty']) and 状态相同(当前,监视):#干净且没变
                continue#跳过
            发布(标识,监视,当前)#变了，或上次没公布成功

    def 同步监视():
        '按当前图增减监视。路径变了的行先丢掉再重挂'
        with 监视锁:#和轮询互斥
            行表={}#标识到安装监视前的基线
            for 行 in 上下文.clientModules.graph()['entries']:#图里的每一行
                基线=上下文.clientModules.artifactBaseline(行['id'])#启动时记下的路径和时间
                if 基线 is not None:#没有基线的行不监视
                    行表[行['id']]=基线#记下
            for 标识,监视 in list(监视表.items()):#丢掉已删除或换了路径的行
                现行=行表.get(标识)#图里的这一行
                if 现行 is not None and 现行['path']==监视['path']:#路径还是原来的
                    continue#留着
                del 监视表[标识]#删掉旧监视
            for 标识,基线 in 行表.items():#新行补上监视
                if 标识 in 监视表:#已经在监视
                    continue#不用重建
                监视={'path':基线['path'],'mtimeMs':基线['mtimeMs'],'ctimeMs':基线['ctimeMs'],'size':基线['size'],'dirty':False}#用安装前的基线，不用此刻磁盘状态当起点
                监视表[标识]=监视#先登记
                try:#再读现在的磁盘
                    当前=读包状态(基线['path'])#当前状态
                except Exception as 错误:#还读不到
                    监视['dirty']=True#标脏
                    if 系统错误码(错误)!='ENOENT':#不是文件不存在
                        上下文.日志.警告(错误)#记警告
                    continue#下一行
                if not 状态相同(当前,监视):#启动之后文件变过
                    发布(标识,监视,当前)#补一次公布

    def 轮询循环():
        '先等一个间隔再查，拆掉后退出'
        while not 停止旗.wait(轮询间隔毫秒/1000):#setInterval 也是先等再跑
            with 监视锁:#这一轮和同步互斥
                轮询监视()#查每一行

    def 监视效应():
        '先对齐已有图，再订图变更和轮询'
        同步监视()#启动前已经在图里的行
        退订图=上下文.clientModules.onGraphChanged(同步监视)#后到的行
        轮询线程=threading.Thread(target=轮询循环,daemon=True)#不挡住进程退出
        轮询线程.start()#开始轮询
        def 拆除监视():
            '停轮询、退订，并清掉监视表'
            停止旗.set()#轮询循环退出
            退订图()#不再跟图
            with 监视锁:#等正在跑的一轮结束
                监视表.clear()#丢掉监视
        return 拆除监视#交给纤程
    上下文.副作用(监视效应,'client-hmr: bundle watches')#监视生命周期

    def 写出帧(行):
        '抄出当前连接再写，避免写的时候改表'
        with 连接锁:#只在抄名单时占锁
            名单=list(连接集)#当前连接
        for 响应 in 名单:#逐个写
            响应.write(行)#写出

    def 广播图():
        '图变了就推一条 graph 帧'
        写出帧(事件数据行({'type':'graph','graph':上下文.clientModules.graph()}))#整图

    def 路由处理(请求,响应):
        '非 GET、非 HEAD 仍是 405。HEAD 也进入事件流'
        方法=请求.method#HTTP 方法
        if 方法!='GET' and 方法!='HEAD':#不是读
            响应.writeHead(405)#方法不允许
            响应.end()#结束
            return#不升级
        响应.writeHead(200,{'content-type':'text/event-stream','cache-control':'no-cache','connection':'keep-alive'})#事件流头
        响应.write(': connected\n\n')#注释行，没有重建也让对端看到通道是活的
        with 连接锁:#登记之后才会收到后续广播
            连接集.add(响应)#加入
        响应.write(事件数据行({'type':'graph','graph':上下文.clientModules.graph()}))#先推当前整图
        def 关闭():
            '连接关闭时从表里去掉'
            with 连接锁:#和广播互斥
                连接集.discard(响应)#去掉
        响应.on('close',关闭)#关闭时去掉

    def 通道效应():
        '登记路由，并在图变更和重建时广播'
        拆除路由=上下文.webServer.register({'kind':'exact','path':事件端点,'handler':路由处理})#精确路径 /plugins/events
        退订图=上下文.clientModules.onGraphChanged(广播图)#图变广播
        def 广播重建(标识,修订):
            '一行重建时推一条 rebuilt 帧'
            写出帧(事件数据行({'type':'rebuilt','id':标识,'rev':修订}))#重建帧
        退订重建=上下文.clientModules.onRebuilt(广播重建)#重建广播
        def 拆除通道():
            '退订、摘掉路由，并拆掉还开着的连接'
            退订图()#停止图广播
            退订重建()#停止重建广播
            拆除路由()#摘掉路由
            with 连接锁:#抄出再清，destroy 会同步触发 close
                仍在=list(连接集)#还开着的
                连接集.clear()#表先空
            for 响应 in 仍在:#逐个拆
                响应.destroy()#拆掉连接
        return 拆除通道#交给纤程
    上下文.副作用(通道效应,'client-hmr: /plugins/events channel')#通道生命周期

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=热更新配置#框架槽
配置=热更新配置#中文名与 Config 是同一个模式
