'可搜索可编辑的快捷键速查及其通用设置行'
from nicegui import ui as 界面
from ...ui_基础界面组件.按名排序 import 按名排序
from ...ui_基础界面组件.icons import 图标关闭填14,图标刷新14
from .编辑器 import 快捷键编辑器
from .图标 import 快捷键图标
from .反馈 import 快捷键失败,快捷键读取失败

样式表='''
.setting{box-sizing:border-box;display:flex;align-items:center;justify-content:space-between;gap:8px;min-height:60px;padding:16px 0;border-bottom:0.5px solid var(--dsw-alias-border-l2)}
.settingText{flex:1;min-width:0;display:flex;flex-direction:column;gap:4px;padding-right:48px}
.settingTitle{color:var(--dsw-alias-label-primary);font-size:14px;line-height:22px}
.settingDescription{margin:0;color:var(--dsw-alias-label-tertiary);font-size:12px;line-height:18px}
.button{height:36px;min-width:90px}
.dialog{display:flex;flex-direction:column;width:min(480px,100%);max-height:calc(100dvh - 108px);gap:0}
.header{display:flex;align-items:center;justify-content:space-between;padding:22px 24px 0}
.title{color:var(--dsw-alias-label-primary);font-size:16px;line-height:24px;font-weight:500}
.searchRow{display:flex;align-items:center;gap:8px;padding:12px 24px 0}
.searchField{display:flex;align-items:center;gap:8px;flex:1}
.searchIcon{flex:none;color:var(--dsw-alias-label-caption)}
.list{display:flex;flex-direction:column;min-height:0;overflow-y:auto;padding:8px 16px}
.group{color:var(--dsw-alias-label-tertiary);font-size:12px;line-height:18px}
.dialog .row{display:flex;align-items:center;justify-content:space-between;gap:8px;min-height:36px}
.commandLabel{flex:1;min-width:0}
.binding{display:flex;align-items:center;justify-content:flex-end;gap:8px}
.keyBadge{box-sizing:border-box;height:26px;padding:0 12px;border-radius:10px;background:var(--dsw-alias-bg-module-platform);color:var(--dsw-alias-label-secondary)}
.fixedKeyBadge{height:26px;color:var(--dsw-alias-label-tertiary)}
.unbound{color:var(--dsw-alias-label-tertiary);font-size:12px}
.footer{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:12px 24px 16px}
.toast{display:flex;align-items:center;gap:8px;padding:8px 24px 16px}
.toastSuccess{color:var(--dsw-alias-state-success-secondary)}
.toastError{color:var(--dsw-alias-state-warn-secondary)}
.srOnly{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap;border:0}
.hint{color:var(--dsw-alias-label-tertiary)}
'''
界面.add_css(样式表,shared=True)

搜索标='<svg class="searchIcon" width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M10.28 5.86536C10.28 3.41381 8.29245 1.42644 5.84094 1.42627C3.38929 1.42627 1.40186 3.4137 1.40186 5.86536C1.40203 8.31686 3.38939 10.3044 5.84094 10.3044C8.29234 10.3043 10.2799 8.31676 10.28 5.86536ZM11.4174 5.86536C11.4172 8.94498 8.92057 11.4416 5.84094 11.4418C2.76117 11.4418 0.263843 8.94509 0.263672 5.86536C0.263672 2.78548 2.76106 0.288086 5.84094 0.288086C8.92067 0.288258 11.4174 2.78559 11.4174 5.86536Z" fill="currentColor"/><path d="M13.7372 12.9078L12.9323 13.7127L9.9732 10.7536L10.7781 9.94867L13.7372 12.9078Z" fill="currentColor"/></svg>'

def 画键徽章(键列表,类名):
    '每个键位一枚徽章；空列表不画'
    if isinstance(键列表,list) is False:
        return
    for 键位 in 键列表:
        界面.label(str(键位)).classes(类名)

__all__=['核心动作顺序','快捷键设置行','快捷键速查']

核心动作顺序={
    'shortcuts.open':0,
    'session.new':1,
    'sidebar.left.toggle':2,
    'session.search':3,
    'workspace.add':4,
    'session.rename':5,
    'session.fork':6,
    'session.archive':7,
    'settings.open':8,
    'workspace.openLocal':9,
    'sidebar.right.toggle':10,
    'workspace.files':11,
    'browser.new':12,
    'terminal.new':13,
    'pane.split':14,
    'pane.fullscreen.toggle':15,
    'page.refresh':16,
    'page.close':17,
}

