"""压缩词汇：结果类型与 `compaction/*` 会话事件载荷字段。这些事件记录锁与摘要输入但不进入表面，因此不是表面事件；摘要由随后的替换 `user/message` 承载。后端包拥有配置与保留策略。Python 侧以字段元组记录词汇；上游 TypeScript 用 declaration merging 扩展 SessionEventMap。"""
from .品牌 import 压缩标识#再导出压缩事务 id

压缩标识=压缩标识#再导出品牌函数

压缩结果字段=(#一次成功压缩操作的结果
    'compactionId',#本压缩完整耐久生命周期共用的稳定身份
    'sourceCommandId',#发起本次压缩的人类命令（若为手动）
    'startSeq',#已追加 compaction/start 事件的 seq
    'summarySeq',#已追加 compaction/summary 事件的 seq
    'endSeq',#已追加 compaction/end 事件的 seq
    'summary',#后端产出的摘要内容块
    'shadowedRange',#被遮蔽表面边界对 start/end（表面位置跨度，不是数值 seq 区间）
    'shadowedSeqs',#全部被遮蔽表面节点的 seq，按表面顺序
    'shadowedTokenCount',#被遮蔽内容的估算 token 数
)#压缩结果字段结束

压缩开始载荷字段=('compactionId','sourceCommandId','turn')#compaction/start：仅日志，持锁直到 end；turn 为编号所有者或独立事务 null
压缩摘要载荷字段=(#compaction/summary：已完成摘要与模型调用事实——仅日志，无 surfaceOp
    'compactionId',#本事务身份
    'sourceCommandId',#手动触发时的命令 id
    'summary',#摘要内容块
    'shadowedRange',#被遮蔽表面区间的首尾 seq
    'shadowedSeqs',#全部被遮蔽表面节点 seq
    'shadowedTokenCount',#被遮蔽内容的估算 token
    'provider',#写出摘要的提供方路由
    'model',#写出摘要的模型
    'maxTokens',#摘要调用发送的生成上限（若有）
    'usage',#提供方报告的摘要请求 token 用量（若发出）
    'rawOutput',#完整提供方输出（已标记 LLM 流时必填；未标记时可选）
    'llmStreamCall',#true 表示经本上下文 ctx.llm.stream()；未标记摘要禁止声称
)#摘要载荷结束
压缩结束载荷字段=('compactionId','sourceCommandId','turn','error')#compaction/end：仅日志，释放锁；error 记录失败尝试
压缩裁剪载荷字段=('shadowedRange','shadowedSeqs','shadowedTokenCount')#compaction/prune：无模型裁剪替换的影子价格——仅日志，无 surfaceOp
