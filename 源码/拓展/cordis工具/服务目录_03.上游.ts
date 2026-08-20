/** 本包内嵌 SERVICE_API 分片 03（对照原版 api-catalog.ts） */
export const SERVICE_API: readonly ServiceApiEntry[] = [//服务目录
  {//服务
    key: 'agents',
    summary: 'Agent service (`ctx.agents`): tracks live agents and carries the initiating Agent through one process-local asynchronous driver chain.',
    description: 'Agent service (`ctx.agents`): tracks live agents and carries the initiating Agent through one process-local asynchronous driver chain. Agent *creation* is provided by whichever plugin implements the AgentFactory (`@deepseek-ai/dsh-agent-loop`), registered via setFactory.\n\nInitiator methods provide same-process causal attribution only. Ambient presence is neither liveness proof nor authorization; subjects and owners remain explicit, as does identity at worker, process, persistence, and wire boundaries. Returned Promise boundaries drain during teardown, except a nested lineage that starts an owning-fiber unload is excluded from its own drain.',
    methods: [//公开方法
      {//方法
        signature: 'currentInitiator(): Agent | undefined',
        description: 'Read the Agent that initiated the inherited asynchronous driver chain. Use this optional form for logging, tracing, metrics, or host attribution that also supports agentless calls. When a parent creates a child, setup reports the causal parent while `agentCtx.agent` identifies the child.',
        parameters: [],//无参数
        returns: 'the inherited Agent, or `undefined` outside an initiator boundary and inside an explicit clearing boundary.',
        throws: ['when this service instance has been disposed.'],
      },//结束方法
      {//方法
        signature: 'requireInitiator(): Agent',
        description: 'Read the initiating Agent and fail when no initiator boundary is active. Use this for private helpers contractually below a driver, or for a deployment-owned outbound request whose contract forbids agentless calls. Generic or direct-call paths use optional lookup or explicit request fields.',
        parameters: [],//无参数
        returns: 'the inherited Agent.',
        throws: ['when no initiator is active or this service instance has been disposed.'],
      },//结束方法
      {//方法
        signature: 'withInitiator<T>(agent: Agent, operation: () => T): T',
        description: 'Run an operation with one exact Agent as its process-local initiator. The exact synchronous value or Promise returned by the operation is preserved. Custom drivers and test harnesses wrap their complete returned foreground lifetime. A queue or wire receiver may establish this boundary only after validating explicit identity and resolving the exact live Agent; this method does neither. Detached work remains owned by the subsystem that starts it.',
        parameters: [{ name: 'agent', description: 'initiating Agent to inherit; presence is neither liveness proof nor authorization.' }, { name: 'operation', description: 'synchronous or asynchronous operation to invoke.' }],
        returns: 'the exact value returned by `operation`.',
        throws: ['when the initiator scope is closing/disposed, or when `operation` throws.'],
      },//结束方法
      {//方法
        signature: 'withoutInitiator<T>(operation: () => T): T',
        description: 'Run an operation inside a boundary that hides any inherited initiating Agent. The exact synchronous value or Promise is preserved. Use this while creating lazy shared timers, queue pumps, pool maintenance, watchers, or exporters so they do not inherit the first Agent that happens to initialize them. It clears only initiator attribution, not explicit fields, and does not own or drain detached resources.',
        parameters: [{ name: 'operation', description: 'synchronous or asynchronous operation to invoke without an initiator.' }],
        returns: 'the exact value returned by `operation`.',
        throws: ['when the initiator scope is closing/disposed, or when `operation` throws.'],
      },//结束方法
      {//方法
        signature: 'setFactory(factory: AgentFactory): () => void',
        description: 'Register the agent-creation factory (the loop calls this on construction, effect-scoped). A traced Cordis service is canonicalized to its concrete target; each create/resume call is then traced through that caller\'s context so ownership follows the caller without stacking proxy layers. Throws if a factory is already registered. Returns the disposer; on dispose the factory slot is cleared.',
        parameters: [{ name: 'factory', description: 'the loop-owned factory {@link create}/{@link resume} delegate to.' }],
        returns: 'the disposer that clears the factory slot. The exact Cordis effect disposer (single-shot): composite (generator) effects may yield it directly — exact identity nests the teardown in order.',
      },//结束方法
      {//方法
        signature: 'async create(options: CreateAgentOptions): Promise<AgentHandle>',
        description: 'Create and publish a new agent through the registered factory. Distinct from register (which records an already-constructed agent): this constructs the agent and its session. Rejects if no factory is registered or creation/setup fails. The resolved AgentHandle lets the owner tear down exactly this agent.',
        parameters: [{ name: 'options', description: 'shared identity, session seed/metadata, and agent options.' }],
        returns: 'the handle after setup, rollback-covered publication, and loop start complete.',
      },//结束方法
      {//方法
        signature: 'async resume(options: ResumeAgentOptions): Promise<AgentHandle>',
        description: 'Load a persisted session and resume an agent on it through the registered factory. Rejects if no factory is registered; the factory rejects if session persistence is not configured or persistence/setup fails.',
        parameters: [{ name: 'options', description: 'persisted identity, configuration, and optional setup.' }],
        returns: 'the handle after setup, rollback-covered publication, and loop start complete.',
      },//结束方法
      {//方法
        signature: 'register(agent: Agent): () => void',
        description: 'Register a live agent. Throws if an agent with the same id is already registered. Emits `agent/created` on registration and `agent/disposed` when the calling fiber is disposed — both with the agent\'s scope carrier (`scopeTarget(agent, agent)`): the subject is the agent in hand, so the emits are scope-filtered regardless of which context invoked `register` (calling through `agent.ctx` scopes EFFECTS; dispatch scoping always requires passing the carrier). Returns the disposer.',
        parameters: [{ name: 'agent', description: 'the already-constructed agent to record in the store.' }],
        returns: 'the EXACT Cordis effect disposer (single-shot; a repeat call returns undefined without awaiting an in-flight teardown). Exact identity is load-bearing: a composite (generator) effect that owns a teardown ORDER — the agent factory\'s lifecycle chain — must yield THIS function so Cordis nests the unregistration at that yield position; yielding a wrapper would leave it disposing as a concurrent sibling on owner unload, unregistering the agent (and emitting `agent/disposed`) while its final turn is still draining.',
      },//结束方法
      {//方法
        signature: 'enter(agent: Agent, owner: Agent | undefined): () => void',
        description: 'Insert an already-constructed agent without announcing it. This is the advanced ordered-lifecycle primitive used by the async agent factory: it first completes setup while the agent is unpublished, then assigns the returned detach closure into its pre-installed composite teardown before calling announce. Ordinary callers use register.',
        parameters: [{ name: 'agent', description: 'the prepared, unpublished agent.' }, { name: 'owner', description: 'live agent whose scoped context created this agent, or undefined for a top-level runtime root. This is runtime ownership, not the resumed session\'s durable parent lineage.' }],
        returns: 'an idempotent closure that removes this exact entry and emits `agent/disposed` with listener failures contained. When called from a synchronous `agent/created` listener, removal and disposal wait until that creation dispatch unwinds.',
      },//结束方法
      {//方法
        signature: 'announce(agent: Agent): void',
        description: 'Announce an agent previously inserted with enter.',
        parameters: [{ name: 'agent', description: 'the live inserted agent to announce.' }],
        throws: ['if `agent` is not the exact live registry entry for its id, or its creation announcement already began (including a reentrant call from a creation listener).'],
      },//结束方法
      {//方法
        signature: 'get(id: SessionId): Agent | undefined',
        description: 'Look up a live agent.',
        parameters: [{ name: 'id', description: 'the shared agent/session id to look up.' }],
        returns: 'the agent, or undefined when no live agent has that id.',
      },//结束方法
      {//方法
        signature: 'isOwnedBy(id: SessionId, owner: Agent): boolean',
        description: 'Test whether a live agent was created through one exact parent agent\'s scoped context. Runtime ownership is independent of durable session lineage and remains unambiguous when unrelated providers reuse an id.',
        parameters: [{ name: 'id', description: 'the candidate child agent\'s shared agent/session id.' }, { name: 'owner', description: 'the expected runtime creator agent.' }],
        returns: 'true only while the exact child entry is live under that owner.',
      },//结束方法
      {//方法
        signature: 'list(): Agent[]',
        description: 'All live agents, in registration order.',
        parameters: [],//无参数
        returns: 'a fresh array; mutating it does not affect the registry.',
      },//结束方法
      {//方法
        signature: 'roots(): Agent[]',
        description: 'All live top-level agents in registration order. A top-level agent was created without an owning agent context; durable session lineage does not affect this runtime relation, so a resumed fork may still be a root.',
        parameters: [],//无参数
        returns: 'a fresh array; mutating it does not affect the registry.',
      },//结束方法
    ],//结束 methods
  },//结束服务
]
