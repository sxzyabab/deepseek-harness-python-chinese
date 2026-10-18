from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块
from .引用图标 import 引用图标常规

__all__=['用户文本段','引用芯片']

样式模块='user-text'

def 确保样式(文档):
    '用户文本样式只插一次'
    注入模块样式文件(文档,'用户文本样式',os.path.join(os.path.dirname(__file__),'用户文本.module.css'),样式模块)

class 用户文本段:
    '不解释的一段用户文字'
    def __init__(自身,属性=None):
        '记下原文'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
    def 渲染(自身):
        '原样画出'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        确保样式(文档)
        if 自身.根 is not None:
            自身.根.remove()
        根=文档.createElement('span')
        根.className='plainRun'
        标样式模块(根,样式模块)
        根.textContent='' if 属性.get('text') is None else str(属性['text'])
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        return 根

class 引用芯片:
    '引用标签。没有激活回调时只是文字。连点或正在选字不激活'
    def __init__(自身,属性=None):
        '记下外观和标签'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
    def 渲染(自身):
        'skill 和 command 不画图标，其余画引用图标'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        确保样式(文档)
        if 自身.根 is not None:
            自身.根.remove()
        外观='' if 属性.get('appearance') is None else str(属性['appearance'])
        斜杠=外观 in ('skill','command')
        类名='refChip'
        if 斜杠:
            类名=类名+' slashChip'
        激活=属性.get('onActivate')
        if 激活 is None:
            根=文档.createElement('span')
        else:
            根=文档.createElement('button')
            根.type='button'
            类名=类名+' fileMention'
        根.className=类名
        标样式模块(根,样式模块)
        根.setAttribute('data-ref-chip',外观)
        根.title='' if 属性.get('title') is None else str(属性['title'])
        if not 斜杠 and 外观 in ('session','file','folder'):
            图=引用图标常规({'window':窗口,'kind':外观,'size':16,'className':'refIcon'})
            if 图 is not None:
                标样式模块(图,样式模块)
                根.appendChild(图)
        根.appendChild(文档.createTextNode('' if 属性.get('label') is None else str(属性['label'])))
        if 激活 is not None:
            def 点下(事件):
                '连点或选中文字时不激活'
                次数=getattr(事件,'detail',0)
                if 次数>1:
                    return
                if 次数!=0:
                    选=文档.getSelection()
                    if 选 is not None and 选.isCollapsed is False:
                        return
                激活()
            根.addEventListener('click',点下)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        return 根
