"""面向仓库的 Host 包入口，覆盖镜像实现树。

对齐上游 `index.ts`。公开面仅中文名。
"""
from .宿主.插件 import 应用 as 应用宿主,解析检查器选项,启动检查器#Host插件面

__all__=[#仅中文公开名
    '名称','注入','配置','应用','解析检查器选项','启动检查器',
]#公开面结束

名称='experimental-inspector'#插件名
注入=['webServer']#Host依赖webServer

库默认=解析检查器选项()#库默认选项

def 取默认(键,回退=None):#取库默认字段
    """取库默认字段。"""
    if hasattr(库默认,键):#对象
        return getattr(库默认,键)#属性
    if isinstance(库默认,dict):#字典
        return 库默认.get(键,回退)#键
    return 回退#回退

配置={#Host插件配置默认（对齐 Config schema）
    'host':'127.0.0.1',#监听主机
    'port':9230,#起始端口
    'clientOrigins':[],#额外origin
    'captureFetch':True,#是否采集fetch
    'maxRequestBodyBytes':取默认('maxRequestBodyBytes'),#请求体上限
    'maxResponseBodyBytes':取默认('maxResponseBodyBytes'),#响应体上限
    'maxBodyChunkBytes':取默认('maxBodyChunkBytes'),#分块上限
    'maxJournalBytes':取默认('maxJournalBytes'),#日志总字节
    'maxRetainedRequests':取默认('maxRetainedRequests'),#保留请求数
    'maxSourceFrameBytes':取默认('maxSourceFrameBytes'),#帧字节上限
    'maxSourceRecordsPerFrame':取默认('maxSourceRecordsPerFrame'),#每帧记录数
    'maxQueuedRecords':取默认('maxQueuedRecords'),#队列记录上限
    'maxQueuedBytes':取默认('maxQueuedBytes'),#队列字节上限
    'startupTimeoutMs':取默认('startupTimeoutMs'),#启动超时
    'stopTimeoutMs':取默认('stopTimeoutMs'),#停止超时
    'clientReconnectBaseMs':取默认('clientReconnectBaseMs'),#重连基数
    'clientReconnectMaxMs':取默认('clientReconnectMaxMs'),#重连上限
    'clientRuntimeTimeoutMs':取默认('clientRuntimeTimeoutMs'),#Client运行时超时
    'queryTimeoutMs':取默认('queryTimeoutMs'),#查询超时
    'maxClientRuntimeObjects':取默认('maxClientRuntimeObjects'),#Client对象上限
    'maxClientRuntimeProperties':取默认('maxClientRuntimeProperties'),#属性上限
    'maxClientSourceBytes':取默认('maxClientSourceBytes'),#源字节上限
    'maxCordisNodes':取默认('maxCordisNodes'),#Cordis节点上限
    'maxDisconnectedCordisTrees':取默认('maxDisconnectedCordisTrees'),#断联树上限
}#配置结束

def 应用(上下文,配置对象=None):#应用Host插件
    """从仓库标准包入口应用 Host 实现。"""
    应用宿主(上下文,配置对象 if 配置对象 is not None else 配置)#委托Host

apply=应用#Cordis入口别名
Config=配置#Cordis配置别名
resolveInspectorOptions=解析检查器选项#Cordis选项别名
startInspector=启动检查器#Cordis启动别名
