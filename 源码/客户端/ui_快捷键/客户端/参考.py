"""可搜索可编辑的快捷键速查及其通用设置行。"""
from ...ui_基础界面组件.按名排序 import 按名排序
from .编辑器 import 快捷键编辑器
from .图标 import 快捷键图标
from .反馈 import 快捷键失败,快捷键读取失败

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
    """通用设置里打开速查的动作行。"""
    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性

    def 读目录(自身):
        """hooks.catalog 或 useCatalog。"""
        钩=自身.属性.get('hooks') or {}
        存=钩.get('catalog')
        if 存 is not None:
            return 存.getSnapshot()
        取=自身.属性.get('useCatalog')
        if 取 is not None:
            return 取(lambda 快照:快照)
        return []

    def 渲染(自身):
        """设置行视图。"""
        翻译=自身.属性['t']
        打开=自身.属性['actions']['open']
        行=None
        for 项 in 自身.读目录():
            if 项.get('id')=='shortcuts.open':
                行=项
                break
        键=行.get('keys') if 行 is not None else []
        return {
            'type':'shortcuts-settings-row',
            'title':翻译('settings'),
            'description':翻译('description'),
            'viewLabel':翻译('view'),
            'globalHint':翻译('global-hint'),
            'shortcutKeys':键 or [],
            'ariaKeyshortcuts':None if 行 is None else 行.get('aria'),
            'hintDisabled':not 键,
            'onOpen':打开,
        }

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

