from .宿主.插件 import 应用 as 应用宿主,解析检查器选项,启动检查器

__all__=[
    '名称','依赖','配置','应用','解析检查器选项','启动检查器',
]

名称='experimental-inspector'
依赖=['webServer']

库默认=解析检查器选项()

配置={
    'host':'127.0.0.1',
    'port':9230,
    'clientOrigins':[],
    'captureFetch':True,
    'maxRequestBodyBytes':库默认.maxRequestBodyBytes,
    'maxResponseBodyBytes':库默认.maxResponseBodyBytes,
    'maxBodyChunkBytes':库默认.maxBodyChunkBytes,
    'maxJournalBytes':库默认.maxJournalBytes,
    'maxRetainedRequests':库默认.maxRetainedRequests,
    'maxSourceFrameBytes':库默认.maxSourceFrameBytes,
    'maxSourceRecordsPerFrame':库默认.maxSourceRecordsPerFrame,
    'maxQueuedRecords':库默认.maxQueuedRecords,
    'maxQueuedBytes':库默认.maxQueuedBytes,
    'startupTimeoutMs':库默认.startupTimeoutMs,
    'stopTimeoutMs':库默认.stopTimeoutMs,
    'clientReconnectBaseMs':库默认.clientReconnectBaseMs,
    'clientReconnectMaxMs':库默认.clientReconnectMaxMs,
    'clientRuntimeTimeoutMs':库默认.clientRuntimeTimeoutMs,
    'queryTimeoutMs':库默认.queryTimeoutMs,
    'maxClientRuntimeObjects':库默认.maxClientRuntimeObjects,
    'maxClientRuntimeProperties':库默认.maxClientRuntimeProperties,
    'maxClientSourceBytes':库默认.maxClientSourceBytes,
    'maxCordisNodes':库默认.maxCordisNodes,
    'maxDisconnectedCordisTrees':库默认.maxDisconnectedCordisTrees,
}

def 应用(上下文,配置对象=None):
    """从仓库标准包入口应用 Host 实现。"""
    应用宿主(上下文,配置对象 if 配置对象 is not None else 配置)

name=名称
inject=依赖
apply=应用
Config=配置
