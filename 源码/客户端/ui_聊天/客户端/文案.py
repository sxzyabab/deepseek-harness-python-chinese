"""Chat 拥有的本地化命名空间与词典。

对齐上游 `ui-chat/src/client/locale.ts`。公开面仅中文名。
"""

__all__=['命名空间','中文','英文','NS','zh','en']#仅中文公开名

命名空间='chat'#文案命名空间
NS=命名空间#英文别名

中文={#简体中文词典
    'view.chat':'对话',#Chat 视图标签
    'number.groupSeparator':',',#千分位分隔符
    'duration.compactSeconds':'{seconds}秒',#紧凑秒
    'duration.compactMinutes':'{minutes}分{seconds}秒',#紧凑分秒
    'duration.milliseconds':'{milliseconds}毫秒',#毫秒
    'stats.counts':'{turns} 轮 · {steps} 步',#轮次与步骤计数
    'stats.llm':'LLM {duration}',#LLM 耗时
    'stats.toolCall':'工具调用 {duration}',#工具调用耗时
    'stats.ttftAverage':'首 token 平均 {duration}',#平均 TTFT
    'stats.tokensPerSecond':'{throughput} tok/s',#吞吐
    'stats.cacheHit':'缓存命中 {percent}%',#缓存命中率
    'stats.tokens':'输入 {input} tok · 输出 {output} tok',#输入输出 token
    'details.title':'详情',#详情标题
    'details.close':'关闭详情',#关闭详情
    'details.empty':'点击消息流中的工具行查看详情',#详情空态
    'details.notInWindow':'该调用不在当前窗口内',#窗口外提示
    'details.input':'输入',#输入区标题
    'details.output':'输出',#输出区标题
    'details.running':'运行中…',#运行中提示
    'chat.loadingHistory':'载入历史…',#加载历史
    'chat.loadError':'历史加载失败：{message}（{code}）',#加载失败
    'chat.loadOlder':'加载更早',#加载更早
    'chat.toBottom':'回到底部',#回到底部
    'chat.deepDiving':'深度求索中...',#深度求索中
    'chat.turnNavigation.label':'轮次导航',#导航标签
    'chat.turnNavigation.jump':'跳转到第 {turn} 轮',#跳转轮次
    'chat.turnNavigation.jumpLoad':'加载并跳转到第 {turn} 轮',#加载并跳转
    'chat.turnNavigation.turn':'第 {turn} 轮',#轮次标签
    'settings.transcript.title':'对话显示',#设置标题
    'settings.transcript.description':'控制已完成轮次的过程内容',#设置说明
    'settings.transcript.normal':'Normal',#普通模式
    'settings.transcript.compact':'Compact',#紧凑模式
    'fileOpen.title':'无法打开文件',#打开文件失败标题
    'fileOpen.unknown':'无法打开此文件',#打开文件失败正文
    'fileOpen.folderTitle':'无法打开文件夹',#打开文件夹失败标题
    'fileOpen.folderUnknown':'无法打开此文件夹',#打开文件夹失败正文
    'message.extraBlock':'附加内容块',#附加块
    'message.systemPrompt':'系统提示词',#系统提示词
    'message.contextInjection':'上下文注入',#上下文注入
    'message.contextRecall':'跨会话召回',#跨会话召回
    'message.referenceSummary':'引用会话 · {labels}',#引用摘要
    'message.referenceSeparator':'、',#引用分隔符
    'message.context.instructions.loaded':'已载入',#指令已载入
    'message.context.instructions.added':'已新增',#指令已新增
    'message.context.instructions.updated':'已更新',#指令已更新
    'message.context.instructions.removed':'已移除',#指令已移除
    'message.context.catalog.replaced':'替换目录',#目录替换
    'message.context.catalog.more':'…还有 {count} 条',#目录更多
    'message.context.snapshot.supersedes':'取代先前的快照',#快照取代
    'message.context.relay.from':'来自会话 {session}',#中继来源
    'message.context.recall.counts':'保留 {retained} 条 · 省略 {omitted} 条',#召回计数
    'message.context.recall.truncated':'已截断',#召回截断
    'message.compaction':'上下文已压缩',#压缩完成
    'message.compaction.running':'正在压缩…',#压缩进行中
    'message.compaction.completed':'已压缩 {items} 条历史记录（约 {tokens} tokens）',#压缩结果
    'message.compaction.expand':'点击查看压缩摘要',#展开摘要
    'message.compaction.unavailable':'压缩摘要不可用',#摘要不可用
    'message.compaction.commandTitle':'compact',#压缩命令标题
    'message.think':'思考',#思考标签
    'message.unknownSurface':'未知 surface 事件：{type}',#未知 surface
    'message.unknownBlock':'未知内容块',#未知块
    'message.turnProcess.toolCalls.one':'{count} 次工具调用',#工具调用单数
    'message.turnProcess.toolCalls.other':'{count} 次工具调用',#工具调用复数
    'message.turnProcess.messages.one':'{count} 条消息',#消息单数
    'message.turnProcess.messages.other':'{count} 条消息',#消息复数
    'message.turnProcess.subagents.one':'{count} 个 subagent',#subagent 单数
    'message.turnProcess.subagents.other':'{count} 个 subagent',#subagent 复数
    'message.turnProcess.thoughtForAWhile':'已思考',#已思考
    'message.turnProcess.separator':' · ',#过程分隔符
    'message.stopped':'已停止',#已停止
    'message.branch':'在新对话中分支',#分支动作
    'message.branchUnavailable':'仅可从已完成轮次的最后一条消息分支',#分支不可用
    'message.retry.active':'正在重试模型请求',#重试进行中
    'message.retry.cancelled':'模型请求重试已取消',#重试已取消
    'message.retry.started':'已重试模型请求',#已发起重试
    'message.retry.scheduled':'等待重试模型请求',#等待重试
    'message.retry.status':'{label}（{retry}/{maximum}） · {seconds}s',#重试状态
    'message.retry.delay':'重试延迟：',#重试延迟前缀
    'message.retry.failure':'失败原因：',#失败原因前缀
    'message.failure.auth':'API 密钥无效',#鉴权失败
    'message.turnError':'本轮运行失败',#轮次错误
    'message.maxTokens':'已达到输出 token 上限',#达上限
    'message.maxTokens.hint':'回答被截断，已有输出保留在对话中。发送“继续”可让模型接着输出。',#上限提示
    'message.ranFor':'用时 {duration}',#运行时长
    'message.tokensPerSecond':'{tps} tok/s',#消息级吞吐
    'message.turnUsage.title':'本轮用量',#用量标题
    'message.turnUsage.consumed':'用量 {total}',#用量合计
    'message.turnUsage.model':'提供方 / 模型',#模型行
    'message.turnUsage.cacheHit':'缓存命中',#缓存命中
    'message.turnUsage.input':'未缓存输入',#未缓存输入
    'message.turnUsage.cacheRead':'缓存读取',#缓存读取
    'message.turnUsage.cacheWrite':'缓存写入',#缓存写入
    'message.turnUsage.output':'输出',#输出
    'message.turnUsage.reasoning':'（其中推理 {tokens}）',#推理子集
    'message.turnUsage.count':'{count} tok',#token 计数
    'message.turnTime.title':'本轮用时和速度',#用时标题
    'message.turnTime.duration':'本轮总用时',#总用时
    'message.turnTime.speed':'输出速度（TPS）',#输出速度
    'message.turnTime.ttft':'首 token 用时（TTFT）',#TTFT
    'duration.seconds':'{seconds}秒',#秒
    'duration.minutes':'{minutes}分{seconds}秒',#分秒
    'command.running':'执行中…',#命令执行中
    'command.failed':'指令失败',#命令失败
    'command.done':'已完成',#命令完成
    'command.title':'指令',#命令标题
    'row.running':'运行中',#行运行中
    'row.failed':'失败',#行失败
    'json.truncated':'… 已截断，共 {total} 字符',#JSON 截断
    'clock.md':'{m}月{d}日',#月日
    'clock.ymd':'{y}年{m}月{d}日',#年月日
}#中文结束

