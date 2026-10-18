from .回退 import 未知回退定义
from .回合尾 import 登记回合尾会话节点
from .回合错 import 回合错定义
from .回合过程 import 登记回合过程
from .回合最大令牌 import 回合最大令牌定义
from .工具节点 import 登记工具会话节点
from .压缩 import 压缩定义
from .助手 import 登记助手会话节点
from .收件箱 import 下一步收件箱定义,下一回合收件箱定义
from .命令 import 命令定义
from .消息 import 开发者消息定义,消息定义
from .请求提示 import 请求提示定义,系统消息定义
from .过程组 import 过程组定义
from .聊天快照构建器 import 登记聊天会话视图
from .重试 import 重试定义

__all__=['登记会话节点']


def 登记会话节点(上下文):
    '登记聊天业务定义和目标构建器'
    def 检视系统提示(先前,事件):
        '交给会话服务解释系统提示'
        return 上下文.uiConversation.inspectSystemPrompt(先前,事件)

    def 检视请求提示(先前,事件,系统=None):
        '交给会话服务解释请求头提示'
        return 上下文.uiConversation.inspectRequestPrompt(先前,事件,系统)

    上下文.uiConversation.events.register(下一步收件箱定义)
    上下文.uiConversation.events.register(下一回合收件箱定义)
    上下文.uiConversation.events.register(消息定义)
    上下文.uiConversation.events.register(开发者消息定义)
    上下文.uiConversation.events.register(系统消息定义(检视系统提示))
    上下文.uiConversation.events.register(请求提示定义(检视请求提示))
    登记助手会话节点(上下文)
    登记回合过程(上下文)
    登记工具会话节点(上下文)
    上下文.uiConversation.events.register(命令定义)
    上下文.uiConversation.events.register(压缩定义)
    上下文.uiConversation.events.register(重试定义)
    上下文.uiConversation.events.register(回合错定义)
    上下文.uiConversation.events.register(回合最大令牌定义)
    登记回合尾会话节点(上下文)
    上下文.uiConversation.events.registerFallback(未知回退定义)
    登记聊天会话视图(上下文)
    上下文.uiConversation.groups.register(过程组定义)
