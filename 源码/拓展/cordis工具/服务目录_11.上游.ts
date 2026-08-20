/** 本包内嵌 SERVICE_API 分片 11（对照原版 api-catalog.ts）——sessionProjections+Query+Reference */
export const SERVICE_API: readonly ServiceApiEntry[] = [//服务目录
  {//服务
    key: 'sessionProjections',
    summary: '`ctx.sessionProjections`: the projection unit table and its drive.',
    description: '`ctx.sessionProjections`: the projection unit table and its drive. The service subscribes to `session/event` once; every committed event passes every registered unit\'s `apply` (eager drive), and a changed state reference notifies the change feed with the schema-validated view. Cells build lazily — a unit registered after events flowed, or a session older than the registry, folds `init` over the in-memory log on first touch (event or read). Registration is an effect (disposer rides the calling fiber): an unloaded domain plugin\'s key disappears from snapshots and clients read it as capability absence. Domain plugins register under `ctx.inject([\'sessionProjections\'], …)` so headless assemblies without the registry stay unaffected. Registrants sharing a key share one unit and are counted: the same tool package mounted in N agent presets registers N times, and the key survives until the last one unloads.',
    methods: [//公开方法
      {//方法
        signature: 'register<K extends keyof SessionProjectionMap, S>(definition: ProjectionDefinition<K, S>): () => void',
        description: 'Register one domain\'s unit. The registration is an effect on the calling context\'s fiber: disposing the fiber (or calling the returned disposer) removes the key — and the unit\'s cached cells — from subsequent drives and snapshots.',
        parameters: [{ name: 'definition', description: 'key, state schema, pure unit functions, and stateVersion.' }],
        returns: 'the exact disposer that unregisters this unit.',
      },//结束方法
      {//方法
        signature: 'onChanged(listener: ProjectionChangeListener): () => void',
        description: 'Subscribe to the change feed. The registration is an effect on the calling context\'s fiber.',
        parameters: [{ name: 'listener', description: 'called once per unit whose state reference changed, per committed event.' }],
        returns: 'the exact disposer that unsubscribes.',
      },//结束方法
      {//方法
        signature: 'snapshot(session: Session): ProjectionSnapshot',
        description: 'One consistent cut over every registered unit for one session, read from the watermark cache (missing cells fold lazily over the in-memory log). Fully synchronous — every value and `asOfSeq` reflect the same log position. Each value passes its unit\'s schema before leaving.',
        parameters: [{ name: 'session', description: 'the session whose projection values are read.' }],
        returns: 'the snapshot; `values` is empty when no unit is registered.',
      },//结束方法
      {//方法
        signature: 'checkpoint(session: Session): ProjectionCheckpoint',
        description: 'State-level checkpoint of every registered unit for one session, read from the watermark cache (missing cells fold lazily over the in-memory log). This is the write side of the persisted projection cache: the returned rows are the `(key → {ver, seq, val})` part of the durable `(sessionId, key, ver, seq, val)` rows. Every `val` is a DETACHED structured clone — never the live cell reference: the watermark cache is this registry\'s authoritative mutable state, and a caller reaching the live reference could corrupt every subsequent snapshot and frame through it (plain JSON by the unit contract, so the clone is total).',
        parameters: [{ name: 'session', description: 'the session whose unit states are checkpointed.' }],
        returns: 'one row per registered key; empty when no unit is registered.',
      },//结束方法
      {//方法
        signature: 'restoreFloor(checkpoint: ProjectionCheckpoint): number | undefined',
        description: 'The stored seq a restore tail read over `checkpoint` must start at: one event BELOW the lowest usable watermark (a row is usable when its `ver` matches the live unit\'s `stateVersion`; an absent or mismatched row pulls the floor to `0` — that key must refold the full log). The one-below anchor is load-bearing: the tail then proves how far the stored log still extends, so restore can detect a log that shrank below a row\'s watermark (crash-repair truncation) instead of serving the stale row as current — an empty tail read from the anchor yields an end below every watermark and the restore rejects for a full re-read.',
        parameters: [{ name: 'checkpoint', description: 'persisted rows for one session (possibly stale or empty).' }],
        returns: 'the seq to hand the persistence `readFrom`, or `undefined` when no unit is registered (no read needed — {@link restore} would serve empty values regardless).',
      },//结束方法
      {//方法
        signature: 'viewCheckpoint(checkpoint: ProjectionCheckpoint): Partial<SessionProjectionMap>',
        description: 'View a checkpoint\'s rows without any log read: for every registered unit whose row\'s `ver` matches, serve the schema-validated `view` of the stored state; mismatched or absent rows leave their key absent (a cold or listing consumer treats it as not-yet-available and a fuller read path refolds it). The zero-I/O rung of the read ladder — values are as stale as their rows, never wrong.',
        parameters: [{ name: 'checkpoint', description: 'persisted rows for one session (possibly stale or empty).' }],
        returns: 'whole values per key with a usable row; empty when none.',
      },//结束方法
      {//方法
        signature: 'restore(checkpoint: ProjectionCheckpoint, events: readonly SessionEvent[], baseSeq: number): { snapshot: ProjectionSnapshot; checkpoint: ProjectionCheckpoint }',
        description: 'Cold read: fold every registered unit over a stored log suffix, seeding each from its checkpoint row when usable — the one read recipe (cached state + forward tail replay + `view`) applied without a live `Session`. Call with the events returned by a persistence `readFrom(id, restoreFloor(checkpoint))` and that same floor as `baseSeq`; the floor\'s one-below anchor makes the supplied end honest, so a shrunk log is detected here. A row is usable iff its `ver` matches the live unit\'s `stateVersion`, it does not predate `baseSeq` (`seq >= baseSeq - 1`), and it does not claim events past the supplied end (`seq <= endSeq`); an unusable row is discarded and its key refolds from `init` — which is only sound over the full log, so a discarded row with `baseSeq > 0` throws (the caller re-reads from seq 0, e.g. after a crash-repair truncation shrank the log below a row\'s watermark).',
        parameters: [{ name: 'checkpoint', description: 'persisted rows for one session (possibly stale or empty).' }, { name: 'events', description: 'the stored events with `seq >= baseSeq`, in seq order.' }, { name: 'baseSeq', description: 'the seq `events` starts at (its first event\'s seq when non-empty).' }],
        returns: 'the snapshot cut at the supplied log end (`asOfSeq` is the last supplied event\'s seq, `baseSeq - 1` for an empty tail) plus the refreshed checkpoint rows at that cut, ready for a durable write-back.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'sessionReferenceResolver',
    summary: 'Exact-read consumer that prepares immutable cross-session message context.',
    description: 'Exact-read consumer that prepares immutable cross-session message context.',
    methods: [//公开方法
      {//方法
        signature: 'async listCandidates( agent: Agent, query: string = \'\', limit: number = this.config.candidateLimit, signal?: AbortSignal, ): Promise<SessionReferenceCandidate[]>',
        description: 'List reference candidates, ranked by working-directory affinity.',
        parameters: [{ name: 'agent', description: 'target agent; self is excluded and its cwd drives ranking.' }, { name: 'query', description: 'optional case-insensitive session-id/cwd/title substring.' }, { name: 'limit', description: 'optional positive result cap.' }, { name: 'signal', description: 'optional cancellation boundary for host autocomplete teardown.' }],
        returns: 'candidates labeled by latest title or, when absent, session id.',
      },//结束方法
      {//方法
        signature: 'async prepare( agent: Agent, content: ContentBlock[], references: SessionReferenceInput[], signal?: AbortSignal, ): Promise<PreparedReferencedMessage>',
        description: 'Snapshot all references before enqueue and return one aggregated durable context.',
        parameters: [{ name: 'agent', description: 'target agent; references to it are rejected.' }, { name: 'content', description: 'already host-normalized readable message content.' }, { name: 'references', description: 'structured source sessions in mention order.' }, { name: 'signal', description: 'optional cancellation boundary for host request teardown.' }],
        returns: 'detached content and optional referenced-session context.',
      },//结束方法
    ],//结束 methods
  },//结束服务
]
