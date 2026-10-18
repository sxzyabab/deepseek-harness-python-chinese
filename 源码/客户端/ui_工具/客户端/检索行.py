from ...ui_基础界面组件.icons import 图标检索16
from .文案 import 会话命名空间,中文文案
from .检索卡模型 import 检索卡模型
from .调用模型 import 工具行模型
from .工具行 import 工具行
from .槽 import 槽名工具调用视图

__all__=['检索行','检索工具视图']

class 检索行:
    '展开 grep 或 glob。被截断的结果保留恢复定位'
    def __new__(类,属性):
        '交给工具行'
        模型=工具行模型(属性['toolName'],属性['block'])
        名称=属性['toolName']
        if 名称=='grep':
            标题键='tool.title.grep'
        elif 名称=='glob':
            标题键='tool.title.glob'
        else:
            标题键=模型['titleKey']
        return 工具行({
            'window':属性['window'],
            'useDisclosure':属性['useDisclosure'],
            'variant':模型['variant'],
            'toolName':名称,
            'icon':图标检索16({'window':属性['window'],'size':14}),
            'title':中文文案(标题键),
            'summary':模型['summary'],
            'output':模型['output'],
            'errorSummary':模型['errorSummary'],
            'search':检索卡模型(属性['block']),
            'state':模型['state'],
            'inspect':属性.get('inspect'),
        })

def 应用检索工具视图(上下文,配置=None):
    '登记 grep 和 glob'
    def 登记():
        '两个键一起登记'
        yield 上下文.slots.register({
            'name':槽名工具调用视图,'key':'grep','locale':会话命名空间,
        },检索行)
        yield 上下文.slots.register({
            'name':槽名工具调用视图,'key':'glob','locale':会话命名空间,
        },检索行)
    上下文.slots.inject(槽名工具调用视图,登记)

检索工具视图={
    'name':'search-toolview',
    'inject':['slots'],
    'apply':应用检索工具视图,
}
