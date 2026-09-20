from .node.未实现失败 import 运行时错误
from .module_system.模块加载器 import 设活动模块加载器,工作线程模块加载器
from .module_system.posix路径 import 拼接
from .transport.隧道 import 隧道服务器
from .storage.镜像gzip import 解压镜像,流式解压镜像
from .storage.内存 import 加载vfs镜像,加载vfs覆盖层
from .storage.活动 import 设活动vfs
from .镜像布局 import (
    默认根,镜像配置路径,镜像空目录列表,镜像清单路径,降低版本,
)
import json

__all__=['默认根','默认端口','创建工作线程宿主','安装日志汇','启动工作线程宿主']

默认端口=3080

def 要求全局端口(通道):
    """解析消息通道；缺省用全局 postMessage。"""
    if 通道 is not None:
        return 通道
    作用域=globals()
    if 'postMessage' not in 作用域 or not callable(作用域['postMessage']):
        raise 运行时错误('webworker host: 没有通道；专用 worker 之外请传 options.channel')
    发送=作用域['postMessage']
    def 包装发送(消息,转移=None):
        """调用全局 postMessage。"""
        发送(消息,转移)
    return {'postMessage':包装发送}

def 读镜像(镜像):
    """读取镜像字节：内存则解压，URL 则拉取后流式解压。"""
    if not isinstance(镜像,str):
        return 解压镜像(镜像,'the image bytes given to createWorkerHost')
    if 'fetch' not in globals() or not callable(globals()['fetch']):
        raise 运行时错误(f'webworker host: image fetch unavailable for {镜像}')
    响应=globals()['fetch'](镜像)
    if not 响应.ok:
        raise 运行时错误(f'webworker host: image fetch failed with {响应.status} for {镜像}')
    正文=响应.body
    if 正文 is None:
        取缓冲=响应.arrayBuffer
        if callable(取缓冲):
            return 解压镜像(取缓冲(),镜像)
        raise 运行时错误(f'webworker host: image response for {镜像} carried no body')
    return 流式解压镜像(正文,镜像)

def 要求已降低镜像(文件系统,路径):
    """要求已挂载镜像携带本构建能包装的体。"""
    if not 文件系统.存在同步(路径):
        raise 运行时错误(f'webworker host: {路径} is missing, so the image records no lowering; rebuild the image')
    解析值=json.loads(文件系统.读取文件同步(路径,'utf8'))
    if not isinstance(解析值,dict):
        raise 运行时错误(f'webworker host: {路径} does not hold an object')
    降低=解析值['lowered'] if 'lowered' in 解析值 else None
    if 降低!=降低版本:
        raise 运行时错误(f'webworker host: image was lowered by {降低}, this build runs {降低版本}; rebuild the image')

def 启动补丁(加载器,文件系统,配置路径,根):
    """已交付的 preset 根 overlay 与明文 jsonl 补丁。"""
    文本=文件系统.读取文件同步(配置路径,'utf8')
    if 配置路径.endswith('.json'):
        行列表=json.loads(文本)
    else:
        #YAML 由镜像加载器方言读；本批次不内嵌 js-yaml，空行表则无补丁
        行列表=[]
    def 查找(条目列表,标识):
        """递归查找配置行。"""
        if not isinstance(条目列表,list):
            return None
        for 条目 in 条目列表:
            if not isinstance(条目,dict):
                continue
            if 'id' in 条目 and 条目['id']==标识:
                return 条目
            嵌套=查找(条目['config'] if 'config' in 条目 else None,标识)
            if 嵌套 is not None:
                return 嵌套
        return None
    def 取配置(行):
        """取合法 config 对象。"""
        配置=行['config'] if 'config' in 行 else None
        if isinstance(配置,dict):
            return 配置
        return {}
    补丁列表=[]
    预设覆盖=False
    预设=查找(行列表,'agent-presets')
    if 预设 is not None and 'roots' not in 取配置(预设):
        预设覆盖=True
        补丁列表.append({
            'id':'agent-presets',
            'config':{**取配置(预设),'roots':[{'path':拼接(根,'config/agent-presets'),'trust':'system'}]},
        })
    jsonl=查找(行列表,'session-persistence-jsonl')
    if jsonl is not None:#存在则强制无压缩
        补丁列表.append({'id':'session-persistence-jsonl','config':{**取配置(jsonl),'compression':'none'}})
    return {'patches':补丁列表,'presetOverlay':预设覆盖}

def 读boot载荷(上下文):
    """组装页面 Cordis 前引导所需的载荷。"""
    web服务器=上下文['get']('webServer')
    if web服务器 is None:
        raise 运行时错误('webworker host: 没有 webServer 服务，页面收不到 boot 依赖')
    return {'injections':web服务器['collectIndexInjections']()}

def 安装日志汇(上下文,要求):
    """把树自己的警告与错误送到 worker console。"""
    cordis=要求('@deepseek-ai/cordis')
    渲染器=cordis['Logger']
    def 导出(消息):
        """仅警告与错误。"""
        类型=消息['type']
        if 类型 not in ('warn','error'):
            return
        名=消息['name'] if 'name' in 消息 else ''
        行=f"{名}: {渲染器['format'](导出器,消息)}"
        print(行)
    导出器={'colors':False,'levels':{'default':2},'export':导出}
    上下文['logger']['exporter'](导出器)

