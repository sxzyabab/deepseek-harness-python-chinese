/** 本包内嵌 SERVICE_API 分片 17（对照原版 api-catalog.ts）——terminals+tools */
export const SERVICE_API: readonly ServiceApiEntry[] = [//服务目录
  {//服务
    key: 'terminals',
    summary: 'In-process registry for replaceable PTY backends and exact-Agent sessions.',
    description: 'In-process registry for replaceable PTY backends and exact-Agent sessions.',
    methods: [//公开方法
      {//方法
        signature: 'registerBackend(backend: TerminalBackend): () => void',
        description: 'Register one backend type for this effect scope.',
        parameters: [{ name: 'backend', description: 'provider with a non-empty unique type.' }],
        returns: 'disposer that removes exactly this contribution.',
      },//结束方法
      {//方法
        signature: 'listBackends(): string[]',
        description: 'List registered backend types in registration order.',
        parameters: [],//无参数
        returns: 'fresh backend type names.',
      },//结束方法
      {//方法
        signature: 'async spawn(owner: Agent, request: TerminalSpawnRequest, signal?: AbortSignal): Promise<TerminalSpawnResult>',
        description: 'Create and publish one owner-scoped session after backend setup succeeds.',
        parameters: [{ name: 'owner', description: 'exact registered Agent that owns access and cleanup.' }, { name: 'request', description: 'backend type plus optional owner-local name and cwd.' }, { name: 'signal', description: 'cancellation of unpublished setup.' }],
        returns: 'published identity, metadata, status, and MOTD.',
      },//结束方法
      {//方法
        signature: 'hasOwnerActivity(owner: Agent): boolean',
        description: 'Test whether an exact owner has a published session or unpublished spawn.',
        parameters: [{ name: 'owner', description: 'exact live owner to inspect.' }],
        returns: 'true across the entire spawn-to-close interval, with no publication gap.',
      },//结束方法
      {//方法
        signature: 'startSend(owner: Agent, id: TerminalSessionId, request: TerminalSendRequest): TerminalSendOperation',
        description: 'Start one exclusive interactive send.',
        parameters: [{ name: 'owner', description: 'exact session owner.' }, { name: 'id', description: 'target PTY identity.' }, { name: 'request', description: 'explicit text, submit behavior, and cancellation.' }],
        returns: 'live operation handle for foreground await or task registration.',
      },//结束方法
      {//方法
        signature: 'read(owner: Agent, id: TerminalSessionId, request: TerminalReadRequest = {}): TerminalReadResult',
        description: 'Read one bounded scrollback page from an owned session.',
        parameters: [{ name: 'owner', description: 'exact session owner.' }, { name: 'id', description: 'target PTY identity.' }, { name: 'request', description: 'optional newest-relative offset and line count.' }],
        returns: 'bounded retained text and pagination metadata.',
      },//结束方法
      {//方法
        signature: 'signal(owner: Agent, id: TerminalSessionId, signal: TerminalSignal): Promise<TerminalSignalResult>',
        description: 'Deliver an allowed signal through an owned backend session.',
        parameters: [{ name: 'owner', description: 'exact session owner.' }, { name: 'id', description: 'target PTY identity.' }, { name: 'signal', description: 'allowed POSIX signal name.' }],
        returns: 'delivered foreground process-group identity.',
      },//结束方法
      {//方法
        signature: 'async kill(owner: Agent, id: TerminalSessionId, reason: string = \'model request\'): Promise<boolean>',
        description: 'Close one owned session and remove it only after quiescent backend cleanup.',
        parameters: [{ name: 'owner', description: 'exact session owner.' }, { name: 'id', description: 'target PTY identity.' }, { name: 'reason', description: 'diagnostic cleanup reason.' }],
        returns: 'true for a newly closed session, false when the same close is already in flight.',
      },//结束方法
      {//方法
        signature: 'list(owner: Agent): TerminalSessionSnapshot[]',
        description: 'List fresh snapshots for exactly one owner.',
        parameters: [{ name: 'owner', description: 'exact owner whose sessions are visible.' }],
        returns: 'owner-visible snapshots in publication order.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'tools',
    summary: 'Tool registry and execution pipeline.',
    description: 'Tool registry and execution pipeline. Scoped registrations shadow globals; one visibility resolver feeds presentation, lookup, and dispatch.',
    methods: [//公开方法
      {//方法
        signature: 'presentAs(mode: ToolPresentationMode): () => void',
        description: 'Present the calling scope\'s tools in `mode` instead of the deployment default. Nearest scope on the chain wins, so a preset\'s standing declaration covers every agent joined under it.\n\nScoped only, and one declaration per scope: this is how an agent preset composes Code Mode agents beside native ones in the same process, and a process-global override would be the `mode` config field instead.',
        parameters: [{ name: 'mode', description: 'the presentation the covered agents\' models see.' }],
        returns: 'the exact disposer that restores the deployment default.',
      },//结束方法
      {//方法
        signature: 'register(definition: ToolDefinition): () => void',
        description: 'Register globally or in the calling agent scope. Scoped tools shadow globals; duplicates within one layer and the reserved `run_code` name fail.',
        parameters: [{ name: 'definition', description: 'tool schema, execution, and optional finalization/presentation callbacks.' }],
        returns: 'the exact disposer that unregisters the tool.',
      },//结束方法
      {//方法
        signature: 'restrict(filter: ToolRestriction): () => void',
        description: 'Restrict global tools for the calling agent scope. Empty filters, unknown names, scope-local names, and reserved transport names fail. Restrictions intersect; scoped registrations remain visible.',
        parameters: [{ name: 'filter', description: 'global-tool mask: `allow` (keep only) and/or `deny` (remove).' }],
        returns: 'the exact disposer that lifts this restriction.',
      },//结束方法
      {//方法
        signature: 'guard(guard: ToolGuard): () => void',
        description: 'Register a monotonic guard after the extensible `tools/pre-execute` waterfall. A plain-context guard applies globally; one registered through `agent.ctx` applies only to that agent. Any matching guard may deny by returning a reason, while no guard can force-allow a call another guard denied. The exact effect disposer is returned for ordered ownership and HMR cleanup.',
        parameters: [{ name: 'guard', description: 'synchronous check; a returned string denies the execution.' }],
        returns: 'the exact disposer that unregisters the guard.',
      },//结束方法
      {//方法
        signature: 'get(name: string, scope?: ScopeKey): ToolDefinition | undefined',
        description: 'Look up a tool as one scope sees it (scoped shadows global; a restricted-away global reads as absent). Presenters pass the calling agent so the rendered card matches the definition that actually executed.',
        parameters: [{ name: 'name', description: 'the tool name as registered.' }, { name: 'scope', description: 'the viewing scope (the agent); omitted = the global view.' }],
        returns: 'the definition the scope resolves, or undefined when none is visible.',
      },//结束方法
      {//方法
        signature: 'schemas(scope?: ScopeKey): ToolSchema[]',
        description: 'Project visible definitions onto the allowlisted model-facing schema fields, excluding execution and presentation callbacks.',
        parameters: [{ name: 'scope', description: 'the viewing scope (the agent); omitted = the global view.' }],
        returns: 'one deep-cloned schema per visible tool.',
      },//结束方法
      {//方法
        signature: 'executionMode(exec: ToolExecutionInput): ToolExecutionMode',
        description: 'Classify a pending call through the caller\'s visible tool definition. Only an exact `true` is parallel; unknown, hidden, undeclared, invalid, or throwing classifiers are exclusive.',
        parameters: [{ name: 'exec', description: 'call name, parsed arguments, and optional agent scope.' }],
        returns: 'the fail-closed scheduling mode.',
      },//结束方法
      {//方法
        signature: 'async execute(exec: ToolExecutionInput): Promise<ToolExecutionResult>',
        description: 'Execute through pre-policy, guards, around-dispatch, post-policy, definition-owned content finalization, and final notification. Tool and listener failures resolve as materialized error results; an invisible tool reports `UNKNOWN_TOOL`. The returned outcome is the same lossless, frozen snapshot final observers receive. Cancellation arriving after entry and before final result materialization skips a not-yet-started body with `ABORTED_BEFORE_DISPATCH` or replaces a successful started outcome with `ABORTED`; already-started work is still drained and may retain a tool-owned structured error.',
        parameters: [{ name: 'exec', description: 'the typed same-process call input. The registry assigns its correlation token before policy begins.' }],
        returns: 'the materialized final result.',
      },//结束方法
    ],//结束 methods
  },//结束服务
]
