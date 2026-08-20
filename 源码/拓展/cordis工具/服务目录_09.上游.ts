/** 本包内嵌 SERVICE_API 分片 09（对照原版 api-catalog.ts）：lsp..sandboxPolicy */
export const SERVICE_API: readonly ServiceApiEntry[] = [//服务目录
  {//服务
    key: 'lsp',
    summary: 'The LSP capability seam (`ctx.lsp`).',
    description: 'The LSP capability seam (`ctx.lsp`). Owns provider registration/selection and normalized query execution; exposes exactly the four operations and no protocol escape hatch.',
    methods: [//公开方法
      {//方法
        signature: 'registerProvider(provider: LspProvider): () => void',
        description: 'Register a provider, atomically reserving its id and every normalized extension. Any conflict or invalid input publishes nothing and throws `LspError`; the returned disposer releases all reservations. Disposed with the calling fiber.',
        parameters: [{ name: 'provider', description: 'the backend to register.' }],
        returns: 'a synchronous disposer releasing the id and all extension reservations.',
      },//结束方法
      {//方法
        signature: 'query(request: LspQueryRequest, signal?: AbortSignal): Promise<LspQueryResult>',
        description: 'Select a provider by the file\'s extension and run one query. Selection is per-query and order-independent; no match throws `LspError` `LSP_UNAVAILABLE`.',
        parameters: [{ name: 'request', description: 'the normalized query.' }, { name: 'signal', description: 'optional cancellation forwarded to the selected provider.' }],
        returns: 'the normalized, closed-union result.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'messageFeedback',
    summary: 'Storage-domain sidecar service.',
    description: 'Storage-domain sidecar service. It inspects persisted Session history and never creates or resumes an Agent or Session.',
    methods: [//公开方法
      {//方法
        signature: '@Remote(\'list\') async list(request: MessageFeedbackListRequest): Promise<MessageFeedbackListResult>',
        description: 'Read feedback belonging to the current persisted Session lifecycle. A stale row from a reused Session id is invisible.',
        parameters: [{ name: 'request', description: 'Session identity to inspect and list.' }],
        returns: 'current immutable items or `session-not-found`.',
      },//结束方法
      {//方法
        signature: '@Remote(\'put\') put(request: MessageFeedbackPutRequest): Promise<MessageFeedbackPutResult>',
        description: 'Create or replace feedback for one derived append-origin assistant message. Every request must match the addressed item\'s current version; a matching no-op returns the stored item without changing its revision.',
        parameters: [{ name: 'request', description: 'target, desired value, and observed item version.' }],
        returns: 'the committed item or an explicit business failure.',
      },//结束方法
      {//方法
        signature: '@Remote(\'delete\') delete(request: MessageFeedbackDeleteRequest): Promise<MessageFeedbackDeleteResult>',
        description: 'Delete one feedback item. Absence is successful regardless of the supplied version; an existing item requires an exact version match.',
        parameters: [{ name: 'request', description: 'Session, message, and observed item version.' }],
        returns: 'the stable absent postcondition, or an explicit failure.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'permissionPresets',
    summary: 'Owns the deployment\'s permission presets and their write path.',
    description: 'Owns the deployment\'s permission presets and their write path. Requires a confining `ctx.shell` executor and `ctx.approval`; unmatched knob values are reported as CUSTOM_PRESET, not an error.',
    methods: [//公开方法
      {//方法
        signature: 'current(events: readonly SessionEvent[]): string',
        description: 'Resolve the preset matching the effective knob values. A still-matching last selection wins shared-bundle ties; otherwise the first table match wins, or CUSTOM_PRESET when no entry matches.',
        parameters: [{ name: 'events', description: 'the session\'s events in log order.' }],
        returns: 'the effective preset name, or `custom` when nothing matches.',
      },//结束方法
      {//方法
        signature: 'selectFor(state: KnobState): PermissionSelect',
        description: 'Build the whole select value for one folded knob state: every table option in declaration order, `custom` appended exactly while derived.',
        parameters: [{ name: 'state', description: 'the folded knob overrides.' }],
        returns: 'the `permissions` projection payload.',
      },//结束方法
      {//方法
        signature: 'resolve(name: string): PresetSpec',
        description: 'Resolve a preset\'s knob bundle.',
        parameters: [{ name: 'name', description: 'the preset name to resolve.' }],
        returns: 'the configured bundle.',
        throws: ['when `name` is not in the table.'],
      },//结束方法
      {//方法
        signature: 'optionOf(name: string): PresetOption',
        description: 'Build the client option for a table entry or CUSTOM_PRESET. A missing label falls back to the table key.',
        parameters: [{ name: 'name', description: 'a table key, or `custom`.' }],
        returns: 'the option a client renders.',
        throws: ['when `name` is neither a table key nor `custom`.'],
      },//结束方法
      {//方法
        signature: 'set(session: Session, name: string): void',
        description: 'Record a changed preset, then update each changed knob through its own setter. Selecting the effective preset again appends nothing.',
        parameters: [{ name: 'session', description: 'the session the switch belongs to.' }, { name: 'name', description: 'the preset to switch to; unknown names throw.' }],
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'planMode',
    summary: '`ctx.planMode`: owns logged plan state, applies and narrates selected state at step start, the `plan:policy` section, the `/plan` command, and the stable exit tool.',
    description: '`ctx.planMode`: owns logged plan state, applies and narrates selected state at step start, the `plan:policy` section, the `/plan` command, and the stable exit tool. UIs observe committed flips through `session/event`; there is no live mirror.',
    methods: [//公开方法
      {//方法
        signature: 'get(agent: Agent): { active: boolean; pending?: boolean }',
        description: 'Read the logged plan state and any selected state awaiting the next accepted in-turn pre-step.',
        parameters: [{ name: 'agent', description: 'The agent to read.' }],
        returns: 'Current logged state plus a pending selection, when present.',
      },//结束方法
      {//方法
        signature: 'set(agent: Agent, active: boolean): \'committed\' | \'queued\' | \'cancelled\' | \'noop\'',
        description: 'Select whether plan mode should be active. Between turns the method appends the change immediately because no in-turn pre-step will run until another prompt starts a turn. The open-turn fold is the idle signal: agent status stays `running` through post-turn checkpointing, when no further in-turn pre-step runs. During an open turn the selection remains pending until the next accepted in-turn pre-step. Repeated selection of the current or already-pending state is a no-op.',
        parameters: [{ name: 'agent', description: 'The agent to switch.' }, { name: 'active', description: 'Whether plan mode should be active.' }],
        returns: 'what happened: `committed` (logged now), `queued` (awaiting the next accepted in-turn pre-step), `cancelled` (an opposite pending selection was cleared; the logged state already matches), or `noop` (already in that state).',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'sandbox',
    summary: 'Abstract process-sandbox service.',
    description: 'Abstract process-sandbox service. confine must return enforcing argv or fail closed at wrap or runner-execution time; silent unconfined passthrough is forbidden. Functional probes arbitrate multi-runner chains and may be skipped for a sole candidate, whose own refusal remains the fail-closed end.',
    methods: [//公开方法
      {//方法
        signature: 'abstract confine(argv: readonly string[], policy: SandboxPolicy): ConfinedArgv',
        description: 'Wrap `argv` so it executes confined under `policy` on this host; the caller spawns the returned argv in place of its own.',
        parameters: [{ name: 'argv', description: 'the exact argv the caller is about to spawn (program plus arguments), NOT a shell string — a shell-shaped consumer passes `[\'bash\', \'-c\', command]`.' }, { name: 'policy', description: 'the file-effect policy this execution runs under, carried per call (see {@link SandboxPolicy}).' }],
        returns: 'the argv to spawn instead, plus the enforcement completeness the selected backend achieves for it.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'sandboxPolicy',
    summary: 'The sandbox-policy service (`ctx.sandboxPolicy`).',
    description: 'The sandbox-policy service (`ctx.sandboxPolicy`). Owns the deployment default mode, fallback workspace root, and current request-time policy section. Tool layers call resolve for each execution so a session\'s mode log and immutable cwd travel together to every enforcing capability.',
    methods: [//公开方法
      {//方法
        signature: 'readonly defaultMode: SandboxMode',
        description: 'The deployment default mode — the fallback beneath a session override.',
        parameters: [],//无参数
      },//结束方法
      {//方法
        signature: 'readonly workspaceRoot: string',
        description: 'The absolute `workspace-write` fallback root for calls without a session cwd.',
        parameters: [],//无参数
      },//结束方法
      {//方法
        signature: 'resolve(request: SandboxPolicyRequest = {}): SandboxExecutionPolicy',
        description: 'Resolve the complete policy for one capability call. An approved explicit mode outranks the session\'s last `sandbox/mode` event, which outranks the deployment default. A session cwd is its workspace-write boundary; the configured root is the fallback for agentless calls and sessions without a cwd.',
        parameters: [{ name: 'request', description: 'optional session and approved mode override.' }],
        returns: 'the fully resolved per-call mode and absolute workspace root.',
      },//结束方法
      {//方法
        signature: 'overrideOf(session: Session): SandboxMode | undefined',
        description: 'Read the session override without applying the deployment default.',
        parameters: [{ name: 'session', description: 'session whose log supplies the override.' }],
        returns: 'the last logged mode, or `undefined` without one.',
      },//结束方法
    ],//结束 methods
  },//结束服务
]
