"""会话槽声明及其组合后的组件 props。

对齐上游 `ui-conversation/src/client/contract/slots.ts`。公开面仅中文名。
TypeScript 声明合并的 SlotMap / SessionStandardProps 在此以子槽表与注释面保留；
可执行域面仅 `待决审批`。
"""
__all__=[#仅中文公开名
    '撰写附件','英雄智能体预设属主','会话体属主','页眉动作属主',
    '输入区','视图属主','聊天文件提及','回合尾属主','助手动作属主','聊天节点属主',
    '详情工具属主','命令行属主','会话根注入','会话体注入','会话页眉注入',
    '撰写栏属主','撰写栏注入','输入控件属主','撰写链属主','聊天滚动位置','聊天视图注入',
    '详情注入','空白工作区属主','审批等待','待决审批','会话根子槽','聊天节点回合注入',
    '槽名主会话','槽名会话','槽名会话体','槽名页眉','槽名视图','槽名聊天节点','槽名命令视图',
    '槽名回合尾','槽名助手动作','槽名详情工具','槽名撰写链','槽名撰写栏','槽名输入停靠',
    '槽名撰写停靠','槽名输入左','槽名输入右','槽名计划','槽名模型','槽名英雄工作区',
    '槽名英雄预设','槽名输入叠层','槽名详情','对话错误',
]#公开面结束

槽名主会话='main.conversation'#主面板会话壳
槽名会话='conversation'#历史根别名（文档/旧登记）
槽名会话体='conversation.session'#严格会话体
槽名页眉='conversation.session.header'#页眉
槽名视图='conversation.view'#视图环
槽名聊天节点='conversation.chat.node'#键控节点
槽名命令视图='conversation.chat.commandview'#命令行
槽名回合尾='conversation.chat.turnTail'#回合尾
槽名助手动作='conversation.chat.assistant-actions'#助手动作
槽名详情工具='conversation.details.tool'#详情工具
槽名撰写链='conversation.composer'#撰写接管链
槽名撰写栏='conversation.composer.bar'#默认栏
槽名输入停靠='conversation.input.dock'#卡片上方停靠
槽名撰写停靠='conversation.composer.dock'#卡片下方停靠
槽名输入左='conversation.input.left'#工具行左
槽名输入右='conversation.input.right'#工具行右
槽名计划='conversation.input.plan'#计划席
槽名模型='conversation.input.model'#模型席
槽名英雄工作区='conversation.hero.workspace'#英雄工作区
槽名英雄预设='conversation.hero.agentPreset'#英雄预设
槽名输入叠层='conversation.input.overlay'#输入叠层
槽名详情='details'#详情栏

会话根子槽={#主会话壳 children 表
    'conversation.session':{'kind':'single','scope':'session'},#严格会话体
    'conversation.session.header':{'kind':'single','scope':'session'},#页眉
    'conversation.composer':{'kind':'chain','scope':'session'},#撰写链
    'conversation.composer.bar':{'kind':'single','scope':'session-maybe'},#栏
    'conversation.input.overlay':{'kind':'list','scope':'session'},#叠层
    'conversation.input.dock':{'kind':'list','scope':'session'},#输入停靠
    'conversation.composer.dock':{'kind':'list','scope':'session'},#撰写停靠
    'conversation.input.left':{'kind':'list','scope':'session'},#左
    'conversation.input.right':{'kind':'list','scope':'session'},#右
    'conversation.hero.workspace':{'kind':'single','scope':'root'},#英雄工作区
    'conversation.hero.agentPreset':{'kind':'single','scope':'root'},#英雄预设
    'conversation.hero.brand.mark':{'kind':'single','scope':'root'},#英雄品牌
}#子槽结束

