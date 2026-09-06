"""Worker 装配入口：整棵 harness Cordis 树放进一个 dedicated Web Worker。

每个平台对象都经 options 到达——`node:*` 代理表、应用假 `node:http` 捕获的
请求监听器、镜像字节——因此本包从不回伸进组装它的应用。

构造故意拆成两步。创建工作者宿主是同步的，使 worker 能接受消息
并排队 boot 期间到达的请求；工作者宿主.start 再挂载镜像、模块加载器
与树。启动工作者宿主两步都做。

对齐上游 `webworker-runtime/src/worker-host.ts`。公开面仅中文名。
"""
from .node.未实现失败 import 运行时错误#本包错误
import json as _json#清单解析
from .module_system.模块加载器 import 设活动模块加载器,工作线程模块加载器#模块加载器
from .module_system.posix路径 import 目录名,拼接#路径工具
from .node.globals.进程 import 安装进程全局#process全局
from .transport.隧道 import 隧道服务器#隧道服务器
from .storage.镜像gzip import 解压镜像,流式解压镜像#镜像解压
from .storage.内存 import 加载vfs镜像,加载vfs覆盖层,内存vfs#内存VFS
from .storage.活动 import 设活动vfs#活动VFS槽
from .镜像布局 import (#布局常量
    默认根,镜像配置路径,镜像空目录列表,镜像主目录,镜像清单路径,降低版本,
)#镜像布局

__all__=[#仅中文公开名
    '默认根','默认端口','创建工作者宿主','安装日志汇','启动工作者宿主',
]#公开面结束

默认端口=3080#默认报告端口

def 要求全局端口(通道):#解析消息通道
    """解析消息通道；缺省时要求 dedicated worker 作用域。"""
    if 通道 is not None:#显式通道
        return 通道#显式
    作用域=globals()#全局作用域
    投递=作用域.get('postMessage')#postMessage
    if not callable(投递):#非dedicated worker
        raise 运行时错误('webworker host: no channel; pass options.channel outside a dedicated worker')#拒绝
    def 包装投递(消息,转移=None):#包装 postMessage
        """把出站消息交给全局 postMessage。"""
        投递(消息,转移)#投递
    return {'postMessage':包装投递}#包装端口

def 读镜像(镜像):#读取镜像字节
    """读取镜像字节或从 URL 拉取并解压。"""
    if not isinstance(镜像,str):#内存字节
        return 解压镜像(镜像,'the image bytes given to createWorkerHost')#内存字节
    # URL 拉取：Python 侧由宿主注入 fetch；此处要求已是字节或可调用拉取
    raise 运行时错误(f'webworker host: image URL fetch must be provided by the host for {镜像}')#须宿主拉取

