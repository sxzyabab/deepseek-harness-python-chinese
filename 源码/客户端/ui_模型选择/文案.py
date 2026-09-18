
__all__=['命名空间','中文','英文']#仅中文公开名

命名空间='model'#词表命名空间

中文={#简体中文
    'command.label':'模型',#命令标签
    'command.description':'选择本会话使用的模型',#命令描述
    'option.loadError':'目录加载失败：{message}',#目录加载失败
    'option.deepseekV4Flash.description':'快速、高效且经济；适合目标明确、常规或并行任务。',#内置 flash
    'option.deepseekV4Pro.description':'更强的自主编码、知识与复杂推理能力；适合复杂或质量优先的任务，但成本更高。',#内置 pro
    'trigger.fallback':'选择模型',#回退标签
    'trigger.loading':'正在加载模型…',#加载中
    'trigger.selectAria':'选择模型',#未选定无障碍
    'trigger.aria':'选择模型，当前 {model}',#已选定无障碍
    'trigger.ariaEffort':'选择模型，当前 {model}，推理等级 {effort}',#带力度
    'menu.aria':'模型与推理等级',#菜单无障碍
    'menu.model':'模型',#模型
    'menu.effort':'推理等级',#推理
    'effort.providerDefault':'Default',#默认力度
    'status.loading':'正在刷新模型列表…',#刷新中
    'error.action':'模型操作失败：{message}',#操作失败
    'error.sessionInUse':'当前会话已被占用，可能是其他正在运行的 DSH 导致的（如其他 dsh web、桌面端），请退出其他正在运行的 DSH 后重试。',#会话占用
    'action.reload':'重新加载',#重载
    'warning.groupLoad':'{name} 加载失败：{message}',#分组失败
    'empty.models':'没有可用的模型。',#无模型
    'blocked.composer':'当前模型不可用，请先选择模型',#阻断
    'empty.efforts':'当前模型未提供推理等级。',#无力度
}#中文结束

英文={#英文
    'command.label':'Model',#命令标签
    'command.description':'Select the model for this conversation',#命令描述
    'option.loadError':'Catalog failed to load: {message}',#目录失败
    'option.deepseekV4Flash.description':'Fast, efficient, and economical; suited to focused, routine, or parallel tasks.',#内置 flash
    'option.deepseekV4Pro.description':'Stronger agentic coding, knowledge, and difficult reasoning; suited to complex or quality-critical tasks at higher cost.',#内置 pro
    'trigger.fallback':'Select model',#回退
    'trigger.loading':'Loading models…',#加载中
    'trigger.selectAria':'Select model',#未选定
    'trigger.aria':'Select model, current {model}',#已选定
    'trigger.ariaEffort':'Select model, current {model}, reasoning effort {effort}',#带力度
    'menu.aria':'Model and reasoning effort',#菜单
    'menu.model':'Model',#模型
    'menu.effort':'Effort',#力度
    'effort.providerDefault':'Default',#默认
    'status.loading':'Refreshing model list…',#刷新
    'error.action':'Model operation failed: {message}',#失败
    'error.sessionInUse':'This session is already in use, possibly by another running DSH instance (such as dsh web or the desktop app). Quit other running DSH instances and try again.',#会话占用
    'action.reload':'Reload',#重载
    'warning.groupLoad':'{name} failed to load: {message}',#分组
    'empty.models':'No models available.',#空
    'blocked.composer':'This model is unavailable — select one to continue',#阻断
    'empty.efforts':'This model provides no reasoning effort levels.',#无力度
}#英文结束
