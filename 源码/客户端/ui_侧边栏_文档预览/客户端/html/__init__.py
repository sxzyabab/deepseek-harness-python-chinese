"""内置 HTML 元数据与带键正文登记；装配属于包入口。

对齐上游 `ui-sidebar-documentpreview/src/client/html/index.ts`。公开面仅中文名。
"""
from ..远程过程调用 import 宿主文件#宿主文件
from .文案 import 中文,英文,超文本预览键#词典
from .超文本体 import 超文本体#正文

__all__=['超文本体标识','超文本体定义','应用','超文本体','中文','英文','超文本预览键']#仅中文公开名

超文本体标识='@deepseek-ai/dsh-client-ui-sidebar-documentpreview/html'#实现 id


def 超文本体定义(标题):
    """描述内置 HTML 渲染器的文件类型与加载模式。"""
    return {#元数据
        'id':超文本体标识,
        'extensions':['html','htm'],
        'priority':'builtin',
        'title':标题,
        'loading':'bytes-complete',
        'wrap':False,
    }#结束


def 应用(上下文):
    """登记 HTML 词典、元数据与正文。"""
    翻译=上下文.locale.bind('documentHtml')#绑定

    def 登记词典():
        """挂 HTML 词典。"""
        return 上下文.locale.register('documentHtml',{'zh':中文,'en':英文})#登记

    上下文.副作用(登记词典)#寿命

    def 登记元数据():
        """挂 HTML 元数据。"""
        return 上下文.documentPreviews.register(超文本体定义(lambda:翻译('title')))#登记

    上下文.副作用(登记元数据)#寿命

    def 挂正文():
        """正文进文档子槽。"""

        def 登记正文():
            """登记 HTML 正文。"""
            def 注入():
                """绑定关联读取。"""
                def 关联读取(地址,相对路径,信号):
                    """经 Host 相对根 HTML 读取依赖。"""
                    文件=宿主文件(地址)#宿主文件
                    return 上下文.remote.workspaceFiles.readRelated(文件['sessionId'],文件['path'],相对路径,信号)#结果

                return {'readRelated':关联读取}#注入

            return 上下文.slots.register({#席位
                'name':'sidebar.right.tab.document',
                'key':超文本体标识,
                'locale':'documentHtml',
                'inject':注入,#关联读
            },超文本体)#正文

        return 上下文.slots.inject('sidebar.right.tab.document',登记正文)#等洞

    上下文.副作用(挂正文)#寿命


apply=应用#框架槽
