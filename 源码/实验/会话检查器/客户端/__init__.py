'贡献会话检查器日志侧边栏标签的浏览器插件'

from .文案 import 命名空间,中文,英文
from .视图 import 登记检查器标签

__all__=['依赖','应用']

依赖=['slots','locale','sessions','uiSession','uiConversation','sidebarRightTabs']

def 应用(上下文):
    '在本插件寿命内登记检查器标签'
    def 卸词典():
        '登记词典'
        return 上下文.locale.register(命名空间,{'en':英文,'zh':中文})
    上下文.副作用(卸词典,'session-inspector: dictionaries')
    登记检查器标签(上下文)

inject=依赖
apply=应用
