from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块

__all__=['分段标签页']

样式模块='segmented-tabs'

class 分段标签页:
    '等宽标签。滑块跟着选中项。只有选中项能被 Tab 停住'
    def __init__(自身,属性=None):
        '记下标签和当前值'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 渲染(自身):
        '画出 tablist'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(文档,'分段标签页样式',os.path.join(os.path.dirname(__file__),'分段标签页.module.css'),样式模块)
        项列=属性['items'] if isinstance(属性.get('items'),(list,tuple)) else []
        值=属性.get('value')
        选中=0
        序=0
        for 项 in 项列:
            if 项.get('value')==值:
                选中=序
            序=序+1
        根=文档.createElement('div')
        根.setAttribute('role','tablist')
        根.setAttribute('aria-label','' if 属性.get('label') is None else str(属性['label']))
        根.className='tabs'
        附加=属性.get('className')
        if isinstance(附加,str) and 附加!='':
            根.className=根.className+' '+附加
        标样式模块(根,样式模块)
        根.style.gridTemplateColumns='repeat('+str(len(项列))+', minmax(0, 1fr))'
        滑=文档.createElement('span')
        滑.className='indicator'
        标样式模块(滑,样式模块)
        滑.setAttribute('aria-hidden','true')
        if len(项列)>0:
            滑.style.width='calc((100% - 8px) / '+str(len(项列))+')'
            滑.style.transform='translateX('+str(选中*100)+'%)'
        根.appendChild(滑)
        序=0
        for 项 in 项列:
            活=项.get('value')==值
            钮=文档.createElement('button')
            钮.type='button'
            钮.id=str(项.get('id'))
            钮.className='tab'
            标样式模块(钮,样式模块)
            钮.setAttribute('role','tab')
            钮.setAttribute('aria-selected','true' if 活 else 'false')
            钮.setAttribute('aria-controls',str(项.get('panelId')))
            钮.tabIndex=0 if 活 else -1
            钮.textContent='' if 项.get('label') is None else str(项['label'])
            def 点下(事件,项=项):
                '交给 onChange'
                改=属性.get('onChange')
                if 改 is not None:
                    改(项.get('value'))
            def 按键(事件,序=序):
                '左右和 Home、End 移动选中并聚焦'
                if 事件.key=='ArrowLeft':
                    下=(序+len(项列)-1)%len(项列)
                elif 事件.key=='ArrowRight':
                    下=(序+1)%len(项列)
                elif 事件.key=='Home':
                    下=0
                elif 事件.key=='End':
                    下=len(项列)-1
                else:
                    return
                事件.preventDefault()
                事件.stopPropagation()
                钮列=根.querySelectorAll('[role="tab"]')
                if 下<钮列.length:
                    钮列.item(下).focus()
                改=属性.get('onChange')
                if 改 is not None:
                    改(项列[下].get('value'))
            钮.addEventListener('click',点下)
            钮.addEventListener('keydown',按键)
            根.appendChild(钮)
            序=序+1
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        return 根
