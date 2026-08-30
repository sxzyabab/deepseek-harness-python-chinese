"""所选 Remote 贡献的载荷词表再导出面。

对齐上游 `api/remotes/src/client/index.ts`：
- 「PluginInventorySnapshot」再导出
- 「载体面向客户端的类型再导出」段：仅邻叶已有厚类型时真再导出
- gateway/client、cordis-host-runner/remote 类型面侧效拉入
- 「命名空间载荷词表再导出」段（cordis-host-runner/types）
- 「JsonValue」再导出（session/types ← session/json）
- 转发事件白名单投影（本组装 `$on` 键面）

客户端贡献点名收发内容时不必导入宿主包；本组装是两平面合法相遇处。
公开面仅中文名；线上字面量与上游英文字段键保持原样。
"""
from typing import TypeAlias,TypedDict#递归 JsonValue 别名与结构类型
from ...内核.会话.json值 import 是否json值,快照json值#会话无损 JSON 判定与脱离快照（权威运行时）
from ...拓展.cordis_服务端.类型 import (#动态包运行器线协议词汇
    动态运行模式,请求运行结局,运行状态,巡检平面,#枚举联合
    动态插件标识,动态包标识,动态运行标识,审批请求标识,巡检查询标识,#品牌 id
    巡检方法清单字段,巡检提供方清单字段,巡检提供方视图字段,#巡检清单
    巡检查询请求字段,巡检查询决议形,巡检查询已落定字段,巡检认领回执字段,#巡检查询
    错误细节字段,半边状态字段,运行诊断字段,运行尝试字段,#运行态与诊断
    动态包公告字段,运行请求字段,请求已落定字段,撤回公告字段,#公告载荷
    清单包字段,清单行字段,取消定义回执形,渲染失败字段,#清单与渲染
    运行响应形,停止响应形,宿主半结果形,客户端源字段,#响应形
    运行决议形,调用结果形,#决议与 invoke
)#动态载荷结束
from ...host.plugin_inventory.类型 import (#插件清单 Remote 投影
    插件清单快照,插件清单条目,插件条目标识,插件光纤阶段,#清单词表
)#清单结束
from ...客户端.连接.客户端 import (#邻叶厚类型：仅真再导出（对齐 connection/client）
    连接句柄,#浏览器连接句柄
    #接口客户端协议,#IApiClient
)#连接厚类型结束
from ..网关 import 客户端面 as _网关客户端#侧效：拉入网关客户端类型面（对齐 export type {} from gateway/client）
from ...拓展.cordis_服务端 import 远程 as _动态远程#侧效：拉入动态包 Remote 类型面（对齐 export type {} from cordis-host-runner/remote）
from .远程事件 import 远程转发事件,API_REMOTE_FORWARDED_EVENTS#转发白名单常量
from .类型 import 远程转发事件名#白名单元素联合投影

# ---------------------------------------------------------------------------
# JsonValue：对齐上游 `export type { JsonValue } from session/types`（← session/json）
# null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue }
# session.类型未单独钉中文名；本面按 json.ts 递归定义再导出。运行时权威仍是是否json值/快照json值。
# ---------------------------------------------------------------------------
Json值:TypeAlias=None|bool|int|float|str|list['Json值']|dict[str,'Json值']#无损 JSON 值（递归）
会话JSON值=Json值#上游 JsonValue 经 session/types 再导出面的对照名

# ---------------------------------------------------------------------------
# DynamicCordisResolveAck：上游 remotes 再导出，宿主类型叶未单独中文命名
# 与 CordisInspectResolveAck 同形（accepted:boolean），身份不同不得合并公开名。
# ---------------------------------------------------------------------------
class 运行认领回执字段(TypedDict):#动态运行决议是否到达仍在等待的请求
    """客户端激活决议是否到达仍在等待的请求。对齐 DynamicCordisResolveAck：{accepted: bool}。"""
    accepted:bool#迟到、未知或过期的回答为 false

