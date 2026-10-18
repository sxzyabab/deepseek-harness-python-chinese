from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块
from .icons import 图标关闭描边常规

__all__=['图像灯箱']

样式模块='lightbox'

class 图像灯箱:
    '点缩略图后的原图预览。Escape、点遮罩或关闭钮都会关，卸下时把焦点还回打开前的元素'
    def __init__(自身,属性=None):
        '记下地址和文案'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.拆除=None

    def 渲染(自身):
        '画到 body 上，盖住视口'
        if 自身.拆除 is not None:
            自身.拆除()
            自身.拆除=None
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(文档,'图像灯箱样式',os.path.join(os.path.dirname(__file__),'图像灯箱.module.css'),样式模块)
        标签=属性['labels'] if isinstance(属性.get('labels'),dict) else {}
        还原=文档.activeElement if hasattr(文档.activeElement,'focus') else None
        罩=文档.createElement('div')
        罩.className='backdrop'
        标样式模块(罩,样式模块)
        罩.setAttribute('role','dialog')
        罩.setAttribute('aria-modal','true')
        罩.setAttribute('aria-label','' if 标签.get('dialog') is None else str(标签['dialog']))
        台=文档.createElement('div')
        台.className='stage'
        标样式模块(台,样式模块)
        蒙=文档.createElement('div')
        蒙.className='mask'
        标样式模块(蒙,样式模块)
        蒙.setAttribute('aria-hidden','true')
        def 关(事件=None):
            '交给打开方'
            回=属性.get('onClose')
            if 回 is not None:
                回()
        蒙.addEventListener('mousedown',关)
        图=文档.createElement('img')
        图.className='image'
        标样式模块(图,样式模块)
        图.src='' if 属性.get('src') is None else str(属性['src'])
        图.alt='' if 属性.get('alt') is None else str(属性['alt'])
        钮=文档.createElement('button')
        钮.type='button'
        钮.className='close'
        标样式模块(钮,样式模块)
        钮.setAttribute('aria-label','' if 标签.get('close') is None else str(标签['close']))
        图标=图标关闭描边常规({'window':窗口,'size':16})
        if 图标 is not None:
            钮.appendChild(图标)
        钮.addEventListener('click',关)
        台.appendChild(蒙)
        台.appendChild(图)
        台.appendChild(钮)
        罩.appendChild(台)
        文档.body.appendChild(罩)
        钮.focus()
        def 按键(事件):
            'Escape 关闭。Tab 只停在关闭钮上'
            if 事件.key=='Escape':
                事件.stopPropagation()
                关()
            if 事件.key=='Tab':
                事件.preventDefault()
                钮.focus()
        窗口.addEventListener('keydown',按键,True)
        def 拆除():
            '卸键盘，并把焦点还回去'
            窗口.removeEventListener('keydown',按键,True)
            if 还原 is not None:
                还原.focus()
        自身.拆除=拆除
        自身.根=罩
        return 罩
