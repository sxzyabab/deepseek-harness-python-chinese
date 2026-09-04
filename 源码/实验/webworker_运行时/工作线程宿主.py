"""Worker 装配入口：整棵 harness Cordis 树放进一个 dedicated Web Worker。

对齐上游 `webworker-runtime/src/worker-host.ts`。公开面仅中文名。
"""
from .module_system.模块加载器 import 设活动模块加载器,工作线程模块加载器#模块加载器
from .module_system.posix路径 import 目录名,拼接#路径工具
from .transport.隧道 import 隧道服务器#隧道服务器
from .storage.镜像gzip import 解压镜像,流式解压镜像#镜像解压
from .storage.内存 import 加载vfs镜像,加载vfs覆盖层,内存vfs#内存VFS
from .storage.活动 import 设活动vfs#活动VFS槽
from .镜像布局 import (#布局常量
    默认根,镜像配置路径,镜像空目录们,镜像主目录,镜像清单路径,降低版本,
)#镜像布局
import json as _json#manifest解析

__all__=['默认根','默认端口','创建工作线程宿主','安装日志汇','启动工作线程宿主']#仅中文公开名

默认端口=3080#默认报告端口

def 要求全局端口(通道):#解析消息通道
    """解析消息通道；缺省用全局 postMessage。"""
    if 通道 is not None:#显式通道
        return 通道#通道
    作用域=globals()#全局作用域
    发送=作用域.get('postMessage')#postMessage
    if not callable(发送):#非dedicated worker
        raise Exception('webworker host: no channel; pass options.channel outside a dedicated worker')#拒绝
    def 包装发送(消息,转移=None):#包装端口
        """调用全局 postMessage。"""
        发送(消息,转移)#发送
    return {'postMessage':包装发送}#包装端口

def 读镜像(镜像):#读取镜像字节
    """读取镜像字节：内存则解压，URL 则拉取后流式解压。"""
    if not isinstance(镜像,str):#内存字节
        return 解压镜像(镜像,'the image bytes given to createWorkerHost')#解压
    拉取=globals().get('fetch')#fetch
    if not callable(拉取):#无fetch
        raise Exception(f'webworker host: image fetch unavailable for {镜像}')#拒绝
    响应=拉取(镜像)#拉取URL
    成功=响应.get('ok') if isinstance(响应,dict) else getattr(响应,'ok',False)#是否成功
    if not 成功:#失败
        状态=响应.get('status') if isinstance(响应,dict) else getattr(响应,'status',None)#状态
        raise Exception(f'webworker host: image fetch failed with {状态} for {镜像}')#失败
    正文=响应.get('body') if isinstance(响应,dict) else getattr(响应,'body',None)#正文流
    if 正文 is None:#无体
        取缓冲=响应.get('arrayBuffer') if isinstance(响应,dict) else getattr(响应,'arrayBuffer',None)#缓冲面
        if callable(取缓冲):#有缓冲
            return 解压镜像(取缓冲(),镜像)#缓冲解压
        raise Exception(f'webworker host: image response for {镜像} carried no body')#无体
    return 流式解压镜像(正文,镜像)#流式解压

def 要求已降低镜像(文件系统,路径):#校验降低契约
    """要求已挂载镜像携带本构建能包装的体。"""
    if not 文件系统.existsSync(路径):#manifest缺失
        raise Exception(f'webworker host: {路径} is missing, so the image records no lowering; rebuild the image')#拒绝
    解析值=_json.loads(文件系统.readFileSync(路径,'utf8'))#解析JSON
    if not isinstance(解析值,dict):#非对象
        raise Exception(f'webworker host: {路径} does not hold an object')#拒绝
    降低=解析值.get('lowered')#契约字段
    if 降低!=降低版本:#版本不匹配
        raise Exception(f'webworker host: image was lowered by {降低}, this build runs {降低版本}; rebuild the image')#拒绝

