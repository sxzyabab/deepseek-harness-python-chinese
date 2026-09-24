from .文案 import 中文,英文,侧栏文件文案键
from .定义 import 文件种类,文件标识,文件定义
from .存储 import 文件树错误,创建文件存储
from .面 import 已中止,创建列举,子路径,文件面
from .文件体 import (
    排序条目,
    失败行,
    工作区标题,
    文件资源地址,
    文件体,
    样式表,
)
from .文件标题 import 文件标题

__all__=[
    '依赖',
    '应用',
    '命名空间',
    '中文',
    '英文',
    '侧栏文件文案键',
    '文件种类',
    '文件标识',
    '文件定义',
    '文件树错误',
    '创建文件存储',
    '已中止',
    '创建列举',
    '子路径',
    '文件面',
    '排序条目',
    '失败行',
    '工作区标题',
    '文件资源地址',
    '文件体',
    '样式表',
    '文件标题',
]

#常量
#线路字面量：文案命名空间
命名空间='sidebarFiles'
依赖=['slots','locale','sidebarRightTabs','remote','remote.workspaceFiles']

#
def 应用(上下文):
    """登记类型与词典，再挂正文和芯片标题。存储按会话铸造，不在这里实例化。"""
    翻译=上下文.locale.bind(命名空间)

    def 登记类型():
        """把 files 类型挂进右侧侧栏注册表。"""
        return 上下文.sidebarRightTabs.register(文件定义(翻译))

    上下文.副作用(登记类型,'ui-sidebar-files: files type')

    def 登记词典():
        """挂载中英文案。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})

    上下文.副作用(登记词典,'ui-sidebar-files: dictionaries')

    存储=创建文件存储()
    注入面=文件面(创建列举(上下文.remote))

    def 挂正文():
        """正文进带键席位，等洞就绪再登记。"""
        def 登记正文():
            """登记 files 正文。"""
            return 上下文.slots.register({
                'name':'sidebar.right.pane.tab',
                'key':文件标识,
                'locale':命名空间,
                'store':存储,
                'inject':注入面,
            },文件体)
        return 上下文.slots.inject('sidebar.right.pane.tab',登记正文)

    上下文.副作用(挂正文,'ui-sidebar-files: files tab body')

    def 挂标题():
        """芯片标题进带键席位。"""
        def 登记标题():
            """登记 files 芯片标题。"""
            return 上下文.slots.register({
                'name':'sidebar.right.pane.tab.title',
                'key':文件标识,
            },文件标题)
        return 上下文.slots.inject('sidebar.right.pane.tab.title',登记标题)

    上下文.副作用(挂标题,'ui-sidebar-files: files tab title')


#框架槽
inject=依赖
apply=应用
