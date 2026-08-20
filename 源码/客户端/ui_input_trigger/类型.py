"""输入触发流水线的冻结跨包约定。仅类型形——无运行时代码。

对齐上游 `ui-input-trigger/src/types.ts`。公开面仅中文名。
来源（ui-commands / ui-skill / ui-subagent）与会话输入层从此导入；改动须经主线程仲裁。
提供方每次调用收到会话投影——绝不是 Cordis 上下文或可变 Session。
"""

__all__=[#仅中文公开名
    '客户端会话上下文','触发字符','触发位置','选定途径','输入触发候选','词跨度',
    '命令认领','引用插入','提交结果','选定结果','候选请求','输入触发选定',
    '引用编解码','输入触发源','触发守卫','仲裁键','仲裁结果',
    '开始命令请求','插入引用请求','消费词请求','插入文本请求',
    '斜杠输入事件名',
]#公开面结束

#客户端会话上下文：提供方面对的单会话投影，只携带稳定身份
#字段 sessionId
客户端会话上下文=dict#单会话投影形

触发字符=('/','@')#来源绑定的触发字符
触发位置=('leading','inline')#触发词在草稿中的位置
选定途径=('menu','space','enter')#三条选定路径

#输入触发候选：纯展示数据——零行为声明
#字段 name / description? / icon? / hint?
输入触发候选=dict#菜单候选形

#词跨度：选定瞬间的触发词跨度快照；CAS：过期 draftRev ⇒ 整次动作空操作
#字段 start / end / draftRev
词跨度=dict#词跨度快照形

#命令认领：命令模式入场凭证；纯数据 + submit 闭包
#字段 token / hint? / submit(args,actx)
命令认领=dict#命令认领形

#引用插入：行内引用；草稿每个出现处持有 U+FFFC 占位符
#字段 source / ref / label / clipboardText
引用插入=dict#行内引用插入形

#提交结果：命令提交事务的已结算结果
#字段 kind='success'|'error' / text?
提交结果=dict#提交结算形

#选定结果：claim / insert / text / 'handled' / None
选定结果=object#统一选定返回形

#候选请求：传给来源的候选请求；查询变更/菜单关闭时 signal 被取代
#字段 query / position / signal
候选请求=dict#候选请求形

#输入触发选定：选定时来源收到的全部
#字段 candidate / session / position / via / span
输入触发选定=dict#选定载荷形

#引用编解码：产出 insert 结果的来源所拥有
#方法 clipboardText(ref) / serialize(ref,signal)
引用编解码=dict#引用编解码器形

#输入触发源：一个触发来源
#字段 trigger / name / order? / codec?
#方法 candidates / onPick / matchSpace? / matchEnter? / warm? / lexicon? / subscribeLexicon?
输入触发源=dict#触发来源形

#触发守卫：触发可用性档位
#字段 tier='plain'|'claimed'|'frozen'
触发守卫=dict#触发守卫形

仲裁键=('up','down','enter','escape')#菜单打开时拦截的键
仲裁结果=('consumed','pick-highlighted','pass')#键仲裁结果

#开始命令请求：slash/input-begin-command
#字段 claim / span
开始命令请求=dict#开始命令事件请求形

#插入引用请求：slash/input-insert-reference
#字段 reference / span
插入引用请求=dict#插入引用事件请求形

#消费词请求：slash/input-consume-token
#字段 guard={kind:'span',span}|{kind:'bare-token',token}
消费词请求=dict#消费词事件请求形

#插入文本请求：slash/input-insert-text
#字段 text / span
插入文本请求=dict#插入文本事件请求形

斜杠输入事件名=(#向 Cordis Events 声明合并的斜杠输入事件
    'slash/input-begin-command',#把命令认领应用到作用域 Input
    'slash/input-insert-reference',#把引用插入作用域 Input
    'slash/input-consume-token',#业务成功后消费命令词
    'slash/input-insert-text',#用字面文本替换触发词跨度
)#事件名结束
