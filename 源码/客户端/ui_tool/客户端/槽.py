"""工具 UI 槽声明及其组合后的组件 props。

对齐上游 `ui-tool/src/client/contract/slots.ts`。公开面仅中文名。
向槽位包声明合并：按线上工具名键分发的原子工具调用视图。
"""

__all__=[#仅中文公开名
    '工具调用属主属性','工具调用视图属性','工具树属性','工具详情属性',
    '槽名工具调用视图','槽名聊天节点','槽名详情工具',
]#公开面结束

槽名工具调用视图='tool.call.toolview'#按工具名键分发的原子调用视图
槽名聊天节点='conversation.chat.node'#聊天节点槽
槽名详情工具='conversation.details.tool'#详情工具输出槽

# 工具调用属主份额字段（运行时由宿主填入）
工具调用属主属性=(#每个原子工具视图的标准属主份额
    'callId',#工具调用身份
    'toolName',#线上工具名
    'block',#冻结的运行中或已结算节点
    'cwd',#会话工作区根路径
    'openFile',#经宿主打开参数路径
    'inspect',#轨迹视图检视回调
)#属主字段结束

工具调用视图属性=工具调用属主属性#原子工具视图完整 props（加 runtime/locale 由宿主叠）

工具树属性=(#tool-call Chat 节点运行时套件
    'callId','toolName','block','cwd','openFile','inspectCall',
    'renderSlot','selected','children','t','sessionId','useSessions',
)#树 props

工具详情属性=('block','t')#详情工具输出运行时套件与会话文案席
