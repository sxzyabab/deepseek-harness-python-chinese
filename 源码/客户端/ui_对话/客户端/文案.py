
__all__=['命名空间','中文','英文']#仅中文公开名

命名空间='conversation'#词典命名空间名

计划下一步中文='描述你的任务以生成计划'#中文下一步动作文案
计划下一步英文='describe your task to generate plan'#英文下一步动作文案

中文={#简体中文词条
    'hint.plan':计划下一步中文,#计划模式输入提示
    'hint.goal':'输入目标，智能体将持续执行',#目标模式输入提示
    'hint.goal.active':'当前目标进行中。可输入 edit 修改 / pause 暂停 / resume 继续 / clear 清除',#活跃目标提示
    'placeholder.plan':计划下一步中文,#计划模式占位
    'placeholder.default':'发消息或创建任务, / 调用指令, @ 文件或对话',#默认输入占位
    'placeholder.unavailable':'会话不可用',#会话不可用占位
    'placeholder.parentOffline':'父会话已离线，无法继续发送；仍可停止当前运行',#父会话离线占位
    'placeholder.hero':'描述你想要构建的内容, / 调用指令, @ 文件或对话',#英雄页输入占位
    'placeholder.workspace':'选择一个工作区开始',#未选工作区占位
    'placeholder.steerQueue':'Cmd/Ctrl+Enter 插话发送全部排队消息',#插话发送占位
    'input.commands':'添加文件或调用指令',#添加文件或指令按钮
    'input.file':'文件',#文件动作标题
    'input.stop':'停止生成',#停止生成按钮
    'input.send':'发送消息',#发送按钮
    'input.send.queue':'排队发送',#排队发送按钮
    'input.send.steer':'插话发送',#插话发送按钮
    'attachment.pending':'待发送附件',#待发附件区
    'attachment.scrollLeft':'向左滚动附件',#左滚附件
    'attachment.scrollRight':'向右滚动附件',#右滚附件
    'attachment.dropTitle':'文件或图片拖动到此处即可添加',#拖放区标题
    'attachment.dropDesc':'图片限制：最多 {count} 张，每张 {size}',#拖放区说明
    'attachment.dropBlocked':'当前无法添加文件或图片',#拖放被拒
    'image.pending':'待发送图片',#待发图片区
    'image.openOriginal':'查看原图',#打开原图
    'image.openOriginalLabel':'{label}，点击查看原图',#原图无障碍标签
    'image.remove':'移除图片 {name}',#移除图片
    'image.original':'原图',#原图标签
    'image.label':'图片',#图片通用标签
    'image.loadFailed':'图片加载失败，点击重试',#加载失败
    'image.loading':'图片加载中…',#加载中
    'image.preview':'原图预览',#预览标题
    'image.closePreview':'关闭原图预览',#关闭预览
    'image.unsupportedType':'仅支持 PNG、JPG、WebP、GIF 格式的图片',#格式不支持
    'image.tooMany':'一条消息最多添加 {count} 张图片',#数量超限
    'image.fileTooLarge':'单张图片不能超过 {size}',#单张过大
    'image.totalTooLarge':'图片总大小超过 {size}，请移除部分图片',#总量过大
    'image.tooManyPixels':'图片分辨率过大，请压缩后重试',#分辨率过大
    'image.dimensionTooLarge':'图片宽高不能超过 {size}px，请缩小后重试',#边长过大
    'image.modelUnsupported':'当前模型不支持图片，请切换支持图片的模型',#模型不支持图
    'image.sendFailed':'图片发送失败（{reason}），请重新添加图片后再试',#发送失败
    'file.pending':'待发送文件',#待发文件区
    'file.remove':'移除文件 {name}',#移除文件
    'file.uploading':'上传中…',#上传中
    'file.uploadFailed':'上传失败，点击重试',#上传失败
    'file.retry':'重试上传 {name}',#重试上传
    'file.stillUploading':'文件还在上传，请等待上传完成后发送',#仍在上传提示
    'file.sessionUnavailable':'会话不可用，无法上传文件',#会话不可用上传
    'file.notStaged':'文件尚未上传成功，请重新添加后再试',#未暂存
    'file.label':'文件',#文件通用标签
    'context.aria':'上下文已用 {percent}',#上下文用量无障碍
    'context.used':'上下文已用',#上下文已用标签
    'context.system':'系统提示词',#系统提示词分段
    'context.tools':'工具定义',#工具分段
    'context.messages':'对话消息',#消息分段
    'settings.enter.title':'繁忙时的发送行为',#Enter 设置标题
    'settings.enter.description':'智能体运行时 Enter 键和发送按钮的行为；Cmd/Ctrl+Enter 使用另一行为',#Enter 设置说明
    'settings.enter.queue':'排队发送',#排队选项
    'settings.enter.steer':'插话发送',#插话选项
    'hero.headline':'探索未至之境',#英雄页标题
    'hero.preview':'预览版',#预览版徽章
    'hero.chooseWorkspace':'选择工作区',#选工作区按钮
    'session.hierarchy':'会话层级',#会话层级标题
    'todo.title':'任务',#待办标题
    'todo.progress.done':'{done} 已完成',#已完成计数
    'todo.progress.active':'{active} 进行中',#进行中计数
    'todo.progress.pending':'{pending} 待处理',#待处理计数
    'todo.rowTitle':'更新任务清单',#待办行标题
    'todo.completed':'{done}/{total} 已完成',#完成进度
    'command.attachmentsUnsupported':'/{command} 不接受附件，请先移除附件',#命令不接受附件
    'ask.rowTitle':'提问',#提问行标题
    'ask.waiting':'等待回答',#等待回答
    'ask.cancelled':'已取消',#已取消
    'ask.cancelledDetail':'本轮已取消，未提交回答',#取消说明
    'ask.interrupted':'已中断',#已中断
    'ask.interruptedDetail':'本轮已中断，未提交回答',#中断说明
    'ask.answered':'{answered}/{total} 已回答',#已回答进度
    'ask.skipped':'未回答',#未回答
    'bash.running':'运行中',#bash 运行中
    'bash.failed':'失败',#bash 失败
    'bash.stopped':'已停止',#bash 已停止
    'row.running':'运行中',#行运行中
    'row.failed':'失败',#行失败
    'row.stopped':'已停止',#行停止
    'row.input':'输入',#行输入
    'row.output':'输出',#行输出
    'row.inspect':'查看',#行检视
    'tool.title.search':'搜索',#搜索工具标题
    'tool.title.read':'读取',#读取工具标题
    'tool.title.bash':'Bash',#Bash 工具标题
    'tool.title.write':'写入',#写入工具标题
    'tool.title.edit':'编辑',#编辑工具标题
    'tool.title.code':'代码',#代码工具标题
    'tool.title.generic':'工具调用',#通用工具标题
    'tool.title.inspect':'查看',#检视工具标题
    'tool.title.runCordis':'运行 Cordis 插件',#运行 Cordis
    'tool.title.stopCordis':'停止 Cordis 插件',#停止 Cordis
    'tool.title.removeCordis':'移除 Cordis 插件',#移除 Cordis
    'tool.title.pwsh':'Pwsh',#Pwsh 标题
    'tool.title.readImage':'读取图片',#读图标题
    'tool.title.grep':'Grep',#Grep 标题
    'tool.title.glob':'Glob',#Glob 标题
    'tool.title.webSearch':'网页搜索',#网页搜索标题
    'tool.title.webFetch':'网页获取',#网页获取标题
    'tool.autoReviewRejected':'Auto review 已拒绝',#自动审查拒绝折叠摘要
    'tool.autoReviewNotExecuted':'工具未执行。原因：{reason}',#自动审查拒绝展开行
    'tool.autoReviewReasonFallback':'Auto review 未授权此次操作',#无可见原因时的回退
    'diff.files.one':'{count} 个文件',#diff 文件数单数
    'diff.files.other':'{count} 个文件',#diff 文件数复数
    'diff.collapseAria':'收起差异',#收起 diff
    'diff.expandAria':'展开其余 {count} 行差异',#展开 diff
    'diff.expandRest':'… 其余 {count} 行',#展开剩余
    'read.window':'显示 {shown} / {total} 行',#读卡窗口
    'read.collapseAria':'收起内容',#收起读卡
    'read.expandAria':'展开其余 {count} 行',#展开读卡
    'read.expandRest':'… 其余 {count} 行',#展开剩余
    'search.paths':'{shown} 个路径',#检索路径数
    'search.paths.truncated':'显示 {shown} / 共 {total} 个路径',#截断路径
    'search.matches':'{shown} 处匹配 · {files} 个文件',#匹配摘要
    'search.matches.truncated':'显示 {shown} / 共 {total} 处匹配 · {files} 个文件',#截断匹配
    'search.noResults':'无结果',#无检索结果
    'search.collapseAria':'收起结果',#收起检索
    'search.expandAria':'展开其余 {count} 行结果',#展开检索
    'search.expandRest':'… 其余 {count} 行',#展开剩余
    'web.noResults':'未找到结果',#网页无结果
    'web.sourcesTruncated':'来源列表已截断',#来源截断
    'web.http':'HTTP',#HTTP 标签
    'web.contentTruncated':'内容已截断',#内容截断
    'details.running':'运行中…',#详情运行中
    'queue.count':'{n} 条排队消息',#排队计数
    'queue.sending':'发送中…',#发送中
    'queue.image':'排队消息图片',#排队图片
    'queue.file':'排队文件 {name}',#排队文件
    'queue.edit':'编辑排队消息',#编辑排队
    'queue.edit.unsupported':'包含非文本内容，暂不支持编辑',#不可编辑
    'queue.save':'保存排队消息',#保存排队
    'queue.cancelEdit':'取消编辑',#取消编辑
    'queue.remove':'删除排队消息',#删除排队
    'queue.steer':'插话发送',#插话发送
    'queue.steer.unavailable':'仅运行中可插话发送',#插话不可用
    'error.sessionInUse':'当前会话已被占用，可能是其他正在运行的 DSH 导致的（如其他 dsh web、桌面端），请退出其他正在运行的 DSH 后重试。',#会话占用
    'queue.editFailed':'编辑失败：这条消息可能已经开始发送。',#编辑失败
    'queue.removeFailed':'删除失败：这条消息可能已经开始发送。',#删除失败
    'queue.steerFailed':'插话发送失败，请重试。',#插话失败
    'terminal.signal':'信号 {signal}',#终端信号
    'terminal.exitCode':'退出码 {code}',#退出码
    'terminal.noExitCode':'未正常退出',#无退出码
    'terminal.running':'运行中',#终端运行中
    'terminal.failed':'失败',#终端失败
    'terminal.done':'已完成',#终端完成
    'terminal.noOutput':'无输出',#无输出
    'terminal.collapseAria':'收起输出',#收起输出
    'terminal.expandAria':'展开其余 {n} 行输出',#展开输出
    'terminal.expandRest':'… 其余 {n} 行',#展开剩余
    'terminal.sendInput':'（发送输入）',#发送输入占位
    'terminal.session':'终端 {sessionId}',#终端会话
}#结束中文

