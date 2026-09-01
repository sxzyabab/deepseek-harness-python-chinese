"""动态 Cordis 插件服务：默认导出运行器服务类。

对齐上游 `@deepseek-ai/dsh-cordis-host-runner`。公开面仅中文名。本包默认导出运行器服务。
叶子已齐（本轮新迁 0）；宿主半用 compile/exec 近似 Node vm，非硬缺口 2 的浏览器 Function/vm。
"""
from .运行器 import (#运行器与再导出
    动态插件运行器服务,#默认服务类
    巡检注册表服务,#巡检注册表
    宿主内置巡检,#内置巡检符号
    DynamicCordisRunnerService,#上游类名
)#再导出
from .类型 import (#品牌、巡检与线协议字段
    动态运行模式,请求运行结局,运行状态,巡检平面,#枚举
    动态插件标识,动态包标识,动态运行标识,审批请求标识,巡检查询标识,#品牌
    巡检方法清单字段,巡检提供方清单字段,巡检提供方视图字段,#巡检清单
    巡检查询请求字段,巡检查询决议形,巡检查询已落定字段,巡检认领回执字段,#巡检查询
    错误细节字段,半边状态字段,运行诊断字段,运行尝试字段,#运行态
    动态包公告字段,运行请求字段,请求已落定字段,撤回公告字段,#公告
    清单包字段,清单行字段,取消定义回执形,渲染失败字段,#清单/渲染
    运行响应形,停止响应形,宿主半结果形,客户端源字段,#响应
    运行决议形,调用结果形,#决议/调用
    CordisDynamicPluginId,CordisDynamicPackageId,CordisDynamicPluginRunId,#上游品牌
    ApprovalRequestId,CordisInspectRequestId,#上游审批/巡检
)#类型
from .沙箱 import HOST_BUILTIN_INSPECTION#上游内置巡检别名
from .远程 import TYPERT_REMOTE,远程贡献对象#Host-for-Client Remote 贡献

__all__=[#仅中文公开名与上游对照
    '动态插件运行器服务','巡检注册表服务','宿主内置巡检',
    '动态运行模式','请求运行结局','运行状态','巡检平面',
    '动态插件标识','动态包标识','动态运行标识','审批请求标识','巡检查询标识',
    '巡检方法清单字段','巡检提供方清单字段','巡检提供方视图字段',
    '巡检查询请求字段','巡检查询决议形','巡检查询已落定字段','巡检认领回执字段',
    '错误细节字段','半边状态字段','运行诊断字段','运行尝试字段',
    '动态包公告字段','运行请求字段','请求已落定字段','撤回公告字段',
    '清单包字段','清单行字段','取消定义回执形','渲染失败字段',
    '运行响应形','停止响应形','宿主半结果形','客户端源字段',
    '运行决议形','调用结果形',
    'DynamicCordisRunnerService',
    'CordisDynamicPluginId','CordisDynamicPackageId','CordisDynamicPluginRunId',
    'ApprovalRequestId','CordisInspectRequestId',
    'HOST_BUILTIN_INSPECTION','TYPERT_REMOTE','远程贡献对象',
]#公开面结束

default=动态插件运行器服务#默认导出对齐上游