def 启动补丁(加载器,文件系统,配置路径,根):#计算补丁
    """已交付的 preset 根 overlay 与明文 jsonl 补丁。"""
    文本=文件系统.readFileSync(配置路径,'utf8')#配置文本
    if 配置路径.endswith('.json'):#JSON配置
        行们=_json.loads(文本)#解析JSON
    else:#YAML配置——由镜像加载器方言读取
        行们=[]#本批次不内嵌js-yaml；空行表则无补丁
    def 查找(条目们,标识):#按id查找
        """递归查找配置行。"""
        if not isinstance(条目们,list):#非数组
            return None#未找到
        for 条目 in 条目们:#逐行
            if not isinstance(条目,dict):#非对象
                continue#跳过
            if 条目.get('id')==标识:#命中
                return 条目#返回
            嵌套=查找(条目.get('config'),标识)#递归
            if 嵌套 is not None:#命中嵌套
                return 嵌套#返回
        return None#未找到
    def 取配置(行):#取config对象
        """取合法 config 对象。"""
        配置=行.get('config')#config
        if isinstance(配置,dict):#合法对象
            return 配置#已有config
        return {}#空对象
    补丁们=[]#补丁列表
    预设覆盖=False#是否补preset根
    预设=查找(行们,'agent-presets')#presets行
    if 预设 is not None and 'roots' not in 取配置(预设):#缺roots
        预设覆盖=True#标记已应用
        补丁们.append({#追加preset根
            'id':'agent-presets',#目标id
            'config':{**取配置(预设),'roots':[{'path':拼接(根,'config/agent-presets'),'trust':'system'}]},#合并roots
        })#push结束
    jsonl=查找(行们,'session-persistence-jsonl')#jsonl行
    if jsonl is not None:#存在则强制无压缩
        补丁们.append({'id':'session-persistence-jsonl','config':{**取配置(jsonl),'compression':'none'}})#明文补丁
    return {'patches':补丁们,'presetOverlay':预设覆盖}#返回

def 读boot载荷(上下文):#读boot载荷
    """组装页面 Cordis 前引导所需的载荷。"""
    取=上下文.get if isinstance(上下文,dict) else getattr(上下文,'get',None)#取服务
    web服务器=取('webServer') if callable(取) else None#webServer服务
    if web服务器 is None:#缺失
        raise Exception('webworker host: no webServer service, so the page cannot receive its boot injections')#拒绝
    收集=web服务器.get('collectIndexInjections') if isinstance(web服务器,dict) else getattr(web服务器,'collectIndexInjections',None)#收集面
    return {'injections':收集() if callable(收集) else []}#收集注入表

def 安装日志汇(上下文,要求):#安装日志sink
    """把树自己的警告与错误送到 worker console。"""
    cordis=要求('@deepseek-ai/cordis')#消息渲染器包
    渲染器=cordis.get('Logger') if isinstance(cordis,dict) else getattr(cordis,'Logger',None)#Logger
    def 导出(消息):#导出
        """仅警告与错误。"""
        类型=消息.get('type') if isinstance(消息,dict) else getattr(消息,'type',None)#级别
        if 类型 not in ('warn','error'):#忽略info/debug
            return#忽略
        名=消息.get('name') if isinstance(消息,dict) else getattr(消息,'name','')#logger名
        if 渲染器 is not None and hasattr(渲染器,'format'):#有格式化
            行=f'{名}: {渲染器.format(导出器,消息)}'#格式化
        else:#无格式化
            行=f'{名}: {消息}'#原文
        if 类型=='error':#错误
            print(行)#错误
        else:#警告
            print(行)#警告
    导出器={'colors':False,'levels':{'default':2},'export':导出}#导出器
    日志=上下文.get('logger') if isinstance(上下文,dict) else getattr(上下文,'logger',None)#logger
    if 日志 is not None:#有logger
        挂=日志.get('exporter') if isinstance(日志,dict) else getattr(日志,'exporter',None)#exporter面
        if callable(挂):#可挂载
            挂(导出器)#挂载

