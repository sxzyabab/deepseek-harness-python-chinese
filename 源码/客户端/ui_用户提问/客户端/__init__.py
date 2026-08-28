"""Web 提问插件的浏览器半边：把 QuestionComposer 登记为会话声明的 composer 链上一条选择器路由条目，外加 `question` 词典。

选择器把主人的当前项收窄到提问载体；整套行为面骑在载体上；文案走标准 locale 座位。

对齐上游 `ui-user-questions/src/client/index.ts`。公开面仅中文名。
"""
from .约定.槽位 import 待答提问,计划审阅于,取字段#约定再导出
from .文案 import 中文,英文#词典
from .提问撰写器 import 提问撰写器,解析推荐标签#撰写器入口

__all__=[#仅中文公开名
    '注入',
    '应用',
    '待答提问',
    '计划审阅于',
    '解析推荐标签',
    '提问撰写器',
    '中文',
    '英文',
    '命名空间',
]#公开面结束

命名空间='question'#本插件拥有的文案命名空间
注入=['slots','locale']#槽位与文案

def 选择提问(属性):#链路由选择器
    """提问等待挂起时占据 composer（纯函数——只用主人 props）。"""
    交互们=取字段(属性,'interactions') or []#交互列表
    for 项 in 交互们:#逐项
        if 取字段(项,'kind')=='question':#命中提问等待
            return 项#收窄载体
    return None#无提问

def 应用(上下文):#安装浏览器半边
    """登记 `question` 词典，并把提问撰写器登记进 composer 链。"""
    上下文.effect(lambda:上下文.locale.register(命名空间,{'zh':中文,'en':英文}),'ui-user-questions: dictionaries')#登记中英文案
    def 登记撰写器():#等 composer 链槽出现再登记
        """登记选择器路由条目。"""
        return 上下文.slots.register(#登记链条目
            {'name':'conversation.composer','select':选择提问,'locale':命名空间},#选择器 + 文案命名空间
            提问撰写器,#提问撰写器组件
        )#登记结束
    上下文.slots.inject('conversation.composer',登记撰写器)#依赖槽位声明
