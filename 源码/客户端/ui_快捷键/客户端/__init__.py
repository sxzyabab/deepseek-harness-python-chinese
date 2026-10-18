'快捷键速查插件。命令和入口共用一份已声明的存储'
from ...模块.客户端.通告 import 取握手窗口
from ...ui_基础界面组件.模态层 import 关栈顶模态
from ...存储 import 声明存储
from . import 文案
from . import 反馈
from . import 图标
from . import 编辑器
from . import 参考

__all__=['文案','反馈','图标','编辑器','参考','依赖','应用']

依赖=['shortcuts','locale','slots']

def 应用(上下文,配置=None):
    '登记速查命令、设置行，以及唯一的壳层浮层'
    def 登记词典():
        '登记中英文案表。页面上的字不走英文表'
        return 上下文.locale.register('shortcuts',{'zh':文案.中文,'en':文案.英文})
    上下文.副作用(登记词典,'shortcuts: dictionaries')
    def 初值():
        '关着、空查询、焦点代数 0'
        return {'open':False,'query':'','focusRequest':0}
    def 打开(草稿):
        '打开，并把焦点代数加一'
        草稿['open']=True
        草稿['focusRequest']=草稿['focusRequest']+1
    def 关闭(草稿):
        '关掉，并清空查询'
        草稿['open']=False
        草稿['query']=''
    def 搜索(草稿,查询):
        '写入查询'
        草稿['query']=查询
    句柄=声明存储({
        'init':初值,
        'actions':{
            'open':打开,
            'close':关闭,
            'search':搜索,
        },
    })
    实例=句柄.create()
    def 总是这一份(作用域键=None):
        '设置行和浮层共用这一份可见性'
        return 实例
    句柄.create=总是这一份
    def 编辑(*位置参数):
        '转发 shortcuts.edit'
        return 上下文.shortcuts.edit(*位置参数)
    def 录键(开):
        '转发 shortcuts.recording'
        return 上下文.shortcuts.recording(开)
    def 描述绑定(绑定):
        '转发 shortcuts.describeBinding'
        return 上下文.shortcuts.describeBinding(绑定)
    固定表=[
        {
            'id':'move',
            'keys':['↑','↓'],
            'bindings':[
                {'code':'ArrowUp','modifiers':[]},
                {'code':'ArrowDown','modifiers':[]},
            ],
            'group':'menus',
            'label':'移动菜单选择',
        },
        {
            'id':'select',
            'keys':['Enter'],
            'bindings':[{'code':'Enter','modifiers':[]}],
            'group':'menus',
            'label':'选择菜单项',
        },
        {
            'id':'dismiss',
            'keys':['Esc'],
            'bindings':[{'code':'Escape','modifiers':[]}],
            'group':'menus',
            'label':'关闭菜单或顶层弹窗',
        },
    ]
    for 行 in 固定表:
        def 标签(文=行['label']):
            '固定动作的展示名'
            return 文
        命令={
            'id':'fixed.'+行['id'],
            'keys':行['keys'],
            'bindings':行['bindings'],
            'group':行['group'],
            'label':标签,
        }
        def 登记固定(项=命令):
            '登记一条固定命令'
            return 上下文.shortcuts.registerFixed(项)
        上下文.副作用(登记固定,'shortcuts: '+命令['id'])
    def 注入面():
        '平台、运行时，以及目录钩子'
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
        '通用设置里的快捷键行'
        return 上下文.slots.register({
            'name':'settings.general.item',
            'id':'shortcuts',
            'order':16,
            'locale':'shortcuts',
            'store':句柄,
            'inject':注入面,
        },参考.快捷键设置行)
    上下文.slots.inject('settings.general.item',挂设置行)
    def 挂浮层():
        '登记打开速查的命令，以及壳层浮层'
        def 解析(面):
            '被别的模态挡住就放过。开着就关，否则打开'
            模态=面['modal']
            if 模态 is not None and 模态!='settings' and 模态!='shortcuts':
                return {'status':'blocked','reason':'modal'}
            def 跑():
                '开着速查就关最前的模态，否则打开'
                if 模态=='shortcuts':
                    关栈顶模态(取握手窗口().document)
                else:
                    实例.actions['open']()
            return {'status':'handled','run':跑}
        def 命令名():
            '命令面板上的名字'
            return '快捷键速查'
        卸命令=上下文.shortcuts.register({
            'id':'shortcuts.open',
            'label':命令名,
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
            'locale':'shortcuts',
            'store':句柄,
            'inject':注入面,
        },参考.快捷键速查)
        def 拆():
            '卸掉命令和浮层'
            卸命令()
            卸槽()
        return 拆
    上下文.slots.inject('shell.overlay',挂浮层)

inject=依赖
apply=应用
