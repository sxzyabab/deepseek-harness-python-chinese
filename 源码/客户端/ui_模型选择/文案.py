"""model 命名空间词典。

对齐上游 `ui-model-selection/src/client/locales.ts`。公开面仅中文名。
"""

__all__=['命名空间','中文','英文']#仅中文公开名

命名空间='model'#词表命名空间

中文={#简体中文
    'command.description':'选择本会话使用的模型',#命令描述
    'option.loadError':'目录加载失败：{message}',#目录加载失败
    'trigger.fallback':'选择模型',#回退标签
    'trigger.selectAria':'选择模型',#未选定无障碍
    'trigger.aria':'选择模型，当前 {model}',#已选定无障碍
    'trigger.ariaEffort':'选择模型，当前 {model}，推理等级 {effort}',#带力度
    'menu.aria':'模型与推理等级',#菜单无障碍
    'menu.model':'模型',#模型
    'menu.effort':'推理等级',#推理
    'effort.providerDefault':'Default',#默认力度
    'status.loading':'正在刷新模型列表…',#刷新中
    'error.action':'模型操作失败：{message}',#操作失败
    'action.reload':'重新加载',#重载
    'warning.groupLoad':'{name} 加载失败：{message}',#分组失败
    'empty.models':'没有可用的模型。',#无模型
    'blocked.composer':'当前模型不可用，请先选择模型',#阻断
    'empty.efforts':'当前模型未提供推理等级。',#无力度
    'retry':'重试',#重试
}#中文结束

英文={#英文
    'command.description':'Select the model for this conversation',#命令描述
    'option.loadError':'Catalog failed to load: {message}',#目录失败
    'trigger.fallback':'Select model',#回退
    'trigger.selectAria':'Select model',#未选定
    'trigger.aria':'Select model, current {model}',#已选定
    'trigger.ariaEffort':'Select model, current {model}, reasoning effort {effort}',#带力度
    'menu.aria':'Model and reasoning effort',#菜单
    'menu.model':'Model',#模型
    'menu.effort':'Effort',#力度
    'effort.providerDefault':'Default',#默认
    'status.loading':'Refreshing model list…',#刷新
    'error.action':'Model operation failed: {message}',#失败
    'action.reload':'Reload',#重载
    'warning.groupLoad':'{name} failed to load: {message}',#分组
    'empty.models':'No models available.',#空
    'blocked.composer':'This model is unavailable — select one to continue',#阻断
    'empty.efforts':'This model provides no reasoning effort levels.',#无力度
    'retry':'Retry',#重试
}#英文结束
