from ..文案 import 命名空间
from .助手节点视图 import 助手节点视图
from .命令节点视图 import 命令节点视图,手动压缩节点视图
from .消息项 import (
    上下文消息节点视图,压缩节点视图,回合满令牌节点视图,回合错误节点视图,
    未知节点视图,用户消息节点视图,重试节点视图,
)
from .推理内容 import 推理内容,默认推理体
from .系统提示行 import 系统提示节点视图
from .回合过程节点视图 import 回合过程节点视图
from .回合尾节点视图 import 回合尾节点视图
from .回合触发节点视图 import 回合触发节点视图

__all__=['登记聊天节点渲染器']


def 登记聊天节点渲染器(上下文,性能用量,呈现):
    '把本包的节点渲染器登记到 conversation.chat.node'
    槽=上下文.slots

    def 挂推理内容():
        '推理正文工厂'
        return 槽.registerFactory({
            'name':'conversation.chat.reasoning.content',
            'scope':'root',
            'locale':命名空间,
        },推理内容)

    上下文.副作用(挂推理内容)

    def 挂推理体():
        '默认推理体'
        def 登记():
            '优先级 100'
            return 槽.register({
                'name':'conversation.chat.reasoning.body',
                'priority':100,
            },默认推理体)
        return 槽.inject('conversation.chat.reasoning.body',登记)

    上下文.副作用(挂推理体)

    def 挂(键,组件,子=None,注入面=None):
        '等父槽出现再登记这个键'
        选项={'name':'conversation.chat.node','key':键,'locale':命名空间}
        if 子 is not None:
            选项['children']=子
        if 注入面 is not None:
            选项['inject']=注入面

        def 注入(钉选项=选项,钉组件=组件):
            '登记这一键'
            return 槽.register(钉选项,钉组件)

        槽.inject('conversation.chat.node',注入)

    挂('user',用户消息节点视图)
    挂('steering',用户消息节点视图)
    挂('context',上下文消息节点视图)
    挂('turn-trigger',回合触发节点视图)
    挂('system-prompt',系统提示节点视图)

    def 助手注入():
        '工作步骤展示策略'
        return {'hooks':{'presentation':呈现}}

    挂('assistant-step',助手节点视图,{
        'conversation.chat.reasoning.body':{'kind':'single','scope':'session'},
        'conversation.chat.message.images':{'kind':'single','scope':'session'},
    },助手注入)
    挂('command',命令节点视图,{
        'conversation.chat.commandview':{'kind':'keyed','scope':'session'},
    })
    挂('manual-compaction',手动压缩节点视图)
    挂('compaction',压缩节点视图)
    挂('model-retry',重试节点视图)
    挂('turn-error',回合错误节点视图)
    挂('turn-max-tokens',回合满令牌节点视图)
    挂('turn-process',回合过程节点视图)

    def 尾注入():
        '用量明细偏好'
        return {'hooks':{'performanceUsage':性能用量}}

    挂('turn-tail',回合尾节点视图,{
        'conversation.chat.turnTail':{'kind':'list','scope':'session'},
        'conversation.chat.assistant-actions':{'kind':'list','scope':'session'},
    },尾注入)
    挂('unknown',未知节点视图)
