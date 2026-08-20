/** 本包内嵌 SERVICE_API 分片 16（对照原版 api-catalog.ts）——subprocess..toolResultPruner */
export const SERVICE_API: readonly ServiceApiEntry[] = [//服务目录
  {//服务
    key: 'subprocess',
    summary: 'Abstract subprocess service.',
    description: 'Abstract subprocess service. Subclass, implement spawn, and load the subclass as a plugin — it registers as `ctx.subprocess` (one implementation per context; loading a second throws, which is cordis\' standard duplicate-service behavior).\n\nImplementations must honor these semantics:\n\n- Executable paths belong to one execution world shared with the mounted filesystem provider.\n- spawn returns immediately with a live handle; `done` resolves at process close with exit facts and rejects only for spawn-level failures.\n- Collect-mode readers are offset-based and non-consuming, so independent readers never consume one another\'s output; lossy reads report truncation and the spill file holding the complete stream when one exists. Piped streams are handed to the caller raw and never buffered here.\n- SubprocessHandle.terminate (and the spec\'s abort signal) escalates SIGTERM→grace→SIGKILL — the only termination verb — tree-scoped on every platform. SubprocessHandle.waitForExit observes whole-tree liveness, so a consumer-owned teardown ladder can hold each tier on real quiescence.\n- Disposal of the service terminates all still-running managed processes and awaits their exit.\n- spawnTerminal owns terminal allocation, text transport, foreground groups, signalling, and whole-session quiescence behind one awaited termination method; readiness and persistent-shell policy stay in the PTY consumer. Its output stream ends after queued terminal output when the top-level process exits.',
    methods: [//公开方法
      {//方法
        signature: 'abstract resolveExecutable( command: string, env?: Readonly<Record<string, string>>, signal?: AbortSignal, ): Promise<string>',
        description: 'Resolve one configured executable in this provider\'s execution world. Absolute paths are verified; bare names use the provider\'s scrubbed PATH plus explicit environment overrides. Relative paths containing separators are rejected: the resolution base is undefined, so providers fail loud instead of guessing.',
        parameters: [{ name: 'command', description: 'absolute executable path or bare PATH name.' }, { name: 'env', description: 'explicit environment entries used for lookup.' }, { name: 'signal', description: 'aborts remote or local lookup.' }],
        returns: 'a canonical executable path.',
      },//结束方法
      {//方法
        signature: 'abstract spawn(spec: SubprocessSpawnSpec): SubprocessHandle',
        description: 'Start one managed child process from a fully-specified spec; this seam applies no defaults.',
        parameters: [{ name: 'spec', description: 'argv, directory, stdio dispositions, grace, cancellation, and environment.' }],
        returns: 'the live process handle (streams/readers, signalling, outcome promise).',
      },//结束方法
      {//方法
        signature: 'abstract spawnTerminal(spec: SubprocessTerminalSpawnSpec): Promise<SubprocessTerminalHandle>',
        description: 'Allocate a real terminal and start one owned process session. This is the only non-pipe process primitive: implementations own terminal byte I/O, foreground groups, signals, and complete session-tree cleanup.',
        parameters: [{ name: 'spec', description: 'fully specified argv, cwd, environment, dimensions, grace, and allocation cancellation.' }],
        returns: 'the live terminal handle after allocation succeeds.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'systemPrompt',
    summary: 'Registry service for the prompt inputs assembled before each model step.',
    description: 'Registry service for the prompt inputs assembled before each model step.',
    methods: [//公开方法
      {//方法
        signature: 'section(section: PromptSection): () => void',
        description: 'Register an ordered prompt section in the calling context\'s scope. A scoped section shadows a global section with the same name; duplicates within one layer and non-finite orders throw. Registration and disposal emit `system-prompt/change`.',
        parameters: [{ name: 'section', description: 'the section to register.' }],
        returns: 'the exact Cordis effect disposer.',
      },//结束方法
      {//方法
        signature: 'context(context: PromptContext): () => void',
        description: 'Register ordered dynamic context in the calling context\'s scope. Scoped entries shadow global entries with the same name.',
        parameters: [{ name: 'context', description: 'the context contribution to register.' }],
        returns: 'the exact Cordis effect disposer.',
      },//结束方法
      {//方法
        signature: 'suppressRuntimeContext(): () => void',
        description: 'Suppress every dynamic runtime-context contribution in the calling context\'s scope without changing the services that own or enforce those facts. Multiple suppressors remain independently disposable.',
        parameters: [],//无参数
        returns: 'the exact Cordis effect disposer.',
      },//结束方法
      {//方法
        signature: 'tools(provider: (context: AssembleContext) => ToolProviderResult): () => void',
        description: 'Register a tool-schema provider in the calling context\'s scope. Global and matching scoped providers both contribute; returning the reserved TOOL_ORDER_REST name makes assembly fail.',
        parameters: [{ name: 'provider', description: 'evaluated for each assembly with its context.' }],
        returns: 'the exact Cordis effect disposer.',
      },//结束方法
      {//方法
        signature: 'variable(name: string, provider: (context: AssembleContext) => string | undefined): () => void',
        description: 'Register a prompt variable in the calling context\'s scope. Scoped values shadow globals; invalid or duplicate names throw. A provider may return `undefined`, but rendering a section that references that value then fails.',
        parameters: [{ name: 'name', description: 'the `[a-z][a-z0-9_]*` reference name.' }, { name: 'provider', description: 'evaluated for each assembly.' }],
        returns: 'the exact Cordis effect disposer.',
      },//结束方法
      {//方法
        signature: 'async assemble(context: AssembleContext = {}): Promise<PromptAssembly>',
        description: 'Assemble global and scoped providers, detach tool parameters, apply canonical ordering, then run the assembly waterfall. Scoped sections and variables shadow globals. The returned waterfall value is authoritative except that an effective complete section is restored afterwards as the sole prompt section.',
        parameters: [{ name: 'context', description: 'the optional scope and plugin-defined assembly fields.' }],
        returns: 'the post-waterfall assembly with any complete prompt enforced.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'timer',
    summary: 'Disposable timer helpers mixed into Cordis contexts.',
    description: 'Disposable timer helpers mixed into Cordis contexts.',
    methods: [//公开方法
      {//方法
        signature: 'timeout(callback: () => void, delay: number): () => void',
        description: 'Run a callback once and return its disposer.',
        parameters: [],//无参数
      },//结束方法
      {//方法
        signature: 'timeout(delay: number): Promise<void>',
        description: 'Resolve after a delay; disposal rejects the pending promise.',
        parameters: [],//无参数
      },//结束方法
      {//方法
        signature: 'interval(callback: () => void, delay: number): () => void',
        description: 'Run a callback repeatedly and return its disposer.',
        parameters: [],//无参数
      },//结束方法
      {//方法
        signature: 'interval<R = any>(delay: number): AsyncIterableIterator<void, R, void>',
        description: 'Return an async iterator of timer ticks.',
        parameters: [],//无参数
      },//结束方法
      {//方法
        signature: 'throttle<F extends (...args: any[]) => void>(callback: F, delay: number, noTrailing?: boolean): F & { dispose: () => void }',
        description: 'Return a throttled function whose timer is disposed with the current fiber.',
        parameters: [],//无参数
      },//结束方法
      {//方法
        signature: 'debounce<F extends (...args: any[]) => void>(callback: F, delay: number): F & { dispose: () => void }',
        description: 'Return a debounced function whose timer is disposed with the current fiber.',
        parameters: [],//无参数
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'tokenMeter',
    summary: 'Replay owner for one service-wide estimator and isolated per-session folds.',
    description: 'Replay owner for one service-wide estimator and isolated per-session folds.',
    methods: [//公开方法
      {//方法
        signature: 'measure(session: Session, requestHeader?: EpochHeader): TokenMeasurement',
        description: 'Measure current request pressure and surface through the durable tail.\n\nProvider usage is reused only when the latest successful call\'s canonical request envelope matches `requestHeader` and its total is no lower than that call\'s full heuristic anchor; otherwise the complete envelope and surface are heuristically repriced.\n\n`requestHeader` affects request pressure only; surface fields always describe the current session surface. Every call clones those positional nodes, so measurement is O(surface).',
        parameters: [{ name: 'session', description: 'session to replay through its current durable tail.' }, { name: 'requestHeader', description: 'optional effective request envelope replacing the latest logged header.' }],
        returns: 'a detached deeply immutable pressure and surface measurement.',
      },//结束方法
      {//方法
        signature: 'estimateMessage(message: Message): number',
        description: 'Heuristically price one model-visible message (instance face of the pure `estimateMessage` export from `estimate.ts`).',
        parameters: [{ name: 'message', description: 'message to price without mutation.' }],
        returns: 'content and role-framing tokens under the fixed service heuristic.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'toolResultPruner',
    summary: 'Deterministic head/middle/tail pruning for current tool-result surface nodes.',
    description: 'Deterministic head/middle/tail pruning for current tool-result surface nodes.',
    methods: [//公开方法
      {//方法
        signature: 'readonly config: ResolvedConfig',
        description: 'Resolved and immutable character budgets.',
        parameters: [],//无参数
      },//结束方法
      {//方法
        signature: 'measureContent(blocks: readonly ContentBlock[]): number',
        description: 'Measure text content in Unicode code points; non-text blocks cost zero.',
        parameters: [{ name: 'blocks', description: 'tool-result content to measure.' }],
        returns: 'total Unicode code points across text blocks.',
      },//结束方法
      {//方法
        signature: 'pruneContent(blocks: readonly ContentBlock[]): ContentBlock[] | null',
        description: 'Replace an over-budget text middle while retaining rich-block order. Text slicing is by Unicode code point, not UTF-16 code unit, so a retained boundary cannot split a surrogate pair. Grapheme clusters may still split.',
        parameters: [{ name: 'blocks', description: 'original tool-result content.' }],
        returns: 'pruned content, or `null` when the text is within budget.',
      },//结束方法
      {//方法
        signature: 'pruneSession(session: Session): PruneResult',
        description: 'Prune every over-budget tool result from one stable current-surface snapshot. Each replacement preserves the complete event data except for `content`, cites the shadowed node so replay can recover the replacement input, and is immediately preceded by a `compaction/prune` shadow-price event pricing the shadowed node through the injected token meter, so pure consumers can subtract it without per-node state.',
        parameters: [{ name: 'session', description: 'session whose current surface is rewritten.' }],
        returns: 'landed replacements and aggregate Unicode-code-point savings.',
        throws: ['when the session rejects a replacement; replacements committed earlier in the pass remain durable.'],
      },//结束方法
    ],//结束 methods
  },//结束服务
]
