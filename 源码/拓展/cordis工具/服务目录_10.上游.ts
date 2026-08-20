/** 本包内嵌 SERVICE_API 分片 10（对照原版 api-catalog.ts）——sessionPersistence+Cache */
export const SERVICE_API: readonly ServiceApiEntry[] = [//服务目录
  {//服务
    key: 'sessionPersistence',
    summary: 'Durable append-only session storage.',
    description: 'Durable append-only session storage. Implementations preserve contiguous, losslessly JSON-serializable events; append resolves only after durability, and load balances a complete interrupted tail without rewriting committed events.',
    methods: [//公开方法
      {//方法
        signature: 'abstract locate(meta: SessionHeader): SessionLocation | undefined',
        description: 'Resolve this backend\'s independent local artifact for a session without reading, creating, flushing, or otherwise materializing it. Backends such as SQLite that do not own one artifact per session return `undefined`.',
        parameters: [{ name: 'meta', description: 'the immutable session header whose artifact is requested.' }],
        returns: 'the backend-specific absolute location, when one exists.',
      },//结束方法
      {//方法
        signature: 'abstract readonly supportsRawArtifacts: boolean',
        description: 'Whether this backend exposes one verbatim raw artifact per session. A backend that declares `true` must override readRaw.',
        parameters: [],//无参数
      },//结束方法
      {//方法
        signature: 'readRaw(_id: SessionId, signal?: AbortSignal): Promise<SessionRawArtifact | undefined>',
        description: 'Read a session\'s backend-owned artifact text verbatim — the exact durable bytes the backend wrote (decoded from its physical encoding, e.g. a decompressed JSONL). The returned `content` is the raw text, not a reconstruction from parsed events, so it preserves backend-specific serialization (chunk packing, key order, line breaks). Callers first test supportsRawArtifacts; `undefined` then means only that the requested session has no materialized artifact.',
        parameters: [{ name: '_id', description: 'the persisted session to read (unused by the default: no per-session artifact).' }, { name: 'signal', description: 'optional cancellation for backend read work.' }],
        returns: 'the raw artifact plus its parsed header, or `undefined` when the session is absent.',
        throws: ['when this backend does not expose per-session raw artifacts.'],
      },//结束方法
      {//方法
        signature: 'abstract create(meta: SessionHeader): Promise<void>',
        description: 'Register a new session\'s metadata. A backend MAY defer the physical write until the first append (lazy materialization), in which case a created-but-never-appended session is absent from list — abandoned sessions leave nothing behind.',
        parameters: [{ name: 'meta', description: 'the immutable header (id, version, cwd, lineage) to record.' }],
      },//结束方法
      {//方法
        signature: 'abstract append(id: SessionId, events: readonly SessionEvent[]): Promise<void>',
        description: 'Durably persist a batch of events. Honors the append-only and contiguous- seq contracts: the first event\'s `seq` MUST equal the stored next-seq (after `load` has durably closed any interrupted turn). Rejects non-JSON- serializable `event.data` with an error naming the offending event type.',
        parameters: [{ name: 'id', description: 'the session the batch belongs to.' }, { name: 'events', description: 'the contiguous batch to persist, in seq order.' }],
      },//结束方法
      {//方法
        signature: 'async prepare(id: SessionId, signal?: AbortSignal): Promise<SessionPreparation>',
        description: 'Prepare the exact unpublished Session used by resume. Implementations may reuse object graphs retained by an earlier inspect after confirming their durable revision is still current; disposal releases an unpublished reservation. Revision retries require the durable log to remain unchanged for one read/check round trip; continuous external writers may delay completion.',
        parameters: [{ name: 'id', description: 'persisted session to prepare.' }, { name: 'signal', description: 'optional cancellation for preparation work.' }],
        returns: 'one owned unpublished Session preparation.',
      },//结束方法
      {//方法
        signature: 'abstract load(id: SessionId): Promise<SessionInspection>',
        description: 'Load an immutable balanced logical view and commit any required cold recovery. A complete interrupted final turn is preserved and durably closed with missing tool errors plus any open step and turn boundaries; only a torn final record is discarded. Unknown versions and corruption in the committed prefix reject. Implementations MUST NOT crash-repair an identity still bound to a live Session: a balanced live log may return as a durable snapshot, while an open live turn rejects. Returned values may be shared with immutable live or prepared state and must not be mutated. Revision-based implementations may wait for one stable read/check round trip.',
        parameters: [{ name: 'id', description: 'the persisted session to reload.' }],
        returns: 'the header and a log ending on a balanced `turn/end`.',
      },//结束方法
      {//方法
        signature: 'abstract inspect(id: SessionId, signal?: AbortSignal): Promise<SessionInspection>',
        description: 'Inspect an immutable logical session without committing recovery or publishing it. A cold complete interrupted turn receives synthetic closers in memory and a torn physical tail remains untouched. An already-live Session instead yields its current immutable snapshot, which may contain an open turn and its `session/end-seed` boundary. Coordinator-backed implementations retain the exact cold unpublished Session for bounded reuse by a later prepare. A stale ready source is reloaded; a source already committing or reserved for resume remains exclusive, and inspection may borrow its immutable view. Callers borrow only the immutable header and log. Continuous external writers may delay revision convergence.',
        parameters: [{ name: 'id', description: 'the persisted session to inspect.' }, { name: 'signal', description: 'optional cancellation for queued and backend read work.' }],
        returns: 'the validated header and current logical event log.',
      },//结束方法
      {//方法
        signature: 'abstract readFrom(id: SessionId, fromSeq: number, signal?: AbortSignal): Promise<{ meta: SessionHeader; events: SessionEvent[] }>',
        description: 'Read the stored events from `fromSeq` onward — the read-from-seq primitive for read models that resume from a watermark (e.g. a persisted projection cache folding only the tail past its checkpoint). Unlike inspect, it is a detached physical suffix read: no preparation cache, torn-tail truncation, synthetic closers, or coordinator-state publication. Only events from the valid contiguous stored prefix are returned, so a torn fragment never reaches the caller. `fromSeq` at or beyond the stored prefix returns an empty event list (never an error). Backends whose medium can seek by seq (SQLite) read only the suffix; sequential media (JSONL, both encodings) still parse the whole artifact and skip forward — the primitive bounds what is RETURNED and refolded, not every backend\'s physical read.',
        parameters: [{ name: 'id', description: 'the persisted session to read.' }, { name: 'fromSeq', description: 'first event seq to include; a non-negative safe integer.' }, { name: 'signal', description: 'optional cancellation for queued and backend read work.' }],
        returns: 'the header and the stored events with `seq >= fromSeq`.',
      },//结束方法
      {//方法
        signature: 'abstract list(signal?: AbortSignal): Promise<SessionHeader[]>',
        description: 'Lightweight listing from metadata, without a full-log parse.',
        parameters: [{ name: 'signal', description: 'optional cancellation for backend listing work.' }],
        returns: 'one header per materialized session.',
      },//结束方法
      {//方法
        signature: 'abstract listSnapshots(signal?: AbortSignal): Promise<SessionPersistenceSnapshot[]>',
        description: 'List materialized sessions with cheap per-log change tokens.\n\nRepeated observations of an unchanged log return the same revision. A successful mutating load repair changes the next listed revision. Revisions also distinguish independently backed stores so backend-local counters cannot compare equal across different persistence sources.',
        parameters: [{ name: 'signal', description: 'optional cancellation for backend snapshot-listing work.' }],
        returns: 'one header and opaque revision per materialized session without loading full logs.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'sessionProjectionCache',
    summary: 'The persisted projection cache service.',
    description: 'The persisted projection cache service. Opens the `session_projcache` domain at init, checkpoints live sessions on a throttled write-behind (count/interval triggers from Config) plus two mandatory points — `turn/end` and session disposal (the live-to-cold moment) — and serves the cold-read ladder: cached row, persistence `readFrom` tail, registry `restore`, durable write-back. Every durable write is fail-soft: failures log a warning and the cache self-heals on the next write or cold read.',
    methods: [//公开方法
      {//方法
        signature: 'cachedSnapshot(meta: SessionHeader): ProjectionSnapshot | undefined',
        description: 'The zero-I/O listing read: whole values viewed straight from the stored rows (version-matching keys only), each cut carried with its watermark so a client value store can seed under its higher-seq-wins rule — as stale as the last durable checkpoint but never wrong, and never from an unrelated log (the caller\'s header is the identity witness). Fresher paths (the history tail baseline, coldSnapshot) supersede these values whenever a session is actually opened.',
        parameters: [{ name: 'meta', description: 'the listed session\'s header (identity witness; no log read).' }],
        returns: 'the cut (`asOfSeq` = lowest served-row watermark), or `undefined` when no usable row exists for this lifecycle.',
      },//结束方法
      {//方法
        signature: 'async write(session: Session): Promise<void>',
        description: 'Durably checkpoint one live session NOW (both mandatory points call this; tests and carriers may too). The registry cut is snapshotted at this boundary (states are live references), then the whole record is replaced. NOT fail-soft — callers on the fail-soft paths contain it.',
        parameters: [{ name: 'session', description: 'the live session to checkpoint.' }],
        returns: 'resolution after durability and event emission.',
      },//结束方法
      {//方法
        signature: 'async coldSnapshot(id: SessionId, signal?: AbortSignal): Promise<ProjectionSnapshot>',
        description: 'Cold-read one persisted session\'s projections with zero full-log load: cached rows + a persistence `readFrom` tail from the registry\'s restore floor, refolded by the registry and written back (fail-soft) so the next cold read starts closer. A cache row invalidated by a shrunk log (crash-repair truncation) triggers one full re-read from seq 0 — the ladder\'s slow rung, still no crash. Rejects when the session has no persisted log (`not found` from the persistence seam).',
        parameters: [{ name: 'id', description: 'the persisted session to read.' }, { name: 'signal', description: 'optional cancellation for the persistence reads.' }],
        returns: 'the snapshot cut at the stored log end.',
      },//结束方法
    ],//结束 methods
  },//结束服务
]
