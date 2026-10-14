'布局底槽里的窗口本地 NodeJS 诊断页'
from nicegui import ui as 界面
from .文案 import 中文,英文
from .缩放 import 检查器缩放柄
from .键盘 import 绑定检查器键盘

__all__=['检查器页','登记检查器页','快照仓']

命令标识='inspector.toggle'

样式表='''
.检查器底栏{position:relative;display:flex;flex-direction:column;min-height:0;overflow:hidden;box-sizing:border-box;background:var(--dsw-alias-bg-base);border-top:0.5px solid var(--dsw-alias-border-l3)}
.检查器底栏头{display:flex;flex:none;align-items:center;justify-content:space-between;width:100%;padding:6px 12px 4px;color:var(--dsw-alias-label-primary);font-size:12px;line-height:20px}
.检查器缩放{position:absolute;left:0;right:0;top:0;height:6px;cursor:row-resize;touch-action:none;user-select:none}
.检查器底栏页{display:block;flex:1;width:100%;height:0;min-width:0;min-height:0;border:0}
'''
界面.add_css(样式表,shared=True)

class 快照仓:
    'getSnapshot / set；底栏开关'
    def __init__(自身,初值):
        '记下初值'
        自身._状态=初值
        自身._监听=set()

    def getSnapshot(自身):
        '当前状态：unopened、visible 或 hidden'
        return 自身._状态

    def set(自身,次值):
        '写入并通知'
        自身._状态=次值
        for 监听 in list(自身._监听):
            监听()

    def subscribe(自身,监听):
        '返回退订'
        自身._监听.add(监听)
        def 退订():
            '去掉这一个监听'
            自身._监听.discard(监听)
        return 退订

def 读面板(属性):
    '注入面 hooks.panel'
    钩=(属性.get('hooks') or {}).get('panel')
    if 钩 is not None:
        return 钩.getSnapshot()
    取=属性.get('usePanel')
    if 取 is not None:
        return 取(lambda 值:值)
    return 'unopened'

class 检查器页:
    '底栏：缩放、收起，以及首次打开后保留的诊断页'
    def __init__(自身,属性):
        '默认高度为视口的 45%'
        自身.属性=属性
        自身.高度=45
        自身.根=None
        自身.框=None
        自身.释放键盘=None
        自身._画=None
        if 't' in 属性 and 'close' in 属性 and 'frontendUrl' in 属性 and 'bindFrame' in 属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性

    def 改高度(自身,值):
        '记下高度并写到当前面板'
        自身.高度=值
        if 自身.根 is not None:
            自身.根.style(f'height:{值}dvh')

    def _画体(自身):
        '可见时出分隔条；离开 unopened 后保留 iframe'
        翻译=自身.属性['t']
        状态=读面板(自身.属性)
        可见=状态=='visible'
        根=界面.element('section').classes('检查器底栏')
        根.props(f'aria-label="{翻译("title")}" data-inspector-panel')
        根.style(f'height:{自身.高度}dvh;display:{"flex" if 可见 else "none"}')
        自身.根=根
        with 根:
            if 可见:
                检查器缩放柄({
                    'height':自身.高度,
                    'onResize':自身.改高度,
                    'label':翻译('resize'),
                    'panelId':'inspector-panel',
                }).渲染()
            with 界面.row().classes('检查器底栏头'):
                界面.label(翻译('title'))
                界面.button(icon='close', on_click=自身.属性['close']).props('flat round dense').tooltip(翻译('close'))
            if 状态!='unopened':
                框=界面.element('iframe').classes('检查器底栏页')
                网址=自身.属性['frontendUrl']
                框.props(
                    f'src={网址} title="{翻译("frameTitle")}" name=dsh-nodejs-inspector '
                    'referrerpolicy=no-referrer data-inspector-devtools'
                )
                if 自身.释放键盘 is not None:
                    自身.释放键盘()
                自身.框=框
                自身.释放键盘=自身.属性['bindFrame'](框)

    def 渲染(自身):
        '面板状态变化时重画'
        if 自身._画 is None:
            @界面.refreshable
            def 画():
                '按当前开关重画底栏'
                自身._画体()
            自身._画=画
            存储=(自身.属性.get('hooks') or {}).get('panel')
            if 存储 is not None and hasattr(存储,'subscribe'):
                存储.subscribe(lambda:自身._画.refresh())
        自身._画()

    def __call__(自身,属性=None):
        '对齐调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

def 登记检查器页(上下文,源标识):
    '为一个 Client 源登记底栏内容和窗口本地切换命令'
    查询=f'disableLocaleInfoBar=true&clientSourceId={源标识}'
    前端网址=f'inspector/devtools/devtools_app.html?{查询}'
    def 卸词典():
        '登记底栏词典'
        return 上下文.locale.register('inspectorPanel',{'zh':中文,'en':英文})
    上下文.副作用(卸词典,'inspector: bottom dictionaries')
    翻译=上下文.locale.bind('inspectorPanel') if hasattr(上下文.locale,'bind') else (lambda 键:中文[键])
    def 挂():
        '快捷键与底栏槽一起装、一起卸'
        面板=快照仓('unopened')
        打开者={}
        def 关闭():
            '可见时收起，并把焦点还给打开它的元素'
            if 面板.getSnapshot()!='visible':
                return
            面板.set('hidden')
            元素=打开者.get('元素')
            if 元素 is not None and getattr(元素,'isConnected',True) and hasattr(元素,'focus'):
                元素.focus()
        def 读绑定():
            '当前生效绑定，含用户覆盖'
            目录=上下文.shortcuts.catalog.getSnapshot()
            for 行 in 目录 or []:
                if 行.get('id')==命令标识:
                    return 行.get('binding')
            return None
        def 解决(事件):
            '展开或收起'
            def 运行():
                '可见则关闭，否则记下焦点来源再展开'
                if 面板.getSnapshot()=='visible':
                    关闭()
                    return
                目标=事件.get('target') if isinstance(事件,dict) else getattr(事件,'target',None)
                打开者['元素']=目标 if hasattr(目标,'focus') else None
                面板.set('visible')
            return {'status':'handled','run':运行}
        默认键={'code':'Period','modifiers':['primary','shift']}
        壳=('desktop','web')
        平台=('macos','windows','linux')
        默认={}
        for 运行时 in 壳:
            for 系统 in 平台:
                默认[运行时+':'+系统]=dict(默认键)
        yield 上下文.shortcuts.register({
            'id':命令标识,
            'label':lambda:翻译('toggle'),
            'aliases':['inspector','nodejs','devtools'],
            'defaults':默认,
            'regions':['page','editable','terminal'],
            'modals':[],
            'resolve':解决,
        })
        def 注入():
            '底栏看到的地址、关闭和键盘转发'
            return {
                'frontendUrl':前端网址,
                'close':关闭,
                'hooks':{'panel':面板},
                'bindFrame':lambda 框:绑定检查器键盘(框,读绑定),
            }
        yield 上下文.slots.register({
            'name':'shell.bottom',
            'locale':'inspectorPanel',
            'inject':注入,
        },检查器页)
    上下文.slots.inject('shell.bottom',挂)
