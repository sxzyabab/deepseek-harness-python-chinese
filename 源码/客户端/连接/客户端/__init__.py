"""浏览器线客户端。插件选择 fixture 或 HTTP 传输，提供共享 API 客户端，
并让运行时对象层带着自己的汇启动流控制器。

对齐上游 `connection/src/client/index.ts`。公开面仅中文名。
"""
from urllib.parse import parse_qs,urlparse#读查询
from ..回环主机名 import 是否回环主机名#回环主机名判定
from .接口 import (#再导出浏览器可用的网关通道与核心类型辅助
    传输错误,
    会话搜索结果上限,
    抽象接口客户端,
    结果槽,
    Rpc标识,
)#来自本包接口模块
from .连接 import 连接控制器#连接控制器
from .网页接口客户端 import 网页接口客户端#真实 HTTP API 客户端
from .rpc import 创建网页连接rpc#浏览器 RPC 工厂

__all__=[#仅中文公开名
    '注入',
    '应用',
    '连接句柄',
    '宿主描述源',
    '结果槽',
    '抽象接口客户端',
    'Rpc标识',
    '会话搜索结果上限',
    '传输错误',
    '连接控制器',
    '网页接口客户端',
    '创建网页连接rpc',
    'inject',
    'apply',
]#公开面结束

注入=[]#无依赖
inject=注入#上游名

class 宿主描述源:#宿主描述源
    """每次完成的连接握手所发布的可观察宿主描述。"""

    def __init__(自身,取快照,订阅):#绑定闭包
        """登记取快照与订阅。"""
        自身.getSnapshot=取快照#当前快照
        自身.subscribe=订阅#订阅，返回取消函数

class 连接句柄:#浏览器连接句柄
    """`ctx.connection` 服务 API：API 客户端加上一次性控制器启动器。"""

    def __init__(自身,接口,是否回环,宿主描述,rpc,启动函数):#组装
        """只读字段 + start。"""
        自身.api=接口#共享 API 客户端
        自身.isLoopback=是否回环#是否回环
        自身.hostDescription=宿主描述#宿主描述源
        自身.rpc=rpc#客户端 RPC
        自身.start=启动函数#启动循环

def 取页面定位():#读全局 location
    """非浏览器则无。"""
    try:#取 location
        import builtins#全局
        return getattr(builtins,'location',None)#可能缺
    except Exception:#无
        return None#无

def 应用(上下文):#安装浏览器连接插件
    """按页面模式挑选 API，并提供 `ctx.connection`。"""
    页面=取页面定位()#非浏览器则无 location
    用夹具=False#默认真载体
    if 页面 is not None:#有页面
        查询=getattr(页面,'search','') or ''#查询串
        if 查询.startswith('?'):#带问号
            查询=查询[1:]#去掉
        参数=parse_qs(查询)#解析
        用夹具='fixture' in 参数#URL 带 fixture 则用夹具
    夹具客户端=None#夹具或无
    if 用夹具:#需要夹具
        from .夹具 import 夹具接口客户端#延迟导入夹具
        夹具客户端=夹具接口客户端()#造
    接口=夹具客户端 if 夹具客户端 is not None else 网页接口客户端()#夹具优先，否则真实 HTTP
    rpc=getattr(夹具客户端,'rpc',None) if 夹具客户端 is not None else 创建网页连接rpc()#夹具自带 RPC，否则 web RPC
    已启动={'v':False}#流循环是否已被某个消费者占用
    描述={'v':None}#当前世代的宿主描述
    监听们=set()#描述订阅者

    def 发布描述(下一个):#发布或收回描述
        """同一引用则跳过。"""
        if 描述['v'] is 下一个:#同一引用
            return#跳过
        描述['v']=下一个#替换快照
        for 监听 in list(监听们):#快照后逐个通知
            try:#监听器抛错不得打断其余
                监听()#通知
            except Exception as 错误:#只记日志
                print('[web-runtime] host-description listener threw:',错误)#诊断

    def 取快照():#读当前快照
        """最近一次已连接世代的描述。"""
        return 描述['v']#快照

    def 订阅(监听器):#登记监听器
        """返回取消函数。"""
        监听们.add(监听器)#加入集
        def 取消():#退订
            """从集删除。"""
            监听们.discard(监听器)#删
        return 取消#取消器

    def 启动(汇,配置=None):#启动循环，只能一次
        """第二次占用抛错。"""
        if 已启动['v']:#已占用
            raise Exception('connection: the stream loop is already owned by another consumer')#第二次占用失败
        已启动['v']=True#标记已占用
        def 已连接(下一个):#握手完成
            """先发布描述再转发。"""
            发布描述(下一个)#先发布描述
            if 描述['v'] is not 下一个:#已被收回则不再转发
                return#停
            函=汇.get('onConnected') if isinstance(汇,dict) else getattr(汇,'onConnected',None)#消费者
            if callable(函):#有
                函(下一个)#转发
        def 状态变化(状态):#粗粒度状态
            """重连则收回描述。"""
            if 状态=='reconnecting':#重连
                发布描述(None)#收回
            函=汇.get('onStateChange') if isinstance(汇,dict) else getattr(汇,'onStateChange',None)#消费者
            if callable(函):#有
                函(状态)#转发
        包装汇=dict(汇) if isinstance(汇,dict) else {#包一层汇
            'onMuxEnvelope':getattr(汇,'onMuxEnvelope',None),#mux
            'onHostEnvelope':getattr(汇,'onHostEnvelope',None),#host
        }#结束抄
        包装汇['onConnected']=已连接#覆盖
        包装汇['onStateChange']=状态变化#覆盖
        控制器=连接控制器(接口,包装汇,配置 or {})#造控制器
        控制器.启动()#开始泵
        def 停止():#停止循环
            """abort 当前世代并收回描述。"""
            控制器.停止()#abort
            发布描述(None)#收回
        return type('停止句柄',(),{'stop':staticmethod(停止)})()#停止句柄

    主机名=''#默认
    if 页面 is not None:#有页面
        主机名=getattr(页面,'hostname',None) or urlparse(getattr(页面,'href','')).hostname or ''#主机名
    是否回环=页面 is None or 是否回环主机名(主机名)#无页面或主机名是回环
    句柄=连接句柄(#组装服务句柄
        接口,#共享 API
        是否回环,#回环
        宿主描述源(取快照,订阅),#描述源
        rpc,#逻辑 RPC
        启动,#启动器
    )#结束句柄
    上下文.provide('connection',句柄)#提供 ctx.connection

apply=应用#上游名
