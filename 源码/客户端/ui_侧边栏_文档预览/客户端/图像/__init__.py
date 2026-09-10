"""内置图片元数据与带键文档正文登记。

对齐上游 `ui-sidebar-documentpreview/src/client/image/index.ts`。公开面仅中文名。
"""
from .文案 import 中文,英文,图像预览键#词典
from .图像体 import 图像体,图像扩展名#正文

__all__=['图像体标识','图像体定义','应用','图像体','图像扩展名','中文','英文','图像预览键']#仅中文公开名

图像体标识='@deepseek-ai/dsh-client-ui-sidebar-documentpreview/image'#实现 id


def 图像体定义(标题):
    """描述内置图片渲染器。"""
    return {#元数据
        'id':图像体标识,
        'extensions':图像扩展名,
        'priority':'builtin',
        'title':标题,
        'loading':'bytes-complete',
        'wrap':False,
    }#结束


def 应用(上下文):
    """登记图片词典、元数据与正文。"""
    翻译=上下文.locale.bind('sidebarImage')#绑定

    def 登记词典():
        """挂图片词典。"""
        return 上下文.locale.register('sidebarImage',{'zh':中文,'en':英文})#登记

    上下文.副作用(登记词典,'document-image: dictionaries')#寿命

    def 登记元数据():
        """挂图片元数据。"""
        return 上下文.documentPreviews.register(图像体定义(lambda:翻译('title')))#登记

    上下文.副作用(登记元数据,'document-image: metadata')#寿命

    def 挂正文():
        """正文进文档子槽。"""

        def 登记正文():
            """登记图片正文。"""
            return 上下文.slots.register({#席位
                'name':'sidebar.right.tab.document',
                'key':图像体标识,
                'locale':'sidebarImage',
            },图像体)#正文

        return 上下文.slots.inject('sidebar.right.tab.document',登记正文)#等洞

    上下文.副作用(挂正文,'document-image: body')#寿命


apply=应用#框架槽
