from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块

__all__=['标签']

样式模块='tag'

class 标签:
    '只读胶囊。tone 决定调色，自己不带文案'
    def __init__(自身,属性=None):
        '记下语气和子内容'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 渲染(自身):
        '画出 data-tone 标签'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '标签样式',
            os.path.join(os.path.dirname(__file__),'标签.module.css'),
            样式模块,
        )
        根=文档.createElement('span')
        类名='tag'
        附加=属性.get('className')
        if isinstance(附加,str) and 附加!='':
            类名=类名+' '+附加
        根.className=类名
        标样式模块(根,样式模块)
        语气=属性['tone'] if 'tone' in 属性 and 属性['tone'] is not None else 'outline'
        根.setAttribute('data-tone',语气)
        子=属性.get('children')
        if isinstance(子,str):
            根.textContent=子
        elif hasattr(子,'tagName'):
            根.appendChild(子)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        return 自身.根