def 创建工作者宿主(选项):#创建宿主
    """构建 worker 宿主，不触碰网络或镜像。"""
    根=选项.get('root')#虚拟根
    if 根 is None: 根=默认根#??默认根，空串合法
    配置路径=选项.get('configPath')#配置路径
    if 配置路径 is None: 配置路径=拼接(根,镜像配置路径)#??默认配置路径，空串合法
    端口=选项.get('port') if 选项.get('port') is not None else 默认端口#报告端口
    隧道选项={'port':要求全局端口(选项.get('channel')),'requestListener':选项['requestListener']}#隧道选项
    if 选项.get('privilegedMethods') is not None:#特权方法
        隧道选项['privilegedMethods']=选项['privilegedMethods']#挂上
    if 选项.get('unaryApiLane') is not None:#一元通道
        隧道选项['unaryApiLane']=选项['unaryApiLane']#挂上
    隧道=隧道服务器(隧道选项)#隧道服务器
    槽={'vfs':None,'modules':None,'context':None}#可变槽

    def 启动():#启动过程
        """挂载镜像并启动树。"""
        try:#装配树
            主目录=拼接(根,镜像主目录)#home路径
            环境覆盖=选项.get('env')#调用方环境
            if 环境覆盖 is None: 环境覆盖={}#缺席才空表，空字典合法
            环境={'DSH_HOME':主目录,'HOME':主目录,**dict(环境覆盖)}#环境
            安装进程全局({'cwd':根,'env':环境})#安装process
            字节=读镜像(选项['image'])#基础镜像
            覆盖源=选项.get('overlays')#overlays
            if 覆盖源 is None: 覆盖源=[]#??空列表，空 overlays 合法
            覆盖层列表=[读镜像(层) for 层 in 覆盖源]#overlays
            已挂=加载vfs镜像(字节,根)#挂载基础
            for 层 in 覆盖层列表:#应用overlay
                加载vfs覆盖层(层,根,已挂)#应用
            for 目录 in 镜像空目录列表:#补空目录
                已挂.注水目录(拼接(根,目录.rstrip('/')))#播种目录
            设活动vfs(已挂)#设活动VFS
            槽['vfs']=已挂#保存引用
            清单路径=选项.get('manifestPath')#manifest路径
            if 清单路径 is None: 清单路径=拼接(根,镜像清单路径)#??默认清单路径，空串合法
            要求已降低镜像(已挂,清单路径)#校验降低契约
            静态模块=dict(选项['staticModules'])#可变静态表
            for 键 in ('node:process','process'):#补process工厂
                if 键 not in 静态模块:#缺则补
                    def 读进程():#读全局 process
                        """从全局命名空间取 process。"""
                        return globals()['process'] if 'process' in globals() else None#读全局
                    静态模块[键]=读进程#读全局
            加载器选项={#加载器选项
                'vfs':已挂,'root':根,'staticModules':静态模块,#基础
            }#选项
            if 选项.get('staticModulePrefixes') is not None:#前缀
                加载器选项['staticModulePrefixes']=选项['staticModulePrefixes']#挂上
            if 选项.get('alsCausality') is not None:#ALS
                加载器选项['alsCausality']=选项['alsCausality']#挂上
            加载器=工作线程模块加载器(加载器选项)#模块加载器
            设活动模块加载器(加载器)#设活动加载器
            槽['modules']=加载器#保存引用
            要求=加载器.从目录创建require(目录名(配置路径))#配置旁require
            应用启动=要求('@deepseek-ai/dsh-app-boot')#app-boot面
            命令行=要求('@deepseek-ai/dsh-cmdline')#cmdline面
            补丁结果=启动补丁(加载器,已挂,配置路径,根)#计算补丁
            def 准备(宿主上下文):#准备回调
                """注入加载器与命令行。"""
                宿主上下文['loader']['internal']=加载器.internal#注入内部加载器
                安装日志汇(宿主上下文,要求)#挂日志sink
                参数源=选项.get('cmdlineArgs')#命令行参数
                if 参数源 is None: 参数源=['--host','127.0.0.1','--port',str(端口),'--no-open']#??默认参数，空列表合法
                参数=list(参数源)#参数
                def 假退出(码):#假exit
                    """树请求退出。"""
                    print(f'webworker host: tree requested exit({码})')#警告
                命令行['provideCmdline'](宿主上下文,{'args':参数,'exit':假退出})#提供命令行
            上下文=应用启动['boot']('dsh-webworker',配置路径,补丁结果['patches'],准备)#启动树
            槽['context']=上下文#保存上下文
            连接=上下文['get']('connection')#Connection服务
            if 连接 is None:#缺失
                raise 运行时错误('webworker host: the tree activated without a Connection service')#拒绝
            网关=上下文['get']('typertGateway')#Typert网关
            if 网关 is None:#缺失
                raise 运行时错误('webworker host: the tree activated without a typertGateway service')#拒绝
            处理器=连接['createSharedFetchHandler']('/api')#直连fetch面
            用量=加载器.用量()#模块用量
            预设=补丁结果['presetOverlay']#是否应用preset
            因果='inert' if 选项.get('alsCausality') is None else 'snapshot/restore'#ALS诊断
            print(f"webworker host: tree active (modules={用量['modules']}, data overlays={len(覆盖层列表)}, preset root overlay={'applied' if 预设 else 'already in roster'}, direct lane=connection.createSharedFetchHandler, als causality={因果}, image lowering={降低版本})")#诊断
            def 直连fetch(请求):#直连 fetch
                """把请求交给共享 fetch 处理器。"""
                return 处理器['fetch'](请求)#直连
            def 启动载荷():#boot 载荷
                """读页面引导载荷。"""
                return 读启动载荷(上下文)#boot载荷
            隧道.服务({#开始服务
                'directFetch':直连fetch,#直连fetch
                'bootPayload':启动载荷,#boot载荷
                'openStream':网关['wireStream']['open'],#开流
                'streamFailure':网关['wireStream']['failure'],#流失败
            })#serve结束
        except Exception as 原因:#被模拟树装配体什么都可能抛，收不窄
            隧道.失败(原因)#通知页面
            raise#继续抛出

    def 停止():#停止
        """拆除树。"""
        隧道.失败(Exception('webworker host: the tree was disposed'))#拒绝后续
        上下文=槽['context']#上下文
        if 上下文 is not None:#有树
            上下文['fiber']['dispose']()#拆除树

    def 转发消息(数据):#转发消息
        """把入站载荷交给隧道。"""
        隧道.处理消息(数据)#转发
    def 取vfs():#VFS访问器
        """返回当前 VFS。"""
        return 槽['vfs']#当前VFS
    def 取模块():#加载器访问器
        """返回当前模块加载器。"""
        return 槽['modules']#当前加载器

    return {#宿主句柄
        'handleMessage':转发消息,#转发消息
        'start':启动,#启动
        'stop':停止,#停止
        'vfs':取vfs,#VFS访问器
        'modules':取模块,#加载器访问器
    }#返回结束

