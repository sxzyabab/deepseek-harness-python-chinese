/** 本包内嵌 SERVICE_API 分片 04（对照原版 api-catalog.ts）：apiProxy..directoryPicker */
export const SERVICE_API: readonly ServiceApiEntry[] = [//服务目录
  {//服务
    key: 'apiProxy',
    summary: 'Root interface of the unified API.',
    description: 'Root interface of the unified API. New client-request domain = one new file pair + one field here + one map row.',
    methods: [//公开方法
      {//方法
        signature: 'downloads: DownloadsApi',
        description: 'Host-only download surfaces (GET, no wire envelope); absent from IApiClient.',
        parameters: [],//无参数
      },//结束方法
      {//方法
        signature: 'respond(message: ClientResponse): Promise<RpcReceipt>',
        description: 'Response entry for server requests; not a domain method.',
        parameters: [{ name: 'message', description: 'Client response carrying the server request\'s rpcId.' }],
        returns: 'Transport receipt for the response delivery.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'approval',
    summary: 'Approval service that applies session policy before answerers and logs every ask/outcome pair to the requesting session.',
    description: 'Approval service that applies session policy before answerers and logs every ask/outcome pair to the requesting session. It exposes deterministic policy changes to the model through the runtime-context snapshot and switch notices.',
    methods: [//公开方法
      {//方法
        signature: 'setPolicy(agent: Agent, policy: ApprovalPolicy): void',
        description: 'Switch one live agent\'s policy and queue the transition for its next model step. Session initialization uses setApprovalPolicy directly because there is no previously visible policy to change.',
        parameters: [{ name: 'agent', description: 'the live agent whose policy is changing.' }, { name: 'policy', description: 'the new effective policy.' }],
      },//结束方法
      {//方法
        signature: 'async request(req: ApprovalRequest): Promise<ApprovalOutcome>',
        description: 'Ask the composed answerers to decide one readonly same-process request. The service borrows the request, agent, session, and live signal directly. The request requires an open turn because the audit pair must be enclosed by the durable log\'s commit/replay boundary; an idle ask rejects before appending anything. The answerer phase always produces an outcome: an aborted signal yields `\'cancelled\'`, a missing or throwing answerer yields `\'unavailable\'` (fail closed), and a rogue non-vocabulary return value is normalized to `\'unavailable\'`. A failure that prevents either audit append from committing still rejects because returning an unlogged decision would violate the pair. Session contains post-commit observer failures, so an authoritative append cannot reject the request or suppress its matching audit event.',
        parameters: [{ name: 'req', description: 'the pending decision (agent, tool identity, reason, signal).' }],
        returns: 'the closed outcome; `\'allowed-once\'` is the only grant.',
        throws: ['when no turn is open or either audit event fails before the session append commit point.'],
      },//结束方法
      {//方法
        signature: 'overrideOf(session: Session): ApprovalPolicy | undefined',
        description: 'Read the session override without applying the configured default.',
        parameters: [{ name: 'session', description: 'session whose log supplies the override.' }],
        returns: 'the last logged policy, or `undefined` without one.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'attachments',
    summary: 'Immutable binary attachment service.',
    description: 'Immutable binary attachment service. Implementations validate bytes before publishing a reference.',
    methods: [//公开方法
      {//方法
        signature: 'abstract readonly imageLimits: ImageAttachmentLimits',
        description: 'Deployment-resolved image policy used by authoritative and fast-path validation.',
        parameters: [],//无参数
      },//结束方法
      {//方法
        signature: 'abstract validateImage(input: SaveImageAttachment): Promise<void>',
        description: 'Validate one image without persisting it. Batch callers validate every member before saving any member.',
        parameters: [{ name: 'input', description: 'encoded bytes, declared media type, and optional display name.' }],
        returns: 'completion after the encoded raster has been fully decoded.',
      },//结束方法
      {//方法
        signature: 'abstract saveImage(input: SaveImageAttachment): Promise<ImageAttachmentRef>',
        description: 'Validate and durably commit one image before its owning session event is appended.',
        parameters: [{ name: 'input', description: 'encoded bytes, declared media type, and optional display name.' }],
        returns: 'a durable content-addressed reference.',
      },//结束方法
      {//方法
        signature: 'abstract readImage(ref: ImageAttachmentRef, signal?: AbortSignal): Promise<StoredImageAttachment>',
        description: 'Read one image and verify that bytes still match the recorded reference.',
        parameters: [{ name: 'ref', description: 'durable reference from the session log.' }, { name: 'signal', description: 'optional cancellation for backend read and verification work.' }],
        returns: 'the verified bytes and canonical reference.',
        throws: ['the signal reason when aborted, or a storage error when verification fails.'],
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'clientModules',
    summary: 'The web plugin table service: incremental `dsh.client` scan + wire composition + bundle route + index tap.',
    description: 'The web plugin table service: incremental `dsh.client` scan + wire composition + bundle route + index tap. Construction runs the activation scan synchronously — a malformed declaration or missing bundle among the already-loaded entries aggregates into one loud throw (FAILED fiber; the boot activation audit reports it).',
    methods: [//公开方法
      {//方法
        signature: 'graph(): WebBootGraph',
        description: 'Current composed entry graph (stable object between changes).',
        parameters: [],//无参数
        returns: 'the graph served as `window.__DSH_BOOT__`.',
      },//结束方法
      {//方法
        signature: 'clientPath(id: string): string | undefined',
        description: 'Absolute path of an entry\'s client bundle.',
        parameters: [{ name: 'id', description: 'entry id (package name).' }],
        returns: 'the path, or undefined for an unknown id.',
      },//结束方法
      {//方法
        signature: 'rebuilt(id: string): string | undefined',
        description: 'Re-hash one bundle (the HMR watch\'s registration hook — the only entry point through which bundle content changes reach the graph).',
        parameters: [{ name: 'id', description: 'entry id (package name).' }],
        returns: 'the new rev, or undefined for an unknown id.',
      },//结束方法
      {//方法
        signature: 'onRebuilt(listener: (id: string, rev: string) => void): () => void',
        description: 'Subscribe to bundle rebuilds; fires only when the re-hash changed the rev.',
        parameters: [{ name: 'listener', description: 'receives the entry id and its new bundle rev.' }],
        returns: 'the unsubscriber.',
      },//结束方法
      {//方法
        signature: 'onGraphChanged(listener: () => void): () => void',
        description: 'Fires after any flush that recomposed the graph (row added/removed, or a rebuilt rev change). Pull model: listeners re-read graph.',
        parameters: [{ name: 'listener', description: 'notified with no payload.' }],
        returns: 'the unsubscriber.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'codeRuntime',
    summary: 'Registers one `ctx.codeRuntime` implementation.',
    description: 'Registers one `ctx.codeRuntime` implementation. Program, budget, abort, and substrate failures resolve in CodeRunResult; only Service Definition contract misuse rejects. Implementations bridge structured-cloneable bindings, materialize each declared namespace rejection class, treat programs as hostile peers, isolate runs from one another, and terminate and await in-flight runs during disposal.',
    methods: [//公开方法
      {//方法
        signature: 'abstract readonly language: string',
        description: 'The source language run expects `program` to be written in, as a lowercase identifier. Informational, not gating — a consumer that generates language-specific presentation (typed SDK stubs, usage instructions) switches on it and fails loud on a language it cannot present. Well-known values: `\'typescript\'` and `\'python\'`, those `dsh-tools` presents; only `\'typescript\'` has a published backend.',
        parameters: [],//无参数
      },//结束方法
      {//方法
        signature: 'abstract readonly isolation: string',
        description: 'The execution substrate, as a lowercase identifier. Informational, not gating — a descriptor so deployments and diagnostics can tell backends apart, not a security claim. Well-known values: `\'worker-thread\'`, `\'process\'`, `\'container\'`.',
        parameters: [],//无参数
      },//结束方法
      {//方法
        signature: 'abstract run(request: CodeRunRequest): Promise<CodeRunResult>',
        description: 'Execute one program against the request\'s bindings and capture what it emitted. See the class doc for the resolution contract (error is a result field; rejection means Service Definition contract misuse only).',
        parameters: [{ name: 'request', description: 'the program, its bindings, and the abort signal; the request carries everything the runtime acts on, with no hidden defaults.' }],
        returns: 'the run\'s outcome: completion value (when transferable), the ordered log capture, and the failure (if any).',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'commands',
    summary: 'Human-command registry.',
    description: 'Human-command registry. Plain-context definitions are global; definitions registered through a command-injected child of an agent context shadow globals for that agent.',
    methods: [//公开方法
      {//方法
        signature: 'register(definition: CommandDefinition): () => void',
        description: 'Register a global or calling-agent-scoped command.',
        parameters: [{ name: 'definition', description: 'discovery metadata and direct UI handler.' }],
        returns: 'the exact effect disposer that unregisters this definition.',
      },//结束方法
      {//方法
        signature: '@Remote list(agent: Agent): readonly CommandDescriptor[]',
        description: 'List the effective immutable command descriptors for one agent.',
        parameters: [{ name: 'agent', description: 'exact receiving agent and scoped-layer key.' }],
        returns: 'name-sorted descriptors after scoped shadowing.',
      },//结束方法
      {//方法
        signature: 'find(agent: Agent, name: string): CommandDefinition | undefined',
        description: 'Resolve one effective command definition.',
        parameters: [{ name: 'agent', description: 'exact receiving agent and scoped-layer key.' }, { name: 'name', description: 'command name without a slash.' }],
        returns: 'the scoped shadow or global definition.',
      },//结束方法
      {//方法
        signature: '@Remote async execute( agent: Agent, line: string, signal: AbortSignal, ): Promise<CommandExecution | undefined>',
        description: 'Parse and execute a known command without sending it to the model.\n\nA resolved command\'s lifecycle is logged: `command/run` is appended before the handler is invoked and `command/done` after settlement (a thrown or aborted handler settles as `kind: \'error\'`). Both are direct log-only appends — no turn wraps them, and persistence drains them at ordinary checkpoints. Admission misses (syntax or unknown name) log nothing — they never entered a handler. A `command/run` append failure fails the execution loud; a `command/done` append failure on the handler-failure path is contained so the handler\'s own error stays the reported failure.',
        parameters: [{ name: 'agent', description: 'exact receiving agent.' }, { name: 'line', description: 'complete slash-command line.' }, { name: 'signal', description: 'cancellation signal owned by the UI request.' }],
        returns: 'the settled execution (result + lifecycle pairing id), or `undefined` when syntax or name does not resolve.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'compaction',
    summary: 'Abstract compaction service.',
    description: 'Abstract compaction service. Implementations own trigger policy, retention, and summarization, and may consume a separate measurement service. A successful run replaces the selected surface span with one summary node and prevents concurrent compaction of the same session. The replacement user message uses compactCheckpointSource with the transaction identity so consumers recognize and correlate it independently of the backend. Load one implementation per context as `ctx.compaction`.',
    methods: [//公开方法
      {//方法
        signature: 'abstract compactIfNeeded( agent: CompactionAgentContext, trigger: CompactionTrigger, signal: AbortSignal, ): Promise<CompactionResult | null>',
        description: 'Consider automatic compaction for one explicit trigger. Pressure policy uses the latest durable routed request, while context-overflow policy may force a useful balanced reduction even below the normal threshold. Return `null` when no safe range can be compacted. A single oversized retained unit or request envelope cannot be repaired through surface compaction.',
        parameters: [{ name: 'agent', description: 'agent context owning the session surface and routing options.' }, { name: 'trigger', description: 'normal pressure or provider-confirmed context overflow.' }, { name: 'signal', description: 'cancellation signal; model-backed implementations must forward it.' }],
        returns: 'the compaction result, or `null` if no compaction was needed.',
      },//结束方法
      {//方法
        signature: 'abstract compactNow( agent: ManualCompactAgentContext, signal: AbortSignal, sourceCommandId?: CommandId, ): Promise<CompactionResult | null>',
        description: 'Explicitly compact useful history even below automatic pressure thresholds. Implementations synchronously start an idle task before any asynchronous work, select a useful range without writing on a no-op, then append a standalone `compaction/start` before summarization. That durable marker is the compaction lock until one `compaction/end` attempt. Later waking prompts remain accepted in FIFO order and start only after the optional durability checkpoint and idle-task settlement. Context injected while the summary runs may sit between the marker pair; only the selected span must remain stable.',
        parameters: [{ name: 'agent', description: 'idle agent whose durable history should be compacted.' }, { name: 'signal', description: 'cancellation scoped to this compaction request.' }, { name: 'sourceCommandId', description: 'initiating command identity for a manual compaction.' }],
        returns: 'the compaction result, or `null` when no safe useful range exists.',
        throws: ['{@link ManualCompactionError} for expected busy, agent-cancellation, changed-span, summarization/shrink, commit-stage, or persistence failures; an aborted request preserves its exact abort reason. Failed attempts remain visible in the log.'],
      },//结束方法
      {//方法
        signature: 'abstract compactRegion( start: number, end: number, agent: CompactionAgentContext, signal?: AbortSignal, ): Promise<CompactionResult>',
        description: 'Forcibly compact a range of surface nodes into a single summary node. `start` and `end` name an inclusive span by surface position, not numeric seq order; replacements can make visible seqs non-monotonic. Both edges must be balanced so assistant tool calls remain paired with their results. A model- backed implementation forwards cancellation and rejects active, missing, reversed, or unbalanced ranges. The target session is `agent.session`. Its replacement user message must use compactCheckpointSource with the transaction\'s `CompactionId`. Use toolPairingBalancedBefore and toolPairingBalancedAfter for the edge checks.',
        parameters: [{ name: 'start', description: 'first surface seq, inclusive.' }, { name: 'end', description: 'last surface seq, inclusive.' }, { name: 'agent', description: 'context whose session is mutated and whose routing options guide summarization.' }, { name: 'signal', description: 'optional cancellation; model-backed implementations must forward it.' }],
        returns: 'the appended event seqs, summary, replaced range, and token accounting.',
        throws: ['when compaction is active or the range is missing, reversed, or unbalanced.'],
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'credentials',
    summary: 'Abstract credential service.',
    description: 'Abstract credential service. Providers implement the four operations over their source layers; one seam-wide rule binds them all: an empty stored value is absent everywhere — `resolve` skips it, `describe` reports it unconfigured — so a blank never masquerades as a configured secret.',
    methods: [//公开方法
      {//方法
        signature: 'abstract resolve(ref: CredentialRef): Promise<ResolvedCredential | undefined>',
        description: 'Resolve one reference to its current value. Resolution is per call: consumers re-resolve at each operation and must not cache across operations — that per-operation read is what makes a changed credential reach the next operation without a restart.',
        parameters: [{ name: 'ref', description: 'the reference to resolve.' }],
        returns: 'the value and its source, or `undefined` while unconfigured.',
      },//结束方法
      {//方法
        signature: 'abstract describe(ref: CredentialRef): Promise<CredentialInfo>',
        description: 'Describe one reference for configuration surfaces without exposing the value.',
        parameters: [{ name: 'ref', description: 'the reference to describe.' }],
        returns: 'configured state, supplying source, and writability.',
      },//结束方法
      {//方法
        signature: 'abstract set(ref: CredentialRef, value: string): Promise<void>',
        description: 'Durably store one value in the provider-managed writable source. Rejects while a read-only source shadows the reference — the write would appear to succeed while resolution keeps returning the shadowing value — and rejects an empty value (use unset).',
        parameters: [{ name: 'ref', description: 'the reference to store.' }, { name: 'value', description: 'the non-empty secret value.' }],
      },//结束方法
      {//方法
        signature: 'abstract unset(ref: CredentialRef): Promise<void>',
        description: 'Remove one reference from the provider-managed writable source; removing an absent reference is a no-op. Rejects while a read-only source shadows the reference, like set.',
        parameters: [{ name: 'ref', description: 'the reference to remove.' }],
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'directoryPicker',
    summary: 'Abstract directory-picking service.',
    description: 'Abstract directory-picking service. Subclass, implement `capability()`, and load the subclass as a plugin — it registers as `ctx.directoryPicker` (one implementation per context; loading a second throws, cordis\' standard duplicate-service behavior). The capability object must be stable for the service lifetime: consumers may capture it across calls.',
    methods: [//公开方法
      {//方法
        signature: 'abstract capability(): DirectoryPickerCapability',
        description: 'The backend\'s interaction capability.',
        parameters: [],//无参数
        returns: 'the discriminated capability consumers switch on.',
      },//结束方法
    ],//结束 methods
  },//结束服务
]
