"""快捷键速查插件；命令与入口共享一份已声明 store。"""
from types import SimpleNamespace as 简易命名空间
from .存储 import 创建快捷键存储
from .参考 import 快捷键速查,快捷键设置行
from .文案 import 命名空间,中文,英文
from .固定 import 固定命令

__all__=['依赖','应用','命名空间','中文','英文','创建快捷键存储','固定命令','快捷键速查','快捷键设置行']

依赖=['shortcuts','locale','slots']

def 关闭顶层模态(文档):
    """对齐 closeTopModal：关掉最前登记模态的 onClose。"""
    globals()['closeTopModal'](文档)

def 应用(上下文):
    """注册速查命令、设置行与单实例 shell 浮层。"""
    def 登记词典():
        """登记 shortcuts 词典。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词典,'shortcuts: dictionaries')
    翻译=上下文.locale.bind(命名空间)
    句柄=创建快捷键存储()
    实例=句柄.create()
    存储=简易命名空间(spec=句柄.spec,create=lambda *_位置,_关键字=None:实例)
    def 编辑(*位置参数):
        """转发 shortcuts.edit。"""
        return 上下文.shortcuts.edit(*位置参数)
    def 录键(开):
        """转发 shortcuts.recording。"""
        return 上下文.shortcuts.recording(开)
    def 描述绑定(绑定):
        """转发 shortcuts.describeBinding。"""
        return 上下文.shortcuts.describeBinding(绑定)
    for 命令 in 固定命令(翻译):
        def 登记固定(项=命令):
            """登记一条固定命令。"""
            return 上下文.shortcuts.registerFixed(项)
        上下文.副作用(登记固定,'shortcuts: '+命令['id'])
    def 注入面():
        """平台、运行时与目录钩。"""
        return {
            'platform':上下文.shortcuts.platform,
            'runtime':上下文.shortcuts.runtime,
            'edit':编辑,
            'recording':录键,
            'describeBinding':描述绑定,
            'hooks':{
                'catalog':上下文.shortcuts.catalog,
                'config':上下文.shortcuts.config,
                'fixedCatalog':上下文.shortcuts.fixedCatalog,
            },
        }
    def 挂设置行():
        """通用设置项。"""
        return 上下文.slots.register({
            'name':'settings.general.item',
            'id':'shortcuts',
            'order':20,
            'locale':命名空间,
            'store':存储,
            'inject':注入面,
        },快捷键设置行)
    上下文.slots.inject('settings.general.item',挂设置行)
    def 挂浮层():
        """速查命令 + shell.overlay。"""
        def 解析(面):
            """开或关速查。"""
            模态=面['modal'] if isinstance(面,dict) else 面.modal
            if 模态 is not None and 模态!='settings' and 模态!='shortcuts':
                return {'status':'blocked','reason':'modal'}
            def 跑():
                """toggle。"""
                if 模态=='shortcuts':
                    关闭顶层模态(globals()['document'])
                else:
                    实例['actions']['open']()
            return {'status':'handled','run':跑}
        def 标签():
            """命令标签。"""
            return 翻译('open')
        卸命令=上下文.shortcuts.register({
            'id':'shortcuts.open',
            'label':标签,
            'aliases':['shortcuts','keyboard shortcuts'],
            'defaults':{
                'desktop:macos':{'code':'Slash','modifiers':['primary']},
                'desktop:windows':{'code':'Slash','modifiers':['primary']},
                'desktop:linux':{'code':'Slash','modifiers':['primary']},
                'web:macos':{'code':'Slash','modifiers':['primary']},
                'web:windows':{'code':'Slash','modifiers':['primary']},
                'web:linux':{'code':'Slash','modifiers':['primary']},
            },
            'regions':['page','editable','terminal'],
            'modals':['settings','shortcuts'],
            'resolve':解析,
        })
        卸槽=上下文.slots.register({
            'name':'shell.overlay',
            'id':'shortcuts',
            'locale':命名空间,
            'store':存储,
            'inject':注入面,
        },快捷键速查)
        def 拆():
            """卸命令与槽。"""
            卸命令()
            卸槽()
        return 拆
    上下文.slots.inject('shell.overlay',挂浮层)

inject=依赖
apply=应用
