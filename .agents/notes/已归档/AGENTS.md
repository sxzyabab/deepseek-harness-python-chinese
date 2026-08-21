# AGENTS.md — 已归档 Agent Note

kind 目录下的已归档 Agent Note 三联是冻结的历史快照，不是当前权威。绝不要编辑、重排、翻译、修复、删除或移动已封存产物；新决策和新事实用现行 Agent Note 或当前文档。

归档改动只允许：搬迁完整的英文/中文/伴随记录三联、在两处 `Status: implemented` 行下方插入相同的 `Archived: YYYY-MM-DD` 行、重新记录伴随记录、以及修复或删除入站链接。不要检查、核验或修复已归档 note 的出站链接。

运行 [`dsh-archive-agent-notes`](../../skills/dsh-archive-agent-notes/SKILL.md) 工作流，并用 `pnpm run verify-archived-agent-notes --write` 追加新的产物哈希。常规核验器会拒绝已封存产物被改或缺失、三联不完整、未知 kind 文件夹，以及无效的归档元数据。