coreActionOrder=核心动作顺序

class 快捷键设置行:
    '通用设置里打开速查的动作行'
    def __init__(自身,属性):
        '记下 props。槽位只调用构造，键齐才画。'
        自身.属性=属性 if isinstance(属性,dict) else {}
        if callable(自身.属性.get('t')):
            自身.渲染()

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 读目录(自身):
        'hooks.catalog 或 useCatalog'
        钩=自身.属性.get('hooks') or {}
        存=钩.get('catalog')
        if 存 is not None:
            return 存.getSnapshot()
        取=自身.属性.get('useCatalog')
        if 取 is not None:
            return 取(lambda 快照:快照)
        return []

    def 渲染(自身):
        '设置行：标题、说明、查看按钮，有键位时带悬停提示和徽章。没有文案时不画替代句。'
        if not callable(自身.属性.get('t')):
            return None
        翻译=自身.属性['t']
        动作=自身.属性['actions'] if 'actions' in 自身.属性 else None
        def 打开():
            '打开速查'
            if isinstance(动作,dict) and 'open' in 动作:
                动作['open']()
        行=None
        for 项 in 自身.读目录():
            if 'id' in 项 and 项['id']=='shortcuts.open':
                行=项
                break
        键=行['keys'] if 行 is not None and 'keys' in 行 and isinstance(行['keys'],list) else []
        with 界面.row().classes('setting'):
            with 界面.column().classes('settingText'):
                界面.label(翻译('settings')).classes('settingTitle')
                界面.label(翻译('description')).classes('settingDescription')
            钮=界面.button(翻译('view'), on_click=打开).props('flat no-caps').classes('button')
            if len(键)>0:
                钮.tooltip(翻译('global-hint'))
                with 界面.row().classes('binding'):
                    画键徽章(键,'keyBadge')

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

