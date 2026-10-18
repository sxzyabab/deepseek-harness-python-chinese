from . import (
    文案,
    槽,
    服务约定,
    控制器,
    服务,
    菜单视图,
)
from .文案 import 中文,英文#登记用的中英文案

__all__=[
    '文案','槽','服务约定','控制器','服务','菜单视图',
    '依赖','应用',
]

菜单命名空间='slash.menu'#候选菜单文案
依赖=['sessions','locale']#会话和文案

def 应用(上下文,配置=None):
    '挂上触发服务，登记菜单文案，再把菜单视图放进输入叠层'
    上下文.启动插件(服务.触发服务)#以 inputTriggers 挂上

    def 登记词典():
        '登记 slash.menu 的中英文案。页面上的字不读英文表'
        return 上下文.locale.register(菜单命名空间,{'zh':中文,'en':英文})#中英都登记

    上下文.副作用(登记词典,'ui-input-trigger: menu dictionaries')#词典随插件拆掉

    def 叠层就绪(作用域,配置=None):
        '槽位、触发服务和会话都在之后登记菜单'
        触发=作用域.inputTriggers#触发服务
        会话=作用域.sessions#会话服务

        def 登记菜单():
            '按会话注入菜单视图'

            def 注入面(会话标识):
                '没有作用域就抛出。有则交出这场会话的菜单'
                作用=会话.scope(会话标识)#这场会话的作用域
                if 作用 is None:#已经没有
                    raise Exception('ui-input-trigger: session "'+str(会话标识)+'" resolved no scope')#对不上
                这场=触发.sessionOf(作用)#这一场的控制器

                def 点选(来源,下标,动作='pick'):
                    '行上的点选'
                    这场.pick(来源,下标,动作)#落定或下钻

                def 点屑(来源,下标):
                    '页眉面包屑'
                    这场.pickCrumb(来源,下标)#下钻

                def 悬停(来源,下标):
                    '指针移到一行'
                    这场.hover(来源,下标)#停高亮

                def 驳回():
                    '点在编写区外面'
                    这场.dismiss()#关上

                return {#注入面
                    'menu':这场.menu,#菜单仓
                    'headers':这场.headers,#页眉仓
                    'onPick':点选,#点选
                    'onCrumb':点屑,#面包屑
                    'onHover':悬停,#悬停
                    'onDismiss':驳回,#驳回
                }

            return 作用域.slots.register({#挂进输入叠层
                'name':'conversation.input.overlay',#槽名
                'id':'slash-menu',#这一条
                'order':0,#最前
                'locale':菜单命名空间,#文案座位
                'inject':注入面,#按会话
            },菜单视图.菜单视图)#菜单视图

        作用域.slots.inject('conversation.input.overlay',登记菜单)#等槽出现

    上下文.依赖启动(['slots','inputTriggers','sessions'],叠层就绪)#等这三项

inject=依赖#插件依赖
apply=应用#英文入口
