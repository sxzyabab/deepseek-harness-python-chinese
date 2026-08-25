# AGENTS.md

DeepSeek Harness 是基于内嵌 Cordis 的插件式 agent harness（智能体框架）：**一切皆插件**。改 `packages/` 前先读 [docs/architecture.md](docs/architecture.md)；文档规范见 [docs/AGENTS.md](docs/AGENTS.md)。

## 预发布立场：正确基础优先于兼容冲击面

**首次打标签发布时删除本节。** 目前没有外部使用者，应优先采用正确的基础设计，而不是兼容垫片：可自由重命名或重新打包，并一并更新所有引用。后端拒绝旧的磁盘格式。SQLite 使用单调递增的 `SCHEMA_VERSION`；`dsh-session` 将 `SESSION_FORMAT_VERSION` 保持为 `0`，不做兼容承诺。

## 仓库布局

```
vendor/      内嵌的 Cordis 源码 — 清单与同步流程见 vendor/README.md
packages/    @deepseek-ai/dsh-<pkg> 工作区，位于 packages/<group>/<pkg>/
  core/        产品 API 主干：会话、系统提示词、工具、agent、agent loop（智能体循环）
  api/         远程 BFF 组装与 Typert RPC 网关
  typert/      类型图生成器、loader 与运行时注册表
  llm/         LLM（大语言模型）能力：Service Definition/消费方 + DeepSeek 提供方
  e2b/         E2B 概念验证：沙箱 + 文件系统/子进程适配器
  shell/        bash 能力：Service Definition + local/pwsh 提供方 + shell 消费方
  subprocess/  子进程能力 + 本地进程树提供方
  terminal/         持久会话
  fs/          文件系统能力 + 策略
  lsp/         language-server 能力
  skill/       skill（技能）提供方注册表 + 本地实现 + 目录/loader 工具
  web/         web 能力：Service Definition + 搜索/抓取提供方 + 工具消费方
  compaction/     压缩（compaction）能力 + 基础提供方
  context/     请求上下文插件
  subagent/    subagent 能力：Service Definition + 提供方 + 委托消费方
  bundle/      可安装的 dsh --profile 补丁层组合包
  workflow/    工作流能力 + worker 线程提供方 + 工具消费方
  todo/        todo_write 工具
  plan/        以日志状态实现的计划模式
  preset/      按会话从预设 cordis.yml 组合 agent
  guard/       循环卫生 + 工具超时插件
  self-modification/  agent 检查/挂载自身插件
  hooks/       Claude Code/Codex 钩子桥接 + 协议格式库
  session/     持久会话数据：持久化、投影、标题、遥测
  identity/    匿名身份
  settings/    用户设置能力 + 文件提供方
  credentials/ 凭证引用能力 + env/.env 提供方
  acp/         仅用于自动化的 ACP（Agent Client Protocol）服务器
  interaction/ 审批/交互能力、权限、命令、向用户询问
  boot/        共享的应用二进制粘合层
  sdk/         JSON-RPC 协议、服务器与 TypeScript 客户端
  examples/    演示组合包（agent 主干 + CLI（命令行界面）/ACP/JSON-RPC 二进制）
  support/     开发/测试基础设施
  util/        零依赖工具函数
python/      Python SDK 与捆绑运行时（见 python/README.md）
native/      @deepseek-ai/node-addon-landlock-run 的权威源码（见 native/README.md）
examples/    覆盖 packages/examples 组合包的可运行 cordis.yml 叶子（见 examples/AGENTS.md）
.agents/     Agent 工作流与 Agent Note（`notes/`）
docs/        架构、生成目录、事故复盘（postmortem）、实操手册（见 docs/AGENTS.md）
scripts/     仓库门禁与生成器
website/     将选定的双语 docs/ 源文投影为 VitePress 站点
```

包分组：[packages/README.md](packages/README.md)。

## 命令

