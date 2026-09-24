__all__=['命名空间','中文','英文','表单标签']

命名空间='settings.agentLoop'

英文={
    'title':'Agent loop',
    'description':'Control how the Agent dispatches tool calls.',
    'maxParallel':'Parallel tool calls',
    'maxParallelHint':'Upper bound on parallel-safe calls running at once within one step.',
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
    'title':'Agent 循环',
    'description':'控制 Agent 派发工具调用的方式。',
    'maxParallel':'并行工具调用数',
    'maxParallelHint':'同一步内最多同时运行多少个可并行的调用。',
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
