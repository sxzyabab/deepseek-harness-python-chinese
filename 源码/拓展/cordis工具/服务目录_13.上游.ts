/** 本包内嵌 SERVICE_API 分片 13（对照原版 api-catalog.ts）——sessions+telemetry+title */
export const SERVICE_API: readonly ServiceApiEntry[] = [//服务目录
  {//服务
    key: 'sessions',
    summary: 'In-memory session store (`ctx.sessions`).',
    description: 'In-memory session store (`ctx.sessions`).\n\nPersistence is intentionally not implemented here — persistence plugins subscribe to `session/event` and flush on `session/flush` / dispose.',
    methods: [//公开方法
      {//方法
        signature: 'create(id?: SessionId, options?: CreateSessionOptions): Session',
        description: 'Create a session owned by the calling fiber: disposing that fiber stops event notification and removes the session from the store. `options.seed` populates the session with a copy of those events (replay/fork); `options.meta` attaches creation metadata (validated absolute `cwd`, seed and parent lineage, and delegation depth) as the immutable SessionHeader (the store fills `version`/`id`/`createdAt`).\n\nFor an agent whose session must be torn down IN ORDER with its loop (so the loop\'s final events are published before the store attachment ends), do NOT use this — fold the session lifecycle into the agent\'s own effect via prepare + enter + announce (see `dsh-agent-loop`\'s creation transaction).',
        parameters: [{ name: 'id', description: 'the session id; omitted, the store mints `session-<n>`.' }, { name: 'options', description: 'seed events and/or creation metadata for the header.' }],
        returns: 'the live session, already entered and announced.',
        throws: ['if a session with `id` already exists, metadata is not a plain lossless-JSON record with valid scalar fields, or `meta.cwd` is a non-absolute path (storage backends key directories off it).'],
      },//结束方法
      {//方法
        signature: 'prepare(id?: SessionId, options?: PrepareSessionOptions): Session',
        description: 'Build a session WITHOUT entering it into the store — validate the id/cwd and construct the Session (with its immutable SessionHeader). Pairs with enter + announce: a caller that owns a composite `ctx.effect` (the agent factory) folds the session lifecycle into that ONE effect so a fiber unload tears the session + agent down as a single ORDERED chain rather than as racing sibling effects — which would remove the publication hooks before the driver\'s closing events commit, dropping them.',
        parameters: [{ name: 'id', description: 'the session id; omitted, the store mints `session-<n>`.' }, { name: 'options', description: 'seed events and/or creation metadata for the header. With `seedSource: \'persistence\'`, metadata and events must be fresh detached graphs whose ownership transfers to this call: they are validated and frozen in place through {@link Session.fromRestore}, so the caller must retain no mutable aliases.' }],
        returns: 'the constructed session, NOT yet in the store.',
        throws: ['if a session with `id` already exists, metadata is not a plain lossless-JSON record with valid scalar fields, or `meta.cwd` is a non-absolute path.'],
      },//结束方法
      {//方法
        signature: 'enter(session: Session): () => void',
        description: 'Enter a prepared session into the store: install the module-private append publication hooks and add it to the store. Returns the DETACH disposer (hooks + store removal). Does NOT emit `session/created` — the caller yields this disposer inside its effect and THEN calls announce, so a throwing `session/created` listener rolls the attach back instead of leaking it.\n\nRe-checks the id for a duplicate: `prepare` and `enter` are public cross-package primitives and a caller may interleave arbitrary work (or another create) between them, so a stale prepared session must NOT overwrite a live store entry of the same id — its detach disposer would later delete the REAL session. The create convenience and the agent factory call the two back-to-back so they never trip this, but the public API cannot assume that.',
        parameters: [{ name: 'session', description: 'a {@link prepare}d session not yet in the store.' }],
        returns: 'the detach disposer (publication hooks + store removal). When called from a synchronous `session/created` listener, removal and disposal wait until that creation dispatch unwinds.',
        throws: ['if a session with this id is already in the store.'],
      },//结束方法
      {//方法
        signature: 'announce(session: Session): void',
        description: 'Emit `session/created` exactly once for an entered session (with the carrier enter captured). Separate from enter so the caller can yield the detach disposer first (rollback safety — see enter).',
        parameters: [{ name: 'session', description: 'the entered session to announce to listeners.' }],
        throws: ['if the session is not live or its announcement already began, including a reentrant call from a creation listener.'],
      },//结束方法
      {//方法
        signature: 'async flush(session: Session): Promise<boolean>',
        description: 'Dispatch the awaited `session/flush` durability checkpoint for `session`, with the carrier captured at enter. THE flush entry point: the store owns the carrier, so callers (the checkpoint policy\'s per-request barrier, goal-round-driver\'s idle checkpoint, teardown drains, and consumers that flush themselves before reading storage) must come through here rather than dispatch a raw `ctx.parallel(\'session/flush\', …)` — one owner, one spelling, and the scoped-dispatch invariant can pin it.',
        parameters: [{ name: 'session', description: 'the session whose buffered events must reach durable storage.' }],
        returns: 'whether at least one durability listener participated, after every listener has settled successfully.',
        throws: ['the first registered listener failure after every listener settles.'],
      },//结束方法
      {//方法
        signature: 'get(id: SessionId): Session | undefined',
        description: 'Look up a live session.',
        parameters: [{ name: 'id', description: 'the session id to look up.' }],
        returns: 'the session, or undefined when no live session has that id.',
      },//结束方法
      {//方法
        signature: 'list(): Session[]',
        description: 'All live sessions, in creation order.',
        parameters: [],//无参数
        returns: 'a fresh array; mutating it does not affect the store.',
      },//结束方法
      {//方法
        signature: 'fork(source: SessionForkSource, boundary?: number, childSessionId?: SessionId): Session',
        description: 'Create a live child session from a stable prefix of a live source. `boundary` is an inclusive source event seq; omitted means the source\'s current last event. The selected slice may end with a between-turn event but must not end inside an open turn.',
        parameters: [{ name: 'source', description: 'Live source session object or id.' }, { name: 'boundary', description: 'Inclusive source event seq to fork through; omitted means the source\'s current last event, and omitted on an empty source forks an empty child.' }, { name: 'childSessionId', description: 'Optional child session id; omitted delegates to `SessionStore`\'s id policy.' }],
        returns: 'The created live child session.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'sessionTelemetry',
    summary: 'Loadable form of the backend contract: one implementation per context — the cordis `Service` registration under the `telemetry` key throws on a duplicate, cordis\' standard behavior.',
    description: 'Loadable form of the backend contract: one implementation per context — the cordis `Service` registration under the `telemetry` key throws on a duplicate, cordis\' standard behavior. A backend composes a SessionTelemetryCoordinator in its constructor to install the capture side.',
    methods: [//公开方法
      {//方法
        signature: 'abstract readonly sharing: SessionTelemetrySharingStatus',
        description: 'Deployment-selected session-sharing policy, disclosed for acknowledgement surfaces that report whether recorded feedback leaves the process. Every backend must disclose its policy; a consumer renders "not configured" only when no telemetry service is mounted. The seam owns this vocabulary so the disclosure is backend-independent.',
        parameters: [],//无参数
      },//结束方法
      {//方法
        signature: 'abstract emit(record: SessionTelemetryRecord): void',
        description: 'See SessionTelemetrySink.emit — that declaration is the contract\'s one home.',
        parameters: [{ name: 'record', description: 'the logical record to report; owned by the backend after the call.' }],
      },//结束方法
      {//方法
        signature: 'flush?(): void',
        description: 'See SessionTelemetrySink.flush.',
        parameters: [],//无参数
      },//结束方法
      {//方法
        signature: 'abstract shutdown(): Promise<void>',
        description: 'See SessionTelemetrySink.shutdown.',
        parameters: [],//无参数
        returns: 'resolves when the backend\'s pipeline has quiesced.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'sessionTitle',
    summary: 'Log-backed title fold plus asynchronous fallback generation.',
    description: 'Log-backed title fold plus asynchronous fallback generation.',
    methods: [//公开方法
      {//方法
        signature: 'get(session: Session): SessionTitleSnapshot | undefined',
        description: 'Read the latest folded title from one live or replayed session.',
        parameters: [{ name: 'session', description: 'session whose log is the title source of truth.' }],
        returns: 'latest title snapshot, or `undefined` before eligible input.',
      },//结束方法
      {//方法
        signature: 'rename(session: Session, title: string): SessionTitleSnapshot',
        description: 'Accept an explicit user title. Appends a `session/title` event with the `user` source, which pins the title: in-flight automatic generation is superseded and later user messages schedule none (an explicit SessionTitleService.refresh remains the deliberate unpin).',
        parameters: [{ name: 'session', description: 'exact live session to rename.' }, { name: 'title', description: 'raw user input; normalized before acceptance.' }],
        returns: 'the accepted title snapshot.',
        throws: ['{SessionTitleInvalidError} when the title normalizes to empty.', '{Error} when the session is not live or the service is disposed.'],
      },//结束方法
      {//方法
        signature: 'async refresh(session: Session, signal?: AbortSignal): Promise<SessionTitleSnapshot | undefined>',
        description: 'Explicitly retry the registered provider, or materialize the built-in fallback when no provider is registered.',
        parameters: [{ name: 'session', description: 'exact live session to refresh.' }, { name: 'signal', description: 'optional caller cancellation.' }],
        returns: 'latest accepted title, or `undefined` when no eligible text exists.',
      },//结束方法
      {//方法
        signature: 'register(provider: SessionTitleProvider): () => Promise<void>',
        description: 'Register the sole optional title provider. Disposal aborts its pending and active work before another provider may register.',
        parameters: [{ name: 'provider', description: 'provider identity, cadence, and generation function.' }],
        returns: 'exact Cordis effect disposer, which settles after active calls quiesce.',
      },//结束方法
    ],//结束 methods
  },//结束服务
]
