"""行内物理键录制与修订感知的命令编辑。"""
import re
from .反馈 import 快捷键失败,快捷键读取失败

__all__=['快捷键编辑器']

修饰码模式=re.compile(r'^(Control|Alt|Shift|Meta)(Left|Right)$')
元键模式=re.compile(r'^Meta(Left|Right)$')

class 快捷键编辑器:
    """对着用户核对过的配置保存松开的物理组合；失败保留草稿可再录。"""
    def __init__(自身,属性):
        """记下 props 与录键态。"""
        自身.属性=属性
        自身.修订=None
        自身.候选=None
        自身.已捕获=False
        自身.忙=False
        自身.原生就绪=属性.get('runtime')=='web'
        自身.消息=''
        自身.重试=None
        自身.已挂=True
        自身.写入中=False
        自身.重置录=lambda: None
        自身.待定=None
        自身.已死=False
        自身.已拦=False
        自身.按住=set()
        自身.录键卸=None

    def 更新(自身,属性):
        """刷新 props；修订未播种时从配置取。"""
        自身.属性=属性
        if 自身.修订 is None:
            配置=自身.读配置()
            自身.修订=配置.get('revision')

    def 读配置(自身):
        """hooks.config 或 useConfig。"""
        钩=自身.属性.get('hooks') or {}
        存=钩.get('config')
        if 存 is not None:
            return 存.getSnapshot()
        取=自身.属性.get('useConfig')
        if 取 is not None:
            return 取(lambda 快照:快照)
        return {'revision':None,'status':'loading'}

    def 读目录(自身):
        """可编辑命令目录。"""
        钩=自身.属性.get('hooks') or {}
        存=钩.get('catalog')
        if 存 is not None:
            return 存.getSnapshot()
        取=自身.属性.get('useCatalog')
        if 取 is not None:
            return 取(lambda 快照:快照)
        return []

    def 读固定(自身):
        """固定目录。"""
        钩=自身.属性.get('hooks') or {}
        存=钩.get('fixedCatalog')
        if 存 is not None:
            return 存.getSnapshot()
        取=自身.属性.get('useFixedCatalog')
        if 取 is not None:
            return 取(lambda 快照:快照)
        return []

    def 桌面和弦(自身):
        """桌面 mac/win 走和弦录制。"""
        return 自身.属性.get('runtime')=='desktop' and 自身.属性.get('platform') in ('macos','windows')

    def 过期(自身):
        """草稿修订落后于配置。"""
        return 自身.修订!=自身.读配置().get('revision')

    def 报告(自身,文本):
        """写消息并上抛。"""
        自身.消息=文本
        自身.属性['onError'](文本)

    def 保存(自身,操作,已核修订=None):
        """串行写偏好。"""
        if 自身.写入中:
            return
        自身.写入中=True
        自身.忙=True
        修订=自身.修订 if 已核修订 is None else 已核修订
        结果=自身.属性['edit'](操作,修订)
        if not 自身.已挂:
            return
        自身.写入中=False
        自身.忙=False
        if 结果['status']=='saved':
            自身.属性['onSaved']()
        else:
            自身.重试=操作['binding'] if 操作.get('type')=='set' else None
            合并=list(自身.读目录())+list(自身.读固定())
            自身.报告(快捷键失败(结果,合并,自身.属性['t'],自身.属性['runtime']))

    def 捕获(自身,绑定,标识):
        """校验冲突后保存。"""
        自身.候选=绑定
        自身.已捕获=True
        自身.重试=None
        描述=自身.属性['describeBinding'](绑定)
        合并=list(自身.读目录())+list(自身.读固定())
        冲突=[]
        for 值 in 描述.get('conflicts') or []:
            if 值==标识:
                continue
            行=None
            for 项 in 合并:
                if 项.get('id')==值:
                    行=项
                    break
            冲突.append(行['label'] if 行 is not None and 'label' in 行 else 值)
        if 描述.get('issue') is not None:
            自身.报告(自身.属性['t'](描述['issue']))
            return
        if len(冲突)>0:
            自身.报告(自身.属性['t']('conflict',{'commands':', '.join(冲突)}))
            return
        if 自身.过期():
            自身.重试=绑定
            自身.报告(自身.属性['t']('stale'))
            return
        配置=自身.读配置()
        if 配置.get('status')!='ready':
            if 配置.get('status')=='loading':
                自身.报告(自身.属性['t']('not-ready'))
            else:
                自身.报告(快捷键读取失败(配置,自身.属性['runtime'],自身.属性['t']))
            return
        自身.保存({'type':'set','id':标识,'binding':绑定})

    def 重置缓冲(自身):
        """清和弦缓冲。"""
        自身.待定=None
        自身.按住.clear()
        自身.已拦=False
        自身.已死=False

    def 按下(自身,事件):
        """keydown 捕获阶段逻辑。"""
        文档=globals().get('document')
        合成观察=getattr(自身,'_合成',None)
        if 合成观察 is not None and 合成观察.guards(事件):
            if 自身.桌面和弦():
                自身.重置缓冲()
            return
        if 事件.getModifierState and 事件.getModifierState('AltGraph'):
            if 自身.桌面和弦():
                自身.重置缓冲()
            return
        录钮=getattr(自身,'_录钮',None)
        if ((not 自身.桌面和弦() or (文档 is not None and 文档.activeElement is not 录钮))
            and 事件.key=='Escape' and not 事件.ctrlKey and not 事件.altKey and not 事件.metaKey and not 事件.shiftKey):
            事件.preventDefault()
            事件.stopPropagation()
            if not 事件.repeat and not 自身.写入中:
                自身.属性['onClose']()
            return
        命令死键=(自身.属性.get('runtime')=='web' and 自身.属性.get('platform')=='macos'
            and 文档 is not None and 文档.activeElement is 录钮
            and 事件.code=='KeyN' and 事件.metaKey and 事件.altKey and not 事件.ctrlKey and not 事件.shiftKey)
        if 事件.key=='Dead' and not 命令死键:
            if 自身.桌面和弦():
                自身.重置缓冲()
            自身.已死=True
            return
        if 自身.已死:
            自身.已死=False
            return
        修饰=[名 for 名 in ('control','alt','shift','meta') if {
            'control':事件.ctrlKey,'alt':事件.altKey,'shift':事件.shiftKey,'meta':事件.metaKey,
        }[名]]
        录Tab=自身.桌面和弦() or (自身.属性.get('platform') in ('macos','windows') and len(修饰)>=3)
        if 文档 is None or 文档.activeElement is not 录钮 or (事件.key=='Tab' and not 录Tab):
            return
        事件.preventDefault()
        事件.stopPropagation()
        if 自身.写入中 or 事件.repeat:
            return
        if 修饰码模式.match(事件.code):
            if 自身.桌面和弦() and 自身.待定 is not None:
                自身.重置缓冲()
                自身.候选=None
                自身.已捕获=False
            return
        if 自身.桌面和弦():
            自身.按住.add(事件.code)
            if 自身.已拦:
                return
            if len(自身.按住)>2:
                自身.已拦=True
                自身.待定=None
                自身.报告(自身.属性['t']('too-many-keys'))
                return
        try:
            码表=[事件.code]
            if 自身.桌面和弦():
                码表.extend([值 for 值 in 自身.按住 if 值!=事件.code])
            载荷={'code':码表[0],'modifiers':修饰}
            if len(码表)>1:
                载荷['secondCode']=码表[1]
            自身.待定=自身.属性['describeBinding'](载荷)['binding']
            自身.候选=自身.待定
            自身.已捕获=自身.桌面和弦()
            自身.消息=''
            自身.重试=None
        except Exception:
            自身.已拦=自身.桌面和弦()
            自身.待定=None
            自身.报告(自身.属性['t']('unsupported-key'))

    def 抬起(自身,事件):
        """keyup 捕获阶段逻辑。"""
        文档=globals().get('document')
        录钮=getattr(自身,'_录钮',None)
        自身.按住.discard(事件.code)
        if 自身.桌面和弦() and 文档 is not None and 文档.activeElement is 录钮:
            事件.preventDefault()
            事件.stopPropagation()
        绑定=None
        if 自身.待定 is not None:
            待=自身.待定
            命中=(待.get('code')==事件.code or 待.get('secondCode')==事件.code
                or any(修饰==事件.code.replace('Left','').replace('Right','').lower() for 修饰 in 待.get('modifiers') or []))
            if 命中:
                绑定=待
        if 绑定 is not None:
            自身.待定=None
            自身.已拦=自身.桌面和弦()
        if 自身.桌面和弦() and (len(自身.按住)==0 or (自身.属性.get('platform')=='macos' and 元键模式.match(事件.code))):
            自身.按住.clear()
            自身.已拦=False
        if 绑定 is None:
            return
        自身.捕获(绑定,自身.属性['target']['id'])

    def 失焦(自身):
        """窗口/合成失焦清缓冲。"""
        自身.重置缓冲()
        if 自身.桌面和弦():
            自身.候选=None
            自身.已捕获=False

    def 启用录键(自身,录钮=None,合成观察=None):
        """挂 document 监听并开原生录键保护。"""
        自身._录钮=录钮
        自身._合成=合成观察
        自身.已挂=True
        文档=globals().get('document')
        窗=globals().get('window')
        录制=自身.属性['recording']
        def 成():
            """原生保护就绪。"""
            自身.原生就绪=True
        def 败(_错误=None):
            """原生保护失败。"""
            自身.报告(自身.属性['t']('native-failed'))
        结果=录制(True)
        if hasattr(结果,'then'):
            结果.then(成,败)
        else:
            成()
        自身.重置录=自身.重置缓冲
        def 焦(_事件=None):
            """焦点离开录钮则等同失焦。"""
            if 文档 is not None and 文档.activeElement is not 自身._录钮:
                自身.失焦()
        if 文档 is not None:
            文档.addEventListener('keydown',自身.按下,True)
            文档.addEventListener('keyup',自身.抬起,True)
            if 自身.桌面和弦():
                文档.addEventListener('focusin',焦,True)
                文档.addEventListener('compositionstart',自身.失焦,True)
        if 窗 is not None:
            窗.addEventListener('blur',自身.失焦)
        def 卸():
            """拆监听并关录键保护。"""
            自身.已挂=False
            if 合成观察 is not None:
                合成观察.dispose()
            if 文档 is not None:
                文档.removeEventListener('keydown',自身.按下,True)
                文档.removeEventListener('keyup',自身.抬起,True)
                文档.removeEventListener('focusin',焦,True)
                文档.removeEventListener('compositionstart',自身.失焦,True)
            if 窗 is not None:
                窗.removeEventListener('blur',自身.失焦)
            关=录制(False)
            if hasattr(关,'catch'):
                关.catch(lambda _e:None)
        自身.录键卸=卸
        return 卸

    def 拆除录键(自身):
        """幂等拆。"""
        if 自身.录键卸 is not None:
            自身.录键卸()
            自身.录键卸=None

    def 恢复默认(自身):
        """写 reset。"""
        自身.保存({'type':'reset','id':自身.属性['target']['id']})

    def 清除绑定(自身):
        """写 set null。"""
        自身.保存({'type':'set','id':自身.属性['target']['id'],'binding':None})

    def 核对修订(自身):
        """接受当前配置修订。"""
        自身.修订=自身.读配置().get('revision')
        自身.消息=''

    def 重试保存(自身):
        """对重试绑定再捕获。"""
        if 自身.重试 is not None:
            自身.捕获(自身.重试,自身.属性['target']['id'])

    def 点录钮(自身):
        """清空后准备再录。"""
        if not 自身.写入中:
            自身.重置录()
            自身.已捕获=False
            自身.消息=''
            自身.重试=None

    def 帮助键(自身):
        """无错误时的帮助文案键。"""
        if 自身.桌面和弦():
            return ''
        if 自身.属性.get('runtime')=='web':
            平台=自身.属性.get('platform')
            if 平台=='windows':
                return 'windows-web-help'
            if 平台=='macos':
                return 'macos-web-help'
            return 'web-help'
        return 'record-help'

    def 渲染(自身):
        """行内控件树。"""
        翻译=自身.属性['t']
        目标=自身.属性['target']
        配置=自身.读配置()
        if 自身.修订 is None:
            自身.修订=配置.get('revision')
        只读=自身.忙 or 自身.过期() or 配置.get('status')!='ready'
        已录键=None
        if 自身.已捕获 and 自身.消息=='' and 自身.候选 is not None:
            已录键=自身.属性['describeBinding'](自身.候选).get('keys')
        帮助=自身.帮助键()
        return {
            'type':'shortcut-editor',
            'role':'group',
            'ariaLabel':目标.get('label'),
            'shortcutModal':'shortcut-edit',
            'busy':自身.忙,
            'readonly':只读,
            'nativeReady':自身.原生就绪,
            'message':自身.消息,
            'stale':自身.过期(),
            'retry':自身.重试,
            'capturedKeys':已录键,
            'hasBinding':目标.get('binding') is not None,
            'recordLabel':翻译('record'),
            'resetLabel':翻译('reset'),
            'clearLabel':翻译('clear'),
            'reviewLabel':翻译('review'),
            'retryLabel':翻译('retry-save'),
            'staleText':翻译('stale'),
            'helpText':'' if 帮助=='' else 翻译(帮助),
            'onReset':自身.恢复默认,
            'onClear':自身.清除绑定,
            'onReview':自身.核对修订,
            'onRetry':自身.重试保存,
            'onRecordClick':自身.点录钮,
            'onRecordBlur':自身.重置录,
            'enableCapture':自身.启用录键,
            'disposeCapture':自身.拆除录键,
        }

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

ShortcutEditor=快捷键编辑器
