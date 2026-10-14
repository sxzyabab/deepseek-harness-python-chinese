'会话 Header 下载项与 /export 共用的状态对话框'
from nicegui import ui as 界面

__all__=['会话日志下载对话框']

样式表='''
.q-card.导出会话对话{box-sizing:border-box;border:0.5px solid var(--dsw-alias-border-inverted);background:var(--dsw-alias-bg-layer-2)}
.导出会话内容{display:flex;flex-direction:column;width:100%;max-width:420px}
.导出会话题{margin:0;padding:22px 24px 8px;font-size:16px;line-height:24px;font-weight:500;color:var(--dsw-alias-label-primary)}
.导出会话述{margin:0;padding:0 24px 8px;font-size:14px;line-height:22px;color:var(--dsw-alias-label-primary)}
.导出会话动作{display:flex;justify-content:flex-end;width:100%;padding:8px 24px 20px}
button.q-btn.导出会话关{min-width:72px;height:36px;padding:0 16px;border-radius:var(--dsw-radius-md);font-size:14px;font-weight:500;background:var(--dsw-alias-label-primary) !important;color:var(--dsw-alias-bg-layer-3) !important}
'''

界面.add_css(样式表,shared=True)

def 是绝对路径(词):
    '空白分隔后的一词是否为绝对路径或家目录路径'
    统一=词.strip('\'"').replace('\\','/')
    if 统一.startswith('/') or 统一.startswith('~/'):
        return True
    if len(统一)>2 and 统一[0].isalpha() and 统一[1]==':' and 统一[2]=='/':
        return True
    return False

def 失败说明(原文,兜底):
    '失败句去掉绝对路径；没有剩下的字就用兜底'
    if isinstance(原文,BaseException):
        文本=str(原文.args[0]) if len(原文.args)>0 else ''
    elif isinstance(原文,str):
        文本=原文
    else:
        return 兜底
    留下=[]
    for 词 in 文本.split():
        if 是绝对路径(词):
            continue
        留下.append(词)
    说明=' '.join(留下).strip()
    if 说明=='':
        return 兜底
    return 说明

def 读下载(属性):
    '注入面 hooks.sessionLogDownload 的整份快照'
    钩=属性['hooks'] if 'hooks' in 属性 and 属性['hooks'] is not None else {}
    存储=钩['sessionLogDownload'] if isinstance(钩,dict) and 'sessionLogDownload' in 钩 else None
    if 存储 is not None:
        return 存储.getSnapshot()
    if 'useSessionLogDownload' in 属性 and 属性['useSessionLogDownload'] is not None:
        return 属性['useSessionLogDownload'](lambda 快照:快照)
    return {'bySession':{}}

class 会话日志下载对话框:
    '按会话展示准备中、已开始或失败'
    def __init__(自身,属性):
        '记下 props。父组件调用渲染，构造不画'
        自身.属性=属性

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性

    def 条目(自身):
        '当前会话的对话框条目；没有则未打开'
        状态=读下载(自身.属性)
        按会话=状态['bySession'] if isinstance(状态,dict) and 'bySession' in 状态 and 状态['bySession'] is not None else {}
        标识=自身.属性['sessionId'] if 'sessionId' in 自身.属性 else None
        return 按会话[str(标识)] if str(标识) in 按会话 else None

    def 关闭(自身):
        '关掉对话框，不取消在途下载'
        自身.属性['dismiss'](自身.属性['sessionId'])

    def 渲染(自身):
        '打开时画标题、说明和关闭'
        条目=自身.条目()
        if 条目 is None or 条目.get('open') is not True:
            return
        翻译=自身.属性['t']
        状态=条目.get('status')
        if 状态=='error':
            说明原文=失败说明(条目.get('error'),翻译('dialog.commandFailed'))
        else:
            说明原文=None
        if 状态=='downloading':
            标题=翻译('dialog.preparingTitle')
            说明=翻译('dialog.preparingDescription')
        elif 状态=='success':
            标题=翻译('dialog.successTitle')
            说明=翻译('dialog.successDescription')
        else:
            标题=翻译('dialog.errorTitle')
            说明=说明原文 or 翻译('dialog.commandFailed')
        with 界面.dialog() as 对话框:
            with 界面.card().classes('导出会话对话'):
                with 界面.column().classes('导出会话内容'):
                    界面.label(标题).classes('导出会话题')
                    界面.label(说明).classes('导出会话述')
                    with 界面.row().classes('导出会话动作'):
                        界面.button(翻译('dialog.close'), on_click=自身.关闭).props('unelevated no-caps').classes('导出会话关')
        对话框.open()

    def __call__(自身,属性=None):
        '对齐调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