# ---------------------------------------------------------------------------
# 上游 export type 名 → 本面中文名（载荷词表段 + 邻叶已厚载体段）
# 连接其余 stubs（ClientResponse/Rpc*/ContentBlock…）邻叶无厚类型：不在本面冒充再导出。
# ---------------------------------------------------------------------------
载荷上游名对照={#client/index.ts 载荷词表与已厚载体再导出
    'ApprovalRequestId':'审批请求标识',#审批请求身份
    'CordisHalfState':'半边状态字段',#宿主/客户端半边状态
    'CordisDynamicPackageId':'动态包标识',#不可变包身份
    'CordisDynamicPluginId':'动态插件标识',#稳定插件身份
    'CordisDynamicPluginRunId':'动态运行标识',#一次激活尝试身份
    'CordisDynamicRunMode':'动态运行模式',#run|update
    'CordisInspectMethodManifest':'巡检方法清单字段',#巡检方法目录行
    'CordisInspectPlatform':'巡检平面',#host|client
    'CordisInspectProviderManifest':'巡检提供方清单字段',#提供方目录行
    'CordisInspectProviderView':'巡检提供方视图字段',#带平面的提供方视图
    'CordisInspectQueryRequest':'巡检查询请求字段',#巡检查询广播
    'CordisInspectQueryResolution':'巡检查询决议形',#查询结果联合
    'CordisInspectQueryResolved':'巡检查询已落定字段',#查询已离开待答
    'CordisInspectRequestId':'巡检查询标识',#巡检查询身份
    'CordisInspectResolveAck':'巡检认领回执字段',#查询回答是否被接受
    'CordisRunDiagnostic':'运行诊断字段',#结构化失败
    'CordisRunStatus':'运行状态',#激活尝试状态联合
    'DynamicCordisClientSource':'客户端源字段',#客户端半源码
    'DynamicCordisHostHalfResult':'宿主半结果形',#拉起宿主半结果
    'DynamicCordisInventoryRow':'清单行字段',#清单一行插件
    'DynamicCordisInvokeResult':'调用结果形',#invoke 结果联合
    'DynamicCordisPackage':'动态包公告字段',#包上线公告
    'DynamicCordisRequestResolved':'请求已落定字段',#激活请求已落定
    'DynamicCordisResolveAck':'运行认领回执字段',#运行决议认领回执
    'DynamicCordisRetracted':'撤回公告字段',#激活撤回公告
    'DynamicCordisRunRequest':'运行请求字段',#待处理激活请求
    'DynamicCordisRunResolution':'运行决议形',#浏览器裁决联合
    'DynamicCordisRunAttempt':'运行尝试字段',#最近激活尝试
    'DynamicCordisRunResponse':'运行响应形',#运行/更新响应联合
    'DynamicCordisStopResponse':'停止响应形',#停止响应联合
    'DynamicCordisUndefineReceipt':'取消定义回执形',#移除插件回执
    'RequestRunOutcome':'请求运行结局',#请求如何离开待处理
    'JsonValue':'Json值',#会话无损 JSON
    'PluginInventorySnapshot':'插件清单快照',#清单 list 投影
    'ConnectionHandle':'连接句柄',#浏览器连接句柄（邻叶厚）
    'IApiClient':'接口客户端协议',#宿主 API 通道协议（邻叶厚）
}#对照结束

# ---------------------------------------------------------------------------
# 构造用附属词表（宿主 types 拥有；remotes 消费方经本面点名，免直连宿主包）
# CordisErrorDetails / DynamicCordisInventoryPackage / DynamicCordisRenderFailure
# ---------------------------------------------------------------------------
构造附属上游名对照={#非 remotes 顶层再导出，但构造载荷必需
    'CordisErrorDetails':'错误细节字段',#跨平面错误
    'DynamicCordisInventoryPackage':'清单包字段',#清单包元数据
    'DynamicCordisRenderFailure':'渲染失败字段',#客户端渲染失败
}#附属对照结束

def 是否载荷Json值(值):#载荷 JSON 边界
    """测试候选是否为构造 Remote 载荷可用的无损 JSON（委托会话是否json值）。"""
    return 是否json值(值)#会话权威边界

def 快照载荷Json值(值):#载荷 JSON 脱离
    """校验并脱离一份可用于 Remote 载荷的无损 JSON（委托会话快照json值）。"""
    return 快照json值(值)#会话权威快照

def 解析载荷中文名(上游类型名):#上游名 → 中文公开名
    """把上游 remotes 再导出的类型名解析为本面中文公开名；未知则 None。"""
    名=载荷上游名对照.get(上游类型名)#主表
    if 名 is not None:#命中载荷段
        return 名#中文名
    return 构造附属上游名对照.get(上游类型名)#附属表或 None

__all__=[#仅中文公开名
    '动态运行模式','请求运行结局','运行状态','巡检平面',
    '动态插件标识','动态包标识','动态运行标识','审批请求标识','巡检查询标识',
    '巡检方法清单字段','巡检提供方清单字段','巡检提供方视图字段',
    '巡检查询请求字段','巡检查询决议形','巡检查询已落定字段','巡检认领回执字段',
    '错误细节字段','半边状态字段','运行诊断字段','运行尝试字段',
    '动态包公告字段','运行请求字段','请求已落定字段','撤回公告字段',
    '清单包字段','清单行字段','取消定义回执形','渲染失败字段',
    '运行响应形','停止响应形','宿主半结果形','客户端源字段',
    '运行决议形','调用结果形','运行认领回执字段',
    '插件清单快照','插件清单条目','插件条目标识','插件光纤阶段',
    '连接句柄','接口客户端协议',
    '远程转发事件','API_REMOTE_FORWARDED_EVENTS','远程转发事件名',
    'Json值','会话JSON值','是否载荷Json值','快照载荷Json值',
    '载荷上游名对照','构造附属上游名对照','解析载荷中文名',
]#公开面结束
