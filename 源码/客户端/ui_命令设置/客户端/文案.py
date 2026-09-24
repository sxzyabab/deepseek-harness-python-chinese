__all__=['命名空间','中文','英文','表单标签']

命名空间='settings.shell'

英文={
    'title':'Shell',
    'description':'Limit how long each command may run and how much it may output.',
    'timeoutMs':'Command timeout (ms)',
    'timeoutMsHint':'How long one command may run before it is terminated.',
    'maxOutputBytes':'Output cap per stream (bytes)',
    'maxOutputBytesHint':'Output beyond this spills to a temporary file rather than being lost.',
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
    'title':'终端',
    'description':'限制每条命令最多能跑多久、最多输出多少内容。',
    'timeoutMs':'命令超时（毫秒）',
    'timeoutMsHint':'单条命令允许运行多久，超时即终止。',
    'maxOutputBytes':'单流输出上限（字节）',
    'maxOutputBytesHint':'超出部分会转存到临时文件，而不是被丢弃。',
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
