'向导类型的第一段登记：它是什么'
from ...文案 import 中文
from ...约定.种子 import 向导种类

__all__=['向导标识','向导定义']

向导标识='@deepseek-ai/dsh-client-ui-sidebar-right/guide'


def 向导定义(翻译=None):
    '内建向导。标题每次现读中文表。翻译参数不参与显示'
    def 标题(地址=None):
        '芯片上的字'
        return 中文['tab.guide.title']

    return {
        'id':向导标识,
        'kind':向导种类,
        'priority':'builtin',
        'title':标题,
    }
