'侧边栏里的一个检查器，本地选择对话分组或原始日志'

from .检查器表格 import 检查器表格
from .聊天节点.定位 import 检查器聊天定位器

__all__=['会话检查器视图']

def 行钩(属性,名):
    'hooks 里的快照，或已经绑好的 use 钩子'
    钩=(属性.get('hooks') or {}).get(名)
    if 钩 is not None:
        def 使用(选择,钩=钩):
            '把快照交给选择函数'
            return 选择(钩.getSnapshot())
        return 使用
    return 属性['use'+名[0].upper()+名[1:]]

def 记录钩(属性,名):
    'keyedHooks 返回记录源时取出当前快照'
    钩=(属性.get('keyedHooks') or {}).get(名)
    if 钩 is not None:
        def 使用(键,钩=钩):
            '没有来源时是 None'
            源=钩(键)
            if 源 is None:
                return None
            if hasattr(源,'getSnapshot'):
                return 源.getSnapshot()
            return 源
        return 使用
    return 属性['use'+名[0].upper()+名[1:]]

class 会话检查器视图:
    '工具条里切换展示；只有当前表格订阅'
    def __init__(自身,属性):
        '默认原始日志，选取和定位都空着'
        自身.属性=属性
        自身.展示='session-log'
        自身.选取中=False
        自身.选取失败=False
        自身.选取行=None
        自身._选取按钮=None
        自身._选取停止=None
        自身._选取键=None
        自身.定位器=None
        自身._根=None
        自身._定位展示=None
        自身.表=None
        自身._表模式=None

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性

    def _同步定位器(自身):
        '聊天根或展示变了就拆掉上一个定位器'
        根=自身.属性['chatRoot']
        if 自身._根 is not 根:
            if 自身.定位器 is not None:
                自身.定位器.拆除()
            自身.定位器=检查器聊天定位器(根)
            自身._根=根
            自身._定位展示=自身.展示
            return
        if 自身._定位展示!=自身.展示:
            自身.定位器.拆除()
            自身._定位展示=自身.展示

    def _同步选取(自身):
        '选取中且按钮还在时启动选取；条件变了先停上一次'
        键=(自身.选取中,自身.展示,自身.属性.get('pickChat'),自身.属性.get('pickRow'),自身.定位器,自身._选取按钮)
        if 自身._选取键==键:
            return
        if 自身._选取停止 is not None:
            停止=自身._选取停止
            自身._选取停止=None
            停止()
        自身._选取键=键
        if not 自身.选取中 or 自身._选取按钮 is None:
            return
        自身.定位器.拆除()
        def 选中(目标):
            '匹配到行就结束选取'
            行键=自身.属性['pickRow'](目标,自身.展示)
            if 行键 is None:
                自身.选取失败=True
                return False
            自身.选取行={'key':行键}
            自身.选取中=False
            自身.选取失败=False
            return True
        def 取消():
            '手势取消时清掉选取状态'
            自身.选取中=False
            自身.选取失败=False
        停止=自身.属性['pickChat'](自身._选取按钮,选中,取消)
        if 停止 is None:
            自身.选取中=False
            自身.选取失败=True
            自身._选取键=(False,自身.展示,自身.属性.get('pickChat'),自身.属性.get('pickRow'),自身.定位器,自身._选取按钮)
            return
        自身._选取停止=停止

    def _揭示(自身,目标):
        '按解析出的坐标定位主对话'
        自身.定位器.定位(自身.属性['resolveChatTargets'](目标))

    def _目标(自身,键):
        '当前展示下这一行的对话坐标'
        if 自身.展示=='chat-node':
            行=自身.属性['objects']['row'](键)
            if 行 is None:
                return None
            if isinstance(行,dict):
                return 行.get('target')
            return getattr(行,'target',None)
        return 自身.属性['logChatTarget'](键)

    def _改展示(自身,事件):
        '换展示时清掉选取'
        当前=事件['currentTarget'] if isinstance(事件,dict) else 事件.currentTarget
        值=当前['value'] if isinstance(当前,dict) else 当前.value
        自身.选取中=False
        自身.选取失败=False
        自身.选取行=None
        自身.展示='chat-node' if 值=='chat-node' else 'session-log'

    def _点选取(自身):
        '切换选取，并清掉失败提示'
        自身.选取失败=False
        自身.选取中=not 自身.选取中

    def _记按钮(自身,元素):
        '选取按钮；到达后才能开始选取'
        自身._选取按钮=元素
        自身._同步选取()

    def _类型(自身,键):
        '当前展示下这一行的原始类型'
        return 自身.属性['recordType'](键,自身.展示)

    def 渲染(自身):
        '展示选择、选取按钮，以及按展示换掉的表格'
        自身._同步定位器()
        自身._同步选取()
        属性=自身.属性
        翻译=属性['t']
        聊天=自身.展示=='chat-node'
        if 自身.选取中:
            通知=翻译('picker.noMatch' if 自身.选取失败 else 'picker.instructions')
        elif 自身.选取失败:
            通知=翻译('picker.noChat')
        else:
            通知=None
        选择器={
            'type':'span',
            'className':'modeControls',
            'cssModule':'检查器.module.css',
            'select':{
                'className':'modeSelector',
                'aria-label':翻译('view.presentation'),
                'value':自身.展示,
                'onChange':自身._改展示,
                'options':[
                    {'value':'session-log','label':翻译('view.sessionLog')},
                    {'value':'chat-node','label':翻译('view.chatNode')},
                ],
            },
            'pick':{
                'type':'button',
                'className':'pickButton',
                'ref':自身._记按钮,
                'aria-pressed':自身.选取中,
                'aria-label':翻译('picker.pick'),
                'title':翻译('picker.cancel' if 自身.选取中 else 'picker.pick'),
                'onClick':自身._点选取,
                'icon':{'type':'svg','width':16,'height':16,'viewBox':'0 0 16 16','fill':'none','stroke':'currentColor','strokeWidth':1.3,'aria-hidden':True,'circle':{'cx':8,'cy':8,'r':4.5},'path':'M8 0v5M8 11v5M0 8h5M11 8h5'},
            },
        }
        表属性={
            'title':翻译('view.chatNode' if 聊天 else 'view.sessionLog'),
            'modeSelector':选择器,
            'pickedRow':自身.选取行,
            'notice':通知,
            'useRows':行钩(属性,'chatRows' if 聊天 else 'logRows'),
            'useRecord':记录钩(属性,'chatRecord' if 聊天 else 'logRecord'),
            'useSession':属性['useSession'],
            'loadOlder':属性['loadOlder'],
            'typeOf':自身._类型,
            't':翻译,
            'flash':聊天,
            'showTime':not 聊天,
            'navigation':{'reveal':自身._揭示,'target':自身._目标},
        }
        if 聊天:
            表属性['objects']=属性['objects']
        if 自身.表 is None or 自身._表模式!=自身.展示:
            自身.表=检查器表格(表属性)
            自身._表模式=自身.展示
        else:
            自身.表.更新(表属性)
        return 自身.表.渲染()

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
