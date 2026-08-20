/** 本包内嵌 SERVICE_API 分片 12（对照原版 api-catalog.ts）——sessionQuery */
export const SERVICE_API: readonly ServiceApiEntry[] = [//服务目录
  {//服务
    key: 'sessionQuery',
    summary: 'Unified live-preferred session query service.',
    description: 'Unified live-preferred session query service.\n\nExact reads, filters, and traces are backend-independent concrete behavior. A backend implements full-text observation, reconciliation, ranking, cursor generations, and query execution on the same `ctx.sessionQuery` service.',
    methods: [//公开方法
      {//方法
        signature: 'abstract searchSessions( request: SessionSearchRequest, exec?: SessionSearchExecContext, ): Promise<SessionSearchPage<SessionSearchHit>>',
        description: 'Search the live-preferred logical corpus and group by session.',
        parameters: [{ name: 'request', description: 'query text, metadata filters, page size, and cursor.' }, { name: 'exec', description: 'optional cancellation control.' }],
        returns: 'session hits ranked by their strongest matching event.',
      },//结束方法
      {//方法
        signature: 'abstract searchEvents( request: SessionEventSearchRequest, exec?: SessionSearchExecContext, ): Promise<SessionEventSearchPage>',
        description: 'Search events within one live-preferred logical session.',
        parameters: [{ name: 'request', description: 'target session, query text, filters, page size, and cursor.' }, { name: 'exec', description: 'optional cancellation control.' }],
        returns: 'matching event hits and their target header from one indexed generation.',
      },//结束方法
      {//方法
        signature: 'listSessions(signal?: AbortSignal): Promise<SessionRecord[]>',
        description: 'List the complete logical corpus using live-preferred records.',
        parameters: [{ name: 'signal', description: 'optional cancellation for persistence listing.' }],
        returns: 'deterministic newest-first cloned session records.',
      },//结束方法
      {//方法
        signature: 'async readSession(sessionId: SessionId): Promise<SessionLogSnapshot>',
        description: 'Read and replay-validate one complete logical session log without making it live.',
        parameters: [{ name: 'sessionId', description: 'live or persisted session id to read.' }],
        returns: 'cloned header and complete raw event log from one observation.',
        throws: ['when persistence, header compatibility, or replay validation fails.'],
      },//结束方法
      {//方法
        signature: 'async filterSessions( filters: readonly SessionResultFilter[], signal?: AbortSignal, ): Promise<SessionRecord[]>',
        description: 'Filter the complete logical corpus with provider-independent predicates.',
        parameters: [{ name: 'filters', description: 'ANDed session metadata and availability clauses.' }, { name: 'signal', description: 'optional cancellation for persistence listing.' }],
        returns: 'matching cloned records in deterministic newest-first order.',
      },//结束方法
      {//方法
        signature: 'async readTitle( sessionId: SessionId, signal?: AbortSignal, ): Promise<SessionTitleSnapshot | undefined>',
        description: 'Fold the latest log-backed title from one live-preferred logical session.',
        parameters: [{ name: 'sessionId', description: 'live or persisted session id to read.' }, { name: 'signal', description: 'optional cancellation for source resolution and title folding.' }],
        returns: 'latest title snapshot, or `undefined` when the log has no title event.',
      },//结束方法
      {//方法
        signature: 'async readTitleSnapshot( sessionId: SessionId, signal?: AbortSignal, ): Promise<SessionTitleObservation>',
        description: 'Fold the latest title and return its source header from one corpus observation.',
        parameters: [{ name: 'sessionId', description: 'live or persisted session id to read.' }, { name: 'signal', description: 'optional cancellation for source resolution and title folding.' }],
        returns: 'cloned source header and optional latest title snapshot.',
      },//结束方法
      {//方法
        signature: 'async readTitleSnapshots( sessionIds: readonly SessionId[], signal?: AbortSignal, ): Promise<SessionTitleObservationResult[]>',
        description: 'Fold titles for unique sessions from one cancellable corpus observation.\n\nResults preserve first-occurrence input order. Operational failures stay isolated per session, while cancellation rejects the complete operation.',
        parameters: [{ name: 'sessionIds', description: 'live or persisted session ids to observe.' }, { name: 'signal', description: 'optional cancellation shared by all source reads.' }],
        returns: 'one fulfilled or rejected result per unique requested id.',
      },//结束方法
      {//方法
        signature: 'async listEvents(sessionId: SessionId): Promise<SessionEventRecord[]>',
        description: 'List lightweight raw-log event records for one logical session.',
        parameters: [{ name: 'sessionId', description: 'live-preferred session id to read.' }],
        returns: 'event records in ascending seq order.',
      },//结束方法
      {//方法
        signature: 'async filterEvents( sessionId: SessionId, filters: readonly SessionEventResultFilter[], ): Promise<SessionEventSearchDocument[]>',
        description: 'Scan first-party semantic event documents with provider-independent filters.',
        parameters: [{ name: 'sessionId', description: 'live-preferred session id to scan.' }, { name: 'filters', description: 'ANDed metadata and literal-text predicates.' }],
        returns: 'matching semantic documents in ascending seq order.',
      },//结束方法
      {//方法
        signature: 'async readSurface(sessionId: SessionId): Promise<SessionSurfaceSnapshot>',
        description: 'Read one session\'s complete current model surface from one corpus observation.',
        parameters: [{ name: 'sessionId', description: 'live-preferred session id to read.' }],
        returns: 'cloned header, current surface, and the last sequence number included in the raw-log capture.',
        throws: ['when source resolution fails or the session surface is invalid.'],
      },//结束方法
      {//方法
        signature: 'async traceSession(sessionId: SessionId, signal?: AbortSignal): Promise<SessionLineageTrace>',
        description: 'Trace known ancestry and descendants from one corpus observation.',
        parameters: [{ name: 'sessionId', description: 'logical session id to trace.' }, { name: 'signal', description: 'optional cancellation for persistence listing.' }],
        returns: 'a complete lineage or the first parent that could not be resolved.',
        throws: ['when corpus resolution fails, the target is absent, or its known ancestry cycles.'],
      },//结束方法
      {//方法
        signature: 'async traceEvent(request: SessionEventTraceRequest, signal?: AbortSignal): Promise<SessionEventTraceObservation>',
        description: 'Trace one event\'s direct positional replacements and cited source events.',
        parameters: [{ name: 'request', description: 'target session id and event seq.' }, { name: 'signal', description: 'optional cancellation for persisted source resolution.' }],
        returns: 'source header, direct links, and the target\'s positional replacement chain.',
        throws: ['when source resolution fails, the target is absent, or surface/source-event validation fails.'],
      },//结束方法
      {//方法
        signature: 'async readEvent(request: SessionEventReadRequest, signal?: AbortSignal): Promise<SessionEventWindow>',
        description: 'Read one full event plus a bounded raw-log context window.',
        parameters: [{ name: 'request', description: 'target session/seq and context sizes.' }, { name: 'signal', description: 'optional cancellation for persisted source resolution.' }],
        returns: 'cloned target and neighboring events.',
      },//结束方法
    ],//结束 methods
  },//结束服务
]
