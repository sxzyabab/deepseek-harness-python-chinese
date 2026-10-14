'插件页上的翻译服务、目标语言和出站说明'
from nicegui import ui as 界面
from .文案 import 表单标签

__all__=['思考设置']

def 填(翻译,键,表=None):
    '词典插值'
    文=翻译(键)
    if 表 is None:
        return 文
    return 文.format(**表)

def 读表单(属性):
    '注入面 hooks.translationForm'
    钩=属性.get('hooks') or {}
    存储=钩.get('translationForm')
    if 存储 is not None:
        return 存储.getSnapshot()
    def 全量(快照):
        '整份表单'
        return 快照
    return 属性['useTranslationForm'](全量)

def 读可用(属性):
    '注入面 hooks.availableProviders'
    钩=属性.get('hooks') or {}
    存储=钩.get('availableProviders')
    if 存储 is not None:
        return 存储.getSnapshot()
    def 全量(快照):
        '当前合格提供方'
        return 快照
    return 属性['useAvailableProviders'](全量)

def 服务名(提供方,翻译):
    '提供方在选项里的文案'
    if 提供方=='bing':
        return 翻译('bing')
    if 提供方=='google':
        return 翻译('google')
    if 提供方=='deepseek-account':
        return 翻译('deepseekAccount')
    if 提供方=='deepseek-official':
        return 翻译('deepseekOfficial')
    return 提供方

class 思考设置:
    '暂存的翻译偏好，并写明哪些文本会离开宿主'
    def __init__(自身,属性):
        '记下 props，并在刷新函数变化时重读合格路由'
        自身.属性=属性
        自身.服务标识='cot-translation-provider'
        自身.语言标识='cot-translation-language'
        自身.已刷新=None
        自身.同步()
        钩=属性.get('hooks') if isinstance(属性.get('hooks'),dict) else {}
        表单齐='translationForm' in 钩 or 'useTranslationForm' in 属性
        提供方齐='availableProviders' in 钩 or 'useAvailableProviders' in 属性
        if 't' in 属性 and 'refreshProviders' in 属性 and 表单齐 and 提供方齐:
            自身.渲染()

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性
        自身.同步()

    def 同步(自身):
        'refreshProviders 换了身份就再读一次合格路由'
        刷新=自身.属性['refreshProviders']
        if 刷新 is not 自身.已刷新:
            自身.已刷新=刷新
            刷新()

    def 改服务(自身,值):
        '写入 provider 草稿'
        自身.属性['edit']('provider',值)

    def 复位服务(自身):
        '把 provider 恢复成默认'
        自身.属性['resetField']('provider')

    def 改语言(自身,值):
        '写入 targetLanguage 草稿'
        自身.属性['edit']('targetLanguage',值)

    def 复位语言(自身):
        '把 targetLanguage 恢复成默认'
        自身.属性['resetField']('targetLanguage')

    def 渲染(自身):
        '隐私说明、服务选择和目标语言'
        翻译=自身.属性['t']
        态=读表单(自身.属性)
        可用=读可用(自身.属性)
        服务文本=态['provider']['text']
        缺失=服务文本!='' and not any(项==服务文本 for 项 in 可用)
        付费=服务文本=='deepseek-account' or 服务文本=='deepseek-official'
        禁用=not 态['writable'] or 态['saving']
        选项=[]
        if 缺失:
            选项.append({
                'value':服务文本,
                'disabled':True,
                'label':填(翻译,'providerUnavailableOption',{'provider':服务名(服务文本,翻译)}),
            })
        for 提供方 in 可用:
            选项.append({'value':提供方,'label':服务名(提供方,翻译)})
        覆盖=None
        if 态['provider']['overridden']:
            覆盖={
                'tag':翻译('overridden'),
                'resetLabel':翻译('reset'),
                'onReset':自身.复位服务,
                'disabled':禁用,
            }
        非法=None
        if 态['provider']['invalid']:
            非法=翻译('invalidProvider')
        不可用=None
        if 缺失 and not 态['provider']['invalid']:
            不可用=翻译('providerUnavailable')
        语言=态['targetLanguage']
        视图={
            'type':'translation-settings',
            'cssModule':'思考翻译.module.css',
            'labels':表单标签(翻译),
            'state':态,
            'onSave':自身.属性['save'],
            'onDiscard':自身.属性['discard'],
            'notices':[
                {'className':'notice','text':翻译('privacy')},
                {'className':'notice','text':翻译('paidNotice' if 付费 else 'anonymousNotice')},
            ],
            'provider':{
                'className':'field',
                'id':自身.服务标识,
                'label':翻译('provider'),
                'text':服务文本,
                'disabled':禁用,
                'invalid':True if 态['provider']['invalid'] else None,
                'onChange':自身.改服务,
                'overridden':覆盖,
                'options':选项,
                'invalidText':非法,
                'unavailable':不可用,
            },
            'language':{
                'id':自身.语言标识,
                'label':翻译('targetLanguage'),
                'hint':翻译('targetLanguageHint'),
                'text':语言['text'],
                'overridden':语言['overridden'],
                'invalid':语言['invalid'],
                'overriddenLabel':翻译('overridden'),
                'resetLabel':翻译('reset'),
                'invalidLabel':翻译('invalidLanguage'),
                'disabled':禁用,
                'onEdit':自身.改语言,
                'onReset':自身.复位语言,
            },
        }
        标签=表单标签(翻译)
        with 界面.column().classes('翻译设置'):
            if not 态.get('available',True):
                界面.label(标签['unavailable'])
            if not 态['writable']:
                界面.label(标签['readOnly'])
            if 态.get('failed'):
                界面.label(标签['saveFailed'])
            if 态['saving']:
                界面.label(标签['saving'])
            界面.label(翻译('privacy'))
            界面.label(翻译('paidNotice' if 付费 else 'anonymousNotice'))
            选项表={}
            for 项 in 选项:
                选项表[项['value']]=项['label']
            界面.label(翻译('provider'))
            if 覆盖 is not None:
                界面.label(覆盖['tag'])
            服务选择=界面.select(选项表, value=服务文本, on_change=lambda 事件:自身.改服务(事件.value)).props('dense options-dense')
            if 禁用:
                服务选择.disable()
            if 非法:
                界面.label(非法)
            if 不可用:
                界面.label(不可用)
            if 覆盖 is not None:
                复位服务=界面.button(覆盖['resetLabel'], on_click=覆盖['onReset']).props('flat no-caps')
                if 覆盖['disabled']:
                    复位服务.disable()
            界面.label(翻译('targetLanguage'))
            界面.label(翻译('targetLanguageHint'))
            语言输入=界面.input(value=语言['text'], on_change=lambda 事件:自身.改语言(事件.value))
            if 禁用:
                语言输入.disable()
            if 语言['overridden']:
                界面.label(翻译('overridden'))
                复位语言=界面.button(翻译('reset'), on_click=自身.复位语言).props('flat no-caps')
                if 禁用:
                    复位语言.disable()
            if 语言['invalid']:
                界面.label(翻译('invalidLanguage'))
            if callable(自身.属性.get('save')):
                保存钮=界面.button(标签['saving'] if 态['saving'] else 标签['save'], on_click=自身.属性['save']).props('flat no-caps')
                if 禁用 or not 态.get('dirty') or 态.get('invalid'):
                    保存钮.disable()
        return 视图

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
