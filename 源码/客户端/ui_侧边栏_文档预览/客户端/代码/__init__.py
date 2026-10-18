'代码预览的元数据和正文'
from ....ui_基础界面组件.代码高亮语法 import 代码高亮扩展名
from .文案 import 中文,英文
from .代码体 import 代码体

__all__=['文案','代码体','应用']

标识='@deepseek-ai/dsh-client-ui-sidebar-documentpreview/code'
命名空间='sidebarCodePreview'

def 应用(上下文,配置=None):
    '登记本地化元数据和对应的文档正文'
    def 登记词典():
        '登记中英文案表。页面显示不走英文表'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词典)
    def 标题():
        '实现名。是代码'
        return 中文['title']
    def 登记元数据():
        '后缀跟代码高亮表'
        return 上下文.documentPreviews.登记({
            'id':标识,
            'extensions':代码高亮扩展名,
            'priority':'builtin',
            'title':标题,
            'loading':'text-pages',
            'wrap':True,
        })
    上下文.副作用(登记元数据)
    def 登记正文():
        '挂上代码正文'
        def 登记():
            '登记代码体'
            return 上下文.slots.register({
                'name':'sidebar.right.tab.document',
                'key':标识,
                'locale':命名空间,
            },代码体)
        return 上下文.slots.inject('sidebar.right.tab.document',登记)
    上下文.副作用(登记正文)
