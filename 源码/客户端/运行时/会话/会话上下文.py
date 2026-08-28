"""会话上下文世代：从表面替换重建出的一代不可变模型上下文。

对齐上游 `runtime/src/client/sessions/conversation-context.ts`。公开面仅中文名。
本模块只承载种类常量与字段约定说明；实例由组装器铸造。
"""

__all__=['上下文来源种类']#仅中文公开名

上下文来源种类=('compaction','rewind','rewrite')#压缩、回退或改写

# ConversationContext 字段约定（字典形态）：
# id:int — 会话内从零起的世代号；后续追加保持稳定
# parentId:int|缺席 — 本会话的上一代；初始上下文缺席
# origin:str|缺席 — 本世代为何存在（见 上下文来源种类）；初始缺席
# originSeq:int|缺席 — 创建本世代的那次替换的事件 seq
# createdAt:int|缺席 — 创建本世代的那次替换的 Unix 纪元毫秒
# prompt:dict|缺席 — 本世代观察到的最近请求头快照
# nodes:list — 历史世代的最终冻结节点，或尾世代当前折叠后的节点
