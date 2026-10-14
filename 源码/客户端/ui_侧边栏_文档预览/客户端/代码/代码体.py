from nicegui import ui as 界面
from ....ui_基础界面组件.代码高亮语法 import 路径语言
from ....ui_基础界面组件.markdown.代码块 import 代码块
from ..远程过程调用 import 宿主文件#宿主文件

__all__=['代码体','代码面板','样式表']
样式表='''
.renderer{display:flex;flex:1 1 auto;flex-direction:column;width:100%;height:100%;min-width:0;min-height:0;overflow:hidden;white-space:normal}
.renderer .code{--dsl-code-block-border-radius:0px;--dsl-code-block-background:transparent;display:flex;flex:1 1 auto;flex-direction:column;height:100%;min-height:0;margin:0}
.renderer .code pre{box-sizing:border-box;padding:16px;min-width:100%;white-space:pre}
.renderer[data-wrap=true] .code pre{white-space:pre-wrap;overflow-wrap:anywhere}
'''
界面.add_css(样式表,shared=True)

def 代码体(资源地址,内容,换行,翻译):
    '产出稳定代码块结构，或字节内容时无正文'
    if 内容.get('kind')!='text':#非文本
        return None#无
    文件=宿主文件(资源地址)#会话文件
    语言=路径语言(文件['path'])#文法
    return {#结构
        'kind':'code-body',
        'wrap':换行,
        'code':内容['text'],
        'lang':语言,
        'streaming':not 内容['eof'],
        'copyLabel':翻译('copy'),
        'copiedLabel':翻译('copied'),
    }#结束


def _键齐(属性):
    '内容、地址和文案都在才画'
    return isinstance(属性,dict) and 'content' in 属性 and 'resourceAddress' in 属性 and 't' in 属性

class 代码面板:
    '高亮代码正文与复制'

    def __init__(自身,属性):
        '记下文档席 props。槽位只调用构造，键齐了才画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        if _键齐(自身.属性):
            自身.渲染()

    def 渲染(自身):
        '文本交付画成代码块；字节交付不画正文'
        属性=自身.属性
        if not _键齐(属性):
            return
        内容=属性['content']
        地址=属性['resourceAddress']
        翻译=属性['t']
        换行=属性['wrap'] is True if 'wrap' in 属性 else False
        模型=代码体(地址,内容,换行,翻译)
        if 模型 is None:
            return
        根=界面.column().classes('renderer')
        if 模型['wrap'] is True:
            根.props('data-wrap=true')
        with 根:
            代码块({
                'code':模型['code'],
                'lang':模型['lang'],
                'copyLabel':模型['copyLabel'],
                'copiedLabel':模型['copiedLabel'],
            }).渲染()

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.属性=属性 if isinstance(属性,dict) else {}
        return 自身.渲染()
