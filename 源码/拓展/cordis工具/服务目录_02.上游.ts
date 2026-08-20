/** 本包内嵌 SERVICE_API 分片 02（对照原版 api-catalog.ts） */
export const SERVICE_API: readonly ServiceApiEntry[] = [//服务目录
  {//服务
    key: 'agentPresets',
    summary: 'Registry over the deployment\'s agent presets.',
    description: 'Registry over the deployment\'s agent presets.\n\nDiscovery is unmemoized: `list()` and `resolve()` re-read the roots on every call so a preset authored while the process runs is visible immediately, and a preset deleted underneath a picker disappears from the next read.',
    methods: [//公开方法
      {//方法
        signature: 'async list(): Promise<AgentPreset[]>',
        description: 'Every preset the configured roots currently supply.',
        parameters: [],//无参数
        returns: 'the presets, first-root-wins per id.',
      },//结束方法
      {//方法
        signature: 'async resolve(id?: string): Promise<AgentPreset>',
        description: 'Resolve one preset by id.\n\nA broken preset resolves — deleting one, reading one, and reporting one all need the row — and the mounting paths refuse it AFTER resolution through resolveMountable.',
        parameters: [{ name: 'id', description: 'the preset id, or `undefined` for {@link defaultId}.' }],
        returns: 'the resolved preset.',
        throws: ['when no configured root supplies that id.'],
      },//结束方法
      {//方法
        signature: 'async mount(agentCtx: Context, id?: string): Promise<AgentPreset>',
        description: 'Compose one agent from a preset: ensure the preset\'s standing mount, then parent the agent\'s scope key to it so the mount\'s registrations and listeners cover this agent.\n\nCall from the agent factory\'s `setup(agentCtx)`; a rejection there rolls the agent creation back, so a broken preset never yields a half-composed session.',
        parameters: [{ name: 'agentCtx', description: 'the agent\'s scope context.' }, { name: 'id', description: 'the preset id, or `undefined` for {@link defaultId}.' }],
        returns: 'the preset that was composed, for the caller to record.',
        throws: ['when the preset is unknown or its composition is unusable.'],
      },//结束方法
      {//方法
        signature: 'composeFrom(agentCtx: Context, parentCtx: Context): string | undefined',
        description: 'Join one agent to the SAME standing composition another already runs on.\n\nThis is how a child agent inherits its parent\'s capabilities. It is a bind, not a mount: the parent\'s generation is already composed, so the child gets that exact instance — the same plugin objects, the same tool registrations, the same prompt sections. Re-resolving the parent\'s preset by id instead would re-read the roster, and a composition file edited since the parent started would hand the child a DIFFERENT generation than the one its parent\'s history was produced under (and a preset deleted since would fail the child outright while its parent keeps running).\n\nSynchronous, and with no composition failure mode of its own — it reads no roster, mounts nothing, and touches no file — which is what lets a child creation window use it: the two in-process subagent drivers compose their children inside a synchronous `setup`. It still rejects a caller error, as the `@throws` below record.\n\nA parent that joined no preset — a rosterless deployment — yields no join and no error: there, the model-facing rows sit in the host composition and the child already sees them through the global layer.',
        parameters: [{ name: 'agentCtx', description: 'the joining agent\'s scope context.' }, { name: 'parentCtx', description: 'the scope context of the agent whose composition to join.' }],
        returns: 'the preset id joined, or undefined when the parent joined none.',
        throws: ['when `agentCtx` carries no scope, or has already joined a preset.'],
      },//结束方法
      {//方法
        signature: 'composedPreset(agentCtx: Context): string | undefined',
        description: 'The preset one live agent runs on.\n\nRead from the live scope chain rather than from the session, so it answers for an agent whose session has not recorded a preset yet — a child agent whose durable header is being built from its parent\'s composition.',
        parameters: [{ name: 'agentCtx', description: 'the agent\'s scope context.' }],
        returns: 'the preset id, or undefined when the agent joined none.',
      },//结束方法
      {//方法
        signature: 'async read(id: string): Promise<string>',
        description: 'Read one preset\'s composition text.',
        parameters: [{ name: 'id', description: 'the preset id.' }],
        returns: 'the composition exactly as stored.',
        throws: ['when no configured root supplies that id.'],
      },//结束方法
      {//方法
        signature: 'async copy(from: string, id: string, name?: string): Promise<void>',
        description: 'Create a locally authored preset by copying an existing one whole.\n\nCopy is the only authoring write. Composition text never crosses this seam: the source is named by id and its directory is copied as it stands, so the copy is exactly as loadable as its source and authoring grants no capability the roster did not already carry. The copy is NOT mounted to validate — a source that mounts today yields a copy that mounts today.',
        parameters: [{ name: 'from', description: 'the preset the copy starts from; shipped presets are the primary source, so any trust is accepted.' }, { name: 'id', description: 'the new preset\'s id, which becomes its directory name.' }, { name: 'name', description: 'display name for the copy; absent falls back to the id.' }],
        throws: ['when the source is unknown, the id is unusable or already taken, or the deployment configures no writable root.'],
      },//结束方法
      {//方法
        signature: 'async remove(id: string): Promise<void>',
        description: 'Delete a locally authored preset.',
        parameters: [{ name: 'id', description: 'the preset id.' }],
        throws: ['when the preset is unknown or ships with the deployment.'],
      },//结束方法
      {//方法
        signature: 'serviceFor<K extends string & keyof Context>(agent: { ctx: Context }, name: K): Context[K] | undefined',
        description: 'One agent\'s instance of a service its preset mounted.\n\nA preset publishes services behind `isolate` realms, which are invisible outside the group that declares them — including to the host. This is how a caller holding the agent reads one anyway: a request that is ABOUT a session but arrives from outside it, which is every browser RPC.\n\nRead addressing only. A host row that `inject`s a service cannot use this, because injection resolves before any session exists and has no agent to key by; such a service belongs on the host plane instead.',
        parameters: [{ name: 'agent', description: 'the agent whose composition to look inside.' }, { name: 'name', description: 'the service name as the preset\'s rows resolve it.' }],
        returns: 'the agent\'s instance, or undefined when its preset mounts none.',
      },//结束方法
      {//方法
        signature: 'async recompose(agentCtx: Context, id: string): Promise<AgentPreset>',
        description: 'Re-link one agent to a different preset\'s standing composition.\n\nOnly valid while the agent has produced nothing: swapping tools mid conversation would leave logged tool calls the new composition cannot make. The CALLER owns that check — this method does not read session history.\n\nThe swap is a parent re-link, not an unmount: standing mounts are shared and permanent, so the old composition stays for its other agents and the new one is ensured BEFORE the link moves. An unknown or unusable preset therefore throws with the agent exactly as it was — there is no torn-down state to restore. The re-link runs through the binding this roster kept from the agent\'s mount — dsh-scope\'s only re-link authority. An agent that never composed one has nothing to re-link: the switch is then the agent\'s first bind, exactly a mount.',
        parameters: [{ name: 'agentCtx', description: 'the agent\'s scope context.' }, { name: 'id', description: 'the preset to compose the agent from instead.' }],
        returns: 'the preset now installed.',
        throws: ['when the preset is unknown or its composition is unusable.'],
      },//结束方法
      {//方法
        signature: 'async standingKeyFor(id?: string): Promise<ScopeKey>',
        description: 'The standing scope key of one preset, for a host reader with no agent.\n\nA cold transcript read resolves tool presenters against the composition the session recorded, and the standing mount makes that possible without resuming anything: ensuring the mount composes plugins but starts no agent, no session, and no turn.',
        parameters: [{ name: 'id', description: 'the preset id, or `undefined` for {@link defaultId}.' }],
        returns: 'the standing scope key readers pass as a registry view scope.',
        throws: ['when the preset is unknown or its composition is unusable.'],
      },//结束方法
    ],//结束 methods
  },//结束服务
]
