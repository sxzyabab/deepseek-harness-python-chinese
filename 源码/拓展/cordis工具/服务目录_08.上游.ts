/** 本包内嵌 SERVICE_API 分片 08（对照原版 api-catalog.ts）——jobs+llm */
export const SERVICE_API: readonly ServiceApiEntry[] = [//服务目录
  {//服务
    key: 'jobs',
    summary: 'Abstract background job registry.',
    description: 'Abstract background job registry. Subclass, implement the abstract methods, and load the subclass as a plugin — it registers as `ctx.jobs` (one implementation per context; loading a second throws, which is cordis\' standard duplicate-service behavior).\n\nImplementations must honor these semantics:\n\n- Registrations outlive producer and controller fibers. Owner and service disposal cancel live work and await compliant producers; a throwing teardown cancel force-fails only the record. Teardown cancellation also marks the record reported, because a record its owner is being destroyed for has no reader left.\n- Owned-job access is fenced by the owner\'s session id. Ids are predictable, so authorization — not secrecy — is the boundary.\n- Settlement is first-wins: one terminal record, released waiters, and one round of contained listener notification, even against a late producer outcome. Completion is announced last, after the record is committed and every other observer of the settlement has seen it, because a reporter may open a model turn synchronously.\n- start refuses work while no attached job controller serves the spec\'s owner, so a producer cannot start work that owner cannot collect or stop. One registry serves every composition in the process, so this question — and completion-listener delivery — is owner-relative rather than process-wide: registrations made from an unscoped context serve every owner, and registrations made under an agent composition\'s scope serve exactly the agents composed under it.',
    methods: [//公开方法
      {//方法
        signature: 'abstract start(spec: JobStart): JobId',
        description: 'Preflight access, validation, owner cleanup, and implementation-owned admission before starting and atomically registering work. Any preflight rejection leaves no job id or execution resource. A throwing starter leaves nothing registered; after it returns, registration cannot fail. Settlement records the outcome, notifies listeners, and releases waiters.',
        parameters: [{ name: 'spec', description: 'job identity, owner, and synchronous starter.' }],
        returns: 'the registry-issued `<kind>-N` id.',
      },//结束方法
      {//方法
        signature: 'abstract list(caller?: Agent): JobSnapshot[]',
        description: 'List caller-owned and unowned jobs in registration order without exposing another session\'s labels.',
        parameters: [{ name: 'caller', description: 'reading agent; a non-agent caller sees only unowned jobs.' }],
        returns: 'fresh snapshots.',
      },//结束方法
      {//方法
        signature: 'abstract get(id: JobId, caller?: Agent): JobSnapshot',
        description: 'Return a non-consuming snapshot without changing its read cursor or notice state. Throws for an unknown or foreign job.',
        parameters: [{ name: 'id', description: 'job to look up.' }, { name: 'caller', description: 'reading agent checked against the owner.' }],
        returns: 'a fresh snapshot.',
      },//结束方法
      {//方法
        signature: 'abstract read(id: JobId, caller?: Agent): JobRead',
        description: 'Read the next stream delta, or the idempotent final output after settlement. A terminal read marks the job reported. Throws for an unknown or foreign job.',
        parameters: [{ name: 'id', description: 'job to read.' }, { name: 'caller', description: 'reading agent checked against the owner.' }],
        returns: 'output text and the post-read snapshot.',
      },//结束方法
      {//方法
        signature: 'abstract kill(id: JobId, caller?: Agent, reason?: string): \'requested\' | \'already-finished\'',
        description: 'Request cancellation, then mark the job stopping and reported. A producer throw propagates without changing job state. Throws for an unknown or foreign job.',
        parameters: [{ name: 'id', description: 'job to cancel.' }, { name: 'caller', description: 'killing agent checked against the owner.' }, { name: 'reason', description: 'logged reason forwarded to the producer.' }],
        returns: '`requested` for live work, otherwise `already-finished`.',
      },//结束方法
      {//方法
        signature: 'abstract wait(id: JobId, timeoutMs: number, caller?: Agent, signal?: AbortSignal): Promise<JobSnapshot>',
        description: 'Wait for settlement or timeout without cancelling the job. Caller abort rejects only while the job is live; after settlement the terminal snapshot wins so a notice suppressed for this waiter is still delivered. Throws for invalid, unknown, or foreign input.',
        parameters: [{ name: 'id', description: 'job to wait for.' }, { name: 'timeoutMs', description: 'positive finite wait bound in milliseconds.' }, { name: 'caller', description: 'waiting agent checked against the owner.' }, { name: 'signal', description: 'optional cancellation of the wait itself.' }],
        returns: 'snapshot at settlement or timeout.',
      },//结束方法
      {//方法
        signature: 'abstract onJobDone(listener: JobDoneListener): () => void',
        description: 'Register an effect-scoped completion listener. It receives the settlements of the owners its registering context\'s scope covers; each listener is contained; returned promises are observed but not awaited. No listener runs after service disposal.',
        parameters: [{ name: 'listener', description: 'receives each terminal snapshot and its exact owner.' }],
        returns: 'disposer that unregisters the listener.',
      },//结束方法
      {//方法
        signature: 'abstract onJobsChanged(listener: JobsChangedListener): () => void',
        description: '/** Register an effect-scoped observer of visible-set changes. It fires after every commit that changes what list returns for that owner — registration, every stopping transition (including the one teardown performs before it awaits a slow producer), settlement, owner-disposal removal, and the emptying that service disposal commits — so an observer re-reads rather than accumulating deltas.\n\nDelivery is owner-relative on the same terms as onJobDone: an observer registered from an unscoped context — a host composition\'s own carrier — sees every owner, while one registered under an agent composition\'s scope sees exactly the agents composed under it.\n\nThis is not a superset of onJobDone: that one delivers the terminal record under first-wins semantics a job controller couples to notice delivery, while this one carries no delivery meaning and marks nothing reported. Listeners are contained and never awaited.',
        parameters: [{ name: 'listener', description: 'receives the owner whose visible set changed, or `undefined` when an unowned job changed and every caller\'s set did.' }],
        returns: 'disposer that unregisters the listener.',
      },//结束方法
      {//方法
        signature: 'abstract attachController(name: string): () => void',
        description: 'Attach an effect-scoped controller that can read and stop jobs. It serves the owners its registering context\'s scope covers, and start refuses an owner no attached controller serves.',
        parameters: [{ name: 'name', description: 'diagnostic label; duplicate names remain independent.' }],
        returns: 'disposer that detaches this controller.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'llm',
    summary: 'The abstract `llm` service: an adapter registry plus a streaming model-call API, interceptable via the `llm/stream` waterfall.',
    description: 'The abstract `llm` service: an adapter registry plus a streaming model-call API, interceptable via the `llm/stream` waterfall.',
    methods: [//公开方法
      {//方法
        signature: 'registerAdapter(providers: string[], adapter: LlmAdapter): AdapterRegistrationHandle',
        description: 'Register an adapter for the given provider routes. Throws `LlmError` with code `DUPLICATE_ADAPTER` if any provider already has an adapter (all-or-nothing). Disposed with the fiber.',
        parameters: [{ name: 'providers', description: 'every provider route this adapter should serve.' }, { name: 'adapter', description: 'the adapter that streams calls for those providers.' }],
        returns: 'the disposer, carrying {@link AdapterRegistrationHandle.replace}.',
      },//结束方法
      {//方法
        signature: 'listProviders(): LlmProviderInfo[]',
        description: 'Describe provider routes with a registered adapter.',
        parameters: [],//无参数
        returns: 'detached provider metadata in registration order.',
      },//结束方法
      {//方法
        signature: 'registerConfigurableProviders(entries: readonly LlmConfigurableProvider[]): DirectoryRegistrationHandle',
        description: 'Declare provider routes an adapter plugin can activate through configuration. Registration is all-or-nothing: an empty list, invalid entry, or a provider already declared by any registration throws `LlmError` without registering the rest. Disposed with the fiber.',
        parameters: [{ name: 'entries', description: 'every configurable provider this plugin owns.' }],
        returns: 'a handle that withdraws all of them, and can atomically replace them.',
      },//结束方法
      {//方法
        signature: 'listConfigurableProviders(): LlmConfigurableProvider[]',
        description: 'List every declared configurable provider, registered or dormant.',
        parameters: [],//无参数
        returns: 'detached directory entries in declaration order.',
      },//结束方法
      {//方法
        signature: 'registerModelDiscovery( settingsNs: string, discover: (request: LlmModelDiscoveryRequest) => Promise<readonly LlmDiscoveredModel[]>, ): () => void',
        description: 'Offer to interrogate provider endpoints on behalf of the settings namespace this plugin owns. The namespace is the key because that is what a configuration surface already holds from the configurable-provider directory, and because a provider being *added* has no route to name yet. Disposed with the fiber.',
        parameters: [{ name: 'settingsNs', description: 'the namespace whose profiles this discovery serves.' }, { name: 'discover', description: 'interrogates one endpoint; must honor `request.signal`.' }],
        returns: 'the disposer that withdraws the offer.',
      },//结束方法
      {//方法
        signature: 'async discoverModels( settingsNs: string, request: LlmModelDiscoveryRequest, ): Promise<LlmDiscoveredModel[]>',
        description: 'Interrogate one provider endpoint for the models it advertises. The request describes a draft, not a stored route, so nothing here reads or writes settings or credentials — the caller owns both, and the reply is candidate metadata a surface may offer for adoption.',
        parameters: [{ name: 'settingsNs', description: 'namespace whose registered discovery serves this draft.' }, { name: 'request', description: 'the endpoint, protocol, and one-shot credential to use.' }],
        returns: 'the advertised models, deduplicated in endpoint order.',
      },//结束方法
      {//方法
        signature: 'providerRetryPolicy(provider: string): ResolvedRetryPolicy',
        description: 'Resolve the retry policy captured when one provider route was registered.',
        parameters: [{ name: 'provider', description: 'registered provider route to inspect.' }],
        returns: 'the provider-owned policy, with normal defaults already resolved.',
      },//结束方法
      {//方法
        signature: 'async listModels(provider: string): Promise<LlmModelInfo[]>',
        description: 'Discover models advertised by one registered provider. Catalog membership is advisory and never changes routing or request validation.',
        parameters: [{ name: 'provider', description: 'registered provider route to inspect.' }],
        returns: 'detached model metadata in adapter-preferred order.',
      },//结束方法
      {//方法
        signature: 'async resolveModelInfo( provider: string, model: string, signal?: AbortSignal, ): Promise<LlmResolvedModelInfo>',
        description: 'Resolve and validate all metadata from the adapter that owns one exact route. The result is detached from adapter-owned objects; catalog membership remains advisory and does not control request routing.',
        parameters: [{ name: 'provider', description: 'registered provider route to inspect.' }, { name: 'model', description: 'exact model id passed to the adapter.' }, { name: 'signal', description: 'optional cancellation for adapter-owned asynchronous lookup.' }],
        returns: 'exact model identity plus available context and reasoning metadata.',
      },//结束方法
      {//方法
        signature: 'async resolveCallConfig(config: LlmCallConfig, signal?: AbortSignal): Promise<LlmCallConfig>',
        description: 'Validate a conversation call config against its exact model capability and materialize adapter-configured defaults. Unsupported explicit efforts reject before provider I/O; no clamping or aliasing is performed. This standalone query does not bind a later dispatch; use prepareCall when logging and streaming must share one adapter registration.',
        parameters: [{ name: 'config', description: 'provider/model route and optional request controls.' }, { name: 'signal', description: 'optional cancellation for adapter-owned capability lookup.' }],
        returns: 'a detached config only when a default must be materialized.',
      },//结束方法
      {//方法
        signature: 'async prepareCall(config: LlmCallConfig, signal?: AbortSignal): Promise<PreparedLlmCall>',
        description: 'Resolve one call under its current adapter registration. The returned one-shot handle keeps that registration across header logging and dispatch, so HMR cannot combine one adapter\'s capability result with another adapter.',
        parameters: [{ name: 'config', description: 'provider/model route and optional request controls.' }, { name: 'signal', description: 'optional cancellation for adapter-owned capability lookup.' }],
        returns: 'a prepared config and its registration-bound stream entry point.',
      },//结束方法
      {//方法
        signature: 'stream(options: GenerateOptions): AsyncIterable<StreamChunk>',
        description: 'Stream one model call as raw chunks (token-level deltas). Replay state is retained only when the same adapter instance owns its historical provider and the target provider. Final adapter selection remains fixed through asynchronous exact-model resolution and dispatch. Adapter selection, dispatch, and iteration failures become terminal `error` or `aborted` finish chunks; middleware, nested-call, cleanup, and consumer failures remain thrown.',
        parameters: [{ name: 'options', description: 'the full request; `options.provider` selects the adapter.' }],
        returns: 'the chunk stream, possibly wrapped by `llm/stream` listeners.',
      },//结束方法
    ],//结束 methods
  },//结束服务
]
