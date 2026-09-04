"""Chat 拥有的槽位声明与组合组件 props。

对齐上游 `ui-chat/src/client/contract/slots.ts`。公开面仅中文名。
TypeScript 声明合并以注释与常量形状保留。
"""

__all__=[#仅中文公开名
    '取字段','回合尾属主','助手动作属主','聊天文件提及','聊天节点回合注入',
    '聊天节点属主','回合过程属主','详情工具属主','命令行属主','聊天滚动位置',
    '聊天视图注入','详情注入','槽名聊天节点','槽名消息图片','槽名命令视图',
    '槽名回合尾','槽名助手动作','槽名详情工具','槽名详情','槽名对话视图',
]#公开面结束

槽名对话视图='conversation.view'#Chat 视图
槽名聊天节点='conversation.chat.node'#按键节点
槽名消息图片='conversation.message.images'#消息图片
槽名命令视图='conversation.chat.commandview'#命令行
槽名回合尾='conversation.chat.turnTail'#轮次尾部链
槽名助手动作='conversation.chat.assistant-actions'#Assistant 动作
槽名详情工具='conversation.details.tool'#工具详情
槽名详情='details'#详情栏

回合尾属主=dict#turn / seq / openFile
助手动作属主=dict#messageId
聊天文件提及=dict#forClosing(回合尾属主)
聊天节点属主=dict#selectedCallId / cwd / openFile / inspectCall / forkAt / loadImage / …
回合过程属主=dict#spec / foldable / open / setOpen
详情工具属主=dict#block / cwd
命令行属主=dict#node / compaction
聊天滚动位置=dict#anchorKey / anchorTop / scrollTop
聊天视图注入=dict#hooks / keyedHooks / openDetails / …
详情注入=dict#closeDetails

聊天节点回合注入={#CHAT_NODE_INJECT 形状
    'hooks':{'turnData':'SlotHookFactory'},#按节点读回合数据
}#注入形结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性
