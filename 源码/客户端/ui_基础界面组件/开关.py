from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块

__all__=['开关']

样式模块='switch'

class 开关:
    '两态开关。checked 完全受控，label 是无障碍名'
    def __init__(自身,属性=None):
        '记下 props'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '画出 role=switch 的按钮和滑块'
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '开关样式',
            os.path.join(os.path.dirname(__file__),'开关.module.css'),
            样式模块,
        )
        选中=属性.get('checked') is True
        禁用=属性.get('disabled') is True
        钮=文档.createElement('button')
        钮.type='button'
        钮.setAttribute('role','switch')
        钮.setAttribute('aria-checked','true' if 选中 else 'false')
        钮.setAttribute('aria-label','' if 属性.get('label') is None else str(属性['label']))
        if 'title' in 属性 and 属性['title'] is not None:
            钮.title=str(属性['title'])
        钮.disabled=禁用
        类名='switch'
        附加=属性.get('className')
        if isinstance(附加,str) and 附加!='':
            类名=类名+' '+附加
        钮.className=类名
        标样式模块(钮,样式模块)
        块=文档.createElement('span')
        块.className='thumb'
        标样式模块(块,样式模块)
        钮.appendChild(块)
        def 点下(事件):
            '把点击要求的下一态交给 onChange'
            改=属性.get('onChange')
            if 改 is None:
                return
            改(选中 is False)
        钮.addEventListener('click',点下)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(钮)
        自身.根=钮
        return 自身.根

    def __call__(自身,属性=None):
        '再次调用时先换 props 再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