def 创建工作线程宿主(选项):
    """构建 worker 宿主，不触碰网络或镜像。"""
    if 'root' not in 选项: 根=默认根#??默认根，空串合法
    else: 根=选项['root']
    if 'configPath' not in 选项: 配置路径=拼接(根,镜像配置路径)#??默认配置路径，空串合法
    else: 配置路径=选项['configPath']
    通道=选项['channel'] if 'channel' in 选项 else None
    隧道选项={'port':要求全局端口(通道),'requestListener':选项['requestListener']}
    if 'privilegedMethods' in 选项 and 选项['privilegedMethods'] is not None:
        隧道选项['privilegedMethods']=选项['privilegedMethods']
    if 'unaryApiLane' in 选项 and 选项['unaryApiLane'] is not None:
        隧道选项['unaryApiLane']=选项['unaryApiLane']
    隧道=隧道服务器(隧道选项)
    状态={'vfs':None,'modules':None,'context':None}

    def 启动():
        """挂载镜像并启动树。"""
        try:
            字节=读镜像(选项['image'])
            if 'overlays' not in 选项: 覆盖源=[]#??空列表，空 overlays 合法
            else: 覆盖源=选项['overlays']
            覆盖层列表=[读镜像(层) for 层 in 覆盖源]
            已挂=加载vfs镜像(字节,根)
            for 覆盖 in 覆盖层列表:
                加载vfs覆盖层(覆盖,根,已挂)
            for 目录 in 镜像空目录列表:
                已挂.注水目录(拼接(根,目录.rstrip('/')))
            设活动vfs(已挂)
            状态['vfs']=已挂
            if 'manifestPath' not in 选项: 清单路径=拼接(根,镜像清单路径)#??默认清单路径，空串合法
            else: 清单路径=选项['manifestPath']
            要求已降低镜像(已挂,清单路径)
            静态模块=dict(选项['staticModules'])
            for 键 in ('node:process','process'):
                if 键 not in 静态模块:
                    def 读process():
                        """读取已安装全局。"""
                        return globals()['process'] if 'process' in globals() else None
                    静态模块[键]=读process
            加载器选项={'vfs':已挂,'root':根,'staticModules':静态模块}
            if 'staticModulePrefixes' in 选项 and 选项['staticModulePrefixes'] is not None:
                加载器选项['staticModulePrefixes']=选项['staticModulePrefixes']
            if 'alsCausality' in 选项 and 选项['alsCausality'] is not None:
                加载器选项['alsCausality']=选项['alsCausality']
            加载器=工作线程模块加载器(加载器选项)
            设活动模块加载器(加载器)
            状态['modules']=加载器
            补丁结果=启动补丁(加载器,已挂,配置路径,根)
            用量=加载器.用量()
            print(f"webworker host: tree active (modules={用量['modules']}, data overlays={len(覆盖层列表)}, "
                  f"preset root overlay={'applied' if 补丁结果['presetOverlay'] else 'already in roster'}, "
                  f"direct lane=connection.createSharedFetchHandler, "
                  f"als causality={'inert' if 'alsCausality' not in 选项 else 'snapshot/restore'}, "
                  f"image lowering={降低版本})")
            def 直达fetch(请求):
                """树未接线时拒绝。"""
                raise 运行时错误('webworker host: 本 Python 批次里树尚未完全接线')
            def boot载荷():
                """读 boot 载荷；无上下文则空依赖表。"""
                if 状态['context'] is None:
                    return {'injections':[]}
                return 读boot载荷(状态['context'])
            def 开流(端点,载荷,信号):
                """树未接线时空迭代。"""
                return iter(())
            def 流失败(错误):
                """稳定失败字段。"""
                return {'code':'carrier','message':str(错误),'details':{}}
            隧道.服务({
                'directFetch':直达fetch,
                'bootPayload':boot载荷,
                'openStream':开流,
                'streamFailure':流失败,
            })
        except Exception as 原因:#被模拟树装配体什么都可能抛，收不窄
            隧道.失败(原因)
            raise

    def 处理消息(数据):
        """喂入一条 postMessage 载荷。"""
        隧道.处理消息(数据)

    def 停止():
        """拆除树；之后隧道继续拒绝。"""
        隧道.失败(Exception('webworker host: the tree was disposed'))
        上下文=状态['context']
        if 上下文 is not None:
            上下文['fiber']['dispose']()

    def 取vfs():
        """返回当前 VFS。"""
        return 状态['vfs']
    def 取模块():
        """返回当前模块加载器。"""
        return 状态['modules']

    return {
        'handleMessage':处理消息,
        'start':启动,
        'stop':停止,
        'vfs':取vfs,
        'modules':取模块,
    }

def 启动工作线程宿主(选项):
    """安装消息处理器并启动树。"""
    宿主=创建工作线程宿主(选项)
    if 'channel' not in 选项:
        作用域=globals()
        if 'addEventListener' not in 作用域 or not callable(作用域['addEventListener']):
            raise 运行时错误('webworker host: 没有消息源；专用 worker 之外请传 options.channel')
        def 收消息(事件):
            """转发 message 事件。"""
            宿主['handleMessage'](事件.data)#MessageEvent 对象载荷
        作用域['addEventListener']('message',收消息)
    宿主['start']()
