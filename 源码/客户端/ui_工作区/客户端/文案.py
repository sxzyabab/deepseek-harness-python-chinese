"""`workspace` 命名空间词典：浏览区与挑选/添加流程。

对齐上游 `ui-workspace/src/client/locales.ts`。公开面仅中文名；词典键与英文字面量保持上游。
运行时失败消息（传输层错误字符串）按政策原样透传、不翻译。
"""

__all__=['中文','英文','工作区文案键']#仅中文公开名

中文={#简体中文词条（键集合的权威源）
    'group.ungrouped':'未分组',#未分组标签
    'session.new':'新会话',#新会话按钮
    'section.workspaces':'工作区',#工作区分区标题
    'section.sessions':'会话',#会话分区标题
    'viewOptions.label':'视图选项',#视图选项标签
    'groupBy.label':'分组方式',#分组方式标签
    'groupBy.workspace':'按工作区',#按工作区分组
    'groupBy.flat':'单列表',#扁平单列表
    'orderBy.label':'排序方式',#排序方式标签
    'orderBy.manual':'手动排序',#手动排序
    'orderBy.updated':'最近更新',#按最近更新排序
    'sessions.expand':'展开其余 {n} 个会话',#展开其余会话
    'sessions.collapse':'收起',#收起会话列表
    'empty.none':'暂无会话',#无会话空态
    'empty.noMatches':'无匹配结果',#无匹配空态
    'workspace.add':'添加工作区',#添加工作区按钮
    'search.sessions.aria':'搜索会话',#搜索会话无障碍名
    'search.placeholder':'搜索会话…',#搜索占位
    'search.clear':'清除搜索',#清除搜索
    'search.results.aria':'搜索结果',#搜索结果无障碍名
    'search.pending':'正在搜索会话历史…',#搜索进行中
    'search.unavailable':'内容搜索暂不可用，仅显示名称匹配。',#内容搜索不可用
    'search.noMatches':'无匹配会话',#无匹配会话
    'search.hasMore':'仅显示前 {n} 条结果，请缩小搜索范围。',#结果截断提示
    'menu.addWorkspace':'添加工作区…',#菜单添加工作区
    'picker.loading':'正在加载工作区…',#挑选器加载中
    'conflict.named':'已存在名为“{name}”的工作区。',#重名冲突
    'folderError.title':'无法打开文件夹',#打开文件夹失败标题
    'folderError.retry':'重新选择',#重新选择文件夹
    'rename':'重命名',#重命名
    'rename.workspace.title':'重命名工作区',#重命名工作区标题
    'rename.session.title':'重命名会话',#重命名会话标题
    'field.workspaceName':'工作区名称',#工作区名称字段
    'field.sessionName':'会话名称',#会话名称字段
    'delete.workspace':'删除工作区',#删除工作区
    'delete.desc':'将把“{name}”从工作区列表中移除。文件夹与会话记录会保留，其会话将显示在“未分组”下。',#删除工作区说明
    'delete.pending':'正在删除工作区…',#删除进行中
    'menu.fork':'分叉会话',#分叉会话菜单
    'menu.archiveSession':'归档会话',#归档会话菜单
    'sessions.count.one':'{n} 个会话',#会话数单数
    'sessions.count.other':'{n} 个会话',#会话数复数
    'actions.workspace.aria':'工作区“{name}”的操作',#工作区操作无障碍名
    'actions.session.aria':'会话“{name}”的操作',#会话操作无障碍名
    'actions.newSession.aria':'在“{name}”中新建会话',#新建会话无障碍名
    'status.running':'进行中',#运行中状态
    'status.subagentsRunning.one':'{n} 个子代理运行中',#子代理运行单数
    'status.subagentsRunning.other':'{n} 个子代理运行中',#子代理运行复数
    'status.idle':'空闲',#空闲状态
    'status.waitingApproval':'等待审批',#等待审批状态
    'status.planReview':'计划待审',#计划待审状态
    'status.waitingAnswer':'等待回答',#等待回答状态
    'status.completed':'已完成',#已完成状态
    'hover.created':'创建于 {time}',#创建时间悬停
    'hover.copied':'已复制',#已复制提示
    'date.ymd':'{y}年{m}月{d}日',#年月日格式
    'time.now':'刚刚',#刚刚
    'time.minutes':'{n}分钟',#分钟相对时间
    'time.hours':'{n}小时',#小时相对时间
    'time.days':'{n}天',#天相对时间
    'time.months':'{n}个月',#月相对时间
    'time.years':'{n}年',#年相对时间
    'time.ago':'{t}前',#相对时间后缀
}#中文词典结束