```sh
pnpm install            # pnpm 工作区，node ^22.19 || >=24
pnpm run clean           # 删除构建产物以及已删包留下的可安全清理残留
pnpm run test           # vitest 单元测试
pnpm run test:coverage  # CI 覆盖率门禁：packages/*/*/src 按文件 100%
pnpm run test:e2e       # 真实 API 测试；没有 DEEPSEEK_API_KEY 时自行跳过
pnpm run test:snapshot  # 无需密钥的 ACP/headless 回放，对照预期输出；过滤：-t <name>
pnpm run test:snapshot:record  # 重新录制预期输出（需要密钥）
pnpm run typecheck
pnpm run lint
pnpm run duplication    # 跨文件 TypeScript 克隆检测
pnpm run build          # tsc 产出 lib/types，tsdown 打包运行时
pnpm run hygiene        # knip + publint + 工作区约束 + NodeNext 消费方检查
pnpm run check:windows-wine  # 仅用于诊断已知 Windows 失败（需要 wine）；该信号由 CI 负责
pnpm run doc-sync       # 全部文档门禁；叶子列表在 scripts/run-gates.ts
pnpm run website:build  # VitePress 构建（同时检查死链）
pnpm dsh --profile headless "task"  # 从源码运行一项任务（需要 DEEPSEEK_API_KEY）
pnpm run demo:cordis    # agent 修改自身运行时（需要密钥）
pnpm run demo:acp       # ACP 自动化服务器（需要 DEEPSEEK_API_KEY）
```

### 宿主沙箱失败

当必需的 `gh`、`pnpm`、构建、测试或生成器命令因 agent 沙箱拦截凭证、网络、IPC、文件监视或嵌套 `sandbox-exec` 而失败时，先以最小范围提升宿主权限原样重试，再诊断认证或项目故障。必须有沙箱拦截证据；不得绕过真实测试失败，也不得绕过被测产品沙箱。

### 在本地运行相关检查

推送前按 [dsh-pre-push-checks](.agents/skills/dsh-pre-push-checks/SKILL.md) 运行检查；只报告实际跑过的命令。`gh stack sync` 之后立刻验证；检查未通过不得合并。

- 证据要对准改动面：行为用针对性测试，模型或用户输出用快照，文档用 `doc-sync`，已发布路径用构建/hygiene 与已构建冒烟测试，提供方行为用真实 API 的 e2e。
- 提交或推送时，不要默认跑全套，也不要重复已通过的检查。穷尽覆盖和平台矩阵由 CI 负责；只有在明确要求、诊断 CI，或改动无法缩小到仓库局部时，才在本地把全部检查走一遍。
- CI 覆盖率门禁是 `test:coverage`，不是 `test`（[原因](docs/testing.md)）。

## 密钥 / .env

