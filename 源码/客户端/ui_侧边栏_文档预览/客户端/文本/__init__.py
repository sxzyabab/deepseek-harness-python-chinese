from .文本体 import 文本体#正文

__all__=['纯文本体标识','文本体定义','应用','文本体']#仅中文公开名

纯文本体标识='@deepseek-ai/dsh-client-ui-sidebar-documentpreview/text'#实现 id


def 文本体定义(标题):
    """描述纯文本兜底。标题为无参可调用。"""
    return {#元数据
        'id':纯文本体标识,
        'extensions':[],
        'priority':'builtin',
        'title':标题,
        'loading':'text-pages',
        'wrap':True,
    }#定义结束


def 应用(上下文):
    """登记兜底元数据与带键正文。"""
    翻译=上下文.locale.bind('sidebarDocumentPreview')#绑定

    def 登记元数据():
        """挂纯文本元数据。"""
        return 上下文.documentPreviews.register(文本体定义(lambda:翻译('viewer.text')))#登记

    上下文.副作用(登记元数据)#寿命

    def 挂正文():
        """正文进文档子槽。"""

        def 登记正文():
            """登记纯文本正文。"""
            return 上下文.slots.register({#席位
                'name':'sidebar.right.tab.document',
                'key':纯文本体标识,
            },文本体)#正文

        return 上下文.slots.inject('sidebar.right.tab.document',登记正文)#等洞

    上下文.副作用(挂正文)#寿命


apply=应用#框架槽
