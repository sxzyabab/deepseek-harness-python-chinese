__all__=['权限访问命名空间','中文','英文','访问中文','访问英文']#仅中文公开名

权限访问命名空间='permission.access'#当前会话选择器命名空间

中文={#settings.permission 简体
    'title':'权限',#标题
    'description':'选择新会话的默认权限模式',#说明
    'loading':'加载中',#加载
    'unavailable':'不可用',#不可用
    'preset.readOnly':'仅可查看',#只读
    'preset.workspaceWrite':'工作区内修改',#工作区写
    'preset.fullAccess':'完全权限',#完全
    'confirm.title':'确认启用完全权限？',#确认标题
    'confirm.description':'启用完全权限后，新会话将减少确认步骤，并且可以直接执行更多操作，包括敏感操作、文件修改或外部命令。仅建议在你信任后续任务时使用。',#确认说明
    'confirm.acknowledge':'我已了解风险，并愿意继续',#确认已知
    'confirm.cancel':'取消',#取消
    'confirm.enable':'启用完全权限',#启用
}#中文结束

英文={#settings.permission 英文
    'title':'Permission',#标题
    'description':'Choose the default permission mode for new sessions',#说明
    'loading':'Loading',#加载
    'unavailable':'Unavailable',#不可用
    'preset.readOnly':'Read Only',#只读
    'preset.workspaceWrite':'Workspace Write',#工作区写
    'preset.fullAccess':'Full access',#完全
    'confirm.title':'Enable Full access?',#确认标题
    'confirm.description':'Full access lets new sessions reduce confirmation steps and perform more actions directly, including sensitive operations, file changes, or external commands. Only use it when you trust subsequent tasks.',#确认说明
    'confirm.acknowledge':'I understand the risks and want to continue',#确认已知
    'confirm.cancel':'Cancel',#取消
    'confirm.enable':'Enable Full access',#启用
}#英文结束

访问中文={#permission.access 简体
    'mode':'访问模式，当前：{name}',#模式
    'close':'关闭',#关闭
    'preset.readOnly':'仅可查看',#只读
    'preset.workspaceWrite':'工作区内修改',#工作区写
    'preset.fullAccess':'完全权限',#完全
    'confirm.title':'确认启用完全权限？',#确认标题
    'confirm.description':'启用完全权限后，智能体将减少确认步骤，并且可以直接执行更多操作，包括敏感操作、文件修改或外部命令。仅建议在你信任当前任务时使用。',#确认说明
    'confirm.acknowledge':'我已了解风险，并愿意继续',#确认已知
    'confirm.cancel':'取消',#取消
    'confirm.enable':'启用完全权限',#启用
    'auto.label':'Auto review',#自动审查标签
    'auto.badge':'EXP',#实验徽标
    'auto.description':'无沙箱运行；每次原生工具调用和 PTC 内层调用前由同一模型进行实验性审查。',#说明
    'auto.confirm.title':'确认启用 Auto review（实验）？',#确认标题
    'auto.confirm.description':'Auto review 不使用沙箱。每次原生工具调用和 PTC 内层调用前，都会由与当前 agent 相同的模型进行审查。此功能仍属实验性，可能误放行或误拒绝，并会消耗额外 token。',#确认说明
    'auto.confirm.acknowledge':'我已了解这些风险，并愿意继续',#确认已知
    'auto.confirm.enable':'启用 Auto review',#启用
}#访问中文结束

访问英文={#permission.access 英文
    'mode':'Access mode, current: {name}',#模式
    'close':'Close',#关闭
    'preset.readOnly':'Read Only',#只读
    'preset.workspaceWrite':'Workspace Write',#工作区写
    'preset.fullAccess':'Full access',#完全
    'confirm.title':'Enable Full access?',#确认标题
    'confirm.description':'Full access reduces confirmation steps and lets the agent perform more actions directly, including sensitive operations, file changes, or external commands. Only use it when you trust the current task.',#确认说明
    'confirm.acknowledge':'I understand the risks and want to continue',#确认已知
    'confirm.cancel':'Cancel',#取消
    'confirm.enable':'Enable Full access',#启用
    'auto.label':'Auto review',#自动审查标签
    'auto.badge':'EXP',#实验徽标
    'auto.description':'Run without a sandbox after an experimental same-model review of every native tool call and PTC inner call.',#说明
    'auto.confirm.title':'Enable Auto review (experimental)?',#确认标题
    'auto.confirm.description':'Auto review runs without a sandbox. Before every native tool call and PTC inner call, the same model as the current agent reviews whether to allow it. This feature is experimental, can falsely allow or deny actions, and uses additional tokens.',#确认说明
    'auto.confirm.acknowledge':'I understand these risks and want to continue',#确认已知
    'auto.confirm.enable':'Enable Auto review',#启用
}#访问英文结束
