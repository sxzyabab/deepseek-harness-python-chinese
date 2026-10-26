'登记引用准入、选区按钮和字面引用'
from .文案 import 中文,命名空间,日文,俄文,德文,英文,法文,葡萄牙文,西班牙文
from .引用规则 import 引用规则 as 引用规则值
from .引用选择 import 引用选择动作
from .已引用用户文本 import 已引用用户文本
from . import 文案,引用文本,引用规则,引用选择,已引用用户文本

__all__=['文案','引用文本','引用规则','引用选择','已引用用户文本','名称','依赖','应用']

名称='message-quotes'
依赖=['slots','locale','sessions','uiConversation']
inject=依赖


def 应用(上下文,配置值=None):
    '登记词典、引用规则、选区交互、选区按钮和用户文本节点'

    def 登记词典():
        '登记八种语言'
        return 上下文.locale.register(命名空间,{
            'zh':中文,'en':英文,'ja':日文,'es':西班牙文,
            'fr':法文,'de':德文,'ru':俄文,'pt':葡萄牙文,
        })

    上下文.副作用(登记词典,'message-quotes: dictionaries')

    def 登记规则():
        '用户文本里的引用规则'
        return 上下文.uiConversation.userText.register(引用规则值)

    上下文.副作用(登记规则,'message-quotes: UserText rule')

    def 取(请求,名):
        '交互请求是字典或带方法的对象'
        if isinstance(请求,dict):
            return 请求.get(名)
        return getattr(请求,名)

    def 交互(请求):
        '选区有文字，并且这一会话还能继续，才打开引用'
        读文字=取(请求,'readText')
        if 取(请求,'trigger')!='selection' or not callable(读文字) or 读文字() is None:
            return
        绑定=上下文.sessions.binding(取(请求,'sessionId'))
        if 绑定 is None:
            return
        会话=绑定['session'].getSnapshot()
        子=会话.get('subagent')
        if 会话.get('removed') is True:
            return
        if 子 is not None:
            地址=子.get('address') if isinstance(子,dict) else None
            if not isinstance(地址,dict) or 地址.get('mode')!='continuable' or 子.get('parentAvailable') is not True:
                return
        打开=取(请求,'open')
        if callable(打开):
            打开()

    def 登记交互():
        '选区交互'
        return 上下文.uiConversation.interactions.register({
            'id':'quote',
            'onInteraction':交互,
        })

    上下文.副作用(登记交互,'message-quotes: selection interaction')

    def 登记选择():
        '选区上的引用按钮'
        return 上下文.slots.register({
            'name':'conversation.chat.text-interaction',
            'key':'quote',
            'locale':命名空间,
        },引用选择动作)

    上下文.slots.inject('conversation.chat.text-interaction',登记选择)

    def 登记节点():
        '用户文本里的引用节点'
        return 上下文.slots.register({
            'name':'conversation.user.text.node',
            'key':'quote',
            'priority':100,
        },已引用用户文本)

    上下文.slots.inject('conversation.user.text.node',登记节点)


name=名称
apply=应用
