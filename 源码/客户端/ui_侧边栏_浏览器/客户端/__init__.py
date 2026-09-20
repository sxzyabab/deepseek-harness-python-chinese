from .文案 import 中文,英文,侧栏浏览器文案键#词典
from .定义 import 浏览器种类,浏览器标识,浏览器定义#类型定义
from .浏览器.存储 import 创建浏览器存储#视图存储
from .浏览器.控制 import 创建浏览器控制表#控制器表
from .浏览器.地址 import 解析浏览器地址,最大地址字节#地址
from .浏览器.导航 import 浏览器导航,最大历史条数#导航
from .视图.浏览器体 import 浏览器体,网页沙箱令牌#正文
from .视图.浏览器标题 import 浏览器标题#标题

__all__=[#仅中文公开名
    '依赖','应用','命名空间','中文','英文','侧栏浏览器文案键',
    '浏览器种类','浏览器标识','浏览器定义',
    '创建浏览器存储','创建浏览器控制表',
    '解析浏览器地址','最大地址字节',
    '浏览器导航','最大历史条数',
    '浏览器体','网页沙箱令牌','浏览器标题',
]

命名空间='sidebarBrowser'#本包文案命名空间（线路字面量）
依赖=['slots','locale','sidebarRightTabs']#槽、文案、右侧标签

def 应用(上下文):
    """登记浏览器类型、词典、正文与芯片标题。"""
    翻译=上下文.locale.bind(命名空间)#绑定词表
    存储=创建浏览器存储()#每会话独占

    def 登记词典():
        """挂载中英文案。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记

    上下文.副作用(登记词典,'ui-sidebar-browser.copy')#词典寿命

    def 登记类型():
        """把 browser 类型挂进右侧侧栏注册表。"""
        return 上下文.sidebarRightTabs.register(浏览器定义(翻译))#登记

    上下文.副作用(登记类型,'ui-sidebar-browser.type')#类型寿命

    def 挂正文():
        """正文进带键席位。"""

        def 登记正文():
            """登记 browser 正文。"""
            return 上下文.slots.register({#席位
                'name':'sidebar.right.pane.tab',#席名
                'key':浏览器标识,#实现键
                'locale':命名空间,#文案
                'store':存储,#独占存储
                'inject':lambda _会话,动作:创建浏览器控制表(动作),#注入面
            },浏览器体)#正文组件

        return 上下文.slots.inject('sidebar.right.pane.tab',登记正文)#等洞就绪

    上下文.副作用(挂正文,'ui-sidebar-browser.body')#正文寿命

    def 挂标题():
        """芯片标题进带键席位。"""

        def 登记标题():
            """登记 browser 标题。"""
            return 上下文.slots.register({#席位
                'name':'sidebar.right.pane.tab.title',#席名
                'key':浏览器标识,#实现键
                'store':存储,#共享存储
            },浏览器标题)#标题组件

        return 上下文.slots.inject('sidebar.right.pane.tab.title',登记标题)#等洞就绪

    上下文.副作用(挂标题,'ui-sidebar-browser.title')#标题寿命

inject=依赖#框架槽
apply=应用#框架槽
