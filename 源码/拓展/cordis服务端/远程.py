'向 typert 注册动态 Cordis 宿主运行器的远程贡献'
from ...类型化远程调用.协议 import 严格编解码,调用描述符,远程贡献#制品辅助

__all__=['默认','远程贡献表']#仅中文公开名；TYPERT_REMOTE 为 typert 框架槽不入表

智能体参数={#agent lookup
    'name':'agent','wire':'agent','source':'lookup','lookup':'agent',
    'codec':严格编解码('Agent'),
}#结束
作用域={'context':'agent','wire':'agent'}#agent scope
包名='@deepseek-ai/dsh-cordis-host-runner'
服务='dynamicCordisRunner'#服务键
命名空间='dynamicCordisRunner'#命名空间
类前=包名+'#DynamicCordisRunnerService.'#调用 id 前缀

def 参数(名称,类型符号):#json 参数
    '一条 json 线路参数'
    return {'name':名称,'wire':名称,'source':'json','codec':严格编解码(类型符号)}

远程贡献表=远程贡献(包名,[#贡献
    调用描述符(类前+'undefineFromPanel',服务,命名空间,'undefineFromPanel',
        [智能体参数,参数('pluginId','CordisDynamicPluginId')],
        严格编解码('DynamicCordisUndefineReceipt'),{'file':'src/index.ts','line':231,'column':3},
        作用域=作用域),
    调用描述符(类前+'runHostHalf',服务,命名空间,'runHostHalf',
        [智能体参数,
         参数('pluginId','CordisDynamicPluginId'),
         参数('packageId','CordisDynamicPackageId'),
         参数('mode','CordisDynamicRunMode'),
         参数('requestId','ApprovalRequestId | null'),
         参数('approveFutureVersions','boolean')],
        严格编解码('DynamicCordisHostHalfResult'),{'file':'src/index.ts','line':329,'column':3},
        作用域=作用域),
    调用描述符(类前+'getClientCode',服务,命名空间,'getClientCode',
        [智能体参数,
         参数('pluginId','CordisDynamicPluginId'),
         参数('pluginRunId','CordisDynamicPluginRunId')],
        严格编解码('DynamicCordisClientSource'),{'file':'src/index.ts','line':388,'column':3},
        作用域=作用域),
    调用描述符(类前+'resolveRequestRun',服务,命名空间,'resolveRequestRun',
        [参数('requestId','ApprovalRequestId'),参数('resolution','DynamicCordisRunResolution')],
        严格编解码('DynamicCordisResolveAck'),{'file':'src/index.ts','line':417,'column':3}),
    调用描述符(类前+'settleUserRun',服务,命名空间,'settleUserRun',
        [智能体参数,参数('pluginId','CordisDynamicPluginId'),参数('resolution','DynamicCordisRunResolution')],
        严格编解码('DynamicCordisRunResponse'),{'file':'src/index.ts','line':442,'column':3},
        作用域=作用域),
    调用描述符(类前+'stopFromPanel',服务,命名空间,'stopFromPanel',
        [智能体参数,参数('pluginId','CordisDynamicPluginId')],
        严格编解码('DynamicCordisStopResponse'),{'file':'src/index.ts','line':484,'column':3},
        作用域=作用域),
    调用描述符(类前+'syncInspectManifest',服务,命名空间,'syncInspectManifest',
        [参数('providers','CordisInspectProviderManifest[]')],
        严格编解码('null'),{'file':'src/index.ts','line':502,'column':3}),
    调用描述符(类前+'resolveInspectQuery',服务,命名空间,'resolveInspectQuery',
        [智能体参数,
         参数('requestId','CordisInspectRequestId'),
         参数('resolution','CordisInspectQueryResolution')],
        严格编解码('CordisInspectResolveAck'),{'file':'src/index.ts','line':515,'column':3},
        作用域=作用域),
    调用描述符(类前+'inventory',服务,命名空间,'inventory',
        [],严格编解码('DynamicCordisInventoryRow[]'),{'file':'src/index.ts','line':529,'column':3}),
    调用描述符(类前+'reportRenderFailure',服务,命名空间,'reportRenderFailure',
        [智能体参数,
         参数('pluginId','CordisDynamicPluginId'),
         参数('pluginRunId','CordisDynamicPluginRunId'),
         参数('failure','DynamicCordisRenderFailure')],
        严格编解码('null'),{'file':'src/index.ts','line':688,'column':3},
        作用域=作用域),
    调用描述符(类前+'reportClientGuardFailure',服务,命名空间,'reportClientGuardFailure',
        [智能体参数,
         参数('pluginId','CordisDynamicPluginId'),
         参数('pluginRunId','CordisDynamicPluginRunId'),
         参数('failure','CordisErrorDetails')],
        严格编解码('null'),{'file':'src/index.ts','line':722,'column':3},
        作用域=作用域),
    调用描述符(类前+'invoke',服务,命名空间,'invoke',
        [参数('pluginId','CordisDynamicPluginId'),
         参数('pluginRunId','CordisDynamicPluginRunId'),
         参数('method','string'),
         参数('args','JsonValue')],
        严格编解码('DynamicCordisInvokeResult'),{'file':'src/index.ts','line':745,'column':3}),
])#结束
默认=远程贡献表
TYPERT_REMOTE=远程贡献表#typert框架槽
