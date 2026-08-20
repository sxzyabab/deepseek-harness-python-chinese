/** 本包内嵌 SERVICE_API 分片 14（对照原版 api-catalog.ts）——settings..storageDomain */
export const SERVICE_API: readonly ServiceApiEntry[] = [//服务目录
  {//服务
    key: 'settings',
    summary: 'Abstract settings service.',
    description: 'Abstract settings service. Providers implement raw-document storage (`load`/`persist`) and push external changes through Settings.publish; the base class owns namespace registration, resolution, validation, change detection, and the `settings/updated` commit event.',
    methods: [//公开方法
      {//方法
        signature: 'abstract readonly writable: boolean',
        description: 'Whether update may persist through this provider.',
        parameters: [],//无参数
      },//结束方法
      {//方法
        signature: 'prepareDocument(): Promise<string | undefined>',
        description: 'Prepare the provider\'s user-editable document for a native editor. File providers may materialize an absent document before returning its path; non-file providers return undefined.',
        parameters: [],//无参数
        returns: 'the absolute local document path, or undefined for non-file storage.',
      },//结束方法
      {//方法
        signature: 'register<T>(ns: SettingsNamespace, schema: z<T>, options?: SettingsRegisterOptions<T>): SettingsScope<T>',
        description: 'Register a namespace schema and receive its owner scope. The registration is an effect on the calling plugin\'s fiber: disposing that fiber removes the namespace and its observers. An invalid stored section fails the registration itself — the earliest point where the schema can judge it.',
        parameters: [{ name: 'ns', description: 'unique namespace; duplicate registration fails loud.' }, { name: 'schema', description: 'schemastery schema resolving this namespace\'s value.' }, { name: 'options', description: 'composition `base` layer and effect timing.' }],
        returns: 'the owner scope for reads, observation, and updates.',
      },//结束方法
      {//方法
        signature: 'describe(options?: SettingsDescribeOptions): SettingsDescriptor[]',
        description: 'Describe every registered namespace for configuration surfaces, including the composition `base` and raw user layers so a form can mark which fields the user overrode (presence in `user`) and what a reset returns to.',
        parameters: [{ name: 'options', description: 'redaction switch; wire surfaces must redact.' }],
        returns: 'one descriptor per registered namespace, in registration order.',
      },//结束方法
      {//方法
        signature: 'get(ns: SettingsNamespace): unknown',
        description: 'Read one registered namespace\'s resolved value.',
        parameters: [{ name: 'ns', description: 'the namespace to read.' }],
        returns: 'the resolved value, or `undefined` while unregistered.',
      },//结束方法
      {//方法
        signature: 'async update(ns: SettingsNamespace, patch: object, expectedRevision?: number): Promise<void>',
        description: 'Merge a patch into one registered namespace\'s user layer, validate the resolved candidate, persist through the provider, then commit and emit. A validation failure rejects before anything is persisted. Writes to one namespace are serialized: concurrent updates apply in call order, each merging over the previous write\'s committed section.',
        parameters: [{ name: 'ns', description: 'the registered namespace to update.' }, { name: 'patch', description: 'plain-object patch over the user section.' }, { name: 'expectedRevision', description: 'the descriptor `revision` the caller read; a namespace that moved past it rejects with {@link SettingsConflictError}.' }],
      },//结束方法
      {//方法
        signature: 'async replace(ns: SettingsNamespace, section: object, expectedRevision?: number): Promise<void>',
        description: 'Replace one registered namespace\'s user section wholesale, validate, persist, then commit and emit. Keys absent from `section` fall back to the composition `base` and schema defaults — this is the removal/reset path a merge-only patch cannot express (`replace({})` re-inherits everything).',
        parameters: [{ name: 'ns', description: 'the registered namespace to replace.' }, { name: 'section', description: 'the complete next user section.' }, { name: 'expectedRevision', description: 'the descriptor `revision` the caller read; a namespace that moved past it rejects with {@link SettingsConflictError}.' }],
      },//结束方法
      {//方法
        signature: 'async mutate(ns: SettingsNamespace, ops: readonly SettingsPathOp[], expectedRevision?: number): Promise<void>',
        description: 'Apply path-addressed edits to one registered namespace\'s user section, validate, persist, then commit and emit. The ops are applied to the section as it stands when the write reaches the front of the queue, so a caller never has to restate fields it did not touch — and, crucially, cannot delete fields it never saw. This is the write path for any caller holding a redacted view; `replace` remains the wholesale reset.',
        parameters: [{ name: 'ns', description: 'the registered namespace to edit.' }, { name: 'ops', description: 'ordered path edits; later ops observe earlier ones.' }, { name: 'expectedRevision', description: 'the descriptor `revision` the caller read; a namespace that moved past it rejects with {@link SettingsConflictError}.' }],
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'shell',
    summary: 'Abstract bash execution service.',
    description: 'Abstract bash execution service. Subclass, implement the abstract methods, and load the subclass as a plugin — it registers as `ctx.shell` (one implementation per context; loading a second throws, which is cordis\' standard duplicate-service behavior).\n\nImplementations must honor these semantics:\n\n- run rejects only for infrastructure failures. Nonzero exits, timeout kills, and abort kills resolve with a ShellRunResult.\n- start returns immediately; no timeout applies to background processes. `done` settles at process close and never rejects; spawn failures settle as `killed` with the error on stderr.\n- ShellProcess.readOutput is incremental: consecutive reads never repeat output. Lossy reads report truncation and available spill files.\n- A still-running background process is stopped and awaited when its owning composition tears down. With the subprocess seam that boundary is `ctx.subprocess` disposal, so a background process survives an executor-only reload.',
    methods: [//公开方法
      {//方法
        signature: 'abstract resolve(request: ShellExecRequest): ShellExecSpec',
        description: 'Apply implementation-owned defaults and caps to a request before execution.',
        parameters: [{ name: 'request', description: 'the caller\'s request; omitted fields get this implementation\'s defaults, capped fields are clamped.' }],
        returns: 'the fully-specified spec to hand to {@link run}/{@link start}.',
      },//结束方法
      {//方法
        signature: 'abstract run(spec: ShellExecSpec): Promise<ShellRunResult>',
        description: 'Run a command in the foreground; resolves when it finishes.',
        parameters: [{ name: 'spec', description: 'a resolved spec from {@link resolve}, never a raw request.' }],
        returns: 'the outcome; nonzero exits, timeout kills, and abort kills resolve with a descriptive result rather than reject.',
      },//结束方法
      {//方法
        signature: 'abstract start(spec: ShellExecSpec): ShellProcess',
        description: 'Start a background process and return its handle immediately.',
        parameters: [{ name: 'spec', description: 'a resolved spec from {@link resolve}, never a raw request.' }],
        returns: 'the live process handle (reads, kill, quiescence promise).',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'shellEnv',
    summary: 'Registry (`ctx.shellEnv`) for trusted, per-execution `DSH_*` variables.',
    description: 'Registry (`ctx.shellEnv`) for trusted, per-execution `DSH_*` variables. The namespace is rebuilt for every model shell call: ambient `DSH_*` values are discarded by the executor, then the registry\'s current snapshot is injected. Built-in shell facts remain owned by the registry itself while plugins can register additional, enumerable facts with effect-scoped disposal.',
    methods: [//公开方法
      {//方法
        signature: 'register(contributor: BashEnvContributor): () => void',
        description: 'Register one environment contributor. Names and keys are unique; built-in keys are reserved. Registration is disposed with the calling plugin fiber.',
        parameters: [{ name: 'contributor', description: 'declared key ownership and per-execution resolver.' }],
        returns: 'the disposer that unregisters the contribution.',
      },//结束方法
      {//方法
        signature: 'collect(execution: ToolExecution): DshEnvironment',
        description: 'Build the trusted `DSH_*` snapshot for one shell tool execution.',
        parameters: [{ name: 'execution', description: 'the current tool execution.' }],
        returns: 'an immutable environment overlay containing built-ins and current contributions.',
      },//结束方法
      {//方法
        signature: 'list(): BashEnvVariableInfo[]',
        description: 'Enumerate plugin-contributed variables without executing their resolvers.',
        parameters: [],//无参数
        returns: 'declarations sorted by environment variable name.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'skills',
    summary: 'Layered registry of skill providers, the host+per-scope shape the tools registry established.',
    description: 'Layered registry of skill providers, the host+per-scope shape the tools registry established. A registration files into the layer of its calling context\'s scope (scopeOf): host rows and repository plugins land in the global layer, while a plugin mounted by an agent preset\'s standing composition lands in that preset\'s layer. A read merges the global layer with the viewing scope\'s chain — the nearest layer\'s entry wins a duplicate name outright, and the rank order decides duplicates only within one layer. It exposes sorted invocation-neutral summaries and loads full skill bodies on demand.',
    methods: [//公开方法
      {//方法
        signature: 'registerProvider(create: (control: SkillProviderControl) => SkillProvider): () => void',
        description: 'Register a borrowed same-process provider synchronously during plugin apply, into the calling context\'s layer: a scoped context (an agent preset\'s standing mount) registers for that scope alone, an unscoped context registers globally. Duplicate names within one layer and reserved names throw; remote initialization belongs in `list()`. Fiber disposal unregisters the provider and invalidates catalog caches.',
        parameters: [{ name: 'create', description: 'synchronous factory receiving this registration\'s lifecycle and invalidation control.' }],
        returns: 'the exact Cordis effect disposer that unregisters this provider; composite effects may yield it directly to preserve teardown ordering.',
      },//结束方法
      {//方法
        signature: 'register(skill: SkillRegistration): () => void',
        description: 'Register a borrowed readonly runtime skill into the calling context\'s layer. Project entries outrank runtime entries, which outrank user entries, within one layer. Same-name runtime entries in one layer are first-wins; a duplicate logs a warning and receives a no-op disposer so it cannot remove the winner.',
        parameters: [{ name: 'skill', description: 'the skill definition input; omitted invocation and provider fields receive defaults.' }],
        returns: 'the exact Cordis effect disposer, preserving composite teardown order and invalidating caches.',
      },//结束方法
      {//方法
        signature: 'async list(options: SkillViewOptions = {}): Promise<SkillSummary[]>',
        description: 'List invocation-neutral skill summaries for a workspace. Consumers apply model or user invocation policy at their operational boundary. Lookup options and provider candidates are readonly same-process values borrowed throughout discovery.',
        parameters: [{ name: 'options', description: 'view options; `scope` selects the viewing agent\'s layers, `cwd` selects project roots, and `signal` cancels discovery.' }],
        returns: 'all sorted winning summaries.',
      },//结束方法
      {//方法
        signature: 'async snapshot(options: SkillViewOptions = {}): Promise<SkillCatalogSnapshot>',
        description: 'Observe the current invocation-neutral catalog and whether discovery completed within a stable revision. Incomplete observations are never cached, allowing consumers to retain last-good state and retry on their next request boundary.',
        parameters: [{ name: 'options', description: 'view options; `scope` selects the viewing agent\'s layers, `cwd` selects project roots, and `signal` cancels discovery.' }],
        returns: 'sorted summaries plus discovery-completeness state.',
      },//结束方法
      {//方法
        signature: 'async get(name: string, options: SkillViewOptions = {}): Promise<SkillDefinition | undefined>',
        description: 'Load and validate the winning candidate, passing its opaque discovery locator back to the provider. Cancellation is rechecked after selection, including cache hits, and raced against loading so an uncooperative provider cannot hang the caller.',
        parameters: [{ name: 'name', description: 'kebab-case skill name.' }, { name: 'options', description: 'view options; `scope` selects the viewing agent\'s layers, `cwd` selects workspace-sensitive skills, and `signal` cancels work.' }],
        returns: 'the full skill, including body content, or `undefined`.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'spillStore',
    summary: 'Abstract spill storage service.',
    description: 'Abstract spill storage service. Subclass, implement saveText, and load the subclass as a plugin — it registers as `ctx.spillStore` (one implementation per context; loading a second throws, cordis\' standard duplicate-service behavior).\n\nSemantics every implementation must honor:\n\n- saveText persists the FULL `content` verbatim and returns an opaque locator, exact byte length, and model-facing retrieval guidance.\n- Storage is scoped by the request\'s SaveTextSpill.owner session; the backend chooses a private (not world-readable) location and a collision-free name derived from — never equal to — the caller\'s `suggestedName`.\n- `saveText` REJECTS on a real storage failure (permissions, ENOSPC, backend unavailable); the caller decides how to degrade (the spill policy treats a rejection as best-effort and keeps the inline result).',
    methods: [//公开方法
      {//方法
        signature: 'abstract saveText(input: SaveTextSpill): Promise<SpillRef>',
        description: 'Persist `input.content` to a session-scoped spill artifact.',
        parameters: [{ name: 'input', description: 'the owner, caller-supplied source fields, suggested name, and full text to save.' }],
        returns: 'the saved artifact\'s {@link SpillRef}; rejects on a storage failure.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'storage',
    summary: 'The storage hub service.',
    description: 'The storage hub service. Backends register under `backend`; data forms mount under their `StorageForms` key and are reached as `ctx.storage.<form>`.',
    methods: [//公开方法
      {//方法
        signature: 'readonly backend: BackendRegistry = new BackendRegistry()',
        description: 'Named backend table; multiple backends stay mounted side by side.',
        parameters: [],//无参数
      },//结束方法
      {//方法
        signature: 'mount<K extends keyof StorageForms>(form: K, facility: StorageForms[K]): () => void',
        description: 'Mount a data-form facility on the hub. Mounting is an effect: the returned disposer unmounts the form.',
        parameters: [{ name: 'form', description: 'Form key declared in {@link StorageForms}.' }, { name: 'facility', description: 'The facility instance to expose.' }],
        returns: 'the disposer that unmounts the form.',
      },//结束方法
      {//方法
        signature: 'form<K extends keyof StorageForms>(form: K): StorageForms[K]',
        description: 'Resolve a mounted data form.',
        parameters: [{ name: 'form', description: 'Form key declared in {@link StorageForms}.' }],
        returns: 'the mounted facility.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'storageDomain',
    summary: 'The mounted domain facility.',
    description: 'The mounted domain facility. Opens declared domains over routed backends; one facility instance owns the open-domain table and enforces single-open per domain name.',
    methods: [//公开方法
      {//方法
        signature: 'async open<S extends DomainSpec>(spec: S): Promise<Domain<S>>',
        description: 'Open one declared domain. Steps, each failing the whole call: reject a name that is already open (`already-open`); resolve the backend route (`backend-not-found` passes through from the hub); require its `kv` facet (`facet-unsupported`); open the unit projected from the spec (backend `version-mismatch`/`malformed-medium` pass through); load and validate every stored record against the spec\'s zod schemas (`invalid-record` with the offending table and key); construct the domain.\n\nLifecycle: the CALLER owns the returned handle and closes it via `Domain.close()` (typically as its own `ctx.effect` disposer) — the facility does not tie the domain to any consumer fiber. Domains still open when the facility unmounts are closed by the plugin disposer.',
        parameters: [{ name: 'spec', description: 'The domain declaration, typically from `defineDomain`.' }],
        returns: 'the opened domain handle, typed by the spec.',
      },//结束方法
      {//方法
        signature: 'get(name: string): DomainImpl | undefined',
        description: 'Look up an open domain by name, untyped. Diagnostic surface (the package invariant cross-checks change events against live domain state); typed consumers hold the handle returned by open.',
        parameters: [{ name: 'name', description: 'Domain name.' }],
        returns: 'the open domain runtime, or `undefined` when not open.',
      },//结束方法
      {//方法
        signature: 'async closeAll(): Promise<void>',
        description: 'Close every domain still open on this facility. The unmount path for consumers that never called `Domain.close()` themselves; closing is idempotent, so double-closing an already-closed domain is harmless.',
        parameters: [],//无参数
        returns: 'resolution after every unit is released.',
      },//结束方法
    ],//结束 methods
  },//结束服务
]
