from . import (
    文案,
    约定,
    解析,
    呈现,
    选项组,
    弹出层,
    目录,
    服务,
    弹出选择视图,
)
from .文案 import 中文,英文

__all__=[
    '文案','约定','解析','呈现','选项组','弹出层','目录','服务','弹出选择视图',
    '依赖','应用',
]

依赖=['inputTriggers','sessions','remote','remote.commands','locale']
命名空间='command'

def 应用(上下文,配置=None):
    '登记文案表和命令运行时，再把弹出壳放进输入叠层'
    def 登记词典():
        '登记 command 命名空间的中英文案。页面显示不走英文表'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词典,'ui-commands: dictionaries')
    上下文.启动插件(服务.命令界面运行时)
    def 叠层就绪(作用域,配置=None):
        '槽位、命令界面和会话都在之后登记弹出'
        命令=作用域.commandUi
        会话=作用域.获取服务('sessions')
        def 登记弹层():
            '按会话解析弹出注入'
            def 注入面(会话标识):
                '没有作用域就抛出。有则交出这场会话的弹出'
                作用=会话.scope(会话标识)
                if 作用 is None:
                    raise Exception('ui-commands: session "'+str(会话标识)+'" resolved no scope')
                return {'popup':命令.popupFor(作用)}
            return 作用域.slots.register({
                'name':'conversation.input.overlay',
                'id':'command-popup',
                'order':1,
                'locale':命名空间,
                'inject':注入面,
            },弹出选择视图.弹出选择视图)
        作用域.slots.inject('conversation.input.overlay',登记弹层)
    上下文.依赖启动(['slots','commandUi','sessions'],叠层就绪)

inject=依赖
apply=应用
