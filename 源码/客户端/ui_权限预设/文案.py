"""权限设置与弹窗门控词典。



对齐上游 `ui-permission-presets/src/client/locales.ts`。公开面仅中文公开名。

"""



__all__=['设置中文','设置英文','访问中文','访问英文']#仅中文公开名



设置中文={#settings.permission 中文

    'title':'权限',#标题

    'description':'选择新会话的默认权限模式',#说明

    'loading':'加载中',#加载中

    'unavailable':'不可用',#不可用

    'confirm.title':'确认启用 Full access？',#确认标题

    'confirm.description':'启用 Full access 后，新会话将减少确认步骤，并且可以直接执行更多操作，包括敏感操作、文件修改或外部命令。仅建议在你信任后续任务时使用。',#确认说明

    'confirm.acknowledge':'我已了解风险，并愿意继续',#知晓

    'confirm.cancel':'取消',#取消

    'confirm.enable':'启用 Full access',#启用

}#设置中文结束



设置英文={#settings.permission 英文

    'title':'Permission',#标题

    'description':'Choose the default permission mode for new sessions',#说明

    'loading':'Loading',#加载中

    'unavailable':'Unavailable',#不可用

    'confirm.title':'Enable Full access?',#确认标题

    'confirm.description':'Full access lets new sessions reduce confirmation steps and perform more actions directly, including sensitive operations, file changes, or external commands. Only use it when you trust subsequent tasks.',#确认说明

    'confirm.acknowledge':'I understand the risks and want to continue',#知晓

    'confirm.cancel':'Cancel',#取消

    'confirm.enable':'Enable Full access',#启用

}#设置英文结束



访问中文={#当前会话弹窗门控中文

    'confirm.title':'确认启用 Full access？',#确认标题

    'confirm.description':'启用 Full access 后，agent 将减少确认步骤，并且可以直接执行更多操作，包括敏感操作、文件修改或外部命令。仅建议在你信任当前任务时使用。',#确认说明

    'confirm.acknowledge':'我已了解风险，并愿意继续',#知晓

    'confirm.cancel':'取消',#取消

    'confirm.enable':'启用 Full access',#启用

}#访问中文结束



访问英文={#当前会话弹窗门控英文

    'confirm.title':'Enable Full access?',#确认标题

    'confirm.description':'Full access reduces confirmation steps and lets the agent perform more actions directly, including sensitive operations, file changes, or external commands. Only use it when you trust the current task.',#确认说明

    'confirm.acknowledge':'I understand the risks and want to continue',#知晓

    'confirm.cancel':'Cancel',#取消

    'confirm.enable':'Enable Full access',#启用

}#访问英文结束


