/** 本包内嵌 EVENT_API 分片 02（对照原版 api-catalog.ts） */
export const EVENT_API: readonly EventApiEntry[] = [//事件目录
  {//事件
    name: 'goal/changed',
    mode: 'emit',//分发模式
    signature: '\'goal/changed\'(this: import(\'@deepseek-ai/dsh-scope\').Scoped<Agent>, payload: { agent: Agent; change: GoalChanged }): void',
    summary: 'Goal mutation accepted by one live agent.',
    description: 'Goal mutation accepted by one live agent. The matching `goal/change` session event has already committed. Listener failures are contained. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): agent-scoped listeners receive only that agent.',
    parameters: [{ name: 'payload', description: '.change - fresh current projection or clear tombstone.' }],
  },
  {//事件
    name: 'llm/adapters-updated',
    mode: 'emit',//分发模式
    signature: '\'llm/adapters-updated\'(): void',
    summary: 'The provider topology changed: an adapter registered or unregistered routes, or the configurable-provider directory gained or lost entries.',
    description: 'The provider topology changed: an adapter registered or unregistered routes, or the configurable-provider directory gained or lost entries. This payload-free registry notification fires at each commit point (including registration disposal); consumers re-read `listProviders()`, `listModels()`, or `listConfigurableProviders()` for the new state. Observer failures are contained and cannot veto the registry mutation.',
    parameters: [],//无参数
  },
  {//事件
    name: 'llm/stream',
    mode: 'waterfall',//分发模式
    signature: '\'llm/stream\'(this: LlmRuntime, options: GenerateOptions, next: () => AsyncIterable<StreamChunk>): AsyncIterable<StreamChunk>',
    summary: 'Waterfall around every streaming model call (retry, replay, routing).',
    description: 'Waterfall around every streaming model call (retry, replay, routing). Bound to the LlmRuntime; call `next()` to reach the resolved adapter\'s stream, or yield your own chunks to short-circuit.',
    parameters: [{ name: 'options', description: 'the full request. A LOOP-built request carries the process-local {@link markAgentLoopRequest} identity and arrives deep-frozen (mutation throws): its content is a pure function of the session log (the reconstructability Agent Note), so listeners read it, never rewrite it. Hand-built calls do not carry that marker; their messages already obey the immutable creation contract.' }],
  },
  {//事件
    name: 'session-telemetry/record',
    mode: 'waterfall',//分发模式
    signature: '\'session-telemetry/record\'(record: SessionTelemetryRecord, next: () => SessionTelemetryRecord): SessionTelemetryRecord',
    summary: 'Transform one outbound record before it reaches the backend.',
    description: 'Transform one outbound record before it reaches the backend. This waterfall is the Service Definition\'s redaction extension point. It ships NO rules of its own: the innermost `next()` passes the record through unchanged, and with no listener mounted records reach the backend as captured, so exported data is exactly as clean as the rules a deployment mounts. Listeners stack by transforming `next()`\'s return value; returning without `next()` replaces everything beneath. Dispatched synchronously on the capture hot path inside the coordinator\'s containment: a throwing listener withholds that one record (fail-closed) and never reaches the agent loop. Live capture dispatches at append time; on-demand capture dispatches while reading the canonical log. Redaction applies to the exported copy only; the canonical session log is never rewritten.',
    parameters: [{ name: 'record', description: 'the candidate record, already the coordinator\'s own deep copy; listeners return a (possibly new) record and must not mutate it.' }],
  },
  {//事件
    name: 'session/created',
    mode: 'emit',//分发模式
    signature: '\'session/created\'(this: Scoped<Session>, session: Session): void',
    summary: 'Creation announcement during session publication.',
    description: 'Creation announcement during session publication. A synchronous throw vetoes and rolls back with a paired disposal; detach requested during dispatch is deferred. A returned-promise rejection is logged but cannot retroactively veto this synchronous boundary. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): agent-scoped listeners receive only sessions entered through that agent\'s context.',
    parameters: [{ name: 'session', description: 'the session just entered and announced.' }],
  },
  {//事件
    name: 'session/disposed',
    mode: 'emit',//分发模式
    signature: '\'session/disposed\'(this: Scoped<Session>, session: Session): void',
    summary: 'Emitted once when an announced session leaves the store, including publication rollback, but never for an entry whose creation announcement did not begin.',
    description: 'Emitted once when an announced session leaves the store, including publication rollback, but never for an entry whose creation announcement did not begin. Listener failures are logged and contained. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`) reuses the owner scope.',
    parameters: [{ name: 'session', description: 'the session that is no longer live in the store.' }],
  },
  {//事件
    name: 'session/event',
    mode: 'emit',//分发模式
    signature: '\'session/event\'(this: Scoped<Session>, session: Session, event: SessionEvent): void',
    summary: 'Post-commit, fire-and-forget append feed.',
    description: 'Post-commit, fire-and-forget append feed. The listener snapshot resolves before the log push, but callbacks run after it; observer failures are logged and contained without making the committed append fail. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): agent-scoped listeners receive only events from sessions entered through that agent\'s context.',
    parameters: [{ name: 'session', description: 'the session whose log grew.' }, { name: 'event', description: 'the appended event, exactly as recorded.' }],
  },
  {//事件
    name: 'session/flush',
    mode: 'parallel',//分发模式
    signature: '\'session/flush\'(this: Scoped<Session>, session: Session): Promise<void> | void',
    summary: 'Awaited parallel durability checkpoint: every listener runs and the caller awaits all of them, with no waterfall veto.',
    description: 'Awaited parallel durability checkpoint: every listener runs and the caller awaits all of them, with no waterfall veto. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`) reuses the session\'s owner scope.',
    parameters: [{ name: 'session', description: 'the session whose buffered events must reach durable storage.' }],
  },
  {//事件
    name: 'settings/document-updated',
    mode: 'emit',//分发模式
    signature: '\'settings/document-updated\'(ns: SettingsNamespace, revision: number): void',
    summary: 'One registered namespace\'s RAW user section changed, whether or not the resolved value did.',
    description: 'One registered namespace\'s RAW user section changed, whether or not the resolved value did. `settings/updated` is the consumer-facing event and stays deep-equal-gated; this one exists for configuration surfaces, which must learn that a field went from inherited to overridden (same resolved value, different meaning) and that their held revision is stale. Listener containment matches `settings/updated`.',
    parameters: [{ name: 'ns', description: 'the namespace whose stored section changed.' }, { name: 'revision', description: 'the namespace\'s new revision.' }],
  },
  {//事件
    name: 'settings/updated',
    mode: 'emit',//分发模式
    signature: '\'settings/updated\'(ns: SettingsNamespace, next: unknown, prev: unknown, source: SettingsUpdateSource): void',
    summary: 'Committed change to one registered namespace\'s resolved value.',
    description: 'Committed change to one registered namespace\'s resolved value. Emitted after the provider persisted (for `update`) or published (`provider`) the change; never emitted when the resolved value is deep-equal. Listener failures are contained and logged — a sync throw and an async rejection alike — except `INVARIANT`-coded failures, which rethrow after every listener ran; that rethrow reaches the emitter only from synchronous listeners, so invariant checks on this event must not be async functions.',
    parameters: [{ name: 'ns', description: 'the namespace whose resolved value changed.' }, { name: 'next', description: 'the new resolved value.' }, { name: 'prev', description: 'the previous resolved value.' }, { name: 'source', description: 'whether the change entered through `update()` or the provider.' }],
  },
  {//事件
    name: 'skills/change',
    mode: 'emit',//分发模式
    signature: '\'skills/change\'(): void',
    summary: 'A skill provider, runtime contribution, or provider-backed catalog may have changed.',
    description: 'A skill provider, runtime contribution, or provider-backed catalog may have changed. This is an unfiltered invalidation notification; consumers refetch the catalog for their own lookup options. Listener failures are contained and cannot veto the registry mutation.',
    parameters: [],//无参数
  },
  {//事件
    name: 'subagent/end',
    mode: 'emit',//分发模式
    signature: '\'subagent/end\'(this: Scoped<SubagentRuntime>, info: SubagentRunEndInfo): void',
    summary: 'A published child settled.',
    description: 'A published child settled. Scope-filtered dispatch uses the same delegating parent carrier as `subagent/start`, so the lifecycle pair reaches the same scoped audience.',
    parameters: [{ name: 'info', description: 'the run identity and terminal outcome.' }],
  },
  {//事件
    name: 'subagent/provider-added',
    mode: 'emit',//分发模式
    signature: '\'subagent/provider-added\'(provider: SubagentProvider): void',
    summary: 'A provider became resolvable in the registry.',
    description: 'A provider became resolvable in the registry.',
    parameters: [{ name: 'provider', description: 'the registered provider.' }],
  },
  {//事件
    name: 'subagent/provider-removed',
    mode: 'emit',//分发模式
    signature: '\'subagent/provider-removed\'(name: string): void',
    summary: 'A provider left the registry.',
    description: 'A provider left the registry. Accepted runs remain holder-owned.',
    parameters: [{ name: 'name', description: 'the provider name that no longer resolves.' }],
  },
  {//事件
    name: 'subagent/start',
    mode: 'emit',//分发模式
    signature: '\'subagent/start\'(this: Scoped<SubagentRuntime>, info: SubagentRunInfo): void',
    summary: 'A provider established a published child.',
    description: 'A provider established a published child. For in-process providers, `ctx.agents.get(info.id)` resolves during this notification. Scope-filtered dispatch keys the carrier by the delegating parent, so a parent-scoped listener observes only its own delegations. Paired with `subagent/end`.',
    parameters: [{ name: 'info', description: 'the provider and published child identity.' }],
  },
  {//事件
    name: 'system-prompt/assemble',
    mode: 'waterfall',//分发模式
    signature: '\'system-prompt/assemble\'(this: Scoped<SystemPrompt>, assembly: PromptAssembly, context: AssembleContext, next: () => Promise<PromptAssembly>): Promise<PromptAssembly>',
    summary: 'Expert waterfall over the assembled sections, contexts, tools, and variables.',
    description: 'Expert waterfall over the assembled sections, contexts, tools, and variables. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): scoped listeners receive only that scope\'s assemblies. The returned value is authoritative. A supplied signal controls only this explicit assembly request and must not be retained to control later turns. A registered complete section is restored after this waterfall, so listeners cannot add to or replace that scope\'s system prompt.',
    parameters: [{ name: 'assembly', description: 'the mutable assembly built from registered providers.' }, { name: 'context', description: 'the caller\'s per-assembly context.' }],
  },
  {//事件
    name: 'system-prompt/change',
    mode: 'emit',//分发模式
    signature: '\'system-prompt/change\'(): void',
    summary: 'Emitted when any prompt provider changes.',
    description: 'Emitted when any prompt provider changes. This registry notification is unfiltered because a global change affects every scope.',
    parameters: [],//无参数
  },
  {//事件
    name: 'tools/change',
    mode: 'emit',//分发模式
    signature: '\'tools/change\'(): void',
    summary: 'A tool was registered or unregistered, or a scoped restriction changed (the available tool set changed — possibly for one scope only).',
    description: 'A tool was registered or unregistered, or a scoped restriction changed (the available tool set changed — possibly for one scope only). An UNFILTERED registry-subject notification, deliberately not scope-filtered dispatch: a global change concerns every agent\'s next assembly, so a scoped listener subscribing here sees every change, not just its own scope\'s.',
    parameters: [],//无参数
  },
  {//事件
    name: 'tools/code-dispatch-log',
    mode: 'waterfall',//分发模式
    signature: '\'tools/code-dispatch-log\'(this: Scoped<ToolRuntime>, dispatch: CodeDispatchLog, next: () => Promise<ContentBlock[]>): Promise<ContentBlock[]>',
    summary: 'Allow a listener to replace content in the DURABLE LOG COPY of one `run_code` sub-dispatch outcome before the bridge appends its `tool/code-dispatch` event.',
    description: 'Allow a listener to replace content in the DURABLE LOG COPY of one `run_code` sub-dispatch outcome before the bridge appends its `tool/code-dispatch` event. `next()` keeps the content unchanged; a listener may return replacement blocks (e.g. the spill policy\'s preview + locator for an oversized text result). Only the logged copy is affected — the program already received the complete value, and the model sees neither. A throwing listener is contained: the bridge falls back to logging the original settled content. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): agent-scoped listeners receive only that agent\'s dispatches.',
    parameters: [{ name: 'dispatch', description: 'the parent execution, sub-call identity, and the settled content to log.' }],
  },
  {//事件
    name: 'tools/execute',
    mode: 'waterfall',//分发模式
    signature: '\'tools/execute\'(this: Scoped<ToolRuntime>, exec: ToolDispatchExecution, next: () => Promise<ToolExecutionResult>): Promise<ToolExecutionResult>',
    summary: 'Around-dispatch waterfall for timeout, retry, or metrics.',
    description: 'Around-dispatch waterfall for timeout, retry, or metrics. `next()` returns a normalized result; wrappers may change only `exec.signal`, while call identity remains immutable. The registry re-fuses the original caller signal before the body, so replacement cannot detach caller cancellation; wrappers must still restore their signal and reach quiescence. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): agent-scoped listeners receive only that agent\'s calls.',
    parameters: [{ name: 'exec', description: 'the allowed call about to dispatch (name, parsed arguments, caller agent, signal).' }],
  },
  {//事件
    name: 'tools/post-execute',
    mode: 'waterfall',//分发模式
    signature: '\'tools/post-execute\'(this: Scoped<ToolRuntime>, exec: ToolExecution, result: Readonly<ToolExecutionResult>, next: () => Promise<PostToolDecision>): Promise<PostToolDecision>',
    summary: 'Accept, replace, enrich, or block a normalized dispatch result.',
    description: 'Accept, replace, enrich, or block a normalized dispatch result. `next()` accepts it unchanged; thrown tools still reach this waterfall as errors. Async listeners must observe `exec.signal`; after they settle, caller cancellation replaces only a successful accepted outcome with the code selected by whether the tool body was invoked. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): agent-scoped listeners receive only that agent\'s calls.',
    parameters: [{ name: 'exec', description: 'the call that just ran (name, parsed arguments, caller agent).' }, { name: 'result', description: 'the dispatch outcome a listener may accept, replace, or block.' }],
  },
  {//事件
    name: 'tools/pre-execute',
    mode: 'waterfall',//分发模式
    signature: '\'tools/pre-execute\'(this: Scoped<ToolRuntime>, exec: ToolExecution, next: () => Promise<PreToolDecision>): Promise<PreToolDecision>',
    summary: 'Allow, deny, or ask before dispatch.',
    description: 'Allow, deny, or ask before dispatch. `next()` delegates to allow; missing approval support turns `ask` into denial. Async gates must observe `exec.signal`; the registry rechecks cancellation after they settle but never abandons their promise. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): agent-scoped listeners receive only that agent\'s calls.',
    parameters: [{ name: 'exec', description: 'the pending call (name, parsed arguments, caller agent).' }],
  },
  {//事件
    name: 'tools/result',
    mode: 'emit',//分发模式
    signature: '\'tools/result\'(this: Scoped<ToolRuntime>, exec: Readonly<ToolExecution>, result: Readonly<ToolExecutionResult>): undefined',
    summary: 'Observe the frozen, lossless-JSON final outcome.',
    description: 'Observe the frozen, lossless-JSON final outcome. Listener failures are contained. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): keyed by `exec.agent`.',
    parameters: [{ name: 'exec', description: 'the execution object that traversed the pipeline.' }, { name: 'result', description: 'a deep-frozen snapshot of the final returned result.' }],
  },
  {//事件
    name: 'workflow/agent-end',
    mode: 'emit',//分发模式
    signature: '\'workflow/agent-end\'(info: WorkflowRunInfo, agent: WorkflowAgentEndInfo): void',
    summary: 'One `agent()` call settled (clean result, child failure, or run cancellation).',
    description: 'One `agent()` call settled (clean result, child failure, or run cancellation). Paired with Events[\'workflow/agent-start\'] by `agent.seq`, exactly once per started call on every stop path — on an engine termination path (a worker killed past its grace) the end is engine-synthesized with outcome `\'cancelled\'`.',
    parameters: [{ name: 'info', description: 'the run\'s identity snapshot.' }, { name: 'agent', description: 'the call identity plus its outcome.' }],
  },
  {//事件
    name: 'workflow/agent-start',
    mode: 'emit',//分发模式
    signature: '\'workflow/agent-start\'(info: WorkflowRunInfo, agent: WorkflowAgentInfo): void',
    summary: 'One `agent()` call established a published child run.',
    description: 'One `agent()` call established a published child run. Paired with Events[\'workflow/agent-end\'] by `agent.seq`. A call that never receives a published run from the provider emits neither event in this pair.',
    parameters: [{ name: 'info', description: 'the run\'s identity snapshot.' }, { name: 'agent', description: 'the call\'s sequence number, label, phase, and child id.' }],
  },
  {//事件
    name: 'workflow/end',
    mode: 'emit',//分发模式
    signature: '\'workflow/end\'(info: WorkflowRunInfo, result: WorkflowResultInfo): void',
    summary: 'A workflow run settled (any stop reason).',
    description: 'A workflow run settled (any stop reason). Fired when WorkflowRun.result resolves. Paired with Events[\'workflow/start\'].',
    parameters: [{ name: 'info', description: 'the run\'s identity snapshot.' }, { name: 'result', description: 'the outcome data (stop reason, error, agent count) — deliberately WITHOUT the result value (see {@link WorkflowResultInfo}).' }],
  },
  {//事件
    name: 'workflow/log',
    mode: 'emit',//分发模式
    signature: '\'workflow/log\'(info: WorkflowRunInfo, message: string): void',
    summary: 'The script emitted a narration line (a `log(message)` call).',
    description: 'The script emitted a narration line (a `log(message)` call).',
    parameters: [{ name: 'info', description: 'the run\'s identity snapshot.' }, { name: 'message', description: 'the logged message, verbatim.' }],
  },
  {//事件
    name: 'workflow/phase',
    mode: 'emit',//分发模式
    signature: '\'workflow/phase\'(info: WorkflowRunInfo, title: string): void',
    summary: 'The script entered a phase (a `phase(title)` call) — progress grouping for observers; no execution semantics.',
    description: 'The script entered a phase (a `phase(title)` call) — progress grouping for observers; no execution semantics.',
    parameters: [{ name: 'info', description: 'the run\'s identity snapshot.' }, { name: 'title', description: 'the phase title, verbatim.' }],
  },
  {//事件
    name: 'workflow/start',
    mode: 'emit',//分发模式
    signature: '\'workflow/start\'(info: WorkflowRunInfo): void',
    summary: 'A workflow run started — the script\'s meta block validated, the body about to execute.',
    description: 'A workflow run started — the script\'s meta block validated, the body about to execute. Paired with Events[\'workflow/end\'].',
    parameters: [{ name: 'info', description: 'the run\'s identity snapshot (id + meta).' }],
  },
]