class 快捷键速查:
    '打开时渲染单实例速查对话框；核心动作按产品序，组内其余按 id'
    def __init__(自身,属性):
        '记下 props 与对话框态。槽位只调用构造，键齐才画。编辑器构造时不画。'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.目标=None
        自身.重置修订=None
        自身.忙=False
        自身.吐司=None
        自身.已挂=True
        自身.编辑器=None
        自身._编辑标识=None
        if callable(自身.属性.get('t')) and isinstance(自身.属性.get('actions'),dict):
            自身.渲染()

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 读存储(自身):
        '根 store 快照'
        取=自身.属性.get('useStore')
        if 取 is not None:
            return 取(lambda 态:态)
        动作=自身.属性.get('actions')
        if 动作 is not None and hasattr(动作,'getSnapshot'):
            return 动作.getSnapshot()
        return {'open':False,'query':'','focusRequest':0}

    def 读钩(自身,名):
        'hooks 或 use*'
        钩=自身.属性.get('hooks') or {}
        存=钩.get(名)
        if 存 is not None:
            return 存.getSnapshot()
        键={'catalog':'useCatalog','config':'useConfig','fixedCatalog':'useFixedCatalog'}[名]
        取=自身.属性.get(键)
        if 取 is not None:
            return 取(lambda 快照:快照)
        if 名=='config':
            return {'status':'loading','revision':None,'document':{'profiles':{}}}
        return []

    def 通知(自身,文本,错误=False):
        '吐司；同错文案不重复抬序号'
        前=自身.吐司
        if 错误 and 前 is not None and 前.get('error') and 前.get('text')==文本:
            return
        序=0 if 前 is None else 前.get('seq',0)+1
        自身.吐司={'text':文本,'error':错误,'seq':序}

    def 消吐司(自身):
        '清吐司'
        自身.吐司=None

    def 关编辑器(自身):
        '退出行内编辑'
        自身.目标=None
        自身.编辑器=None

    def 关速查(自身):
        '忙则忽略；确认优先于编辑器优先于关对话框'
        if 自身.忙:
            return
        if 自身.重置修订 is not None:
            自身.重置修订=None
        elif 自身.目标 is not None:
            自身.关编辑器()
        else:
            自身.属性['actions']['close']()

    def 持久化(自身,*位置参数):
        '包一层 edit，跟踪忙'
        自身.忙=True
        结果=自身.属性['edit'](*位置参数)
        if 自身.已挂:
            自身.忙=False
        return 结果

    def 全部恢复(自身):
        '确认后 reset-all'
        if 自身.重置修订 is None:
            return
        结果=自身.持久化({'type':'reset-all'},自身.重置修订)
        if not 自身.已挂:
            return
        if 结果['status'] in ('saved','stale'):
            自身.重置修订=None
        翻译=自身.属性['t']
        if 结果['status']=='saved':
            文=翻译('reset-saved')
            错=False
        elif 结果['status']=='write-failed':
            文=翻译('reset-failed')
            错=True
        else:
            文=快捷键失败(结果,自身.读钩('catalog'),翻译,自身.属性['runtime'])
            错=True
        自身.通知(文,错)

    def 排序键(自身,行):
        'stop 置后，再核心序，再 id'
        标识=行['id']
        停=1 if 标识=='response.stop' else 0
        核=核心动作顺序[标识] if 标识 in 核心动作顺序 else len(核心动作顺序)
        return (停,核,标识)

    def 匹配行(自身,查询):
        '拼检索名后按名排序，去重保序'
        目录=自身.读钩('catalog')
        固定=自身.读钩('fixedCatalog')
        条目=[]
        for 行 in 目录:
            键=行.get('keys') or []
            名表=list(行.get('aliases') or [])
            名表.append('+'.join([键位 for 键位 in 键 if 键位!='+']))
            名表.append(''.join([键位 for 键位 in 键 if 键位!='+']))
            aria=行.get('aria') or ''
            名表.append(aria)
            名表.append(aria.replace('Meta','Cmd'))
            条目.append({**行,'names':名表,'group':'application'})
        for 行 in 固定:
            条目.append({**行,'names':[行['id'],' '.join(行.get('keys') or [])]})
        条目.sort(key=自身.排序键)
        扁平=[]
        for 行 in 条目:
            for 名 in 行['names']:
                扁平.append({'name':名,'label':行.get('label'),'row':行})
        排序后=按名排序(扁平,查询.strip())
        见过=[]
        匹配=[]
        for 项 in 排序后:
            行=项['row']
            if 行['id'] in 见过:
                continue
            见过.append(行['id'])
            匹配.append(行)
        return 匹配

    def 编辑属性(自身):
        '传给行内编辑器的注入面'
        def 已存():
            '保存成功'
            自身.通知(自身.属性['t']('saved'))
            自身.关编辑器()
        def 出错(消息):
            '保存/录键错误'
            自身.通知(消息,True)
        return {
            'useCatalog':自身.属性.get('useCatalog'),
            'useConfig':自身.属性.get('useConfig'),
            'useFixedCatalog':自身.属性.get('useFixedCatalog'),
            'hooks':自身.属性.get('hooks'),
            'platform':自身.属性.get('platform'),
            'runtime':自身.属性.get('runtime'),
            'edit':自身.持久化,
            'recording':自身.属性.get('recording'),
            'describeBinding':自身.属性.get('describeBinding'),
            't':自身.属性['t'],
            'onClose':自身.关编辑器,
            'onSaved':已存,
            'onError':出错,
        }

    def 渲染(自身):
        '速查、恢复确认和吐司。编辑器在行内空构造、更新后再画。没有文案时不画替代句。'
        if not callable(自身.属性.get('t')):
            return None
        翻译=自身.属性['t']
        态=自身.读存储()
        打开='open' in 态 and 态['open'] is True
        查询=态['query'] if 'query' in 态 and isinstance(态['query'],str) else ''
        配置=自身.读钩('config')
        if 打开 and 配置.get('status')=='unreadable':
            自身.通知(快捷键读取失败(配置,自身.属性['runtime'],翻译),True)
        if 打开 is not True and 自身.重置修订 is not None:
            自身.重置修订=None
        if 打开 is not True:
            return
        运行时=自身.属性.get('runtime')
        平台=自身.属性.get('platform')
        档键=str(运行时)+':'+str(平台)
        文档=配置['document'] if 'document' in 配置 and isinstance(配置['document'],dict) else {}
        档表=文档['profiles'] if 'profiles' in 文档 and isinstance(文档['profiles'],dict) else {}
        档=档表[档键] if 档键 in 档表 and isinstance(档表[档键],dict) else {}
        改数=len(档)
        匹配=自身.匹配行(查询)
        def 开重置():
            '打开恢复全部确认'
            自身.目标=None
            自身.重置修订=配置.get('revision')
        def 关确认():
            '关确认'
            if 自身.忙 is not True:
                自身.重置修订=None
        def 改搜(事件):
            '写入搜索'
            if 'actions' in 自身.属性 and 'search' in 自身.属性['actions']:
                自身.属性['actions']['search'](事件.value)
        def 清搜():
            '清空查询'
            if 'actions' in 自身.属性 and 'search' in 自身.属性['actions']:
                自身.属性['actions']['search']('')
        with 界面.column().classes('dialog'):
            with 界面.row().classes('header'):
                界面.label(翻译('title')).classes('title')
                关=界面.button(on_click=自身.关速查).props('flat round aria-label="'+翻译('close')+'"').classes('close')
                with 关:
                    图标关闭填14({'size':14})
            with 界面.row().classes('searchRow'):
                with 界面.row().classes('searchField'):
                    界面.html(搜索标,sanitize=False)
                    界面.input(value=查询, placeholder=翻译('search'), on_change=改搜).props('aria-label="'+翻译('search')+'"')
                    if 查询!='':
                        清=界面.button(on_click=清搜).props('flat round aria-label="'+翻译('clear-search')+'"').classes('clearSearch')
                        with 清:
                            图标关闭填14({'size':10})
            with 界面.column().classes('list'):
                for 组 in ('application','input','menus','approval'):
                    行们=[行 for 行 in 匹配 if 行.get('group')==组]
                    if len(行们)==0:
                        continue
                    if 组!='application':
                        界面.label(翻译(组)).classes('group')
                    for 行 in 行们:
                        可改='modified' in 行
                        在编=自身.目标 is not None and 'id' in 自身.目标 and 'id' in 行 and 自身.目标['id']==行['id']
                        键=行['keys'] if 'keys' in 行 and isinstance(行['keys'],list) else []
                        标签=行['label'] if 'label' in 行 else ''
                        def 开编(_事件=None,目标行=行):
                            '进入行内编辑'
                            自身.目标=目标行
                        with 界面.row().classes('row'):
                            if isinstance(标签,str) and 标签!='':
                                界面.label(标签).classes('commandLabel')
                            with 界面.row().classes('binding'):
                                if 可改 and 在编:
                                    面={**自身.编辑属性(),'target':行}
                                    if 自身.编辑器 is None or 自身._编辑标识!=行.get('id'):
                                        自身.编辑器=快捷键编辑器()
                                        自身._编辑标识=行.get('id')
                                    自身.编辑器.更新(面)
                                    自身.编辑器.渲染()
                                elif 可改:
                                    快捷键图标({'kind':'edit','className':'rowActions'}).渲染()
                                    if len(键)==0:
                                        界面.label(翻译('unbound')).classes('unbound')
                                    else:
                                        画键徽章(键,'keyBadge')
                                    编辑钮=界面.button(翻译('edit-label',{'command':标签}), on_click=开编).props('flat no-caps').classes('rowButton')
                                    if 自身.忙 or 配置.get('status')!='ready':
                                        编辑钮.disable()
                                else:
                                    画键徽章(键,'fixedKeyBadge')
                if len(匹配)==0:
                    界面.label(翻译('empty')).classes('hint')
            with 界面.row().classes('footer'):
                复位=界面.button(on_click=开重置).props('flat no-caps').classes('resetAll')
                with 复位:
                    图标刷新14({'size':12})
                    界面.label(翻译('reset-all'))
                if 自身.忙 or 配置.get('status')!='ready' or 改数==0:
                    复位.disable()
                if 改数>0:
                    界面.label(翻译('modified-count',{'count':改数})).classes('modifiedCount')
            if 自身.重置修订 is not None:
                with 界面.dialog() as 对话框:
                    with 界面.card():
                        界面.label(翻译('reset-title'))
                        界面.label(翻译('reset-description'))
                        界面.button(翻译('close-confirmation'), on_click=关确认).props('flat no-caps')
                        界面.button(翻译('cancel'), on_click=关确认).props('flat no-caps')
                        恢复=界面.button(翻译('reset'), on_click=自身.全部恢复).props('unelevated no-caps')
                        if 自身.忙 or 配置.get('status')!='ready':
                            恢复.disable()
                对话框.open()
            if 自身.吐司 is not None:
                吐=自身.吐司
                错=吐['error'] is True if 'error' in 吐 else False
                with 界面.row().classes('toast toastError' if 错 else 'toast toastSuccess'):
                    快捷键图标({'kind':'error' if 错 else 'success'}).渲染()
                    界面.label(吐['text'] if 'text' in 吐 else '')

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

ShortcutsRow=快捷键设置行
ShortcutReference=快捷键速查
