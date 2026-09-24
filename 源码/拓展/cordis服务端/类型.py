"""动态 Cordis 插件运行器的客户端安全线协议词汇。"""

__all__=[
    '动态cordis错误',
    '动态插件标识','动态包标识','动态运行标识','审批请求标识','巡检查询标识',
    '巡检平面','动态运行模式','请求运行结局','运行状态',
    '半边状态取值','运行诊断阶段','巡检查询失败原因',
    '运行失败原因','停止失败原因','调用失败码','运行决议失败原因',
    '运行成功状态',
    '巡检方法清单','巡检提供方清单','巡检提供方视图',
    '巡检查询请求','巡检查询决议','巡检查询已落定','巡检认领回执',
    '动态cordis错误细节','半边状态','运行诊断','动态运行尝试',
    '动态包','动态运行请求','动态请求已落定','动态已撤回',
    '清单包','清单行','取消定义回执','渲染失败',
    '运行响应','停止响应','宿主半结果','客户端源码',
    '运行决议','运行认领回执','调用结果',
]

#常量
巡检平面=('host','client')
动态运行模式=('run','update')
请求运行结局=('approved','completed','rejected','cancelled','failed')
运行状态=(
    'awaiting-approval','starting-host','client-pending','running',
    'waiting','rejected','failed','cancelled','stopped',
)
半边状态取值=('absent','pending','stopped','running','waiting','failed')
运行诊断阶段=(
    'approval','host-load','host-apply','client-load','client-apply','client-render',
)
巡检查询失败原因=(
    'provider-missing','method-missing','invalid-input','provider-error','cancelled',
)
运行失败原因=(
    'plugin-missing','package-missing','invalid-mode','transition-in-flight',
    'host-half-failed','client-half-failed','rejected','cancelled','not-running',
)
停止失败原因=('plugin-missing','not-running')
调用失败码=('plugin-not-running','stale-run','method-not-found','handler-error')
运行决议失败原因=('rejected','host-half-failed','client-half-failed')
运行成功状态=('awaiting-approval','starting','running')

#工具
def 动态插件标识(标识):
    """把字符串标成动态插件标识，不做校验。"""
    return 标识

def 动态包标识(标识):
    """把字符串标成动态包标识，不做校验。"""
    return 标识

def 动态运行标识(标识):
    """把字符串标成动态运行标识，不做校验。"""
    return 标识

def 审批请求标识(标识):
    """把字符串标成审批请求标识，不做校验。"""
    return 标识

def 巡检查询标识(标识):
    """把字符串标成巡检查询标识，不做校验。"""
    return 标识

#
class 动态cordis错误(Exception):
    """动态 Cordis 运行器的异常基类。"""
    def __init__(自身,消息):
        """用消息构造。"""
        super().__init__(消息)
        自身.message=消息

class 巡检方法清单:
    """巡检提供方暴露的一条模型可调用只读查询。线协议键：name、description、inputSchema、outputSchema。"""
    字段=('name','description','inputSchema','outputSchema')

class 巡检提供方清单:
    """一个巡检提供方的可序列化目录条目。线协议键：id、description、methods。"""
    字段=('id','description','methods')

class 巡检提供方视图:
    """cordis_inspect_list 返回的提供方目录行。线协议键在清单之上加 platform。"""
    字段=('id','description','methods','platform')

class 巡检查询请求:
    """宿主广播，请求一条现场客户端巡检结果。input 在方法无字段时省略。"""
    字段=('requestId','agentId','provider','method','input')

class 巡检查询决议:
    """客户端提供方发给正在等待的宿主查询的结果。成功含 ok/data，失败含 ok/reason/message。"""
    成功字段=('ok','data')
    失败字段=('ok','reason','message')

class 巡检查询已落定:
    """通知某次客户端巡检查询已无法再回答。"""
    字段=('requestId',)

class 巡检认领回执:
    """客户端回答是否认领了仍在等待的查询。"""
    字段=('accepted',)

class 动态cordis错误细节:
    """跨宿主/客户端传输保留的错误字段。stack 可省略。"""
    字段=('message','stack')

class 半边状态:
    """一次激活尝试中的一个平台半边。error 可省略。"""
    字段=('status','waitingFor','error')

class 运行诊断:
    """与一次精确激活尝试关联的结构化失败。stack 可省略。"""
    字段=('phase','message','stack','pluginId','packageId','pluginRunId')

class 动态运行尝试:
    """与物理运行分开保留的最近一次激活尝试。审批与诊断字段可省略。"""
    字段=(
        'pluginRunId','packageId','mode','status',
        'approvalRequestId','requiresApproval','host','client','error',
    )

class 动态包:
    """向浏览器页面宣布的一个正在运行的包。"""
    字段=('pluginId','packageId','pluginRunId','name')

class 动态运行请求:
    """转发给浏览器页面的一条待处理、模型驱动的客户端激活。"""
    字段=(
        'requestId','agentId','pluginId','packageId',
        'mode','name','purpose','requiresApproval',
    )

class 动态请求已落定:
    """向所有页面广播的一条已落定、模型驱动的客户端激活请求。"""
    字段=('requestId','outcome')

class 动态已撤回:
    """从每个页面撤回的一次激活。"""
    字段=('pluginId','packageId','pluginRunId')

class 清单包:
    """清单暴露的包元数据，不含源码。"""
    字段=('packageId','name','purpose','hasHostHalf','hasClientHalf')

class 清单行:
    """整帧清单里的一行稳定插件。当前包、下一包、活动运行与最近尝试可省略。"""
    字段=(
        'pluginId','agentId','packages','currentPackageId',
        'nextPackageId','activeRun','latestRun',
    )

class 取消定义回执:
    """移除一个插件及其全部包版本的答复。成功含 ok/wasRunning，失败含 ok/reason/message。"""
    成功字段=('ok','wasRunning')
    失败字段=('ok','reason','message')

class 渲染失败:
    """客户端半加载后观察到的一次渲染失败。stack 可省略。"""
    字段=('slot','message','stack','abdicated')

class 运行响应:
    """模型驱动与面板驱动激活共用的结果。失败时 stack 可省略。"""
    成功字段=(
        'ok','status','pluginId','packageId','pluginRunId','waitingFor',
        'clientWaitingFor','currentPackageId','nextPackageId','mode',
    )
    失败字段=('ok','reason','message','stack')

class 停止响应:
    """停止插件但不删除其包的结果。"""
    成功字段=('ok',)
    失败字段=('ok','reason','message')

class 宿主半结果:
    """加载客户端半之前拉起宿主半的结果。失败时叠错误细节。"""
    成功字段=('ok','pluginId','packageId','pluginRunId','waitingFor','startedHere')
    失败字段=('ok','message','stack')

class 客户端源码:
    """一次精确激活的客户端半源码。"""
    字段=('code','name','pluginId','packageId','pluginRunId')

class 运行决议:
    """已批准的工具运行与面板运行共用的浏览器裁决。失败字段均可省略。"""
    成功字段=('ok','pluginRunId','waitingFor')
    失败字段=('ok','reason','pluginRunId','startedHere','message','stack')

class 运行认领回执:
    """客户端激活决议是否到达仍在等待的请求。"""
    字段=('accepted',)

class 调用结果:
    """把一次客户端调用路由到活动宿主半的结果。失败时叠错误细节。"""
    成功字段=('ok','value')
    失败字段=('ok','code','message','stack')
