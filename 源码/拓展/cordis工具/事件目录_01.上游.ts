/** 本包内嵌 EVENT_API 分片 01（对照原版 api-catalog.ts） */
export const EVENT_API: readonly EventApiEntry[] = [//事件目录
  {//事件
    name: 'agent-loop/config-start-failed',
    mode: 'emit',//分发模式
    signature: '\'agent-loop/config-start-failed\'(payload: { sessionId: SessionId; error: unknown }): void',
    summary: 'A declarative agent entry failed before it could publish a live agent.',
    description: 'A declarative agent entry failed before it could publish a live agent. Consumers that buffer work for the configured identity use this transient signal to reject that work instead of waiting forever. Normal factory teardown suppresses failures from the cancelled startup attempt.',
    parameters: [{ name: 'payload', description: '.error - persistence, setup, or publication failure.' }],
  },
  {//事件
    name: 'agent-preset/selected',
    mode: 'emit',//分发模式
    signature: '\'agent-preset/selected\'(sessionId: SessionId, agentPreset: string): void',
    summary: 'One session committed a different agent preset to its durable log.',
    description: 'One session committed a different agent preset to its durable log. Consumers invalidate only state derived from that session\'s composition.',
    parameters: [{ name: 'sessionId', description: 'the session whose composition changed.' }, { name: 'agentPreset', description: 'the preset recorded by the committed selection.' }],
  },
  {//事件
    name: 'agent/created',
    mode: 'emit',//分发模式
    signature: '\'agent/created\'(this: Scoped<Agent>, payload: { agent: Agent }): void',
    summary: 'A fully configured agent and live session were published.',
    description: 'A fully configured agent and live session were published. Setup is composition-only; `agent/session-start` is the first startup-driving extension point. Synchronous listener failure vetoes publication, while returned-promise rejection is reported. Detach requested during dispatch waits until every creation listener has observed the stable entry.',
    parameters: [{ name: 'payload', description: '.agent - the newly registered agent with its live session and completed setup. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): agent-scoped listeners receive only that agent.' }],
  },
  {//事件
    name: 'agent/disposed',
    mode: 'emit',//分发模式
    signature: '\'agent/disposed\'(this: Scoped<Agent>, payload: { agent: Agent }): void',
    summary: 'An agent left the registry; AgentLoop emits this after driver quiescence and scoped-registration unwind, but before session detachment.',
    description: 'An agent left the registry; AgentLoop emits this after driver quiescence and scoped-registration unwind, but before session detachment. Custom registry users own their driver-ordering contract.',
    parameters: [{ name: 'payload', description: '.agent - the exact agent removed from the registry. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): agent-scoped listeners receive only that agent.' }],
  },
  {//事件
    name: 'agent/error',
    mode: 'emit',//分发模式
    signature: '\'agent/error\'(this: Scoped<Agent>, payload: { agent: Agent; turn: number; step: number; error: unknown }): void',
    summary: 'A step or turn errored.',
    description: 'A step or turn errored. The machine reports a failure here even when the error has no in-turn position for a durable record.',
    parameters: [{ name: 'payload', description: '.error - the failure, verbatim. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): agent-scoped listeners receive only that agent.' }],
  },
  {//事件
    name: 'agent/inbox/claimed',
    mode: 'emit',//分发模式
    signature: '\'agent/inbox/claimed\'(this: Scoped<Agent>, payload: { agent: Agent; message: UserMessage; turn: number }): void',
    summary: 'One message left the inbox inside its open turn.',
    description: 'One message left the inbox inside its open turn. If the proposed step is rejected, the claimed message ends here: it is neither discarded nor re-emitted as a user/message, and the turn closes without a step.',
    parameters: [{ name: 'payload', description: '.turn - the owning turn. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): agent-scoped listeners receive only that agent.' }],
  },
  {//事件
    name: 'agent/inbox/discarded',
    mode: 'emit',//分发模式
    signature: '\'agent/inbox/discarded\'(this: Scoped<Agent>, payload: { agent: Agent; message: UserMessage }): void',
    summary: 'One message was discarded from the live inbox.',
    description: 'One message was discarded from the live inbox.',
    parameters: [{ name: 'payload', description: '.message - the discarded message. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): agent-scoped listeners receive only that agent.' }],
  },
  {//事件
    name: 'agent/inbox/inserted',
    mode: 'emit',//分发模式
    signature: '\'agent/inbox/inserted\'(this: Scoped<Agent>, payload: { agent: Agent; message: UserMessage }): void',
    summary: 'One message entered the live inbox.',
    description: 'One message entered the live inbox.',
    parameters: [{ name: 'payload', description: '.message - the inserted message. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): agent-scoped listeners receive only that agent.' }],
  },
  {//事件
    name: 'agent/pre-step',
    mode: 'waterfall',//分发模式
    signature: '\'agent/pre-step\'(this: Scoped<Agent>, payload: { agent: Agent; messages: UserMessage[]; turn: number; step: number; signal: AbortSignal }, next: () => Promise<PreStepDecision>): Promise<PreStepDecision>',
    summary: 'Reject a proposed step or replace the messages that enter it.',
    description: 'Reject a proposed step or replace the messages that enter it. Calling `next()` preserves the current messages.',
    parameters: [{ name: 'payload', description: '.signal - the current turn\'s cancellation signal. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): agent-scoped listeners receive only that agent.' }],
  },
  {//事件
    name: 'agent/request',
    mode: 'waterfall',//分发模式
    signature: '\'agent/request\'(this: Scoped<Agent>, payload: { agent: Agent; turn: number; step: number; signal: AbortSignal }, next: () => Promise<LlmCallConfig>): Promise<LlmCallConfig>',
    summary: 'Replace the frozen call configuration.',
    description: 'Replace the frozen call configuration. `await next()` yields the config the machine would use (agent options on the first request, the logged header afterwards); return a replacement to switch. Model-visible content must use logged channels; this waterfall cannot mutate messages.',
    parameters: [{ name: 'payload', description: '.signal - the current turn\'s explicit abort signal. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): agent-scoped listeners receive only that agent.' }],
  },
  {//事件
    name: 'agent/request-error',
    mode: 'waterfall',//分发模式
    signature: '\'agent/request-error\'(this: Scoped<Agent>, payload: { agent: Agent; turn: number; step: number; provider: string; failure: LlmFailure; retryPolicy: ResolvedRetryPolicy | undefined; signal: AbortSignal }, next: () => Promise<RequestErrorAction>): Promise<RequestErrorAction>',
    summary: 'Handle one failed model-request attempt before the loop retries or closes its step.',
    description: 'Handle one failed model-request attempt before the loop retries or closes its step. A listener returns `{ kind: \'retry\' }` without calling `next()` when it owns recovery, or calls `next()` to delegate. The default `undefined` leaves the failure terminal.',
    parameters: [{ name: 'payload', description: '.signal - the turn abort signal. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): agent-scoped listeners receive only that agent.' }],
  },
  {//事件
    name: 'agent/session-start',
    mode: 'emit',//分发模式
    signature: '\'agent/session-start\'(this: Scoped<Agent>, payload: { agent: Agent; source: SessionStartSource }): void',
    summary: 'The session lifecycle began, once before the first turn.',
    description: 'The session lifecycle began, once before the first turn. Use `agent.inject()` to seed model-facing context. This is a notification, not a veto; disposal requested by a lifecycle owner is rechecked before the driver starts.',
    parameters: [{ name: 'payload', description: '.source - why the session started (fresh startup, resume, …). Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): agent-scoped listeners receive only that agent.' }],
  },
  {//事件
    name: 'agent/status',
    mode: 'emit',//分发模式
    signature: '\'agent/status\'(this: Scoped<Agent>, payload: { agent: Agent; status: AgentStatus }): void',
    summary: 'Agent status changed (`idle` ⇄ `running`).',
    description: 'Agent status changed (`idle` ⇄ `running`). A waking delivery enters `running` synchronously after reserving cancellation; `idle` means no driver remains scheduled or active.',
    parameters: [{ name: 'payload', description: '.status - the status just entered (the transition\'s destination). Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): agent-scoped listeners receive only that agent.' }],
  },
  {//事件
    name: 'agent/turn-stopping',
    mode: 'serial',//分发模式
    signature: '\'agent/turn-stopping\'(this: Scoped<Agent>, payload: { agent: Agent; turn: number; signal: AbortSignal }): Promise<void> | void',
    summary: 'The turn is about to close: the model owes no response (no live tool calls, no fresh steering).',
    description: 'The turn is about to close: the model owes no response (no live tool calls, no fresh steering). Awaited before the boundary commits — a listener that objects steers (`agent.steer(...)`) and the machine re-reads its inbox: fresh steering runs another step, none closes the turn. Data decides, so listener order cannot change the outcome. The inverse control (stop a tool loop early) is data too: a tool result carrying `concludesTurn` ends the turn at its step. The conclusion never short-circuits already-submitted next-step work: same-step `additionalContexts` or racing steering still runs, and the turn closes only when that inbox drains.',
    parameters: [{ name: 'payload', description: '.signal - the current turn\'s explicit abort signal. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): agent-scoped listeners receive only that agent.' }],
  },
  {//事件
    name: 'approval/request',
    mode: 'waterfall',//分发模式
    signature: '\'approval/request\'(this: Scoped<ApprovalService>, req: ApprovalRequest, next: () => Promise<ApprovalOutcome>): Promise<ApprovalOutcome>',
    summary: 'Ask composed answerers for one decision.',
    description: 'Ask composed answerers for one decision. Return an outcome to claim the request or call `next()`; failure yields the fail-closed default. Scope-filtered dispatch (`@deepseek-ai/dsh-scope`): agent-scoped listeners receive only that agent.',
    parameters: [{ name: 'req', description: 'the pending decision (agent, tool identity, reason, signal).' }],
  },
  {//事件
    name: 'commands/change',
    mode: 'emit',//分发模式
    signature: '\'commands/change\'(): void',
    summary: 'A command was registered or unregistered.',
    description: 'A command was registered or unregistered. This is an unfiltered registry notification because a global or scoped change may affect any UI view. Observer failures are contained and cannot veto the registry mutation.',
    parameters: [],//无参数
  },
  {//事件
    name: 'cordis/dynamic-package',
    mode: 'emit',//分发模式
    signature: '\'cordis/dynamic-package\'(pkg: DynamicCordisPackage): void',
    summary: 'One exact Plugin/Package activation is now live in the Host.',
    description: 'One exact Plugin/Package activation is now live in the Host.',
    parameters: [{ name: 'pkg', description: 'stable plugin, immutable package, run identity, and label.' }],
  },
  {//事件
    name: 'cordis/dynamic-retract',
    mode: 'emit',//分发模式
    signature: '\'cordis/dynamic-retract\'(retracted: DynamicCordisRetracted): void',
    summary: 'One exact activation was withdrawn.',
    description: 'One exact activation was withdrawn.',
    parameters: [{ name: 'retracted', description: 'plugin, package, and run identity.' }],
  },
  {//事件
    name: 'cordis/inspect-query',
    mode: 'emit',//分发模式
    signature: '\'cordis/inspect-query\'(request: CordisInspectQueryRequest): void',
    summary: 'Request a live read-only query from the Client inspect registry.',
    description: 'Request a live read-only query from the Client inspect registry.',
    parameters: [{ name: 'request', description: 'correlation, Session, provider, method, and JSON input.' }],
  },
  {//事件
    name: 'cordis/inspect-query-resolved',
    mode: 'emit',//分发模式
    signature: '\'cordis/inspect-query-resolved\'(resolved: CordisInspectQueryResolved): void',
    summary: 'Notify every Client that an inspect query has settled or been cancelled.',
    description: 'Notify every Client that an inspect query has settled or been cancelled.',
    parameters: [{ name: 'resolved', description: 'exact query identity that is no longer answerable.' }],
  },
  {//事件
    name: 'cordis/request-run',
    mode: 'emit',//分发模式
    signature: '\'cordis/request-run\'(request: DynamicCordisRunRequest): void',
    summary: 'A Client-bearing activation needs a browser page, and may require a user decision.',
    description: 'A Client-bearing activation needs a browser page, and may require a user decision.',
    parameters: [{ name: 'request', description: 'correlation identity, owner, target version, mode, and approval requirement.' }],
  },
  {//事件
    name: 'cordis/request-run-resolved',
    mode: 'emit',//分发模式
    signature: '\'cordis/request-run-resolved\'(resolved: DynamicCordisRequestResolved): void',
    summary: 'A pending Client activation request left the answerable state.',
    description: 'A pending Client activation request left the answerable state.',
    parameters: [{ name: 'resolved', description: 'request identity and outcome.' }],
  },
  {//事件
    name: 'credentials/updated',
    mode: 'emit',//分发模式
    signature: '\'credentials/updated\'(ref: CredentialRef): void',
    summary: 'Committed change to a provider-managed credential source: a `set`, an `unset`, or an external edit observed in storage.',
    description: 'Committed change to a provider-managed credential source: a `set`, an `unset`, or an external edit observed in storage. Ambient process-environment changes are not observable and never emit. Listener failures are contained and logged — a sync throw and an async rejection alike — without changing the committed operation\'s outcome, except `INVARIANT`-coded failures, which rethrow after every listener ran; that rethrow reaches the emitter only from synchronous listeners, so invariant checks on this event must not be async functions.',
    parameters: [{ name: 'ref', description: 'the reference whose stored value changed.' }],
  },
  {//事件
    name: 'domain/changed',
    mode: 'emit',//分发模式
    signature: '\'domain/changed\'(change: DomainChanged): void',
    summary: 'A domain record or the global singleton changed, emitted once per write strictly after the backend acknowledged durability.',
    description: 'A domain record or the global singleton changed, emitted once per write strictly after the backend acknowledged durability. Events of one domain arrive in its write-chain order.',
    parameters: [{ name: 'change', description: 'domain, table (`\'\'` for global), key (`\'\'` for global), operation discriminant, and on `put` the new snapshot.' }],
  },
  {//事件
    name: 'fs/edit-intent',
    mode: 'waterfall',//分发模式
    signature: '\'fs/edit-intent\'(target: FsTarget, actor: object | undefined, next: () => { version: FsVersion } | undefined | Promise<{ version: FsVersion } | undefined>): Promise<{ version: FsVersion } | undefined>',
    summary: 'Single-slot decision for the next FileSystem.editText.',
    description: 'Single-slot decision for the next FileSystem.editText. Calling `next()` yields an unconditional edit; the first returned guard wins.',
    parameters: [{ name: 'target', description: 'the resolved target about to be edited.' }, { name: 'actor', description: 'the opaque tool-execution context the decider keys off.' }],
  },
  {//事件
    name: 'fs/observed',
    mode: 'emit',//分发模式
    signature: '\'fs/observed\'(target: FsTarget, observation: FsObservation, actor: object | undefined): void',
    summary: 'Record an authoritative positive or negative observation.',
    description: 'Record an authoritative positive or negative observation. Listeners must be synchronous recorders: throws fail the tool call and returned promises are not awaited.',
    parameters: [{ name: 'target', description: 'the target whose presence or absence was observed.' }, { name: 'observation', description: 'present with its version, or confirmed absent.' }, { name: 'actor', description: 'the observing tool-execution context; undefined records nothing useful.' }],
  },
  {//事件
    name: 'fs/write-intent',
    mode: 'waterfall',//分发模式
    signature: '\'fs/write-intent\'(target: FsTarget, actor: object | undefined, next: () => FsWriteIntent | undefined | Promise<FsWriteIntent | undefined>): Promise<FsWriteIntent | undefined>',
    summary: 'Single-slot decision for the next FileSystem.writeText.',
    description: 'Single-slot decision for the next FileSystem.writeText. Calling `next()` yields the bare provider\'s unconditional write; the first listener that returns an intent owns the decision rather than composing with peers.',
    parameters: [{ name: 'target', description: 'the resolved target about to be written.' }, { name: 'actor', description: 'the opaque tool-execution context the decider keys off.' }],
  },
]
