/** 本包内嵌 SERVICE_API 分片 18（对照原版 api-catalog.ts）——typert..workspaceRegistry */
export const SERVICE_API: readonly ServiceApiEntry[] = [//服务目录
  {//服务
    key: 'typert',
    summary: 'Registry of generated schemas, package reflection, invocations, and Remote dependency providers.',
    description: 'Registry of generated schemas, package reflection, invocations, and Remote dependency providers.',
    methods: [//公开方法
      {//方法
        signature: 'register(contribution: TypertContribution): TypertDisposer',
        description: 'Register one generated contribution atomically for the calling fiber. Duplicate package-face identities, schemas, invocation ids, or endpoints reject the whole batch.',
        parameters: [{ name: 'contribution', description: 'generated schemas, reflection, and Host invocations.' }],
        returns: 'the exact effect disposer that removes this contribution.',
      },//结束方法
      {//方法
        signature: 'get(key: string): TypertSchemaRecord | undefined',
        description: 'Look up one schema by `<package>#<name>`.',
        parameters: [{ name: 'key', description: 'global schema key.' }],
        returns: 'the live schema record, or `undefined` when absent.',
      },//结束方法
      {//方法
        signature: 'resolve(key: string): TypertSchemaRecord',
        description: 'Resolve one required schema.',
        parameters: [{ name: 'key', description: 'global schema key.' }],
        returns: 'the live schema record.',
        throws: ['when the key is malformed, the package face is absent, or the schema is not contributed.'],
      },//结束方法
      {//方法
        signature: 'list(filter: TypertSchemaFilter = {}): TypertSchemaRecord[]',
        description: 'Enumerate live schemas in registration order.',
        parameters: [{ name: 'filter', description: 'optional package and face restriction.' }],
        returns: 'matching schema records.',
      },//结束方法
      {//方法
        signature: 'getPackage(packageName: string, face: TypertFace = \'host\'): TypertPackageRecord | undefined',
        description: 'Look up generated reflection for one package face.',
        parameters: [{ name: 'packageName', description: 'exact npm package name.' }, { name: 'face', description: 'face to query; defaults to the host runtime.' }],
        returns: 'the live package record, or `undefined` when absent.',
      },//结束方法
      {//方法
        signature: 'listPackages(filter: TypertPackageFilter = {}): TypertPackageRecord[]',
        description: 'Enumerate generated package reflection in registration order.',
        parameters: [{ name: 'filter', description: 'optional package and face restriction.' }],
        returns: 'matching package records.',
      },//结束方法
      {//方法
        signature: 'toJSONSchema(key: string, params?: z.core.ToJSONSchemaParams): z.core.JSONSchema.BaseSchema',
        description: 'Project a live Zod schema to JSON Schema without caching the result.',
        parameters: [{ name: 'key', description: 'global schema key.' }, { name: 'params', description: 'Zod projection parameters.' }],
        returns: 'a fresh JSON Schema document.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'typertGateway',
    summary: 'Resolve strict generated definitions or conservative SRC markers against current Cordis Services and Typert providers.',
    description: 'Resolve strict generated definitions or conservative SRC markers against current Cordis Services and Typert providers.',
    methods: [//公开方法
      {//方法
        signature: 'async invoke(request: InvokeRemoteRequest): Promise<unknown>',
        description: 'Invoke one live Remote method through strict generated reflection or SRC markers.',
        parameters: [{ name: 'request', description: 'decoded endpoint and exact named wire arguments.' }],
        returns: 'the validated business result.',
        throws: ['{@link TypertGatewayError} for dispatch, provider, or boundary failures; lookup-policy and business errors retain identity.'],
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'userQuestions',
    summary: '`ctx.userQuestions`: one active UI provider plus an `ask()` API.',
    description: '`ctx.userQuestions`: one active UI provider plus an `ask()` API.',
    methods: [//公开方法
      {//方法
        signature: 'registerProvider(provider: UserQuestionProvider): () => void',
        description: 'Register the UI provider. Only one provider may be active in a context.',
        parameters: [{ name: 'provider', description: 'UI-side implementation that collects answers.' }],
        returns: 'Disposer that unregisters this provider.',
      },//结束方法
      {//方法
        signature: 'async ask(request: AskUserQuestionRequest): Promise<AskUserQuestionAnswer>',
        description: 'Ask the active UI provider and wait for the user\'s answer.\n\nWhen a caller supplies an agent, human interaction is valid only for the exact live runtime root. Runtime ownership, not durable session lineage, decides this boundary: an owned child has no human answerer and would block forever, while a lineage-bearing session resumed as a new runtime root may ask normally.',
        parameters: [{ name: 'request', description: 'Questions, owner agent, and abort signal.' }],
        returns: 'The answer chosen or typed by the human.',
        throws: ['{UserQuestionError} code `CALLER_NOT_LIVE` when a supplied agent is not the registry\'s exact live instance, or `DELEGATED_CALLER` when that live agent is owned by another agent.'],
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'web',
    summary: 'The web access service.',
    description: 'The web access service. Registered as `ctx.web` (one instance per context).\n\nSelection semantics (resolved at execution time, never order-dependent):\n\n- A configured id that is registered and `available()` → that provider.\n- A configured id not registered → `WEB_PROVIDER_CONFIGURED_MISSING`.\n- A configured id registered but unavailable → `WEB_PROVIDER_CONFIGURED_UNAVAILABLE`.\n- No id configured, exactly one registered usable provider → that provider.\n- No id configured, multiple usable providers → `WEB_PROVIDER_AMBIGUOUS`.\n- No id configured, no usable provider → `WEB_PROVIDER_UNAVAILABLE`.',
    methods: [//公开方法
      {//方法
        signature: 'registerSearchProvider(provider: WebSearchProvider): () => void',
        description: 'Register a search provider. Throws WebError `WEB_DUPLICATE_PROVIDER` if its id is already registered for search. Returns a disposer; disposed with the calling fiber.',
        parameters: [{ name: 'provider', description: 'the provider; its `id` is the registry key.' }],
        returns: 'the disposer that unregisters the provider.',
      },//结束方法
      {//方法
        signature: 'registerFetchProvider(provider: WebFetchProvider): () => void',
        description: 'Register a fetch provider. Throws WebError `WEB_DUPLICATE_PROVIDER` if its id is already registered for fetch. Returns a disposer; disposed with the calling fiber.',
        parameters: [{ name: 'provider', description: 'the provider; its `id` is the registry key.' }],
        returns: 'the disposer that unregisters the provider.',
      },//结束方法
      {//方法
        signature: 'async search(request: WebSearchRequest, signal?: AbortSignal): Promise<WebSearchResult>',
        description: 'Run one search through the selected provider. Resolves the provider at call time with the selection rules above; throws WebError when the capability cannot run. The seam enforces `request.maxResults` on the result: if the provider over-returns, `sources[]` is truncated and `truncated` set.',
        parameters: [{ name: 'request', description: 'the query and optional result limit.' }, { name: 'signal', description: 'optional cancellation signal forwarded to the provider.' }],
        returns: 'the provider\'s results, capped to `request.maxResults`.',
      },//结束方法
      {//方法
        signature: 'async fetch(request: WebFetchRequest, signal?: AbortSignal): Promise<WebFetchResult>',
        description: 'Retrieve one URL through the selected provider. Resolves the provider at call time with the selection rules above; throws WebError when the capability cannot run. A non-2xx response is a result, not a throw.',
        parameters: [{ name: 'request', description: 'the URL plus retrieval options.' }, { name: 'signal', description: 'optional cancellation signal forwarded to the provider.' }],
        returns: 'the retrieval outcome; non-2xx responses resolve descriptively.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'webServer',
    summary: 'The browser HTTP carrier service.',
    description: 'The browser HTTP carrier service. Activation listens immediately. Route registration order does not affect requests because configured named routes must be distinct, and the fallback handler answers anything not yet claimed during startup with 404 until its owner registers. A listen failure rejects initialization, and the boot process reports the failed fiber.',
    methods: [//公开方法
      {//方法
        signature: 'register(route: WebRoute): () => void',
        description: 'Register a named route. Duplicate (kind, path) throws — route patterns are a composition-level contract, so a collision is a misconfiguration.',
        parameters: [{ name: 'route', description: 'kind, path, and the owning handler.' }],
        returns: 'the disposer removing the route.',
      },//结束方法
      {//方法
        signature: 'registerUpgrade(route: WebUpgradeRoute): () => void',
        description: 'Register an exact-path HTTP upgrade route. Duplicate paths throw because one socket can have only one protocol owner.',
        parameters: [{ name: 'route', description: 'pathname and handler owning negotiation plus socket use.' }],
        returns: 'the disposer removing the route.',
      },//结束方法
      {//方法
        signature: 'registerFallback(handler: WebRoute[\'handler\']): () => void',
        description: 'Claim the fallback seat: the handler answering every request no named route matches (the SPA dist server in the shipped Web composition). One owner only — a second registration throws, because two fallbacks cannot compose.',
        parameters: [{ name: 'handler', description: 'owns the full response lifecycle of unmatched requests.' }],
        returns: 'the disposer releasing the seat.',
      },//结束方法
      {//方法
        signature: 'tapIndex(transform: (html: string) => string): () => void',
        description: 'Register an index.html transform, applied by the fallback owner to every index response (applyIndexTaps) in registration order.',
        parameters: [{ name: 'transform', description: 'pure html-to-html function.' }],
        returns: 'the disposer removing the transform.',
      },//结束方法
      {//方法
        signature: 'applyIndexTaps(html: string): string',
        description: 'Run an index.html body through the registered taps in registration order — called by the fallback owner on every index response it renders.',
        parameters: [{ name: 'html', description: 'the raw index.html body.' }],
        returns: 'the transformed body.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'workflowEngine',
    summary: 'Workflow Service Definition contract.',
    description: 'Workflow Service Definition contract. Invalid requests throw before publication; a live run is holder-owned, its result never rejects, cancellation and disposal are bounded, and disposal waits for child cleanup within that bound. Lifecycle listener failures are contained, and `workflow/end` fires exactly once as the result settles.',
    methods: [//公开方法
      {//方法
        signature: 'abstract start(request: WorkflowStartRequest): WorkflowRun',
        description: 'Parse and execute a workflow script.',
        parameters: [{ name: 'request', description: 'the script, its `args`, the parent agent, and an optional cancel signal.' }],
        returns: 'the live run; its `result` resolves when the script settles.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'workspaceRegistry',
    summary: 'Durable workspace registry.',
    description: 'Durable workspace registry. Startup waits for `sessionPersistence`, builds one canonical-cwd header index, and completes the one-time history bootstrap before the service becomes active. The persistence dependency is mandatory so an unavailable peer can never be mistaken for an empty history and commit the initialized marker.',
    methods: [//公开方法
      {//方法
        signature: 'async create(path: string, title?: string): Promise<Workspace>',
        description: 'Create or reuse a workspace for an existing directory. The path is canonicalized through `fs.realpath`; a nonexistent path rejects with the original error and a non-directory rejects. Repeated calls for the same canonical path return the existing entity without changing its title. A newly created workspace is prepended to the durable registry order. Different canonical paths may share a display title.',
        parameters: [{ name: 'path', description: 'Existing directory to own, in any path spelling.' }, { name: 'title', description: 'Display title used only when a new record is created.' }],
        returns: 'the existing or newly durable workspace.',
      },//结束方法
      {//方法
        signature: 'get(id: WorkspaceId): Workspace | undefined',
        description: 'Look up a workspace by id.',
        parameters: [{ name: 'id', description: 'Workspace id.' }],
        returns: 'the workspace, or `undefined` when unknown.',
      },//结束方法
      {//方法
        signature: 'list(): Workspace[]',
        description: 'Synchronous workspace projection in durable registry order. Every entity\'s `sessionIds` getter is already filtered by the startup/live canonical-cwd header index; this method performs no persistence reads.',
        parameters: [],//无参数
        returns: 'a fresh ordered array of workspace entities.',
      },//结束方法
      {//方法
        signature: 'delete(id: WorkspaceId): Promise<boolean>',
        description: 'Delete one workspace registration while retaining its directory and every session log. The durable order is updated before the table deletion; a failed table write restores the prior order and keeps the entity published. Unknown ids are an idempotent no-op for domain callers.',
        parameters: [{ name: 'id', description: 'Workspace registration to remove.' }],
        returns: '`true` when a record was deleted, `false` when it was unknown.',
      },//结束方法
      {//方法
        signature: 'insertBefore(id: WorkspaceId, beforeId?: WorkspaceId): Promise<readonly WorkspaceId[]>',
        description: 'Move one workspace within the durable display order, DOM-insertBefore-like. With an anchor it lands before that workspace; without one it appends.',
        parameters: [{ name: 'id', description: 'Workspace to move.' }, { name: 'beforeId', description: 'Workspace anchor; omitted appends.' }],
        returns: 'the complete committed workspace order.',
      },//结束方法
      {//方法
        signature: 'archiveSession(sessionId: SessionId): Promise<void>',
        description: 'Archive one session durably. The session must exist (live or in session persistence); its workspace accounting — or lack of one — is irrelevant. An already archived id resolves without writing.',
        parameters: [{ name: 'sessionId', description: 'The session to archive.' }],
        returns: 'resolution after durability.',
      },//结束方法
      {//方法
        signature: 'async resolveByPath(path: string): Promise<Workspace | undefined>',
        description: 'Resolve by canonical directory path without creating or mutating a workspace. A missing path rejects during `realpath`; an existing unowned directory returns `undefined`.',
        parameters: [{ name: 'path', description: 'Existing directory path in any spelling.' }],
        returns: 'the workspace owning the canonical path, when one exists.',
      },//结束方法
    ],//结束 methods
  },//结束服务
]
