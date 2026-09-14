from .约定 import (#再导出约定形
    选定确认,选定选项,弹出选定规格,动作规格,命令UI规格,
    命令贡献,命令装饰,命令UI约定,命令错误,
)#约定结束
from .文案 import 中文,英文#中英文案
from .服务 import 命令UI运行时#运行时

__all__=[#仅中文公开名
    '注入','应用',
    '命令UI运行时','命令错误',
    '选定确认','选定选项','弹出选定规格','动作规格','命令UI规格',
    '命令贡献','命令装饰','命令UI约定',
]#公开面结束

注入=['inputTriggers','sessions','remote','remote.commands','locale']#所需服务
命名空间='command'#文案命名空间


def 应用(上下文):
    """挂词典与运行时；等槽位/命令界面/会话后登记弹层。"""
    def 登记词典():
        """登记 command 命名空间中英文案。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记
    上下文.副作用(登记词典,'ui-commands: dictionaries')#词典
    上下文.plugin(命令UI运行时)#挂运行时

    def 叠层就绪(作用域):
        """等 slots/commandUi/sessions 后登记弹层。"""
        命令=作用域.commandUi#运行时
        会话=作用域.get('sessions')#会话
        def 登记弹层():
            """按会话解析弹层注入。"""
            def 注入面(会话标识):
                """解析作用域并交出 popup。"""
                作用=会话.scope(会话标识)#作用域
                if 作用 is None:#无
                    raise 命令错误('ui-commands: session "'+str(会话标识)+'" resolved no scope')#失败
                return {'popup':命令.popupFor(作用)}#面
            return 作用域.slots.register({#登记
                'name':'conversation.input.overlay',#叠层
                'id':'command-popup',#id
                'order':1,#序
                'locale':命名空间,#文案
                'inject':注入面,#注入
            },None)#视图由后续弹出层配额补齐
        作用域.slots.inject('conversation.input.overlay',登记弹层)#注入

    上下文.inject(['slots','commandUi','sessions'],叠层就绪)#等齐

inject=注入#框架槽
apply=应用#框架槽