def 安装日志汇(上下文,要求):#安装日志sink
    """把树自己的警告与错误送到 worker console。"""
    日志器=要求('@deepseek-ai/cordis')['Logger']#消息渲染器
    def 导出(消息):#导出
        """导出一条。"""
        if 消息.get('type') not in ('warn','error'):#忽略info/debug
            return#忽略
        行=f"{消息['name']}: {日志器['format'](导出器,消息)}"#格式化
        if 消息['type']=='error':#错误
            print(行)#错误
        else:#警告
            print(行)#警告
    导出器={'colors':False,'levels':{'default':2},'export':导出}#导出器
    上下文['logger']['exporter'](导出器)#挂载

def 要求已降低镜像(文件系统,路径):#校验降低契约
    """要求已挂载镜像携带本构建能包装的体。"""
    if not 文件系统.存在同步(路径):#manifest缺失
        raise 运行时错误(f'webworker host: {路径} is missing, so the image records no lowering; rebuild the image')#拒绝
    已解析=_json.loads(文件系统.读取文件同步(路径,'utf8'))#解析JSON
    if not isinstance(已解析,dict):#非对象
        raise 运行时错误(f'webworker host: {路径} does not hold an object')#拒绝
    已降低=已解析.get('lowered')#契约字段
    if 已降低!=降低版本:#版本不匹配
        raise 运行时错误(f'webworker host: image was lowered by {已降低}, this build runs {降低版本}; rebuild the image')#拒绝

def 启动补丁(加载器,文件系统,配置路径,根):#计算补丁
    """已交付的 preset 根，由拥有组合的应用层供给。"""
    文本=文件系统.读取文件同步(配置路径,'utf8')#配置文本
    if 配置路径.endswith('.json'):#JSON配置
        行列表=_json.loads(文本)#解析JSON
    else:#YAML配置
        包含=加载器.加载(加载器.解析('@deepseek-ai/cordis-plugin-include',根))#Include schema
        yaml=加载器.加载(加载器.解析('js-yaml',根))#YAML加载器
        行列表=yaml['load'](文本,{'schema':包含['entryListSchema']})#按方言加载
    def 查找(条目列表,标识):#按id查找
        """递归按 id 查找。"""
        if not isinstance(条目列表,list):#非数组
            return None#未找到
        for 条目 in 条目列表:#逐行
            if isinstance(条目,dict) and 'id' in 条目 and 条目['id']==标识:#命中
                return 条目#命中
            嵌套=查找(条目['config'] if isinstance(条目,dict) and 'config' in 条目 else None,标识)#递归
            if 嵌套 is not None:#命中嵌套
                return 嵌套#命中
        return None#未找到
    def 配置于(行):#取config对象
        """取 config 对象。"""
        配置=行.get('config')#已有
        if isinstance(配置,dict) and not isinstance(配置,list):#合法对象
            return 配置#已有config
        return {}#空对象
    补丁列表=[]#补丁列表
    预设覆盖=False#是否补preset根
    预设=查找(行列表,'agent-presets')#presets行
    if 预设 is not None and 配置于(预设).get('roots') is None:#缺roots
        预设覆盖=True#标记已应用
        补丁列表.append({#追加preset根
            'id':'agent-presets',#目标id
            'config':{**配置于(预设),'roots':[{'path':拼接(根,'config/agent-presets'),'trust':'system'}]},#合并roots
        })#push结束
    jsonl=查找(行列表,'session-persistence-jsonl')#jsonl行
    if jsonl is not None:#存在则强制无压缩
        补丁列表.append({'id':'session-persistence-jsonl','config':{**配置于(jsonl),'compression':'none'}})#明文补丁
    return {'patches':补丁列表,'presetOverlay':预设覆盖}#返回

def 读启动载荷(上下文):#读boot载荷
    """组装页面 Cordis 前引导所需的载荷。"""
    网页服务=上下文['get']('webServer')#webServer服务
    if 网页服务 is None:#缺失
        raise 运行时错误('webworker host: no webServer service, so the page cannot receive its boot injections')#拒绝
    return {'injections':网页服务['collectIndexInjections']()}#收集注入表

def 启动工作者宿主(选项):#一步启动
    """安装消息处理器并启动树。"""
    宿主=创建工作者宿主(选项)#创建宿主
    if 选项.get('channel') is None:#默认消息源
        作用域=globals()#全局
        加监听=作用域.get('addEventListener')#监听器API
        if not callable(加监听):#无监听器API
            raise 运行时错误('webworker host: no message source; pass options.channel outside a dedicated worker')#拒绝
        def 收消息(事件):#挂处理器
            """转发 Worker MessageEvent。"""
            宿主['handleMessage'](事件.data)#对象载荷
        加监听('message',收消息)#挂处理器
    宿主['start']()#启动树
