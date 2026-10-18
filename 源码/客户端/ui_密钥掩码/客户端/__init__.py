'遮挡已发送用户文本里可识别的凭证。只改显示，不改原文、复制和模型输入'
from .区域文案 import 命名空间,中文文案,英文文案
from .密钥规则 import 创建密钥规则
from .密钥文本 import 呈现

依赖=['locale','slots','uiConversation']

def 应用(上下文,配置=None):
    '登记密钥文本规则'
    def 登记词典():
        '登记遮挡文案'
        return 上下文.locale.register(命名空间,{'zh':中文文案,'en':英文文案})
    上下文.副作用(登记词典,'ui-secret-mask: dictionaries')
    上下文.uiConversation.userText.register(创建密钥规则())
    def 登记节点():
        '用户文本的 secret 节点'
        return 上下文.slots.register({
            'name':'conversation.user.text.node',
            'key':'secret',
            'priority':100,
            'locale':命名空间,
        },呈现)
    上下文.slots.inject('conversation.user.text.node',登记节点)

__all__=['依赖','应用']
inject=依赖#框架槽
apply=应用#框架槽