#撰写附件：kind/id/file/previewUrl
#英雄智能体预设属主：芯片自管，禁止 children
#会话体属主：可选 wrapActiveBody
#页眉动作属主：空份额，控件自给自足
#输入区：session + input 瞬时快照
#视图属主：inspect / onInspectDone
#聊天文件提及：forClosing(回合尾属主)
#回合尾属主：turn / seq / openFile
#助手动作属主：messageId
#聊天节点属主：selectedCallId / cwd / openFile / inspectCall / forkAt / loadImage / fileMentions
#详情工具属主：block / cwd
#命令行属主：node / compaction
#会话根注入：selectWorkspace(经 openWorkspace，打开前 beforeOpen 迁移草稿) + hooks.composerBlock
#会话体注入：views / releaseSessionImages / bindDraftMirror
#会话页眉注入：views / open
#撰写栏属主：variant / blocked / disabled / workspacePickerOpen / …
#撰写栏注入：keyboard / addFiles / … / hooks.busyEnter / fileUploads / …
#输入控件属主：locked
#撰写链属主：interactions / session
#聊天滚动位置：anchorKey / anchorTop / scrollTop
#聊天视图注入：openDetails / openFile / loadOlder / loadImage / inspectCall / chatScroll / forkAt / fileMentions
#详情注入：closeDetails
#空白工作区属主：open / anchorRef / selectedId / onPick / onClose
撰写附件=dict#composer 草稿图片形
英雄智能体预设属主=dict#英雄预设属主形
会话体属主=dict#会话体属主形
页眉动作属主=dict#页眉动作属主形
输入区=dict#输入区属主形
视图属主=dict#视图属主形
聊天文件提及=dict#散文提及服务形
回合尾属主=dict#回合尾属主形
助手动作属主=dict#助手动作属主形
聊天节点属主=dict#聊天节点属主形
详情工具属主=dict#详情工具属主形
命令行属主=dict#命令行属主形
会话根注入=dict#根注入形
会话体注入=dict#体注入形
会话页眉注入=dict#页眉注入形
撰写栏属主=dict#栏属主形
撰写栏注入=dict#栏注入形
输入控件属主=dict#计划/模型属主形
撰写链属主=dict#链属主形
聊天滚动位置=dict#滚动记忆形
聊天视图注入=dict#聊天视图注入形
详情注入=dict#详情注入形
空白工作区属主=dict#空白工作区属主形
审批等待=dict#PendingWait<'approval'> 形

聊天节点回合注入={#CHAT_NODE_INJECT 形状说明
    'hooks':{'turnData':'SlotHookFactory'},#按节点读回合数据
}#注入形结束

class 对话错误(Exception):
    """审批回执与槽面失败。"""
    def __init__(自身,消息,原因=None):
        """记下英文消息与可选结构原因。"""
        super().__init__(消息)#消息原样英文
        自身.reason=原因#结构原因

class 待决审批:
    """渲染身份与问题材料透明转发；answer 拥有线上编码。载体为跨包 dict。"""
    def __init__(自身,等待):
        """记下一次待决审批的运行时载体。"""
        自身.等待=等待#载体

    @property#只读
    def key(自身):
        """不透明渲染键，从载体转发。"""
        return 自身.等待['key']#key

    @property#只读
    def toolName(自身):
        """问题所涉工具，从载荷转发。"""
        return 自身.等待['payload']['toolName']#toolName

    @property#只读
    def reason(自身):
        """人类可读 WHY，从载荷转发。"""
        载荷=自身.等待['payload']#载荷
        return 载荷['reason'] if 'reason' in 载荷 else None#reason

    @property#只读
    def callId(自身):
        """命令行查找键，从载荷转发。"""
        载荷=自身.等待['payload']#载荷
        return 载荷['callId'] if 'callId' in 载荷 else None#callId

    def answer(自身,结果):
        """被拒绝的载体回执会抛。respond 返回任务。"""
        回执=自身.等待.respond({#投递审批响应
            'ok':True,#成功路径
            'value':{#会话、审批 id 与结果
                'sessionId':自身.等待['sessionId'],#会话
                'approvalId':自身.等待['payload']['approvalId'],#审批 id
                'outcome':结果,#allowed-once / rejected
            },#value 结束
        }).等待()#respond 结束
        if 回执['accepted'] is not True:
            原因=回执['reason'] if 'reason' in 回执 else None#拒绝原因
            raise 对话错误('approval response rejected: '+str(原因),原因=原因)#抛
