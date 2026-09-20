from .日程目录动作 import 日程目录动作#目录动作组件
from .文案 import 命名空间,中文,英文#词典与键

__all__=[#仅中文公开名
    '依赖','应用','日程目录动作','命名空间','中文','英文',
]

依赖=['slots','locale']#本地化登记与页眉槽贡献所需服务

def 应用(上下文):
    """登记词典与 Session 页眉目录动作。"""
    def 登记词典():
        """登记日程词典。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记词典
    上下文.副作用(登记词典,'ui-schedule: dictionaries')#登记词典

    def 登记目录():
        """登记页眉目录动作。"""
        return 上下文.slots.register({#登记目录动作
            'name':'conversation.session.header.actions',#槽名
            'id':'schedule-catalog',#条目稳定 id
            'order':10,#排序权重
            'locale':命名空间,#词典命名空间
        },日程目录动作)#组件
    上下文.slots.inject('conversation.session.header.actions',登记目录)#等页眉 actions 声明

inject=依赖#框架槽
apply=应用#框架槽