def 创建工作线程宿主(选项):#创建宿主
    """构建 worker 宿主，不触碰网络或镜像。"""
    根=选项.get('root') or 默认根#虚拟根
    配置路径=选项.get('configPath') or 拼接(根,镜像配置路径)#配置路径
    端口=选项.get('port') if 选项.get('port') is not None else 默认端口#报告端口
    隧道选项={'port':要求全局端口(选项.get('channel')),'requestListener':选项['requestListener']}#隧道选项
    if 选项.get('privilegedMethods') is not None:#特权方法
        隧道选项['privilegedMethods']=选项['privilegedMethods']#挂上
    if 选项.get('unaryApiLane') is not None:#一元通道
        隧道选项['unaryApiLane']=选项['unaryApiLane']#挂上
    隧道=隧道服务器(隧道选项)#隧道服务器
    状态={'vfs':None,'modules':None,'context':None}#可变状态

    def 启动():#启动过程
        """挂载镜像并启动树。"""
        try:#装配树
            主目录=拼接(根,镜像主目录)#home路径
            #installProcessGlobal 由调用方/后续批次接线
            字节=读镜像(选项['image'])#基础镜像
            覆盖层们=[读镜像(层) for 层 in (选项.get('overlays') or [])]#overlays
            已挂=加载vfs镜像(字节,根)#挂载基础
            for 覆盖 in 覆盖层们:#应用overlay
                加载vfs覆盖层(覆盖,根,已挂)#应用
            for 目录 in 镜像空目录们:#补空目录
                已挂.seedDirectory(拼接(根,目录.rstrip('/')))#播种目录
            设活动vfs(已挂)#设活动VFS
            状态['vfs']=已挂#保存引用
            清单路径=选项.get('manifestPath') or 拼接(根,镜像清单路径)#manifest路径
            要求已降低镜像(已挂,清单路径)#校验降低契约
            静态模块=dict(选项['staticModules'])#可变静态表
            for 键 in ('node:process','process'):#补process工厂
                if 键 not in 静态模块:#缺席
                    def 读process():#读全局
                        """读取已安装全局。"""
                        return globals().get('process')#读全局
                    静态模块[键]=读process#补工厂
            加载器选项={'vfs':已挂,'root':根,'staticModules':静态模块}#加载器选项
            if 选项.get('staticModulePrefixes') is not None:#前缀
                加载器选项['staticModulePrefixes']=选项['staticModulePrefixes']#挂上
            if 选项.get('alsCausality') is not None:#ALS
                加载器选项['alsCausality']=选项['alsCausality']#挂上
            加载器=工作线程模块加载器(加载器选项)#模块加载器
            设活动模块加载器(加载器)#设活动加载器
            状态['modules']=加载器#保存引用
            #boot glue：require app-boot / cmdline —— 由镜像提供，后续批次接线完整树
            补丁结果=启动补丁(加载器,已挂,配置路径,根)#计算补丁
            用量=加载器.用量()#模块用量
            print(f"webworker host: tree active (modules={用量['modules']}, data overlays={len(覆盖层们)}, "
                  f"preset root overlay={'applied' if 补丁结果['presetOverlay'] else 'already in roster'}, "
                  f"direct lane=connection.createSharedFetchHandler, "
                  f"als causality={'inert' if 选项.get('alsCausality') is None else 'snapshot/restore'}, "
                  f"image lowering={降低版本})")#诊断
            def 直达fetch(请求):#直连fetch占位
                """树未接线时拒绝。"""
                raise Exception('webworker host: tree not fully wired in this Python batch')#拒绝
            def boot载荷():#boot载荷
                """读boot载荷；无上下文则空注入。"""
                if 状态['context'] is None:#无上下文
                    return {'injections':[]}#空
                return 读boot载荷(状态['context'])#收集
            def 开流(端点,载荷,信号):#开流占位
                """树未接线时空迭代。"""
                return iter(())#空
            def 流失败(错误):#流失败映射
                """稳定失败字段。"""
                return {'code':'carrier','message':str(错误),'details':{}}#映射
            隧道.服务({#开始服务
                'directFetch':直达fetch,#直连fetch
                'bootPayload':boot载荷,#boot载荷
                'openStream':开流,#开流
                'streamFailure':流失败,#流失败
            })#serve结束
        except Exception as 原因:#装配失败
            隧道.失败(原因)#通知页面
            raise#继续抛出

    def 处理消息(数据):#处理消息
        """喂入一条 postMessage 载荷。"""
        隧道.处理消息(数据)#转发消息

    def 停止():#停止
        """处置树；之后隧道继续拒绝。"""
        隧道.失败(Exception('webworker host: the tree was disposed'))#拒绝后续
        上下文=状态['context']#树上下文
        if 上下文 is not None:#有上下文
            fiber=上下文.get('fiber') if isinstance(上下文,dict) else getattr(上下文,'fiber',None)#fiber
            if fiber is not None:#有fiber
                处置=fiber.get('dispose') if isinstance(fiber,dict) else getattr(fiber,'dispose',None)#dispose
                if callable(处置):#可处置
                    处置()#处置树

    return {#宿主句柄
        'handleMessage':处理消息,#转发消息
        'start':启动,#启动
        'stop':停止,#停止
        'vfs':(lambda:状态['vfs']),#VFS访问器
        'modules':(lambda:状态['modules']),#加载器访问器
    }#返回结束

def 启动工作线程宿主(选项):#一步启动
    """安装消息处理器并启动树。"""
    宿主=创建工作线程宿主(选项)#创建宿主
    if 选项.get('channel') is None:#默认消息源
        作用域=globals()#全局
        加监听=作用域.get('addEventListener')#监听API
        if not callable(加监听):#无监听器API
            raise Exception('webworker host: no message source; pass options.channel outside a dedicated worker')#拒绝
        def 收消息(事件):#挂处理器
            """转发 message 事件。"""
            数据=事件.get('data') if isinstance(事件,dict) else getattr(事件,'data',事件)#载荷
            宿主['handleMessage'](数据)#转发
        加监听('message',收消息)#挂处理器
    宿主['start']()#启动树