英文={#英文词条（键与中文权威源一致）
    'hint.plan':计划下一步英文,#计划模式输入提示
    'hint.goal':'describe the objective for a long-running task',#目标模式输入提示
    'hint.goal.active':'goal active — edit / pause / resume / clear',#活跃目标提示
    'placeholder.plan':计划下一步英文,#计划模式占位
    'placeholder.default':'Message or run a task, / commands, @ files or sessions',#默认输入占位
    'placeholder.unavailable':'Session unavailable',#会话不可用占位
    'placeholder.parentOffline':'Parent session offline; sending is unavailable but you can still stop the run',#父会话离线占位
    'placeholder.hero':'Describe what you want to build, / commands, @ files or sessions',#英雄页输入占位
    'placeholder.workspace':'Choose a workspace to start',#未选工作区占位
    'placeholder.steerQueue':'Cmd/Ctrl+Enter steers all queued messages',#插话发送占位
    'input.commands':'Add files or run commands',#添加文件或指令按钮
    'input.file':'File',#文件动作标题
    'input.stop':'Stop generating',#停止生成按钮
    'input.send':'Send message',#发送按钮
    'input.send.queue':'Queue message',#排队发送按钮
    'input.send.steer':'Steer message',#插话发送按钮
    'attachment.pending':'Pending attachments',#待发附件区
    'attachment.scrollLeft':'Scroll attachments left',#左滚附件
    'attachment.scrollRight':'Scroll attachments right',#右滚附件
    'attachment.dropTitle':'Drag files or images here to add them',#拖放区标题
    'attachment.dropDesc':'Image limit: up to {count} images, {size} each',#拖放区说明
    'attachment.dropBlocked':'Files and images cannot be added right now',#拖放被拒
    'image.pending':'Pending images',#待发图片区
    'image.openOriginal':'View original',#打开原图
    'image.openOriginalLabel':'{label}, click to view original',#原图无障碍标签
    'image.remove':'Remove image {name}',#移除图片
    'image.original':'Original image',#原图标签
    'image.label':'Image',#图片通用标签
    'image.loadFailed':'Image failed to load; click to retry',#加载失败
    'image.loading':'Loading image…',#加载中
    'image.preview':'Original image preview',#预览标题
    'image.closePreview':'Close original image preview',#关闭预览
    'image.unsupportedType':'Only PNG, JPG, WebP, and GIF images are supported',#格式不支持
    'image.tooMany':'A message can include up to {count} images',#数量超限
    'image.fileTooLarge':'Each image must be smaller than {size}',#单张过大
    'image.totalTooLarge':'Images exceed {size} in total; remove some and try again',#总量过大
    'image.tooManyPixels':'Image resolution is too high; compress it and try again',#分辨率过大
    'image.dimensionTooLarge':'Image sides must be at most {size}px; downscale it and try again',#边长过大
    'image.modelUnsupported':'The current model does not support images; switch to a model that does',#模型不支持图
    'image.sendFailed':'Sending images failed ({reason}); re-add them and try again',#发送失败
    'file.pending':'Pending files',#待发文件区
    'file.remove':'Remove file {name}',#移除文件
    'file.uploading':'Uploading…',#上传中
    'file.uploadFailed':'Upload failed; click to retry',#上传失败
    'file.retry':'Retry uploading {name}',#重试上传
    'file.stillUploading':'Files are still uploading; send after they finish',#仍在上传提示
    'file.sessionUnavailable':'Session unavailable; files cannot be uploaded',#会话不可用上传
    'file.notStaged':'The file has not finished uploading; re-add it and try again',#未暂存
    'file.label':'File',#文件通用标签
    'context.aria':'{percent} of context used',#上下文用量无障碍
    'context.used':'of context used',#上下文已用标签
    'context.system':'System prompt',#系统提示词分段
    'context.tools':'Tool definitions',#工具分段
    'context.messages':'Messages',#消息分段
    'settings.enter.title':'Send behavior while busy',#Enter 设置标题
    'settings.enter.description':'What Enter and the Send button do while the agent is running; Cmd/Ctrl+Enter uses the other behavior',#Enter 设置说明
    'settings.enter.queue':'Queue',#排队选项
    'settings.enter.steer':'Steer',#插话选项
    'hero.headline':'Into the Unknown',#英雄页标题
    'hero.preview':'Preview',#预览版徽章
    'hero.chooseWorkspace':'Choose workspace',#选工作区按钮
    'session.hierarchy':'Session hierarchy',#会话层级标题
    'todo.title':'To-dos',#待办标题
    'todo.progress.done':'{done} completed',#已完成计数
    'todo.progress.active':'{active} in progress',#进行中计数
    'todo.progress.pending':'{pending} pending',#待处理计数
    'todo.rowTitle':'Update to-do list',#待办行标题
    'todo.completed':'{done}/{total} completed',#完成进度
    'command.attachmentsUnsupported':'/{command} does not accept attachments; remove them first',#命令不接受附件
    'ask.rowTitle':'Ask question',#提问行标题
    'ask.waiting':'waiting',#等待回答
    'ask.cancelled':'cancelled',#已取消
    'ask.cancelledDetail':'This question set was cancelled before answers were submitted.',#取消说明
    'ask.interrupted':'interrupted',#已中断
    'ask.interruptedDetail':'This question set was interrupted before answers were submitted.',#中断说明
    'ask.answered':'{answered}/{total} answered',#已回答进度
    'ask.skipped':'Not answered',#未回答
    'bash.running':'Running',#bash 运行中
    'bash.failed':'Failed',#bash 失败
    'bash.stopped':'Stopped',#bash 已停止
    'row.running':'Running',#行运行中
    'row.failed':'Failed',#行失败
    'row.stopped':'Stopped',#行停止
    'row.input':'IN',#行输入
    'row.output':'OUT',#行输出
    'row.inspect':'Inspect',#行检视
    'tool.title.search':'Search',#搜索工具标题
    'tool.title.read':'Read',#读取工具标题
    'tool.title.bash':'Bash',#Bash 工具标题
    'tool.title.write':'Write',#写入工具标题
    'tool.title.edit':'Edit',#编辑工具标题
    'tool.title.code':'Code',#代码工具标题
    'tool.title.generic':'Tool call',#通用工具标题
    'tool.title.inspect':'Inspect',#检视工具标题
    'tool.title.runCordis':'Run Cordis Plugin',#运行 Cordis
    'tool.title.stopCordis':'Stop Cordis Plugin',#停止 Cordis
    'tool.title.removeCordis':'Remove Cordis Plugin',#移除 Cordis
    'tool.title.pwsh':'Pwsh',#Pwsh 标题
    'tool.title.readImage':'Read image',#读图标题
    'tool.title.grep':'Grep',#Grep 标题
    'tool.title.glob':'Glob',#Glob 标题
    'tool.title.webSearch':'Search',#网页搜索标题
    'tool.title.webFetch':'Fetch',#网页获取标题
    'tool.autoReviewRejected':'Rejected by Auto review',#自动审查拒绝折叠摘要
    'tool.autoReviewNotExecuted':'Tool was not executed. Reason: {reason}',#自动审查拒绝展开行
    'tool.autoReviewReasonFallback':'Auto review did not authorize this action',#无可见原因时的回退
    'diff.files.one':'{count} file',#diff 文件数单数
    'diff.files.other':'{count} files',#diff 文件数复数
    'diff.collapseAria':'Collapse diff',#收起 diff
    'diff.expandAria':'Expand {count} more diff lines',#展开 diff
    'diff.expandRest':'… {count} more lines',#展开剩余
    'read.window':'Showing {shown} of {total} lines',#读卡窗口
    'read.collapseAria':'Collapse content',#收起读卡
    'read.expandAria':'Expand {count} more lines',#展开读卡
    'read.expandRest':'… {count} more lines',#展开剩余
    'search.paths':'{shown} paths',#检索路径数
    'search.paths.truncated':'Showing {shown} of {total} paths',#截断路径
    'search.matches':'{shown} matches · {files} files',#匹配摘要
    'search.matches.truncated':'Showing {shown} of {total} matches · {files} files',#截断匹配
    'search.noResults':'No results',#无检索结果
    'search.collapseAria':'Collapse results',#收起检索
    'search.expandAria':'Expand {count} more result lines',#展开检索
    'search.expandRest':'… {count} more lines',#展开剩余
    'web.noResults':'No results found',#网页无结果
    'web.sourcesTruncated':'Source list truncated',#来源截断
    'web.http':'HTTP',#HTTP 标签
    'web.contentTruncated':'Content truncated',#内容截断
    'details.running':'Running…',#详情运行中
    'queue.count':'{n} queued messages',#排队计数
    'queue.sending':'Sending…',#发送中
    'queue.image':'Queued message image',#排队图片
    'queue.file':'Queued file {name}',#排队文件
    'queue.edit':'Edit queued message',#编辑排队
    'queue.edit.unsupported':'Contains non-text content; editing is not supported yet',#不可编辑
    'queue.save':'Save queued message',#保存排队
    'queue.cancelEdit':'Cancel editing',#取消编辑
    'queue.remove':'Remove queued message',#删除排队
    'queue.steer':'Steer queued message',#插话发送
    'queue.steer.unavailable':'Steering is available only while the agent is running',#插话不可用
    'error.sessionInUse':'This session is already in use, possibly by another running DSH instance (such as dsh web or the desktop app). Quit other running DSH instances and try again.',#会话占用
    'queue.editFailed':'Edit failed: this message may have already started sending.',#编辑失败
    'queue.removeFailed':'Removal failed: this message may have already started sending.',#删除失败
    'queue.steerFailed':'Steering failed. Try again.',#插话失败
    'terminal.signal':'signal {signal}',#终端信号
    'terminal.exitCode':'exit code {code}',#退出码
    'terminal.noExitCode':'no exit code',#无退出码
    'terminal.running':'Running',#终端运行中
    'terminal.failed':'Failed',#终端失败
    'terminal.done':'Done',#终端完成
    'terminal.noOutput':'No output',#无输出
    'terminal.collapseAria':'Collapse output',#收起输出
    'terminal.expandAria':'Expand the remaining {n} output lines',#展开输出
    'terminal.expandRest':'… {n} more lines',#展开剩余
    'terminal.sendInput':'(send input)',#发送输入占位
    'terminal.session':'Terminal {sessionId}',#终端会话
}#结束英文
