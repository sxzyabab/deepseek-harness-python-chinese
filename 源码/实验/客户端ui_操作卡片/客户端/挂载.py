'登记卡片框架、提议行、文案和正文注册表'
from .文案 import 中文,日文,俄文,德文,英文,法文,葡萄牙文,西班牙文
from .注册表 import 操作卡片注册表
from .卡片 import 操作卡片尾
from .提议行 import 提议行

__all__=['依赖','挂载操作卡片']

依赖=['slots','locale','remote']


def 远程值(结果):
    '成功时取出 value。回复丢失时是 None'
    if isinstance(结果,dict) and 结果.get('ok') is True:
        return 结果.get('value')
    if isinstance(结果,dict) and 'ok' in 结果:
        return None
    return 结果


def 登记界面(上下文,注册表):
    '词典、回合尾和提议行跟这一界面纤程走'

    def 登记词典():
        '登记八种语言。界面显示走当前语言'
        return 上下文.locale.register('actionCards',{
            'en':英文,'zh':中文,'ja':日文,'es':西班牙文,
            'fr':法文,'de':德文,'ru':俄文,'pt':葡萄牙文,
        })

    上下文.副作用(登记词典,'action-cards: locale')

    def 注入尾(会话标识):
        '这一会话上的正文表、翻译和操作'

        def 行动(调用号,动词,载荷=None):
            '把用户操作发给这一会话的卡片'
            结果=上下文.remote.actionCards.act(会话标识,调用号,动词,载荷)
            return 远程值(结果)

        return {
            'sessionId':会话标识,
            'hooks':{'bodies':注册表.来源},
            'bind':上下文.locale.bind,
            'act':行动,
        }

    def 登记尾():
        '等回合尾槽出现再登记'
        return 上下文.slots.register({
            'name':'conversation.chat.turnTail',
            'id':'@deepseek-ai/dsh-client-ui-action-cards',
            'locale':'actionCards',
            'inject':注入尾,
        },操作卡片尾)

    上下文.slots.inject('conversation.chat.turnTail',登记尾)

    def 登记行():
        '提议调用的过程行'
        return 上下文.slots.register({
            'name':'tool.call.toolview',
            'key':'propose_action',
            'locale':'actionCards',
        },提议行)

    上下文.slots.inject('tool.call.toolview',登记行)


def 挂载操作卡片(上下文,贡献):
    '先提供正文注册表，再挂 Remote 和界面。卸的时候界面先走'
    注册表=操作卡片注册表(上下文)
    上下文.提供服务('actionCards',注册表)
    卸远程=getattr(上下文.remote,'$mount')(贡献)
    界面=None
    try:
        def 启动界面(子上下文,配置值=None):
            'Remote 方法出现后再登记界面'
            return 登记界面(子上下文,注册表)
        界面=上下文.依赖启动(['remote.actionCards'],启动界面)
        界面.等待()
    except Exception as 错误:
        if 界面 is not None:
            界面.拆除()
        if callable(卸远程):
            卸远程()
        raise 错误

    def 卸下():
        '先卸界面，再卸 Remote'
        界面.拆除()
        if callable(卸远程):
            卸远程()

    return 卸下
