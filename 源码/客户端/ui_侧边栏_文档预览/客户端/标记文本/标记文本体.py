from nicegui import ui as 界面
from ....ui_基础界面组件.markdown.Markdown文本 import Markdown文本

__all__=['标记文本体','标记文本面板','样式表']

样式表='''
.document{min-width:0;padding:10px 12px;font-family:var(--dsw-font,inherit);white-space:normal}
.frontmatter{margin:0 0 16px;padding:10px 12px;border:0.5px solid var(--dsw-alias-border-l2);border-radius:var(--dsw-radius-md);background:var(--dsw-alias-bg-layer-1);font:var(--dsw-font-markdown-small);color:var(--dsw-alias-label-primary);white-space:pre-wrap;overflow-wrap:anywhere}
.frontmatter:empty{display:none}
.frontmatterSource{margin:0;font-family:var(--ds-font-family-code);white-space:inherit}
'''
界面.add_css(样式表,shared=True)

def 标记文本体(内容,翻译):
    '产出 Markdown 结构，或非文本交付时无'
    if 内容.get('kind')!='text':#非文本
        return None#无
    return {#结构
        'kind':'markdown-body',
        'text':内容['text'],
        'streaming':not 内容['eof'],
        'labels':{
            'code':{'copyLabel':翻译('code.copy'),'copiedLabel':翻译('code.copied')},
            'footnotes':翻译('footnotes'),
        },
    }#结束


def _键齐(属性):
    '内容和文案都在才画'
    return isinstance(属性,dict) and 'content' in 属性 and 't' in 属性

class 标记文本面板:
    'Markdown 正文'

    def __init__(自身,属性):
        '记下文档席 props。槽位只调用构造，键齐了才画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        if _键齐(自身.属性):
            自身.渲染()

    def 渲染(自身):
        '把文本交付画成 Markdown'
        属性=自身.属性
        if not _键齐(属性):
            return
        内容=属性['content']
        翻译=属性['t']
        模型=标记文本体(内容,翻译)
        if 模型 is None:
            return
        with 界面.column().classes('document'):
            Markdown文本({'text':模型['text'],'streaming':模型['streaming'] is True}).渲染()

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.属性=属性 if isinstance(属性,dict) else {}
        return 自身.渲染()
