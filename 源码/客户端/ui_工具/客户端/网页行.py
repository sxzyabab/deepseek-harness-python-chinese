from ...ui_基础界面组件.icons import 图标浏览16,图标地球14
from .文案 import 会话命名空间,中文文案
from .网页卡模型 import 网页卡模型,网页获取链接
from .调用模型 import 工具行模型
from .工具行 import 工具行
from .槽 import 槽名工具调用视图

__all__=['网页行','网页工具视图']

class 网页行:
    '展开网页搜索或网页获取'
    def __new__(类,属性):
        '按工具名选图标和标题'
        模型=工具行模型(属性['toolName'],属性['block'])
        名称=属性['toolName']
        if 名称=='web_fetch':
            图标=图标浏览16({'window':属性['window'],'size':14})
        else:
            图标=图标地球14({'window':属性['window'],'size':14})
        if 名称=='web_search':
            标题键='tool.title.webSearch'
        elif 名称=='web_fetch':
            标题键='tool.title.webFetch'
        else:
            标题键=模型['titleKey']
        return 工具行({
            'window':属性['window'],
            'useDisclosure':属性['useDisclosure'],
            'variant':模型['variant'],
            'toolName':名称,
            'icon':图标,
            'title':中文文案(标题键),
            'summary':模型['summary'],
            'output':模型['output'],
            'errorSummary':模型['errorSummary'],
            'web':网页卡模型(属性['block']),
            'href':网页获取链接(属性['block']),
            'state':模型['state'],
            'inspect':属性.get('inspect'),
        })

def 应用网页工具视图(上下文,配置=None):
    '登记 web_search 和 web_fetch'
    def 登记():
        '两个键一起登记'
        yield 上下文.slots.register({
            'name':槽名工具调用视图,'key':'web_search','locale':会话命名空间,
        },网页行)
        yield 上下文.slots.register({
            'name':槽名工具调用视图,'key':'web_fetch','locale':会话命名空间,
        },网页行)
    上下文.slots.inject(槽名工具调用视图,登记)

网页工具视图={
    'name':'web-toolview',
    'inject':['slots'],
    'apply':应用网页工具视图,
}
