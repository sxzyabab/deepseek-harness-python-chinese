"""浏览器半边：把 `text` 登记为右侧侧栏 tab 类型。

对齐上游 `ui-sidebar-textpreview/src/client/index.ts`。公开面仅中文名。
类型只经公开路径到达侧栏：定义进 `ctx.sidebarRightTabs`，正文进定义 `id` 下的
键控 `sidebar.right.pane.tab` 席。不伸进侧栏存储、窗格或序列。
文件元数据来自标准资源面，由 `file` 提供方供给；文本是本类型自持业务，经面一次一页读取。
"""
from .文案 import 中文,英文,侧栏文本预览文案键#词典
from .定义 import 文本预览种类,文本预览标识,取基名,文本定义#类型定义
from .读页 import 文本预览错误,解析文件地址,宿主文件于,创建读页#分页读
from .存储 import 空白页态,创建文本预览存储#预览存储
from .面 import 已中止,文本面#异步面
from .失败行 import 可读字节,失败行#失败说明
from .图标 import 图标换行线16#换行图标
from .文本预览 import (#正文
    页行列表,
    已载页列表,
    已载末行,
    文本预览,
    样式表,
)#正文导出结束

__all__=[#仅中文公开名
    '注入','应用','命名空间',
    '中文','英文','侧栏文本预览文案键',
    '文本预览种类','文本预览标识','取基名','文本定义',
    '文本预览错误','解析文件地址','宿主文件于','创建读页',
    '空白页态','创建文本预览存储',
    '已中止','文本面',
    '可读字节','失败行',
    '图标换行线16',
    '页行列表','已载页列表','已载末行','文本预览','样式表',
]#公开面结束

命名空间='sidebarTextpreview'#本包词典命名空间（线路字面量）
注入=['slots','locale','sidebarRightTabs','remote','remote.workspaceFiles']#槽位、文案、右侧 tab、远程


def 应用(上下文):
    """登记类型、词典与正文。"""

    def 登记类型():
        """登记 text 类型定义。"""
        return 上下文.sidebarRightTabs.register(文本定义())#登记

    上下文.副作用(登记类型,'ui-sidebar-textpreview: text type')#类型

    def 登记词典():
        """登记中英文案。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记

    上下文.副作用(登记词典,'ui-sidebar-textpreview: dictionaries')#词典

    存储=创建文本预览存储()#共享存储规格
    面=文本面(创建读页(上下文.remote))#绑定读页

    def 挂正文():
        """等右侧 tab 席出现再登记正文。"""

        def 登记():
            """登记键控正文。"""
            return 上下文.slots.register({#席位登记
                'name':'sidebar.right.pane.tab',#席名
                'key':文本预览标识,#实现键
                'locale':命名空间,#文案
                'store':存储,#预览存储
                'inject':面,#异步面
            },文本预览)#正文组件

        return 上下文.slots.inject('sidebar.right.pane.tab',登记)#等席

    上下文.副作用(挂正文,'ui-sidebar-textpreview: text body')#正文


inject=注入#框架槽
apply=应用#框架槽
