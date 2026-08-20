/** 本包内嵌 SERVICE_API 分片 06（对照原版 api-catalog.ts）：goals..invariants */
export const SERVICE_API: readonly ServiceApiEntry[] = [//服务目录
  {//服务
    key: 'goals',
    summary: 'Goal service (`ctx.goals`) backed exclusively by the owning session log.',
    description: 'Goal service (`ctx.goals`) backed exclusively by the owning session log.',
    methods: [//公开方法
      {//方法
        signature: 'get(agent: Agent): GoalView | undefined',
        description: 'Read the current goal for one exact live agent.',
        parameters: [{ name: 'agent', description: 'owning live agent.' }],
        returns: 'a fresh view or `undefined` when no goal is current.',
        throws: ['{@link GoalError} when the agent is not the registry\'s live instance.'],
      },//结束方法
      {//方法
        signature: 'disarm(agent: Agent): GoalView | undefined',
        description: 'Remove process-local continuation authority without changing durable goal phase or revision. Lifecycle owners use this before unloading a driver; a later human-authorized resume records the new activation edge.',
        parameters: [{ name: 'agent', description: 'owning live agent.' }],
        returns: 'a fresh disarmed view, or `undefined` when no goal is current.',
      },//结束方法
      {//方法
        signature: 'create(agent: Agent, request: CreateGoalRequest): GoalView',
        description: 'Create and arm a goal. A completed goal may be replaced; every other current phase must be cleared or resumed instead.',
        parameters: [{ name: 'agent', description: 'owning live agent.' }, { name: 'request', description: 'objective and optional round cap.' }],
        returns: 'the created live view.',
      },//结束方法
      {//方法
        signature: '@Remote(\'edit\') edit(agent: Agent, ref: GoalRef, request: EditGoalRequest): GoalView',
        description: 'Edit objective and/or round cap without changing phase.',
        parameters: [{ name: 'agent', description: 'owning live agent.' }, { name: 'ref', description: 'expected current revision.' }, { name: 'request', description: 'at least one replacement field.' }],
        returns: 'the edited view.',
      },//结束方法
      {//方法
        signature: '@Remote(\'pause\') pause(agent: Agent, ref: GoalRef): GoalView',
        description: 'Pause an active goal and disarm automatic continuation.',
        parameters: [{ name: 'agent', description: 'owning live agent.' }, { name: 'ref', description: 'expected current revision.' }],
        returns: 'the paused view.',
      },//结束方法
      {//方法
        signature: '@Remote(\'resume\') resume(agent: Agent, ref: GoalRef): GoalView',
        description: 'Resume and arm a stopped goal, or rearm an active goal after a session-start edge, while its round budget still has capacity.',
        parameters: [{ name: 'agent', description: 'owning live agent.' }, { name: 'ref', description: 'expected current revision.' }],
        returns: 'the active view.',
      },//结束方法
      {//方法
        signature: '@Remote(\'complete\') complete(agent: Agent, ref: GoalRef): GoalView',
        description: 'Mark a current non-complete goal complete and disarm it.',
        parameters: [{ name: 'agent', description: 'owning live agent.' }, { name: 'ref', description: 'expected current revision.' }],
        returns: 'the completed view.',
      },//结束方法
      {//方法
        signature: 'block(agent: Agent, ref: GoalRef, reason: GoalBlockReason): GoalView',
        description: 'Mark an active goal blocked and disarm it.',
        parameters: [{ name: 'agent', description: 'owning live agent.' }, { name: 'ref', description: 'expected current revision.' }, { name: 'reason', description: 'policy-owned stable code and human-readable explanation.' }],
        returns: 'the blocked view with its durable reason.',
      },//结束方法
      {//方法
        signature: '@Remote(\'clear\') clear(agent: Agent, ref: GoalRef): GoalRef',
        description: 'Clear the current goal while retaining a durable tombstone and history.',
        parameters: [{ name: 'agent', description: 'owning live agent.' }, { name: 'ref', description: 'expected current revision.' }],
        returns: 'the tombstone ref whose revision is one past the cleared snapshot.',
      },//结束方法
      {//方法
        signature: '@Remote(\'create\') remoteExportCreate(agent: Agent, request: CreateGoalRequest): CreateGoalResult',
        description: 'Create one Goal through the remote boundary.',
        parameters: [{ name: 'agent', description: 'exact live Agent resolved from the wire identity.' }, { name: 'request', description: 'objective and optional round cap.' }],
        returns: 'the created Goal identity.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'invariants',
    summary: 'Package-owned invariant registry with global and regex-based selection.',
    description: 'Package-owned invariant registry with global and regex-based selection.',
    methods: [//公开方法
      {//方法
        signature: 'register(packageName: string, installer: InvariantInstaller): () => void',
        description: 'Register one package\'s invariant installer. The package name is reserved even when filtering disables its checks. Enabled installers run in a child fiber; failure disposes that fiber and releases the reservation.',
        parameters: [{ name: 'packageName', description: 'full npm package name that owns the contribution.' }, { name: 'installer', description: 'listener or startup-check installer for the child context.' }],
        returns: 'an effect-scoped disposer for the registration.',
      },//结束方法
    ],//结束 methods
  },//结束服务
]
