/** 本包内嵌 SERVICE_API 分片 01（对照原版 api-catalog.ts） */
export const SERVICE_API: readonly ServiceApiEntry[] = [//服务目录
  {//服务
    key: 'agentDefaultModel',
    summary: 'Owns the default model selection independently of any Host or transport.',
    description: 'Owns the default model selection independently of any Host or transport. The composition entry remains usable without a settings provider; when one is mounted, its user layer is read live.',
    methods: [//公开方法
      {//方法
        signature: 'currentSelection(): ModelSelection',
        description: 'Read the current default model selection.',
        parameters: [],//无参数
        returns: 'a detached provider, model, and optional reasoning selection.',
      },//结束方法
      {//方法
        signature: 'async saveSelection(next: ModelSelection): Promise<void>',
        description: 'Save the complete default model selection. A deployment without a settings provider keeps its composition entry.',
        parameters: [{ name: 'next', description: 'resolved selection accepted by an entry point.' }],
        returns: 'fulfillment after the optional settings write settles.',
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'agentLoop',
    summary: 'Concrete agent factory and driver service.',
    description: 'Concrete agent factory and driver service.',
    methods: [//公开方法
      {//方法
        signature: 'readonly config: ResolvedConfig',
        description: 'Validated configuration owned by the agent-loop service.',
        parameters: [],//无参数
      },//结束方法
      {//方法
        signature: 'create(id: SessionId, options: AgentOptions = {}, meta: Pick<SessionHeader, \'cwd\'> = {}): Agent',
        description: 'Create an agent and session under one caller-supplied identity, owned by the accessing fiber. Constructor-driven config calls mint a fresh combined id before entering this boundary.',
        parameters: [{ name: 'id', description: 'shared agent/session identity.' }, { name: 'options', description: 'concrete loop options.' }, { name: 'meta', description: 'optional fresh-session workspace metadata.' }],
        returns: 'the published running agent.',
      },//结束方法
      {//方法
        signature: 'async createAgent(ownerCtx: Context, options: CreateAgentOptions): Promise<AgentHandle>',
        description: 'Create an owned agent on a caller-supplied session id.',
        parameters: [{ name: 'ownerCtx', description: 'caller context that structurally owns the lifecycle.' }, { name: 'options', description: 'identities, session seed/metadata, loop options, setup, and cancellation.' }],
        returns: 'the published handle.',
      },//结束方法
      {//方法
        signature: 'async resume(ownerCtx: Context, options: ResumeAgentOptions): Promise<AgentHandle>',
        description: 'Resume an owned agent from the configured persistence service.',
        parameters: [{ name: 'ownerCtx', description: 'caller context that owns load, setup, and the live lifecycle.' }, { name: 'options', description: 'persisted identity, loop options, setup, and cancellation.' }],
        returns: 'the published handle.',
      },//结束方法
    ],//结束 methods
  },//结束服务
]
