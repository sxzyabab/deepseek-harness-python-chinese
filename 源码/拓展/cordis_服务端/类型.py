"""动态 Cordis 插件运行器的客户端安全线协议词汇。

对齐上游 `拓展/cordis-host-runner/src/types.ts`。公开面仅中文名。
品牌 id 在 Python 侧用普通字符串承载；构造函数作身份入口。
字段元组描述线协议形状（非 vm：与沙箱求值无关的传输词表）。
"""

__all__=[#仅中文公开名
    '动态运行模式','请求运行结局','运行状态','巡检平面',
    '动态插件标识','动态包标识','动态运行标识','审批请求标识','巡检查询标识',
    '巡检方法清单字段','巡检提供方清单字段','巡检提供方视图字段',
    '巡检查询请求字段','巡检查询决议形','巡检查询已落定字段','巡检认领回执字段',
    '错误细节字段','半边状态字段','运行诊断字段','运行尝试字段',
    '动态包公告字段','运行请求字段','请求已落定字段','撤回公告字段',
    '清单包字段','清单行字段','取消定义回执形','渲染失败字段',
    '运行响应形','停止响应形','宿主半结果形','客户端源字段',
    '运行决议形','调用结果形',
    'CordisDynamicPluginId','CordisDynamicPackageId','CordisDynamicPluginRunId',
    'ApprovalRequestId','CordisInspectRequestId',
]#公开面结束

动态运行模式=('run','update')#运行或更新
请求运行结局=('approved','completed','rejected','cancelled','failed')#请求落定结果
运行状态=(#运行状态
    'awaiting-approval','starting-host','client-pending','running',
    'waiting','rejected','failed','cancelled','stopped',
)#联合
巡检平面=('host','client')#宿主或客户端

巡检方法清单字段=('name','description','inputSchema','outputSchema')#方法清单
巡检提供方清单字段=('id','description','methods')#提供方清单
巡检提供方视图字段=('id','description','methods','platform')#带平面视图
巡检查询请求字段=('requestId','agentId','provider','method','input')#查询请求
巡检查询决议形=('ok-true+data','ok-false+reason+message')#决议联合
巡检查询已落定字段=('requestId',)#已落定
巡检认领回执字段=('accepted',)#认领回执

错误细节字段=('message','stack')#跨平面错误
半边状态字段=('status','waitingFor','error')#半边状态；status 为 absent|pending|stopped|running|waiting|failed
运行诊断字段=('phase','message','stack','pluginId','packageId','pluginRunId')#诊断
运行尝试字段=(#最近激活尝试
    'pluginRunId','packageId','mode','status',
    'approvalRequestId','requiresApproval','host','client','error',
)#尝试
动态包公告字段=('pluginId','packageId','pluginRunId','name')#包公告
运行请求字段=(#模型驱动激活请求
    'requestId','agentId','pluginId','packageId','mode','name','purpose','requiresApproval',
)#请求
请求已落定字段=('requestId','outcome')#已落定公告
撤回公告字段=('pluginId','packageId','pluginRunId')#撤回
清单包字段=('packageId','name','purpose','hasHostHalf','hasClientHalf')#清单包
清单行字段=(#清单行
    'pluginId','agentId','packages','currentPackageId','nextPackageId','activeRun','latestRun',
)#行
取消定义回执形=('ok-true+wasRunning','ok-false+plugin-missing')#取消定义
渲染失败字段=('slot','message','stack','abdicated')#渲染失败
运行响应形=('ok-true+status…','ok-false+reason+message')#运行响应
停止响应形=('ok-true','ok-false+plugin-missing|not-running')#停止
宿主半结果形=('ok-true+ids+waitingFor+startedHere','ok-false+错误细节')#宿主半
客户端源字段=('code','name','pluginId','packageId','pluginRunId')#客户端源
运行决议形=('ok-true+pluginRunId','ok-false+reason…')#运行决议
调用结果形=('ok-true+value','ok-false+code+错误细节')#invoke 结果

def 动态插件标识(标识):#品牌化插件 id
    """给宿主铸造的插件 ID 打品牌（Python 侧原样字符串）。"""
    return 标识#原样

def 动态包标识(标识):#品牌化包 id
    """给宿主铸造的包 ID 打品牌。"""
    return 标识#原样

def 动态运行标识(标识):#品牌化运行 id
    """给宿主铸造的插件运行 ID 打品牌。"""
    return 标识#原样

def 审批请求标识(标识):#品牌化审批请求 id
    """给宿主铸造的审批请求 ID 打品牌。"""
    return 标识#原样

def 巡检查询标识(标识):#品牌化巡检查询 id
    """给宿主铸造的巡检查询 ID 打品牌。"""
    return 标识#原样

#上游导出名对照
CordisDynamicPluginId=动态插件标识#上游名
CordisDynamicPackageId=动态包标识#上游名
CordisDynamicPluginRunId=动态运行标识#上游名
ApprovalRequestId=审批请求标识#上游名
CordisInspectRequestId=巡检查询标识#上游名
