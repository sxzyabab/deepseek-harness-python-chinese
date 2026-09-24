__all__=['命名空间','中文','英文','表单标签']

命名空间='settings.webSearch'

英文={
    'title':'Web search',
    'description':'Set up the DeepSeek search provider.',
    'apiKey':'API key',
    'apiKeyHint':'Stored outside the settings file. Leave blank to keep the current key.',
    'apiKeySet':'A key is configured.',
    'apiKeyUnset':'No key is configured; search is unavailable until one is.',
    'baseUrl':'Endpoint',
    'baseUrlHint':'Leave blank to use the provider default.',
    'maxUses':'Max searches per request',
    'maxUsesHint':'How many times one request may search before it must answer.',
    'overridden':'Overridden',
    'reset':'Reset to default',
    'readOnly':'This deployment stores settings read-only.',
    'unavailable':'This plugin is not loaded, so it cannot be configured right now.',
    'save':'Save',
    'saving':'Saving…',
    'saveFailed':'The deployment did not accept these values; they were left for you to correct.',
    'invalidNumber':'Enter a number, or leave blank to use the default.',
}

中文={
    'title':'网页搜索',
    'description':'设置 DeepSeek 的搜索提供方。',
    'apiKey':'API Key',
    'apiKeyHint':'不写入设置文件。留空表示保持当前密钥。',
    'apiKeySet':'已配置密钥。',
    'apiKeyUnset':'未配置密钥；配置之前搜索不可用。',
    'baseUrl':'接口地址',
    'baseUrlHint':'留空则使用提供方默认地址。',
    'maxUses':'单次请求最多搜索次数',
    'maxUsesHint':'一次请求在必须作答前最多可以搜索多少次。',
    'overridden':'已覆盖',
    'reset':'恢复默认',
    'readOnly':'本部署的设置为只读。',
    'unavailable':'该插件当前未加载，暂时无法配置。',
    'save':'保存',
    'saving':'保存中…',
    'saveFailed':'本部署没有接受这些值，已保留供你修改。',
    'invalidNumber':'请填数字；留空表示使用默认值。',
}

def 表单标签(翻译):
    """把本页词典填进共享设置表单的框架文案。"""
    return {
        'unavailable':翻译('unavailable'),
        'readOnly':翻译('readOnly'),
        'saveFailed':翻译('saveFailed'),
        'save':翻译('save'),
        'saving':翻译('saving'),
    }