英文={#英文词条，对照中文权威源核验键齐全
    'group.ungrouped':'Ungrouped',#未分组标签
    'session.new':'New Session',#新会话按钮
    'section.workspaces':'Workspaces',#工作区分区标题
    'section.sessions':'Sessions',#会话分区标题
    'viewOptions.label':'View options',#视图选项标签
    'groupBy.label':'Group by',#分组方式标签
    'groupBy.workspace':'WorkSpace',#按工作区分组
    'groupBy.flat':'In one list',#扁平单列表
    'orderBy.label':'Order by',#排序方式标签
    'orderBy.manual':'Manual',#手动排序
    'orderBy.updated':'Last updated',#按最近更新排序
    'sessions.expand':'Show {n} more sessions',#展开其余会话
    'sessions.collapse':'Show less',#收起会话列表
    'empty.none':'No sessions yet',#无会话空态
    'empty.noMatches':'No matches',#无匹配空态
    'workspace.add':'Add workspace',#添加工作区按钮
    'search.sessions.aria':'Search sessions',#搜索会话无障碍名
    'search.placeholder':'Search sessions...',#搜索占位
    'search.clear':'Clear search',#清除搜索
    'search.results.aria':'Search results',#搜索结果无障碍名
    'search.pending':'Searching session history…',#搜索进行中
    'search.unavailable':'Content search is temporarily unavailable. Showing name matches.',#内容搜索不可用
    'search.noMatches':'No matching sessions',#无匹配会话
    'search.hasMore':'Showing the first {n} results. Narrow your search.',#结果截断提示
    'menu.addWorkspace':'Add workspace…',#菜单添加工作区
    'picker.loading':'Loading workspaces…',#挑选器加载中
    'conflict.named':'A workspace named “{name}” already exists.',#重名冲突
    'folderError.title':'Couldn’t open folder',#打开文件夹失败标题
    'folderError.retry':'Choose again',#重新选择文件夹
    'rename':'Rename',#重命名
    'rename.workspace.title':'Rename workspace',#重命名工作区标题
    'rename.session.title':'Rename session',#重命名会话标题
    'field.workspaceName':'Workspace name',#工作区名称字段
    'field.sessionName':'Session name',#会话名称字段
    'delete.workspace':'Delete workspace',#删除工作区
    'delete.desc':'This removes “{name}” from the workspace list. The folder and session logs will be kept. Its sessions will appear under Ungrouped.',#删除工作区说明
    'delete.pending':'Deleting workspace…',#删除进行中
    'menu.fork':'Fork session',#分叉会话菜单
    'menu.archiveSession':'Archive session',#归档会话菜单
    'sessions.count.one':'{n} session',#会话数单数
    'sessions.count.other':'{n} sessions',#会话数复数
    'actions.workspace.aria':'Workspace actions for {name}',#工作区操作无障碍名
    'actions.session.aria':'Session actions for {name}',#会话操作无障碍名
    'actions.newSession.aria':'New session in {name}',#新建会话无障碍名
    'status.running':'Running',#运行中状态
    'status.subagentsRunning.one':'{n} subagent running',#子代理运行单数
    'status.subagentsRunning.other':'{n} subagents running',#子代理运行复数
    'status.idle':'Idle',#空闲状态
    'status.waitingApproval':'Waiting for approval',#等待审批状态
    'status.planReview':'Plan awaiting review',#计划待审状态
    'status.waitingAnswer':'Waiting for answer',#等待回答状态
    'status.completed':'Completed',#已完成状态
    'hover.created':'Created {time}',#创建时间悬停
    'hover.copied':'Copied',#已复制提示
    'date.ymd':'{y}-{m}-{d}',#年月日格式
    'time.now':'now',#刚刚
    'time.minutes':'{n}min',#分钟相对时间
    'time.hours':'{n}h',#小时相对时间
    'time.days':'{n}d',#天相对时间
    'time.months':'{n}mo',#月相对时间
    'time.years':'{n}y',#年相对时间
    'time.ago':'{t} ago',#相对时间后缀
}#英文词典结束

工作区文案键=tuple(中文.keys())#由中文词典键推导
