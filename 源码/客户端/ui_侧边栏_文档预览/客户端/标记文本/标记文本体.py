from ....ui_基础界面组件.markdown.Markdown文本 import Markdown文本
from .前置元数据 import 拆出前置元数据
from .路径图片 import 标记文本图片地址
from .文案 import 中文

__all__=['标记文本体','标记文本面板','处理标记文本面板','样式表']

样式表='''
.document{min-width:0;padding:10px 12px;font-family:var(--dsw-font,inherit);white-space:normal}
.frontmatter{margin:0 0 16px;padding:10px 12px;border:0.5px solid var(--dsw-alias-border-l2);border-radius:var(--dsw-radius-md);background:var(--dsw-alias-bg-layer-1);font:var(--dsw-font-markdown-small);color:var(--dsw-alias-label-primary);white-space:pre-wrap;overflow-wrap:anywhere}
.frontmatter:empty{display:none}
.frontmatterSource{margin:0;font-family:var(--ds-font-family-code);white-space:inherit}
'''

def 标记文本体(内容,翻译):
    '产出 Markdown 结构，或非文本交付时无'
    if 内容.get('kind')!='text':
        return None
    return {
        'kind':'markdown-body',
        'text':内容['text'],
        'streaming':not 内容['eof'],
        'labels':{
            'code':{'copyLabel':翻译('code.copy'),'copiedLabel':翻译('code.copied')},
            'footnotes':翻译('footnotes'),
        },
    }


def _键齐(属性):
    '内容和文案都在才画'
    return isinstance(属性,dict) and 'content' in 属性 and 't' in 属性

def 处理标记文本面板(window,属性):
    '把文本交付画成 Markdown。有 parent 就挂上去'
    if not _键齐(属性):
        return None
    文档=window.document
    if 文档.getElementById('标记文本面板样式') is None:
        样式=文档.createElement('style')
        样式.id='标记文本面板样式'
        样式.textContent=样式表
        文档.head.appendChild(样式)
    内容=属性['content']
    if not isinstance(内容,dict) or 内容.get('kind')!='text':
        return None
    拆=拆出前置元数据(内容['text'])
    正文=内容['text'] if 拆 is None else 拆['body']
    列=文档.createElement('div')
    列.className='document'
    列.setAttribute('data-document-markdown','')
    if 拆 is not None:
        盒=文档.createElement('div')
        盒.className='frontmatter'
        盒.setAttribute('data-document-frontmatter','')
        源=文档.createElement('pre')
        源.className='frontmatterSource'
        源.textContent=拆['source']
        盒.appendChild(源)
        列.appendChild(盒)
    绝对=None
    if 'useResource' in 属性 and 'resourceAddress' in 属性:
        元=属性['useResource'](属性['resourceAddress'])
        值=元.get('value') if isinstance(元,dict) else None
        if isinstance(值,dict):
            绝对=值.get('absolutePath')
    def 解析图片(目标):
        '相对图片贴在这份文件旁边'
        return 标记文本图片地址(文档.baseURI,绝对,目标)
    文=Markdown文本({
        'text':正文,
        'streaming':内容.get('eof') is not True,
        'window':window,
        'labels':{
            'code':{
                'copyLabel':中文['code.copy'],
                'copiedLabel':中文['code.copied'],
                'toolbarLabels':{
                    'codeLabel':'代码块',
                    'wrapLabel':'自动换行',
                    'unwrapLabel':'取消自动换行',
                },
            },
            'footnotes':中文['footnotes'],
        },
        'pathImages':{'resolve':解析图片},
    }).渲染()
    if getattr(文,'tagName',None) is not None or getattr(文,'nodeType',None) is not None:
        列.appendChild(文)
    if 'parent' in 属性:
        属性['parent'].appendChild(列)
    return 列

class 标记文本面板:
    'Markdown 正文'

    def __init__(自身,属性):
        '记下文档席 props。有 window 且键齐了才画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if _键齐(自身.属性) and 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '拆掉旧正文，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        if 'window' not in 自身.属性:
            自身.根=None
            return None
        自身.根=处理标记文本面板(自身.属性['window'],自身.属性)
        return 自身.根

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
