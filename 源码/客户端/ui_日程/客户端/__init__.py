"""只读 Schedule 目录的浏览器半部。

对齐上游 `ui-schedule/src/client/index.ts`。公开面仅中文名。
"""
from .日程目录动作 import 日程目录动作#目录动作组件
from .文案 import 命名空间,中文,英文,NS,zh,en#词典与键

__all__=[#仅中文公开名
    '注入','应用','日程目录动作','命名空间','中文','英文','NS','zh','en',
]#公开面结束

注入=['slots','locale']#本地化登记与页眉槽贡献所需服务

def 应用(上下文):#浏览器侧安装入口
    """登记词典与 Session 页眉目录动作。"""
    上下文.effect(lambda:上下文.locale.register(NS,{'zh':zh,'en':en}),'ui-schedule: dictionaries')#登记词典
    上下文.slots.inject(#等页眉 actions 声明
        'conversation.session.header.actions',#页眉动作槽
        lambda:上下文.slots.register({#登记目录动作
            'name':'conversation.session.header.actions',#槽名
            'id':'schedule-catalog',#条目稳定 id
            'order':10,#排序权重
            'locale':NS,#词典命名空间
        },日程目录动作),#组件
    )#inject 结束
