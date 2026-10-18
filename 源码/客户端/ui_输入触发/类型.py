'触发源面对的类型。运行时只有别名，字段名保持上游原文'
__all__=[
    '客户端会话上下文','触发字符','触发位置','选定途径','选定动作','候选图标',
    '输入触发候选','输入触发屑','页眉请求','提交信封','提交附件',
    '候选请求','输入触发选定','引用编解码','输入触发源','触发守卫',
    '词跨度','命令认领','引用插入','提交结果','选定结果',
    '仲裁键','仲裁结果','开始命令请求','插入引用请求','消费词请求','插入文本请求',
]

#字段 sessionId
客户端会话上下文=dict#一场会话的稳定身份

触发字符=('/','@')#源绑定的触发字符
触发位置=('leading','inline')#词在草稿里的位置
选定途径=('menu','space','enter')#三条选定路径
选定动作=('pick','drill')#落定或就地下钻
候选图标=('file','folder','session')#行首字形记号

#字段 name / label / description / icon / hint / section / value / drill
输入触发候选=dict#一行候选，只有展示数据

#字段 label / value / current
输入触发屑=dict#页眉上的一节面包屑

#字段 query / quoted / drilled
页眉请求=dict#源决定页眉时拿到的查询

#字段 attachments
提交信封=dict#回车裁决看得见的非文本提交

提交附件=dict#随草稿提交的附件

#字段 query / quoted / position / drilled / signal
候选请求=dict#向源要候选时的请求

#字段 candidate / session / position / via / action / span
输入触发选定=dict#一次点选交给源的全部材料

#方法 clipboardText(ref) / serialize(ref, signal)
引用编解码=dict#引用的剪贴板文本和模型序列化

#字段 trigger / name / order / showGroupTitle / codec
#方法 candidates / header / onPick / matchSpace / matchEnter / matchClaim / warm / lexicon / subscribeLexicon / openReference
输入触发源=dict#一个触发源

#字段 tier：plain / claimed / frozen
触发守卫=dict#这一拍哪些触发字符还活着

#字段 start / end / draftRev
词跨度=dict#触发词在草稿里的跨度

#字段 token / hint / submit
命令认领=dict#命令芯片要恢复的认领

#字段 source / ref / label / appearance / clipboardText
引用插入=dict#插入草稿的一条引用

#字段 kind / text
提交结果=dict#命令提交的结果

选定结果=object#claim、insert、text、handled 或 None

仲裁键=('up','down','escape','tabBack','enter','tab')#菜单打开时拦截的键
仲裁结果=('pass','consumed','pick-highlighted')#键交给浏览器、菜单吃掉，或落定高亮

#字段 claim / span
开始命令请求=dict#slash/input-begin-command

#字段 reference / span
插入引用请求=dict#slash/input-insert-reference

#字段 guard
消费词请求=dict#slash/input-consume-token

#字段 text / span / continue
插入文本请求=dict#slash/input-insert-text
