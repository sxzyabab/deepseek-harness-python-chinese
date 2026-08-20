"""插件配置分区及其插件卡片的文案词典。

对齐上游 `ui-settings-plugins/src/client/locales.ts`。公开面仅中文名。
"""

__all__=['命名空间','中文','英文']#仅中文公开名

命名空间='settings.plugins'#词表命名空间

英文={#英文词条
    'nav':'Plugins',#导航项
    'title':'Plugins',#分区标题
    'intro':'Configure and inspect the plugins installed in this deployment.',#导语
    'tabs':'Plugin views',#页签组
    'configurableTab':'Plugin configuration',#可配置页签
    'empty':'This deployment exposes no plugin settings.',#空态
    'overridden':'Overridden',#已覆盖
    'reset':'Reset to default',#恢复默认
    'readOnly':'This deployment stores settings read-only.',#只读
    'expand':'Show settings',#展开
    'collapse':'Hide settings',#收起
    'save':'Save',#保存
    'saving':'Saving…',#保存中
    'discard':'Discard',#放弃
    'unsaved':'Unsaved',#未保存
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
}#英文结束

中文={#简体中文词条
    'nav':'插件',#导航项
    'title':'插件',#分区标题
    'intro':'配置和查看本部署已安装的插件。',#导语
    'tabs':'插件视图',#页签组
    'configurableTab':'插件配置',#可配置页签
    'empty':'本部署没有开放任何插件设置。',#空态
    'overridden':'已覆盖',#已覆盖
    'reset':'恢复默认',#恢复默认
    'readOnly':'本部署的设置为只读。',#只读
    'expand':'展开设置',#展开
    'collapse':'收起设置',#收起
    'save':'保存',#保存
    'saving':'保存中…',#保存中
    'discard':'放弃修改',#放弃
    'unsaved':'未保存',#未保存
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
}#中文结束
