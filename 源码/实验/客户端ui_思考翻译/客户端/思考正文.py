'一段展开思考的翻译控件'
from nicegui import ui as 界面
from .翻译 import 思考翻译

__all__=['思考正文']

def 读偏好(属性):
    '注入面 hooks.preferences'
    钩=属性.get('hooks') or {}
    存储=钩.get('preferences')
    if 存储 is not None:
        return 存储.getSnapshot()
    def 全量(快照):
        '整份偏好'
        return 快照
    return 属性['usePreferences'](全量)

def 读界面语言(属性):
    '注入面 hooks.translationLocale 的当前语言'
    钩=属性.get('hooks') or {}
    存储=钩.get('translationLocale')
    if 存储 is not None:
        return 存储.getSnapshot()['active']
    def 取当前(快照):
        '当前界面语言'
        return 快照['active']
    return 属性['useTranslationLocale'](取当前)

def 读上限(属性):
    '注入面 hooks.translationLimit'
    钩=属性.get('hooks') or {}
    存储=钩.get('translationLimit')
    if 存储 is not None:
        return 存储.getSnapshot()
    def 全量(快照):
        '请求长度上限'
        return 快照
    return 属性['useTranslationLimit'](全量)

class 思考正文:
    '渲染译文；失败重试前保留完整原文'
    def __init__(自身,属性):
        '记下 props，并按当前偏好建控制器'
        自身.属性=属性
        自身.状态={'text':属性.get('text',''),'pending':False,'failed':False}
        自身.看原文=False
        自身.控制器=None
        自身.选择=None
        自身.同步()
        钩=属性.get('hooks') if isinstance(属性.get('hooks'),dict) else {}
        偏好齐='preferences' in 钩 or 'usePreferences' in 属性
        语言齐='translationLocale' in 钩 or 'useTranslationLocale' in 属性
        上限齐='translationLimit' in 钩 or 'useTranslationLimit' in 属性
        if ('t' in 属性 and 'text' in 属性 and 'running' in 属性 and 'translate' in 属性
                and 偏好齐 and 语言齐 and 上限齐):
            自身.渲染()

    def 更新(自身,属性):
        '刷新 props，选择变了则拆掉旧控制器'
        自身.属性=属性
        自身.同步()

    def 同步(自身):
        '偏好、语言或上限变了就新建控制器，然后采用当前原文'
        偏好=读偏好(自身.属性)
        语言=读界面语言(自身.属性)
        上限=读上限(自身.属性)
        目标=语言 if 偏好['targetLanguage']=='auto' else 偏好['targetLanguage']
        选择=(偏好['provider'],目标,上限,自身.属性['translate'])
        if 选择!=自身.选择:
            if 自身.控制器 is not None:
                自身.控制器.拆除()
            自身.选择=选择
            def 发布(状态):
                '写入展示状态'
                自身.状态=状态
            自身.控制器=思考翻译(
                {'provider':偏好['provider'],'targetLanguage':目标},
                上限,
                自身.属性['translate'],
                发布,
            )
        自身.控制器.更新(自身.属性['text'],自身.属性['running'])

    def 切换(自身):
        '在原文和译文之间切换；失败时按钮不可用'
        显示原文=自身.看原文 or 自身.状态['failed']
        自身.看原文=not 显示原文

    def 重试(自身):
        '重试尚未翻译的片段'
        if 自身.控制器 is not None:
            自身.控制器.重试()

    def 标签(自身):
        '交给思考正文工厂的 Markdown 文案'
        翻译=自身.属性['t']
        return {
            'code':{
                'copyLabel':翻译('copy'),
                'copiedLabel':翻译('copied'),
                'toolbarLabels':{
                    'codeLabel':翻译('codeTitle'),
                    'wrapLabel':翻译('wrap'),
                    'unwrapLabel':翻译('unwrap'),
                },
            },
            'footnotes':翻译('footnotes'),
        }

    def 渲染(自身):
        '工具栏和原文或译文'
        翻译=自身.属性['t']
        显示原文=自身.看原文 or 自身.状态['failed']
        动作文案=翻译('translation' if 显示原文 else 'original')
        if 自身.状态['failed']:
            状态名='failed'
        elif 自身.状态['pending']:
            状态名='pending'
        else:
            状态名='ready'
        正文=自身.属性['text'] if 显示原文 else 自身.状态['text']
        转圈=None
        if 自身.状态['pending']:
            转圈={
                'role':'status',
                'aria-label':翻译('translating'),
                'className':'spinner',
                'size':14,
            }
        失败行=None
        重试行=None
        if 自身.状态['failed']:
            失败行={'className':'failure','role':'status','text':翻译('failed')}
            重试行={'size':'sm','variant':'ghost','label':翻译('retry'),'onClick':自身.重试}
        根=界面.column().classes('思考译文')
        根.props('data-cot-translation=true data-translation-state='+状态名+' data-translation-view='+('original' if 显示原文 else 'translated'))
        with 根:
            切换钮=界面.button(动作文案, on_click=自身.切换).props('flat no-caps')
            if 自身.状态['failed']:
                切换钮.disable()
                界面.label(翻译('failed'))
                界面.button(翻译('retry'), on_click=自身.重试).props('flat no-caps')
            elif 自身.状态['pending']:
                转圈标=界面.spinner(size='14px')
                转圈标.props('role=status aria-label="'+翻译('translating')+'"')
            画正文=自身.属性.get('renderFactorySlot')
            正文槽=None
            if callable(画正文):
                正文槽=画正文('conversation.chat.reasoning.content',{
                    'text':正文,
                    'running':自身.属性['running'],
                    'labels':自身.标签(),
                })
            if isinstance(正文槽,dict):
                if 正文:
                    界面.markdown(正文)
            elif isinstance(正文槽,str) and 正文槽!='':
                界面.markdown(正文槽)
            elif 正文槽 is None and not callable(画正文) and 正文:
                界面.markdown(正文)
        return {
            'type':'cot-translation-body',
            'data-cot-translation':'true',
            'data-translation-state':状态名,
            'data-translation-view':'original' if 显示原文 else 'translated',
            'cssModule':'思考翻译.module.css',
            'toolbar':{
                'className':'toolbar',
                'viewToggle':{
                    'className':'viewToggle',
                    'size':'sm',
                    'variant':'ghost',
                    'disabled':自身.状态['failed'],
                    'label':动作文案,
                    'onClick':自身.切换,
                },
                'spinner':转圈,
                'failure':失败行,
                'retry':重试行,
            },
            'content':正文槽,
        }

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
