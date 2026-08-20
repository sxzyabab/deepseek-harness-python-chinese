"""动态包运行器 Host-for-Client Remote 贡献（对齐上游 `./remote`）。

对照本包已挂 `@远程` 的导出名（与 `远程方法目录` 对齐）。
服务键/命名空间为 `dynamicCordisRunner`（与宿主 `远程服务` 登记名一致）。
"""
from typert.protocol import 严格编解码,调用描述符,远程贡献#制品辅助

__all__=['TYPERT_REMOTE','默认','远程贡献对象']#公开面

智能体参数={#agent lookup
    'name':'agent','wire':'agent','source':'lookup','lookup':'agent',
    'codec':严格编解码('Agent'),
}#结束
作用域={'context':'agent','wire':'agent'}#agent scope
包名='@deepseek-ai/dsh-cordis-host-runner'#上游包名
服务='dynamicCordisRunner'#服务键
命名空间='dynamicCordisRunner'#命名空间

面板取消定义=调用描述符(#undefineFromPanel
    包名+'#DynamicCordisRunnerService.undefineFromPanel',服务,命名空间,'undefineFromPanel',
    [智能体参数,{'name':'pluginId','wire':'pluginId','source':'json','codec':严格编解码('CordisDynamicPluginId')}],
    严格编解码('DynamicCordisUndefineReceipt'),
    {'file':'src/index.ts','line':0,'column':3},作用域=作用域,实现='面板取消定义',
)#结束

运行宿主半=调用描述符(#runHostHalf
    包名+'#DynamicCordisRunnerService.runHostHalf',服务,命名空间,'runHostHalf',
    [
        智能体参数,
        {'name':'pluginId','wire':'pluginId','source':'json','codec':严格编解码('CordisDynamicPluginId')},
        {'name':'packageId','wire':'packageId','source':'json','codec':严格编解码('CordisDynamicPackageId')},
        {'name':'mode','wire':'mode','source':'json','codec':严格编解码('CordisDynamicRunMode')},
        {'name':'requestId','wire':'requestId','source':'json','codec':严格编解码('ApprovalRequestId | undefined'),'acceptsUndefined':True},
        {'name':'approveSubsequentVersions','wire':'approveSubsequentVersions','source':'json','codec':严格编解码('boolean')},
    ],
    严格编解码('DynamicCordisHostHalfResult'),
    {'file':'src/index.ts','line':0,'column':3},作用域=作用域,实现='运行宿主半',
)#结束

取客户端代码=调用描述符(#getClientCode
    包名+'#DynamicCordisRunnerService.getClientCode',服务,命名空间,'getClientCode',
    [
        智能体参数,
        {'name':'pluginId','wire':'pluginId','source':'json','codec':严格编解码('CordisDynamicPluginId')},
        {'name':'pluginRunId','wire':'pluginRunId','source':'json','codec':严格编解码('CordisDynamicPluginRunId')},
    ],
    严格编解码('DynamicCordisClientSource'),
    {'file':'src/index.ts','line':0,'column':3},作用域=作用域,实现='取客户端代码',
)#结束

结算运行请求=调用描述符(#resolveRequestRun
    包名+'#DynamicCordisRunnerService.resolveRequestRun',服务,命名空间,'resolveRequestRun',
    [
        {'name':'requestId','wire':'requestId','source':'json','codec':严格编解码('ApprovalRequestId')},
        {'name':'resolution','wire':'resolution','source':'json','codec':严格编解码('DynamicCordisRunResolution')},
    ],
    严格编解码('DynamicCordisResolveAck'),
    {'file':'src/index.ts','line':0,'column':3},实现='结算运行请求',
)#结束

结算用户运行=调用描述符(#settleUserRun
    包名+'#DynamicCordisRunnerService.settleUserRun',服务,命名空间,'settleUserRun',
    [
        智能体参数,
        {'name':'pluginId','wire':'pluginId','source':'json','codec':严格编解码('CordisDynamicPluginId')},
        {'name':'resolution','wire':'resolution','source':'json','codec':严格编解码('DynamicCordisRunResolution')},
    ],
    严格编解码('DynamicCordisRunResponse'),
    {'file':'src/index.ts','line':0,'column':3},作用域=作用域,实现='结算用户运行',
)#结束

