__all__=['命名空间','中文','英文']#仅中文公开名

命名空间='settings.plugins'#词表命名空间

英文={#英文词条
    'nav':'Built-in plugins',#导航项
    'title':'Built-in plugins',#分区标题
    'intro':'Inspect the plugins this deployment ships.',#导语
    'tabs':'Plugin views',#页签组
    'empty':'This deployment exposes no plugin views.',#空态
    'overridden':'Overridden',#已覆盖
    'reset':'Reset to default',#恢复默认
    'readOnly':'This deployment stores settings read-only.',#只读
    'unavailable':'This plugin is not loaded, so it cannot be configured right now.',#不可用
    'save':'Save',#保存
    'saving':'Saving…',#保存中
    'saveFailed':'The deployment did not accept these values; they were left for you to correct.',#保存失败
    'invalidNumber':'Enter a number, or leave blank to use the default.',#非法数字
    'bashTitle':'Shell',#Shell 标题
    'bashDescription':'Limits every command the agent runs.',#Shell 说明
    'bashTimeoutMs':'Command timeout (ms)',#超时
    'bashTimeoutMsHint':'How long one command may run before it is terminated.',#超时提示
    'bashMaxOutputBytes':'Output cap per stream (bytes)',#输出上限
    'bashMaxOutputBytesHint':'Output beyond this spills to a temporary file rather than being lost.',#输出提示
    'agentLoopTitle':'Agent loop',#Agent 循环标题
    'agentLoopDescription':'How the agent dispatches tool calls.',#Agent 循环说明
    'agentLoopMaxParallel':'Parallel tool calls',#并行上限
    'agentLoopMaxParallelHint':'Upper bound on parallel-safe calls running at once within one step.',#并行提示
    'webSearchTitle':'Web search',#网页搜索标题
    'webSearchDescription':'The DeepSeek search provider.',#网页搜索说明
    'webSearchApiKey':'API key',#API 密钥
    'webSearchApiKeyHint':'Stored outside the settings file. Leave blank to keep the current key.',#密钥提示
    'webSearchApiKeySet':'A key is configured.',#已配置
    'webSearchApiKeyUnset':'No key is configured; search is unavailable until one is.',#未配置
    'webSearchBaseUrl':'Endpoint',#接口地址
    'webSearchBaseUrlHint':'Leave blank to use the provider default.',#地址提示
    'webSearchMaxUses':'Max searches per request',#最多搜索
    'webSearchMaxUsesHint':'How many times one request may search before it must answer.',#次数提示
    'subagentTitle':'Subagent',#子智能体标题
    'subagentDescription':'Set Subagent recursion depth, count, and models.',#子智能体说明
    'subagentLimitsTitle':'Limits',#运行限制
    'subagentMaxDepth':'Maximum recursion depth',#最大递归深度
    'subagentDepthHelpLabel':'About maximum recursion depth',#深度帮助标签
    'subagentDepthHelp':'Limits how many levels of Subagents an Agent can create.',#深度说明
    'subagentDepthZero':'Disable Subagents',#深度零
    'subagentDepthOne':'Only the main Agent can create Subagents',#深度一
    'subagentDepthOverride':'If a tool defines its own maximum recursion depth, that setting takes precedence.',#深度覆盖
    'subagentMaxActive':'Subagent parallelism limit',#并行上限
    'subagentCapacityHelpLabel':'About the Subagent parallelism limit',#容量帮助标签
    'subagentCapacityHelp':'Total live Subagents under the same main Agent, across all recursion levels. The main Agent is excluded. New start requests are rejected when the limit is reached.',#容量说明
    'subagentDepthInvalid':'Enter a whole number of 0 or more.',#深度非法
    'subagentCapacityInvalid':'Enter a whole number of 1 or more.',#容量非法
    'subagentModelSelectionTitle':'Model selection',#模型选择标题
    'subagentModelSelectionToggle':'Allow agents to choose models for Subagents',#开关
    'subagentModelSelectionChoose':'When enabled, agents can choose a provider, model, and reasoning effort for each Subagent from the authorized models below. Applies only to new sessions.',#开启说明
    'subagentModelSelectionAllowed':'Models agents may choose',#可选模型
    'subagentModelSelectionLoading':'Loading models…',#加载中
    'subagentModelSelectionLoadFailed':'Models could not be loaded.',#加载失败
    'subagentModelSelectionRetry':'Retry',#重试
    'subagentModelSelectionPartial':'Some model providers could not be loaded; saved choices remain removable.',#部分失败
    'subagentModelSelectionUnavailable':'Currently unavailable',#当前不可用
    'subagentModelSelectionUnavailableGroup':'Saved but currently unavailable',#已保存但不可用
    'subagentModelSelectionEmpty':'No model provider currently advertises a model.',#空态
    'subagentModelSelectionRequired':'Select at least one model before saving.',#必选
    'subagentModelSelectionConflict':'Settings changed elsewhere. Discard your draft and try again.',#冲突
    'subagentModelSelectionOff':'Subagents use configured defaults or inherit the parent agent\'s model. Saved model choices are retained.',#关闭说明
}#英文结束

