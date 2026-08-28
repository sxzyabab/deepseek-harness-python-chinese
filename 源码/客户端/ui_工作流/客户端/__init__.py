"""浏览器插件：持久化工作流运行会话节点。

对齐上游 `ui-workflow-run/src/client/index.ts`。公开面仅中文名。
"""
from .文案 import 命名空间,中文,英文#词典
from .工作流定义 import 工作流运行定义,取字段#Definition
from .工作流运行面板 import 工作流运行面板#按键渲染器

__all__=['注入','应用','工作流运行定义','工作流运行面板','命名空间','中文','英文']#仅中文公开名

注入=['conversationEvents','slots','sessions','locale']#会话事件、槽位、会话、文案

def 应用(上下文):#安装浏览器半边
    """登记工作流定义、词表与按键 Chat 渲染器。"""
    上下文.conversationEvents.register(工作流运行定义)#登记工作流运行定义
    上下文.effect(lambda:上下文.locale.register(命名空间,{'zh':中文,'en':英文}),'ui-workflow-run: dictionaries')#登记中英文案
    def 登记节点():#等会话聊天节点槽出现再登记
        """登记 workflow-run 按键渲染器。"""
        def 注入面():#组装面板注入
            """打开该会话。"""
            return {'openSession':lambda 标识:上下文.sessions.open(标识)}#打开会话
        return 上下文.slots.register({#登记
            'name':'conversation.chat.node',#槽名
            'key':'workflow-run',#按键匹配
            'locale':命名空间,#文案命名空间
            'inject':注入面,#注入工厂
        },工作流运行面板)#面板组件
    上下文.slots.inject('conversation.chat.node',登记节点)#依赖槽位声明
