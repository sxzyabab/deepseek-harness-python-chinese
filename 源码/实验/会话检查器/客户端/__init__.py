'登记会话检查器的文案和右栏标签'

from .文案 import 命名空间,中文,英文#中英文案表
from .视图 import 登记检查器标签#侧栏页
from . import 文案,视图#同目录模块

__all__=['文案','视图','依赖','应用']#只导出包，不转发里面的类

依赖=['slots','locale','sessions','uiSession','uiConversation','sidebarRightTabs']#登记标签需要的服务

def 应用(上下文,配置=None):
    '在本插件寿命内登记文案和检查器标签'
    def 登记词典():
        '中英文案都登记。页面上的字不走英文表'
        return 上下文.locale.register(命名空间,{'en':英文,'zh':中文})#两份表

    上下文.副作用(登记词典,'session-inspector: dictionaries')#文案寿命
    登记检查器标签(上下文)#侧栏页

inject=依赖#框架槽
apply=应用#框架槽