中文={#简体中文词条
    'nav':'内置插件',#导航项
    'title':'内置插件',#分区标题
    'intro':'查看内置部署的插件列表',#导语
    'tabs':'插件视图',#页签组
    'empty':'本部署没有开放任何插件视图。',#空态
    'overridden':'已覆盖',#已覆盖
    'reset':'恢复默认',#恢复默认
    'readOnly':'本部署的设置为只读。',#只读
    'unavailable':'该插件当前未加载，暂时无法配置。',#不可用
    'save':'保存',#保存
    'saving':'保存中…',#保存中
    'saveFailed':'本部署没有接受这些值，已保留供你修改。',#保存失败
    'invalidNumber':'请填数字；留空表示使用默认值。',#非法数字
    'bashTitle':'终端',#Shell 标题
    'bashDescription':'限制 agent 运行的每一条命令。',#Shell 说明
    'bashTimeoutMs':'命令超时（毫秒）',#超时
    'bashTimeoutMsHint':'单条命令允许运行多久，超时即终止。',#超时提示
    'bashMaxOutputBytes':'单流输出上限（字节）',#输出上限
    'bashMaxOutputBytesHint':'超出部分会转存到临时文件，而不是被丢弃。',#输出提示
    'agentLoopTitle':'Agent 循环',#Agent 循环标题
    'agentLoopDescription':'Agent 如何派发工具调用。',#Agent 循环说明
    'agentLoopMaxParallel':'并行工具调用数',#并行上限
    'agentLoopMaxParallelHint':'同一步内最多同时运行多少个可并行的调用。',#并行提示
    'webSearchTitle':'网页搜索',#网页搜索标题
    'webSearchDescription':'DeepSeek 搜索提供方。',#网页搜索说明
    'webSearchApiKey':'API Key',#API 密钥
    'webSearchApiKeyHint':'不写入设置文件。留空表示保持当前密钥。',#密钥提示
    'webSearchApiKeySet':'已配置密钥。',#已配置
    'webSearchApiKeyUnset':'未配置密钥；配置之前搜索不可用。',#未配置
    'webSearchBaseUrl':'接口地址',#接口地址
    'webSearchBaseUrlHint':'留空则使用提供方默认地址。',#地址提示
    'webSearchMaxUses':'单次请求最多搜索次数',#最多搜索
    'webSearchMaxUsesHint':'一次请求在必须作答前最多可以搜索多少次。',#次数提示
    'subagentTitle':'Subagent',#子智能体标题
    'subagentDescription':'设置 Subagent 的递归层级、数量和模型。',#子智能体说明
    'subagentLimitsTitle':'运行限制',#运行限制
    'subagentMaxDepth':'最大递归深度',#最大递归深度
    'subagentDepthHelpLabel':'最大递归深度说明',#深度帮助标签
    'subagentDepthHelp':'限制 Agent 创建 Subagent 的递归层级。',#深度说明
    'subagentDepthZero':'禁用 Subagent',#深度零
    'subagentDepthOne':'仅允许主 Agent 创建 Subagent',#深度一
    'subagentDepthOverride':'如果某个工具单独设置了最大递归深度，以该工具的设置为准。',#深度覆盖
    'subagentMaxActive':'Subagent 并行数量上限',#并行上限
    'subagentCapacityHelpLabel':'Subagent 并行数量上限说明',#容量帮助标签
    'subagentCapacityHelp':'同一主 Agent 下，所有递归层级同时存活的 Subagent 总数，主 Agent 不计入。达到上限时，新的启动请求会被拒绝。',#容量说明
    'subagentDepthInvalid':'请输入不小于 0 的整数。',#深度非法
    'subagentCapacityInvalid':'请输入不小于 1 的整数。',#容量非法
    'subagentModelSelectionTitle':'模型选择',#模型选择标题
    'subagentModelSelectionToggle':'允许 Agent 为 Subagent 选择模型',#开关
    'subagentModelSelectionChoose':'开启后，Agent 可以从下方授权模型中，为每个 Subagent 选择提供方、模型和推理强度。仅影响新会话。',#开启说明
    'subagentModelSelectionAllowed':'Agent 可选择的模型',#可选模型
    'subagentModelSelectionLoading':'正在加载模型…',#加载中
    'subagentModelSelectionLoadFailed':'无法加载模型。',#加载失败
    'subagentModelSelectionRetry':'重试',#重试
    'subagentModelSelectionPartial':'部分模型提供方暂时无法加载；已保存的选择仍可移除。',#部分失败
    'subagentModelSelectionUnavailable':'当前不可用',#当前不可用
    'subagentModelSelectionUnavailableGroup':'已保存但当前不可用',#已保存但不可用
    'subagentModelSelectionEmpty':'当前没有模型提供方公布模型。',#空态
    'subagentModelSelectionRequired':'保存前请至少选择一个模型。',#必选
    'subagentModelSelectionConflict':'设置已在其他位置更新。请放弃修改后重试。',#冲突
    'subagentModelSelectionOff':'关闭后，Subagent 使用配置的默认模型或继承父 Agent 的模型；已选模型会保留。',#关闭说明
}#中文结束
