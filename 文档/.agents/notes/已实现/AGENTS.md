# AGENTS.md — 已实现 Agent Note

这些 Agent Note 描述已交付的决策。遵循[根说明](../../../AGENTS.md)、[文档规范](../../../docs/AGENTS.md)和 [Agent Note 格式](../README.md#the-file-format)；`verify-agent-note-format` 门禁生命周期特定结构。

## 让已实现 Agent Note 与实际交付保持一致

路径、符号、默认值和机制若有改动，要在同一次改动里更新。就地改写陈旧事实；不要追加变更历史。

当一份已交付 note 不太可能再指导后续工作时，通过 [`dsh-archive-agent-notes`](../../skills/dsh-archive-agent-notes/SKILL.md) 归档其完整三联，而不是继续维护它。

### 这不是重写*决策*的许可

就地更新事实实现。推翻决策或其理由需要新的 Agent Note 并交叉链接；被完全取代的旧 note 只能按 [Agent Note 规则](../README.md) 里的合并规则删除。
