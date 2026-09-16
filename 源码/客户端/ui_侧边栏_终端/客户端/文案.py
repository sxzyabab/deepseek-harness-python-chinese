__all__=['命名空间','中文','英文']#仅中文公开名

命名空间='sidebarTerminal'#词表命名空间

中文={#简体中文词条
    'recoveryFailed':'恢复终端失败：{message}',#恢复失败
    'retryRecovery':'重试恢复终端',#重试恢复
    'shell':'选择 Shell',#选壳
    'shellLoading':'正在读取 Shell…',#读壳中
    'shellEmpty':'没有可用的 Shell',#无壳
    'description':'在会话工作区运行命令',#说明
    'title':'终端',#标题
    'new':'新建终端',#新建
    'loading':'正在读取终端环境…',#读环境
    'creating':'正在启动…',#启动中
    'connecting':'正在连接…',#连接中
    'disconnected':'连接已断开。',#断开
    'reconnect':'重新连接',#重连
    'readonly':'此页面当前只读。',#只读
    'control':'接管输入',#接管
    'closed':'终端已关闭。',#已关
    'exited':'进程已退出（{code}）',#退出
    'failed':'终端错误：{message}',#失败
    'rename':'终端名称',#重命名
    'unavailable':'不可用',#不可用
    'retry':'重试',#重试
    'cleanupFailed':'终端「{title}」未能结束：{message}',#清理失败
    'missingTerminal':'此终端已不存在，请新建终端。',#缺失
    'inputFull':'输入缓冲区已满，请重新连接后重试。',#输入满
    'attachmentEnded':'终端连接已结束，请重新连接。',#附件结束
    'invalidOutput':'终端画面传输异常，请重新连接。',#画面异常
    'terminalLimit':'终端数量已达上限，请关闭不用的终端后重试。已退出的终端也计入数量。',#上限
}#中文结束

英文={#英文词条
    'recoveryFailed':'Terminal recovery failed: {message}',#恢复失败
    'retryRecovery':'Retry terminal recovery',#重试恢复
    'shell':'Choose shell',#选壳
    'shellLoading':'Loading shells…',#读壳中
    'shellEmpty':'No shells available',#无壳
    'description':'Run commands in the Session workspace',#说明
    'title':'Terminal',#标题
    'new':'New terminal',#新建
    'loading':'Reading terminal environment…',#读环境
    'creating':'Starting…',#启动中
    'connecting':'Connecting…',#连接中
    'disconnected':'Disconnected.',#断开
    'reconnect':'Reconnect',#重连
    'readonly':'This view is read-only.',#只读
    'control':'Take control',#接管
    'closed':'Terminal closed.',#已关
    'exited':'Process exited ({code})',#退出
    'failed':'Terminal error: {message}',#失败
    'rename':'Terminal name',#重命名
    'unavailable':'Unavailable',#不可用
    'retry':'Retry',#重试
    'cleanupFailed':'Terminal “{title}” could not be ended: {message}',#清理失败
    'missingTerminal':'This terminal no longer exists. Open a new terminal.',#缺失
    'inputFull':'The input buffer is full. Reconnect and try again.',#输入满
    'attachmentEnded':'The terminal connection ended. Reconnect to continue.',#附件结束
    'invalidOutput':'The terminal screen could not be received. Reconnect to recover it.',#画面异常
    'terminalLimit':'The terminal limit has been reached. Close unused terminals and try again. Exited terminals also count toward the limit.',#上限
}#英文结束
