
__all__=['中文','英文','侧栏文件文案键']#仅中文公开名

中文={#简体中文词条（键集合的权威源）
    'type.label':'文件',#类型标签
    'guide.title':'工作区文件',#向导标题
    'guide.description':'浏览会话工作区的文件',#向导描述
    'loading':'正在读取…',#读取中
    'empty':'空目录',#空目录
    'truncated':'条目太多，只显示了一部分。',#截断提示
    'noWorkspace':'这个会话没有工作区目录。',#无工作区
    'reload':'重新读取',#重新读取
    'entry.other':'这不是文件或目录，没法打开。',#其它条目
    'error.notFound':'这个目录不在了。可能已被移动或删除。',#不存在
    'error.outsideWorkspace':'这个目录在工作区之外，侧栏不会读取它。',#工作区外
    'error.notDirectory':'这不是一个目录。',#非目录
    'error.unavailable':'读取失败：{message}',#其它失败
}#中文词典结束

英文={#英文词条，对照中文权威源核验键齐全
    'type.label':'Files',#类型标签
    'guide.title':'Workspace files',#向导标题
    'guide.description':'Browse files in this session\'s workspace',#向导描述
    'loading':'Reading…',#读取中
    'empty':'Empty directory',#空目录
    'truncated':'Too many entries, showing only some of them.',#截断提示
    'noWorkspace':'This session has no workspace directory.',#无工作区
    'reload':'Reload',#重新读取
    'entry.other':'Not a file or a directory, so it cannot be opened.',#其它条目
    'error.notFound':'That directory is gone. It may have been moved or deleted.',#不存在
    'error.outsideWorkspace':'That directory is outside the workspace, so the sidebar will not read it.',#工作区外
    'error.notDirectory':'That is not a directory.',#非目录
    'error.unavailable':'Read failed: {message}',#其它失败
}#英文词典结束

侧栏文件文案键=tuple(中文.keys())#由中文词典键推导的键域
