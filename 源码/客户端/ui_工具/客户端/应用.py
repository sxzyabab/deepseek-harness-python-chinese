from .文案 import 会话命名空间
from .工具调用树 import 工具调用树
from .bash样例 import bash工具视图样例
from .读行 import 读工具视图
from .读取图像表行 import 读图像工具视图
from .文件变更行 import 文件变更工具视图
from .检索行 import 检索工具视图
from .网页行 import 网页工具视图
from .待办行 import 待办工具视图
from .细节列表表行 import 细节工具视图
from .提问行 import 提问工具视图
from .槽 import 槽名聊天节点,槽名工具调用视图

__all__=['依赖','应用']

依赖=['slots','remote']

def 应用(上下文,配置=None):
    '登记整段工具渲染和内置原子视图'
    def 取宿主():
        '当前宿主事实'
        return 上下文.remote.宿主事实()
    def 订宿主(监听):
        '连接重置时通知'
        return 上下文.监听('connection/reset',监听)
    宿主信息={'getSnapshot':取宿主,'subscribe':订宿主}
    def 工具注入():
        '宿主事实走钩子，避免登记时冻住'
        return {'hooks':{'hostInfo':宿主信息}}
    def 登记调用树():
        '按 tool-call 登记调用树，并声明按键子槽'
        return 上下文.slots.register({
            'name':槽名聊天节点,
            'key':'tool-call',
            'locale':会话命名空间,
            'children':{
                槽名工具调用视图:{'kind':'keyed','scope':'session'},
            },
            'inject':工具注入,
        },工具调用树)
    上下文.slots.inject(槽名聊天节点,登记调用树)
    上下文.启动插件(bash工具视图样例)
    上下文.启动插件(读工具视图)
    上下文.启动插件(读图像工具视图)
    上下文.启动插件(文件变更工具视图)
    上下文.启动插件(检索工具视图)
    上下文.启动插件(网页工具视图)
    上下文.启动插件(待办工具视图)
    上下文.启动插件(细节工具视图)
    上下文.启动插件(提问工具视图)

inject=依赖
apply=应用
