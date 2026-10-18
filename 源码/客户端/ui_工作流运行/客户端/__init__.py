from . import 文案
from . import 工作流定义
from . import 面板
from .文案 import 中文,命名空间,英文
from .工作流定义 import 工作流运行定义
from .面板 import 工作流运行面板

__all__=['文案','工作流定义','面板','依赖','应用']

依赖=['uiConversation','uiWorkspace','slots','sessions','locale']#定义、导航、槽、会话、文案

def 应用(上下文,配置=None):
    '登记工作流定义、中英文案表，以及 workflow-run 聊天节点'
    上下文.uiConversation.events.register(工作流运行定义)#定义
    def 登记词表():
        '登记中英文案表。页面显示不读这张表'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词表,'ui-workflow-run: dictionaries')#词表
    def 登记节点():
        '等 conversation.chat.node 出现后登记渲染器'
        def 打开会话(目标):
            '把目标会话交给工作区打开'
            上下文.uiWorkspace.openSession(目标)
            return
        def 注入():
            '打开子会话'
            return {'openSession':打开会话}
        return 上下文.slots.register({
            'name':'conversation.chat.node',#聊天节点
            'key':'workflow-run',#键
            'locale':命名空间,#文案命名空间
            'inject':注入,#打开子会话
        },工作流运行面板)
    上下文.slots.inject('conversation.chat.node',登记节点)#等槽
    return

inject=依赖
apply=应用
