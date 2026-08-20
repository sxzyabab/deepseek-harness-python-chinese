"""请求检视快照与提示变更约定。

对齐上游 `runtime/src/client/sessions/request-inspection.ts`。公开面仅中文名。
本模块承载检视面字段约定与变更种类常量；实例由轨迹／组装定义铸造。
"""

__all__=['提示变更种类']#仅中文公开名

提示变更种类=('initial','system','tools','system-and-tools')#变更种类

# ConversationPromptSnapshot 字段：config / system / tools
# RequestPromptChange 字段：seq / time / kind / previous?
# RequestView（助手）：purpose='assistant' + turn/step + 生命周期字段
# RequestView（压缩）：purpose='compaction' + turn|None + step=0
# RequestInspectionSnapshot：requests + callSchemas
# AssistantProvenanceView / AssistantRequestConfig 形态见 会话快照.py