英文={#英文词典
    'view.chat':'Chat',#Chat 视图标签
    'number.groupSeparator':',',#千分位分隔符
    'duration.compactSeconds':'{seconds}s',#紧凑秒
    'duration.compactMinutes':'{minutes}m{seconds}s',#紧凑分秒
    'duration.milliseconds':'{milliseconds}ms',#毫秒
    'stats.counts':'{turns} turns · {steps} steps',#轮次与步骤计数
    'stats.llm':'LLM {duration}',#LLM 耗时
    'stats.toolCall':'Tool call {duration}',#工具调用耗时
    'stats.ttftAverage':'TTFT avg {duration}',#平均 TTFT
    'stats.tokensPerSecond':'{throughput} tok/s',#吞吐
    'stats.cacheHit':'Cache hit {percent}%',#缓存命中率
    'stats.tokens':'Input {input} tok · Output {output} tok',#输入输出 token
    'details.title':'Details',#详情标题
    'details.close':'Close details',#关闭详情
    'details.empty':'Click a tool row in the message flow to view its details',#详情空态
    'details.notInWindow':'This call is outside the current window',#窗口外提示
    'details.input':'Input',#输入区标题
    'details.output':'Output',#输出区标题
    'details.running':'Running…',#运行中提示
    'chat.loadingHistory':'Loading history…',#加载历史
    'chat.loadError':'Failed to load history: {message} ({code})',#加载失败
    'chat.loadOlder':'Load earlier',#加载更早
    'chat.toBottom':'Back to bottom',#回到底部
    'chat.deepDiving':'Deep diving...',#深度求索中
    'chat.turnNavigation.label':'Turn navigation',#导航标签
    'chat.turnNavigation.jump':'Jump to turn {turn}',#跳转轮次
    'chat.turnNavigation.jumpLoad':'Load and jump to turn {turn}',#加载并跳转
    'chat.turnNavigation.turn':'Turn {turn}',#轮次标签
    'settings.transcript.title':'Conversation display',#设置标题
    'settings.transcript.description':'Controls process content in completed turns',#设置说明
    'settings.transcript.normal':'Normal',#普通模式
    'settings.transcript.compact':'Compact',#紧凑模式
    'fileOpen.title':"Couldn't open file",#打开文件失败标题
    'fileOpen.unknown':"Couldn't open this file",#打开文件失败正文
    'fileOpen.folderTitle':"Couldn't open folder",#打开文件夹失败标题
    'fileOpen.folderUnknown':"Couldn't open this folder",#打开文件夹失败正文
    'message.extraBlock':'Extra content block',#附加块
    'message.systemPrompt':'System prompt',#系统提示词
    'message.contextInjection':'Context injection',#上下文注入
    'message.contextRecall':'Session recall',#跨会话召回
    'message.referenceSummary':'Referenced session · {labels}',#引用摘要
    'message.referenceSeparator':', ',#引用分隔符
    'message.context.instructions.loaded':'loaded',#指令已载入
    'message.context.instructions.added':'added',#指令已新增
    'message.context.instructions.updated':'updated',#指令已更新
    'message.context.instructions.removed':'removed',#指令已移除
    'message.context.catalog.replaced':'Replacement catalog',#目录替换
    'message.context.catalog.more':'… {count} more',#目录更多
    'message.context.snapshot.supersedes':'Supersedes earlier snapshots',#快照取代
    'message.context.relay.from':'From session {session}',#中继来源
    'message.context.recall.counts':'{retained} kept · {omitted} omitted',#召回计数
    'message.context.recall.truncated':'truncated',#召回截断
    'message.compaction':'Context compacted',#压缩完成
    'message.compaction.running':'Compacting context…',#压缩进行中
    'message.compaction.completed':'Compacted {items} history items (~{tokens} tokens)',#压缩结果
    'message.compaction.expand':'View compaction summary',#展开摘要
    'message.compaction.unavailable':'Compaction summary unavailable',#摘要不可用
    'message.compaction.commandTitle':'compact',#压缩命令标题
    'message.think':'Think',#思考标签
    'message.unknownSurface':'Unknown surface event: {type}',#未知 surface
    'message.unknownBlock':'Unknown content block',#未知块
    'message.turnProcess.toolCalls.one':'{count} tool call',#工具调用单数
    'message.turnProcess.toolCalls.other':'{count} tool calls',#工具调用复数
    'message.turnProcess.messages.one':'{count} message',#消息单数
    'message.turnProcess.messages.other':'{count} messages',#消息复数
    'message.turnProcess.subagents.one':'{count} subagent',#subagent 单数
    'message.turnProcess.subagents.other':'{count} subagents',#subagent 复数
    'message.turnProcess.thoughtForAWhile':'Thought for a while',#已思考
    'message.turnProcess.separator':' · ',#过程分隔符
    'message.stopped':'Stopped',#已停止
    'message.branch':'Branch into a new conversation',#分支动作
    'message.branchUnavailable':'Available only on the last message of a completed turn',#分支不可用
    'message.retry.active':'Retrying model request',#重试进行中
    'message.retry.cancelled':'Model request retry cancelled',#重试已取消
    'message.retry.started':'Retried model request',#已发起重试
    'message.retry.scheduled':'Waiting to retry model request',#等待重试
    'message.retry.status':'{label} ({retry}/{maximum}) · {seconds}s',#重试状态
    'message.retry.delay':'Retry delay: ',#重试延迟前缀
    'message.retry.failure':'Failure reason: ',#失败原因前缀
    'message.failure.auth':'API key is invalid',#鉴权失败
    'message.turnError':'This turn failed',#轮次错误
    'message.maxTokens':'Output token limit reached',#达上限
    'message.maxTokens.hint':'The reply was cut off; earlier output is preserved in the conversation. Send "continue" to let the model resume.',#上限提示
    'message.ranFor':'Ran for {duration}',#运行时长
    'message.tokensPerSecond':'{tps} tok/s',#消息级吞吐
    'message.turnUsage.title':'Turn usage',#用量标题
    'message.turnUsage.consumed':'Usage {total}',#用量合计
    'message.turnUsage.model':'Provider / model',#模型行
    'message.turnUsage.cacheHit':'Cache hit',#缓存命中
    'message.turnUsage.input':'Uncached input',#未缓存输入
    'message.turnUsage.cacheRead':'Cached input',#缓存读取
    'message.turnUsage.cacheWrite':'Cache write',#缓存写入
    'message.turnUsage.output':'Output',#输出
    'message.turnUsage.reasoning':' ({tokens} reasoning)',#推理子集
    'message.turnUsage.count':'{count} tok',#token 计数
    'message.turnTime.title':'Turn time and speed',#用时标题
    'message.turnTime.duration':'Total run time',#总用时
    'message.turnTime.speed':'Tokens per second (TPS)',#输出速度
    'message.turnTime.ttft':'Time to first token (TTFT)',#TTFT
    'duration.seconds':'{seconds}s',#秒
    'duration.minutes':'{minutes}m {seconds}s',#分秒
    'command.running':'Running…',#命令执行中
    'command.failed':'Command failed',#命令失败
    'command.done':'Completed',#命令完成
    'command.title':'Command',#命令标题
    'row.running':'Running',#行运行中
    'row.failed':'Failed',#行失败
    'json.truncated':'… truncated, {total} characters total',#JSON 截断
    'clock.md':'{m}/{d}',#月日
    'clock.ymd':'{y}-{m}-{d}',#年月日
}#英文结束

zh=中文#英文别名
en=英文#英文别名
