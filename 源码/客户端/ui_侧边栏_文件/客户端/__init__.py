from .文案 import 中文,英文,侧栏文件文案键#词典
from .定义 import 文件种类,文件标识,文件定义#类型定义
from .存储 import 文件树错误,创建文件存储#视图存储
from .面 import 已中止,创建列举,子路径,文件面#列举面
from .文件体 import (#正文视图模型
    排序条目,
    失败行,
    工作区标题,
    文件资源地址,
    文件体,
    样式表,
)#文件体导出结束
from .文件标题 import 文件标题#芯片标题

__all__=[#仅中文公开名
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

命名空间='sidebarFiles'#本包文案命名空间（线路字面量）
依赖=['slots','locale','sidebarRightTabs','remote','remote.workspaceFiles']#槽、文案、右侧标签、Remote


def 应用(上下文):
    """登记类型、词典，再挂正文。"""
    翻译=上下文.locale.bind(命名空间)#命名空间绑定翻译

    def 登记类型():
        """把 files 类型挂进右侧侧栏注册表。"""
        return 上下文.sidebarRightTabs.register(文件定义(翻译))#登记类型

    上下文.副作用(登记类型,'ui-sidebar-files: files type')#类型寿命

    def 登记词典():
        """挂载中英文案。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记

    上下文.副作用(登记词典,'ui-sidebar-files: dictionaries')#词典寿命

    存储=创建文件存储()#每会话独占，登记时铸造
    注入面=文件面(创建列举(上下文.remote))#Remote 列举 → 注入工厂

    def 挂正文():
        """正文进带键席位。"""
        def 登记正文():
            """登记 files 正文。"""
            return 上下文.slots.register({#席位
                'name':'sidebar.right.pane.tab',#席名
                'key':文件标识,#实现键
                'locale':命名空间,#文案
                'store':存储,#独占存储
                'inject':注入面,#业务面工厂
            },文件体)#正文组件
        return 上下文.slots.inject('sidebar.right.pane.tab',登记正文)#等洞就绪

    上下文.副作用(挂正文,'ui-sidebar-files: files tab body')#正文寿命

    def 挂标题():
        """芯片标题进带键席位。"""
        def 登记标题():
            """登记 files 芯片标题。"""
            return 上下文.slots.register({#席位
                'name':'sidebar.right.pane.tab.title',#席名
                'key':文件标识,#实现键
            },文件标题)#标题组件
        return 上下文.slots.inject('sidebar.right.pane.tab.title',登记标题)#等洞就绪

    上下文.副作用(挂标题,'ui-sidebar-files: files tab title')#标题寿命


inject=依赖#框架槽
apply=应用#框架槽