class 快捷键速查:
    """打开时渲染单实例速查对话框；核心动作按产品序，组内其余按 id。"""
    def __init__(自身,属性):
        """记下 props 与对话框态。"""
        自身.属性=属性
        自身.目标=None
        自身.重置修订=None
        自身.忙=False
        自身.吐司=None
        自身.已挂=True
        自身.编辑器=None

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性

    def 读存储(自身):
        """根 store 快照。"""
        取=自身.属性.get('useStore')
        if 取 is not None:
            return 取(lambda 态:态)
        动作=自身.属性.get('actions')
        if 动作 is not None and hasattr(动作,'getSnapshot'):
            return 动作.getSnapshot()
        return {'open':False,'query':'','focusRequest':0}

    def 读钩(自身,名):
        """hooks 或 use*。"""
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
        """吐司；同错文案不重复抬序号。"""
        前=自身.吐司
        if 错误 and 前 is not None and 前.get('error') and 前.get('text')==文本:
            return
        序=0 if 前 is None else 前.get('seq',0)+1
        自身.吐司={'text':文本,'error':错误,'seq':序}

    def 消吐司(自身):
        """清吐司。"""
        自身.吐司=None

    def 关编辑器(自身):
        """退出行内编辑。"""
        自身.目标=None
        自身.编辑器=None

    def 关速查(自身):
        """忙则忽略；确认优先于编辑器优先于关对话框。"""
        if 自身.忙:
            return
        if 自身.重置修订 is not None:
            自身.重置修订=None
        elif 自身.目标 is not None:
            自身.关编辑器()
        else:
            自身.属性['actions']['close']()

    def 持久化(自身,*位置参数):
        """包一层 edit，跟踪忙。"""
        自身.忙=True
        结果=自身.属性['edit'](*位置参数)
        if 自身.已挂:
            自身.忙=False
        return 结果

    def 全部恢复(自身):
        """确认后 reset-all。"""
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
        """stop 置后，再核心序，再 id。"""
        标识=行['id']
        停=1 if 标识=='response.stop' else 0
        核=核心动作顺序[标识] if 标识 in 核心动作顺序 else len(核心动作顺序)
        return (停,核,标识)

    def 匹配行(自身,查询):
        """拼检索名后按名排序，去重保序。"""
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
        """传给行内编辑器的注入面。"""
        def 已存():
            """保存成功。"""
            自身.通知(自身.属性['t']('saved'))
            自身.关编辑器()
        def 出错(消息):
            """保存/录键错误。"""
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
        """速查 + 恢复确认 + 吐司。"""
        翻译=自身.属性['t']
        态=自身.读存储()
        打开=bool(态.get('open'))
        查询=态.get('query') or ''
        配置=自身.读钩('config')
        if 打开 and 配置.get('status')=='unreadable':
            自身.通知(快捷键读取失败(配置,自身.属性['runtime'],翻译),True)
        if not 打开 and 自身.重置修订 is not None:
            自身.重置修订=None
        运行时=自身.属性.get('runtime')
        平台=自身.属性.get('platform')
        档键=str(运行时)+':'+str(平台)
        档=(((配置.get('document') or {}).get('profiles') or {}).get(档键)) or {}
        改数=len(档)
        匹配=自身.匹配行(查询) if 打开 else []
        分组行={}
        for 组 in ('application','input','menus','approval'):
            分组行[组]=[行 for 行 in 匹配 if 行.get('group')==组]
        行视图=[]
        for 组 in ('application','input','menus','approval'):
            行们=分组行[组]
            if len(行们)==0:
                continue
            列表=[]
            for 行 in 行们:
                可改='modified' in 行
                在编=自身.目标 is not None and 自身.目标.get('id')==行.get('id')
                编辑树=None
                if 可改 and 在编:
                    面={**自身.编辑属性(),'target':行}
                    if 自身.编辑器 is None or 自身.编辑器.属性.get('target') is not 行:
                        自身.编辑器=快捷键编辑器(面)
                    编辑树=自身.编辑器(面)
                def 开编(目标行=行):
                    """进入行内编辑。"""
                    自身.目标=目标行
                列表.append({
                    'id':行['id'],
                    'label':行.get('label'),
                    'keys':行.get('keys') or [],
                    'editable':可改,
                    'editing':在编,
                    'editLabel':翻译('edit-label',{'command':行.get('label')}),
                    'editDisabled':自身.忙 or 配置.get('status')!='ready',
                    'onEdit':开编 if 可改 and not 在编 else None,
                    'editor':编辑树,
                    'editIcon':快捷键图标('edit') if 可改 and not 在编 else None,
                    'unboundLabel':翻译('unbound'),
                })
            行视图.append({
                'group':组,
                'groupLabel':翻译(组),
                'showHeading':组!='application',
                'rows':列表,
            })
        def 开重置():
            """打开恢复全部确认。"""
            自身.目标=None
            自身.重置修订=配置.get('revision')
        def 关确认():
            """关确认。"""
            if not 自身.忙:
                自身.重置修订=None
        def 搜(值):
            """写查询。"""
            自身.属性['actions']['search'](值)
        def 清搜():
            """清空查询。"""
            自身.属性['actions']['search']('')
        吐司树=None
        if 自身.吐司 is not None:
            吐=自身.吐司
            吐司树={
                'seq':吐['seq'],
                'text':吐['text'],
                'error':吐['error'],
                'icon':快捷键图标('error' if 吐['error'] else 'success'),
                'onDone':自身.消吐司,
            }
        return {
            'type':'shortcut-reference',
            'open':打开,
            'title':翻译('title'),
            'closeLabel':翻译('close'),
            'searchLabel':翻译('search'),
            'clearSearchLabel':翻译('clear-search'),
            'query':查询,
            'busy':自身.忙,
            'configBusy':配置.get('status')=='loading',
            'groups':行视图,
            'empty':翻译('empty') if 打开 and len(匹配)==0 else None,
            'resetAllLabel':翻译('reset-all'),
            'resetDisabled':自身.忙 or 配置.get('status')!='ready' or 改数==0,
            'modifiedCount':改数,
            'modifiedCountLabel':翻译('modified-count',{'count':改数}) if 改数>0 else None,
            'onClose':自身.关速查,
            'onSearch':搜,
            'onClearSearch':清搜,
            'onResetAll':开重置,
            'focusRequest':态.get('focusRequest'),
            'confirm':{
                'open':打开 and 自身.重置修订 is not None,
                'title':翻译('reset-title'),
                'description':翻译('reset-description'),
                'closeLabel':翻译('close-confirmation'),
                'cancelLabel':翻译('cancel'),
                'resetLabel':翻译('reset'),
                'busy':自身.忙,
                'ready':配置.get('status')=='ready',
                'onClose':关确认,
                'onCancel':关确认,
                'onConfirm':自身.全部恢复,
            },
            'toast':吐司树,
        }

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

ShortcutsRow=快捷键设置行
ShortcutReference=快捷键速查
