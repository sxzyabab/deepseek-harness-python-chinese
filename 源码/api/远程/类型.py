"""转发 Host 事件白名单的类型面：消费方键投影以及它所填的选择席位。

对齐上游 `remotes/src/types.ts`。白名单的值在 `./远程事件`，本模块按包约定保持仅类型；
Host 转发循环与消费方 `$on` 键面读同一份声明。

公开面仅中文名。事件名字面量保持上游。
"""
from typing import Literal,TypedDict#字面量真值与结构类型
from .远程事件 import 远程转发事件#转发事件白名单常量

# ---------------------------------------------------------------------------
# 白名单投影与席位合并（对齐 types.ts：仅类型，无运行时值）
# ---------------------------------------------------------------------------

# 上游：export type ApiRemoteForwardedEvent = typeof API_REMOTE_FORWARDED_EVENTS[number]
远程转发事件名=远程转发事件#白名单元素联合投影；消费方与 Host 都读这一份

# 上游 declare module '@deepseek-ai/dsh-typert-protocol' {
#   interface TypertRemoteEventSelection extends Record<ApiRemoteForwardedEvent, true> {}
# }
# Python 无 declare module：下列 TypedDict 即向协议空接口合并的选择席位（键→true）。
# 消费方编译面没有它时 TypertRemoteEvent 是 never，所有 $on 都会失败。
# 不得缩成「远程转发事件名」别名——席位是 Record 映射，不是事件名联合。
远程事件选择席位=TypedDict('远程事件选择席位',{#TypertRemoteEventSelection 席位合并
    'agent-preset/selected':Literal[True],#智能体预设已选定 → 已选
    'commands/change':Literal[True],#命令表已变更 → 已选
    'credentials/updated':Literal[True],#凭证已更新 → 已选
    'cordis/request-run':Literal[True],#请求运行动态包 → 已选
    'cordis/request-run-resolved':Literal[True],#动态包运行请求已决议 → 已选
    'cordis/dynamic-package':Literal[True],#动态包清单 → 已选
    'cordis/dynamic-retract':Literal[True],#动态包撤回 → 已选
    'cordis/inspect-query':Literal[True],#动态包探查查询 → 已选
    'cordis/inspect-query-resolved':Literal[True],#动态包探查查询已决议 → 已选
    'llm/adapters-updated':Literal[True],#大模型适配器已更新 → 已选
    'settings/document-updated':Literal[True],#设置文档已更新 → 已选
})#席位合并结束：白名单每一键标为 true

# 上游：TypertRemoteEvent = Extract<keyof Events, keyof TypertRemoteEventSelection>
# 本面无完整 Events 图；席位键由白名单生成，权威可订阅投影即白名单元素联合。
可订阅远程事件名=远程转发事件名#合法 $on 键：事件图与选择席位的交集投影

# 上游英文名对照（协议/跨包检索用，不进默认公开面叙述）
ApiRemoteForwardedEvent=远程转发事件名#上游名
TypertRemoteEventSelection=远程事件选择席位#上游席位合并名（非事件名联合别名）
TypertRemoteEvent=可订阅远程事件名#上游可订阅键对照

__all__=[#仅中文公开名（types.ts 白名单投影 + 席位合并）
    '远程转发事件名','远程事件选择席位','可订阅远程事件名',
]#公开面结束
