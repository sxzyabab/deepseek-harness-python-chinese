"""内置 Markdown 元数据与带键文档正文登记。

对齐上游 `ui-sidebar-documentpreview/src/client/markdown/index.ts`。公开面仅中文名。
"""
from .文案 import 中文,英文,标记文本预览键#词典
from .标记文本体 import 标记文本体#正文

__all__=['标记文本体标识','标记文本定义','应用','标记文本体','中文','英文','标记文本预览键']#仅中文公开名

标记文本体标识='@deepseek-ai/dsh-client-ui-sidebar-documentpreview/markdown'#实现 id


def 标记文本定义(标题):
    """描述 Markdown 实现而不接管加载。"""
    return {#元数据
        'id':标记文本体标识,
        'extensions':['md','markdown'],
        'priority':'builtin',
        'title':标题,
        'loading':'text-pages',
        'wrap':False,
    }#结束


def 应用(上下文):
    """登记文案、元数据与文档正文。"""
    翻译=上下文.locale.bind('documentMarkdown')#绑定

    def 登记词典():
        """挂 Markdown 词典。"""
        return 上下文.locale.register('documentMarkdown',{'zh':中文,'en':英文})#登记

    上下文.副作用(登记词典,'document-markdown: dictionaries')#寿命

    def 登记元数据():
        """挂 Markdown 元数据。"""
        return 上下文.documentPreviews.register(标记文本定义(lambda:翻译('viewer.label')))#登记

    上下文.副作用(登记元数据,'document-markdown: metadata')#寿命

    def 挂正文():
        """正文进文档子槽。"""

        def 登记正文():
            """登记 Markdown 正文。"""
            return 上下文.slots.register({#席位
                'name':'sidebar.right.tab.document',
                'key':标记文本体标识,
                'locale':'documentMarkdown',
            },标记文本体)#正文

        return 上下文.slots.inject('sidebar.right.tab.document',登记正文)#等洞

    上下文.副作用(挂正文,'document-markdown: body')#寿命


apply=应用#框架槽