面板停止=调用描述符(#stopFromPanel
    包名+'#DynamicCordisRunnerService.stopFromPanel',服务,命名空间,'stopFromPanel',
    [
        智能体参数,
        {'name':'pluginId','wire':'pluginId','source':'json','codec':严格编解码('CordisDynamicPluginId')},
    ],
    严格编解码('DynamicCordisStopResponse'),
    {'file':'src/index.ts','line':0,'column':3},作用域=作用域,实现='面板停止',
)#结束

同步巡检清单=调用描述符(#syncInspectManifest
    包名+'#DynamicCordisRunnerService.syncInspectManifest',服务,命名空间,'syncInspectManifest',
    [{'name':'providers','wire':'providers','source':'json','codec':严格编解码('CordisInspectProviderManifest[]')}],
    严格编解码('null'),
    {'file':'src/index.ts','line':0,'column':3},实现='同步巡检清单',
)#结束

结算巡检查询=调用描述符(#resolveInspectQuery
    包名+'#DynamicCordisRunnerService.resolveInspectQuery',服务,命名空间,'resolveInspectQuery',
    [
        智能体参数,
        {'name':'requestId','wire':'requestId','source':'json','codec':严格编解码('CordisInspectRequestId')},
        {'name':'resolution','wire':'resolution','source':'json','codec':严格编解码('CordisInspectQueryResolution')},
    ],
    严格编解码('CordisInspectResolveAck'),
    {'file':'src/index.ts','line':0,'column':3},作用域=作用域,实现='结算巡检查询',
)#结束

清单=调用描述符(#inventory
    包名+'#DynamicCordisRunnerService.inventory',服务,命名空间,'inventory',
    [],严格编解码('DynamicCordisInventoryRow[]'),
    {'file':'src/index.ts','line':0,'column':3},实现='清单',
)#结束

报告渲染失败=调用描述符(#reportRenderFailure
    包名+'#DynamicCordisRunnerService.reportRenderFailure',服务,命名空间,'reportRenderFailure',
    [
        智能体参数,
        {'name':'pluginId','wire':'pluginId','source':'json','codec':严格编解码('CordisDynamicPluginId')},
        {'name':'pluginRunId','wire':'pluginRunId','source':'json','codec':严格编解码('CordisDynamicPluginRunId')},
        {'name':'failure','wire':'failure','source':'json','codec':严格编解码('DynamicCordisRenderFailure')},
    ],
    严格编解码('null'),
    {'file':'src/index.ts','line':0,'column':3},作用域=作用域,实现='报告渲染失败',
)#结束

报告客户端守卫失败=调用描述符(#reportClientGuardFailure
    包名+'#DynamicCordisRunnerService.reportClientGuardFailure',服务,命名空间,'reportClientGuardFailure',
    [
        智能体参数,
        {'name':'pluginId','wire':'pluginId','source':'json','codec':严格编解码('CordisDynamicPluginId')},
        {'name':'pluginRunId','wire':'pluginRunId','source':'json','codec':严格编解码('CordisDynamicPluginRunId')},
        {'name':'failure','wire':'failure','source':'json','codec':严格编解码('CordisErrorDetails')},
    ],
    严格编解码('null'),
    {'file':'src/index.ts','line':0,'column':3},作用域=作用域,实现='报告客户端守卫失败',
)#结束

调用=调用描述符(#invoke
    包名+'#DynamicCordisRunnerService.invoke',服务,命名空间,'invoke',
    [
        {'name':'pluginId','wire':'pluginId','source':'json','codec':严格编解码('CordisDynamicPluginId')},
        {'name':'pluginRunId','wire':'pluginRunId','source':'json','codec':严格编解码('CordisDynamicPluginRunId')},
        {'name':'method','wire':'method','source':'json','codec':严格编解码('string')},
        {'name':'args','wire':'args','source':'json','codec':严格编解码('JsonValue')},
    ],
    严格编解码('DynamicCordisInvokeResult'),
    {'file':'src/index.ts','line':0,'column':3},实现='调用',
)#结束

TYPERT_REMOTE=远程贡献(包名,[#贡献（对齐远程方法目录顺序）
    面板取消定义,运行宿主半,取客户端代码,结算运行请求,结算用户运行,
    面板停止,同步巡检清单,结算巡检查询,清单,
    报告渲染失败,报告客户端守卫失败,调用,
])#结束
远程贡献对象=TYPERT_REMOTE#中文别名
默认=TYPERT_REMOTE#default
