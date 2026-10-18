from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块
from .markdown.高亮 import 支持高亮
from .提示泡 import 提示泡
from .icons import 图标勾描边常规,图标复制描边常规,图标不换行填充常规,图标换行填充常规

__all__=['代码工具栏']

样式模块='code-card'

class 代码工具栏:
    '代码卡顶栏：语言、标题、换行和复制'
    def __init__(自身,属性=None):
        '记下状态和回调'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 渲染(自身):
        '画出顶栏。动作钮带向上的提示泡'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(文档,'代码卡片样式',os.path.join(os.path.dirname(__file__),'代码卡片.module.css'),样式模块)
        标签=属性['labels'] if isinstance(属性.get('labels'),dict) else {}
        根=文档.createElement('div')
        根.className='header'
        标样式模块(根,样式模块)
        根.setAttribute('data-code-block-banner','')
        头=文档.createElement('div')
        头.className='heading'
        标样式模块(头,样式模块)
        语=文档.createElement('span')
        语.className='language'
        标样式模块(语,样式模块)
        语言=属性.get('lang')
        if 支持高亮(语言):
            语.textContent=str(语言)
        else:
            语.textContent='' if 标签.get('codeLabel') is None else str(标签['codeLabel'])
        头.appendChild(语)
        if 'title' in 属性 and 属性['title'] is not None:
            题=文档.createElement('span')
            题.className='title'
            标样式模块(题,样式模块)
            题.title=str(属性['title'])
            题.textContent=str(属性['title'])
            头.appendChild(题)
        根.appendChild(头)
        动作=文档.createElement('div')
        动作.className='actions'
        标样式模块(动作,样式模块)
        if 'status' in 属性 and 属性['status'] is not None:
            状=文档.createElement('span')
            状.className='status'
            标样式模块(状,样式模块)
            状.textContent=str(属性['status'])
            动作.appendChild(状)
        换行中=属性.get('wrapped') is True
        已复制=属性.get('copied') is True
        换文=标签.get('unwrapLabel') if 换行中 else 标签.get('wrapLabel')
        剪文=属性.get('copiedLabel') if 已复制 else 属性.get('copyLabel')
        if 属性.get('onWrap') is not None:
            钮=文档.createElement('button')
            钮.type='button'
            钮.className='action'
            标样式模块(钮,样式模块)
            钮.setAttribute('aria-label','' if 标签.get('wrapLabel') is None else str(标签['wrapLabel']))
            钮.setAttribute('aria-pressed','true' if 换行中 else 'false')
            图=图标不换行填充常规({'window':窗口,'size':14}) if 换行中 else 图标换行填充常规({'window':窗口,'size':14})
            if 图 is not None:
                钮.appendChild(图)
            def 点换(事件):
                '切换换行'
                属性['onWrap']()
            钮.addEventListener('click',点换)
            提示泡({'window':窗口,'label':'' if 换文 is None else str(换文),'side':'top','portal':True,'children':钮}).渲染()
            动作.appendChild(钮)
        if 属性.get('onCopy') is not None:
            钮=文档.createElement('button')
            钮.type='button'
            钮.className='action'
            标样式模块(钮,样式模块)
            钮.setAttribute('aria-label','' if 剪文 is None else str(剪文))
            图=图标勾描边常规({'window':窗口,'size':14}) if 已复制 else 图标复制描边常规({'window':窗口,'size':14})
            if 图 is not None:
                钮.appendChild(图)
            def 点复(事件):
                '复制'
                属性['onCopy']()
            钮.addEventListener('click',点复)
            提示泡({'window':窗口,'label':'' if 剪文 is None else str(剪文),'side':'top','portal':True,'children':钮}).渲染()
            动作.appendChild(钮)
        根.appendChild(动作)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        return 根
