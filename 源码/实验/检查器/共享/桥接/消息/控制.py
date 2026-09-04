"""Host 到 Worker 的生命周期消息与 Worker 就绪结果。

对齐上游 `shared/bridge/messages/control.ts`。公开面仅中文名。
"""
__all__=[#仅中文公开名
    '检查器工作者配置','检查器工作者启动','检查器工作者关闭','检查器宿主控制',
    '检查器工作者就绪','检查器工作者失败','检查器工作者已停止','检查器工作者控制',
    '检查器客户端引导',
]#公开面结束

class 检查器工作者配置:#Worker配置
    """完全解析后的 Worker 配置。"""
    def __init__(自身,host,startPort,targetId,clientToken,clientOrigins,maxSourceFrameBytes,maxSourceRecordsPerFrame,maxRetainedRequests,maxJournalBytes,clientRuntimeTimeoutMs,maxClientSourceBytes,maxCordisNodes,maxDisconnectedCordisTrees):#构造
        """保存 Worker 配置字段。"""
        自身.host=host#绑定主机
        自身.startPort=startPort#首选端口
        自身.targetId=targetId#目标标识
        自身.clientToken=clientToken#Client令牌
        自身.clientOrigins=tuple(clientOrigins)#允许的来源
        自身.maxSourceFrameBytes=maxSourceFrameBytes#源帧最大字节
        自身.maxSourceRecordsPerFrame=maxSourceRecordsPerFrame#每帧最大记录数
        自身.maxRetainedRequests=maxRetainedRequests#最大保留请求数
        自身.maxJournalBytes=maxJournalBytes#日志最大字节
        自身.clientRuntimeTimeoutMs=clientRuntimeTimeoutMs#Client Runtime超时
        自身.maxClientSourceBytes=maxClientSourceBytes#Client源最大字节
        自身.maxCordisNodes=maxCordisNodes#Cordis最大节点数
        自身.maxDisconnectedCordisTrees=maxDisconnectedCordisTrees#断开树保留上限

class 检查器工作者启动:#Worker启动载荷
    """用于启动 Inspector Worker 的结构化克隆载荷。"""
    def __init__(自身,config,hostSourcePort):#构造
        """保存启动载荷。"""
        自身.config=config#已解析配置
        自身.hostSourcePort=hostSourcePort#Host源端口

def 检查器工作者关闭():#关闭命令
    """Host 请求停止接受流量并关闭 Worker 拥有的全部资源。"""
    return {'type':'shutdown'}#关闭命令

检查器宿主控制=dict#Host控制联合

def 检查器工作者就绪(host,port,targetId):#就绪事件
    """Worker 端点就绪。"""
    return {'type':'ready','host':host,'port':port,'targetId':targetId}#就绪

def 检查器工作者失败(message):#失败事件
    """Worker 启动或运行时失败。"""
    return {'type':'failure','message':message}#失败

def 检查器工作者已停止():#已停止事件
    """Worker 完成优雅关闭。"""
    return {'type':'stopped'}#停止

检查器工作者控制=dict#Worker控制联合

class 检查器客户端引导:#Client引导
    """由 Host 插件注入的浏览器引导数据。"""
    def __init__(自身,endpoint,protocol,maxQueuedRecords,maxQueuedBytes,maxRecordsPerFrame,maxFrameBytes,reconnectBaseMs,reconnectMaxMs,queryTimeoutMs,maxRuntimeObjectsPerSession,maxRuntimePropertiesPerResult,maxClientSourceBytes,maxCordisNodes):#构造
        """保存 Client 引导字段。"""
        自身.endpoint=endpoint#WebSocket端点
        自身.protocol=protocol#子协议名
        自身.maxQueuedRecords=maxQueuedRecords#最大排队记录
        自身.maxQueuedBytes=maxQueuedBytes#最大排队字节
        自身.maxRecordsPerFrame=maxRecordsPerFrame#每帧最大记录
        自身.maxFrameBytes=maxFrameBytes#每帧最大字节
        自身.reconnectBaseMs=reconnectBaseMs#重连基础毫秒
        自身.reconnectMaxMs=reconnectMaxMs#重连最大毫秒
        自身.queryTimeoutMs=queryTimeoutMs#查询超时
        自身.maxRuntimeObjectsPerSession=maxRuntimeObjectsPerSession#每会话最大Runtime对象
        自身.maxRuntimePropertiesPerResult=maxRuntimePropertiesPerResult#每结果最大属性数
        自身.maxClientSourceBytes=maxClientSourceBytes#Client源最大字节
        自身.maxCordisNodes=maxCordisNodes#Cordis最大节点数