真实 API 测试和演示读取 `DEEPSEEK_API_KEY`、可选的 `DEEPSEEK_BASE_URL` 以及根目录 `.env`。cordis.yml 只允许在插件 `config` 和配置项 `disabled` 下使用 `!!js`（绝不用 `!js`）；其余元数据保持字面量，因此条件组合也使用 overlay（[入门](docs/cordis-primer.md#loader-configuration)）。永远不要提交凭证。没有密钥时 CI e2e 会跳过；密钥政策由 [testing.md](docs/testing.md) 规定。

## 约定

- 每个 npm 包都是 `@deepseek-ai/dsh-<name>`；内嵌包会重定作用域（[映射](docs/rescope.md)）且 `private: true`。`@deepseek-ai/cordis` 是每个 harness 包的对等依赖（peer dependency）（外加 dev）。
- 全部使用 ESM（`"type": "module"`）。跨包用包名，本地相对导入用 `.ts`。配置子进程在普通 Node 下运行已构建的 `lib/`；源码回归测试使用其声明的启动器（[测试政策](docs/testing.md#test-subprocess-launch-modes)）。`dsh` CLI 的源码启动走 tsx 的仅 ESM 钩子（`node --import tsx/esm`）；它能到达的模块必须保持 ESM（不能只有 CJS 导出）——在所支持的引擎范围内无法使用 Node 原生 TypeScript 模式（[源码启动约定](.agents/notes/implemented/architecture/2026-07-29-dsh-source-launch-tsx-esm.md)）。Raw/Web `cordis.yml` 中的裸插件名必须出现在其解析器 manifest（元数据清单）的 `dependencies` 里；由 `verify-cordis-config` 强制检查。
- **注册都是 effect**：每一项贡献都经 `ctx.effect()` / `ctx.on()`；注册表的 `register()` 返回 disposer。
- **运行时不变量断言的是所拥有的关系。** 检查权威事件流或可变数据，而不是服务或方法是否存在、插件元数据或 effect，也不是固定的纯示例。若没有说得通的关系，带说明的空配套才是正确的（[包不变量规则](packages/AGENTS.md)）。
- **带类型的事件使用声明合并**以及可合并扩展的映射。事件 JSDoc 需要 `@mode` 和载荷 `@param`；载荷中没有的作用域键需要 `@dshScopeScan unsupported`。公开服务方法要文档化参数和非 void 返回值。`SessionEventMap` 成员默认是读取时必需的——不认识其类型的构建会拒绝该日志，除非事件带有信封上的 `ignorable: true`；只有结构格式变化才提升 `SESSION_FORMAT_VERSION`（[机制](.agents/notes/implemented/architecture/2026-08-10-session-log-version-mechanism.md)）。
- **按判别标签做 switch。** 封闭联合以 `assertNever` 收尾；可合并扩展的联合落入有文档说明的 default。
- **waterfall（瀑布式事件）监听器必须调用 `next()`** 才能委托；不调用就返回会短路整条链（[语义](docs/cordis-primer.md#cordis-waterfall-semantics)）。
- **模型可见 ⟺ 已记录**：任何进入模型请求的内容都必须能从会话日志重建；新增模型可见输入需要一条会话事件。
- **用插件，而不是改循环**：新行为走已文档化的扩展点；改 `agent-loop` 必须同时更新 docs/architecture.md。
- **一个能力 seam 由 Service Definition / Service Provider / 消费方三种角色组成。** 必须完整，绝不能只有一种角色；仅当角色需要独立演化时才拆分（[词汇表](docs/glossary.md#capability-seam)）。
- **优先使用有人维护的依赖，而不是手写**，前提是它们确实能删掉自有代码和测试（[政策](.agents/notes/implemented/process/2026-07-26-dependencies-over-hand-rolling.md)）。
- **包边界上显式优于隐式**：默认值是所属实现里显式的 `resolve(request): Spec` 步骤，绝不是 `run()` 里隐藏的 `?? default`（以 `dsh-shell` 的 request/spec 拆分为模板）。
- **插件里不要硬编码可调参数**：随部署变化的选择应是可通过 cordis.yml 修改、且经过校验的 `Config` 字段；`DEFAULT_*` 常量或测试钩子不算可配置。协议常量、外部规范和安全不变量保持固定。
- **错误配置要大声失败**：能自洽判断时在加载时失败，否则在最早可解析的点失败；绝不要静默跳过缺失的引用对象。
- **跨边界的不透明 id 使用品牌类型**（`dsh-brand` 的 `Branded<B>`），绝不用裸 `string`。
- **在带类型的同进程边界上信任 TypeScript。** 不要仅为静态接口已要求的值再加运行时校验、回退行为或恶意输入测试；在解析器/配置、队列、模型/工具 JSON、持久化/文件、worker、进程和协议边界上校验。
- **源码平面与产物平面，绝不混用。** 静态门禁和测试通过 tsconfig `paths` 把工作区导入解析到 `src`，并在干净树上通过；消费已构建 `lib/` 的门禁必须声明该依赖（[布局](docs/development.md#typescript-project-layout)）。
- **编译器面要显式。** 每个包使用一个聚合，`api/remotes` 除外；仓库级程序从某个面配置播种，绝不用根解决方案（[布局](docs/development.md#typescript-project-layout)）。
- **空的 `catch` 要写明它吞掉了什么**，以及为什么没有别的东西能到达那里；`try` 只保留一条语句。
- 不要注释代码已经能看出来的事实。
- **并列的值优先写成对称形式**；说不清的不对称通常说明漏了一次抽取。
- **测试描述行为，而不是正确性。** 过时行为连同测试一起改；在 PR（Pull Request）里说明原因。
- **非琐碎改动必须在同一 PR 里包含一份 Agent Note；** 只有机械性/局部编辑可豁免（[范围](.agents/notes/README.md#when-to-write-one)）。已归档的 note 是冻结的：绝不要编辑，也绝不要当作当前权威（[归档政策](.agents/notes/README.md#archiving-and-deletion)）。
- **测试政策** — [docs/testing.md](docs/testing.md)。每一项非琐碎的、模型或产品用户可见的行为变化，都要在同一 PR 里通过真实可运行示例新增或更新无需密钥的快照；包测试、仅 e2e 断言和仅 mock 的 fixture（测试前置数据）不能替代已组装应用的 transcript（文本记录）。fixture 必须能在 macOS/Linux 上回放；修 fixture，而不是修归一化器。
- **工具的 UI 渲染意图是设计的一部分**，要事先决定（`generic`/`terminal`/`diff`、`locations`）；展示方法是 `args` 的纯函数（[实操手册](docs/cookbook/adding-a-tool.md)）。
- **为能力 seam、生命周期路径和 transcript 输出规划单元、e2e 和快照覆盖**；缺失的快照 harness 支持要放进同一次改动。
- **有意识地选择 PR 历史。** 独立改动拆开；先修引入该问题的 PR，再向外传播。独立 PR 和官方 stack 在评审后可以 merge-forward 或 rebase。重写使用 `--force-with-lease`，远端有移动则中止，绝不用裸 `--force`；进行中的 merge-forward 在接更新的 base 之前先保住检查点（[理由](.agents/notes/implemented/process/2026-08-02-native-github-stacks-and-optional-rebases.md)）。
- **标签：** 每个 PR 一个 `kind/*`，所有实质性改动都打 `area/*`，以及原生 Issue Type（[分类体系](.agents/notes/implemented/process/2026-08-08-unified-github-label-taxonomy.md)）。
- TODO 标记：按紧急程度使用 `FIXME`/`TODO`/`XXX`（[语义](docs/development.md)）。
- 文件末尾恰好一个换行；由 `git diff --cached --check`（pre-commit）门禁检查。

## 防御模式

做生命周期、并发、子进程或拆除相关工作前，先读 [docs/defensive-patterns.md](docs/defensive-patterns.md)。

## 类型安全与文档

一切都在 `strict: true` 且 `noImplicitAny` 下编译；每一个残留的 `any` 都要说明为何无法收窄。每个模块和导出都有简洁 JSDoc，说明非显而易见的约定；函数式导出包含 `@param`/`@returns`，由 `verify-export-jsdoc` 强制。继承声明的成员、插件协议 slot 和构造函数，把文档留在声明它们的 Service Definition、协议或类上。

注释和文档陈述完整约定与上下文，而不是推理过程记录。用直接、具体的词。不要用比喻。写 `contract`、`boundary` 或 `shape` 之前，先问有没有更精确的词能点名对象：写 `response fields`、`JSON validation` 或 `ESM exports`，而不是 `response shape`、`validation boundary` 或 `module shape`。`contract` 只用于前置条件、后置条件、不变量、兼容承诺，以及其他调用方、被调用方、实现者、提供方、生产者或消费方所依赖的义务。保留字面意义上的进程、协议、安全、事务或生命周期边界。不要叙述控制流或测试，不要保留评审历史，也不要复述代码。保留行为、失败、时机、所有权和安全使用事实；理由用链接。决策见 [dsh-prose-standard](.agents/skills/dsh-prose-standard/SKILL.md)。把可机械检查的不变量接到已执行的顶层门禁上，并证明每条被改过的接受路径都会拒绝无效情形。用狭窄、有理由的例外，而不是全局关掉一条规则。

每次代码改动都要带文档：受影响的 README 和 JSDoc 约定一并更新。日常双语工作遵循 [docs/AGENTS.md](docs/AGENTS.md)；只有用户明确要求时才可运行 `dsh-translate-docs`。当前状态行文、每段一行、一事实一处、以及字数预算都在那里。

## 编辑这些说明

`CLAUDE.md` 在根目录、`packages/` 和 `examples/` 符号链接到 `AGENTS.md`；编辑真正的那份文件。每条规则自成一体，同时链接高层文档。在仍能保持清楚的前提下压缩；所需内容确实需要更多篇幅时，再提高 `verify-doc-budgets` 上限。

## 内嵌政策

`vendor/` 包是钉死的源码副本（带上游 SHA 的清单见 [vendor/README.md](vendor/README.md)）。按那里的同步流程更新；重新应用或废弃已记录的本地修改；再跑 `pnpm run test && pnpm run build`。
