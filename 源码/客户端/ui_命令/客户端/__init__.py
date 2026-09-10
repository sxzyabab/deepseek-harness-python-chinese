"""命令界面插件的浏览器半边。

对齐上游 `ui-commands/src/client/index.ts`。公开面仅中文名。
挂上 CommandUiRuntime（`ctx.commandUi`），并把 popupSelect 壳登记进
conversation.input.overlay。弹出视图依赖未在本批配额内的弹出层模块时，
叠层登记可在宿主补齐后启用。
"""
from .约定 import (#再导出约定形
    选定确认,选定选项,弹出选定规格,动作规格,命令UI规格,
    命令贡献,命令装饰,命令UI约定,
)#约定结束
from .服务 import 命令UI运行时#运行时

__all__=[#仅中文公开名
    '注入','应用',
    '命令UI运行时',
    '选定确认','选定选项','弹出选定规格','动作规格','命令UI规格',
    '命令贡献','命令装饰','命令UI约定',
]#公开面结束

注入=['inputTriggers','sessions','remote','remote.commands','locale']#所需服务
命名空间='command'#文案命名空间


def 应用(上下文):
    """挂服务；叠层声明就绪后再登记 popup 壳。"""
    if hasattr(上下文,'locale') and hasattr(上下文.locale,'register'):#有文案
        def 登记词典():#挂载
            """中英文——词典键由上游 locales 持有；此处仅占位登记命名空间。"""
            try:#尝试导入文案
                from .文案 import 中文,英文#文案
                return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记
            except ImportError:#尚无文案配额
                return lambda:None#空拆除
        上下文.副作用(登记词典,'ui-commands: dictionaries')#词典
    if hasattr(上下文,'plugin'):#可挂插件
        上下文.plugin(命令UI运行时)#挂运行时
    elif hasattr(上下文,'provide'):#简化面
        上下文.provide('commandUi',命令UI运行时(上下文))#提供

    def 叠层就绪(作用域):
        """等 slots/commandUi/sessions 后登记弹层。"""
        命令=作用域.commandUi if hasattr(作用域,'commandUi') else 作用域.get('commandUi')#运行时
        会话=作用域.get('sessions') if hasattr(作用域,'get') else 作用域.sessions#会话
        def 登记弹层():#登记
            """按会话解析弹层注入。"""
            def 注入面(会话标识):#按会话
                """解析作用域并交出 popup。"""
                作用=会话.scope(会话标识)#作用域
                if 作用 is None:#无
                    raise Exception('ui-commands: session "'+str(会话标识)+'" resolved no scope')#失败
                return {'popup':命令.popupFor(作用)}#面
            return 作用域.slots.register({#登记
                'name':'conversation.input.overlay',#叠层
                'id':'command-popup',#id
                'order':1,#序
                'locale':命名空间,#文案
                'inject':注入面,#注入
            },None)#视图由宿主/后续配额补齐
        if hasattr(作用域.slots,'inject'):#可注入
            作用域.slots.inject('conversation.input.overlay',登记弹层)#注入

    if hasattr(上下文,'inject'):#cordis inject
        上下文.inject(['slots','commandUi','sessions'],叠层就绪)#等齐

inject=注入#框架槽
apply=应用#框架槽
