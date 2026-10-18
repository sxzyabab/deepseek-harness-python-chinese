'纯文本实现，走和别的查看器同一套文档扩展点'
from ..文案 import 中文
from .文本体 import 文本体

__all__=['纯文本体标识','应用']

纯文本体标识='@deepseek-ai/dsh-client-ui-sidebar-documentpreview/text'

def 应用(上下文,配置=None):
    '登记纯文本回落的元数据和带键正文'
    def 标题():
        '实现名。用中文表原文，是纯文本'
        return 中文['viewer.text']
    def 登记元数据():
        '登记空后缀的 builtin 回落'
        return 上下文.documentPreviews.登记({
            'id':纯文本体标识,
            'extensions':[],
            'priority':'builtin',
            'title':标题,
            'loading':'text-pages',
            'wrap':True,
        })
    上下文.副作用(登记元数据)
    def 登记正文():
        '挂上 sidebar.right.tab.document 的纯文本键'
        def 登记():
            '登记文本体'
            return 上下文.slots.register({
                'name':'sidebar.right.tab.document',
                'key':纯文本体标识,
            },文本体)
        return 上下文.slots.inject('sidebar.right.tab.document',登记)
    上下文.副作用(登记正文)
