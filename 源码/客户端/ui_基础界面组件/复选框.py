from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块

__all__=['复选框']

样式模块='checkbox'

class 复选框:
    '带可见标签的原生复选框。checked 受控'
    def __init__(自身,属性=None):
        '记下 props'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '标签包住 input 和文字'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '复选框样式',
            os.path.join(os.path.dirname(__file__),'复选框.module.css'),
            样式模块,
        )
        根=文档.createElement('label')
        类名='checkbox'
        附加=属性.get('className')
        if isinstance(附加,str) and 附加!='':
            类名=类名+' '+附加
        根.className=类名
        标样式模块(根,样式模块)
        if 'title' in 属性 and 属性['title'] is not None:
            根.title=str(属性['title'])
        框=文档.createElement('input')
        框.type='checkbox'
        框.checked=属性.get('checked') is True
        框.disabled=属性.get('disabled') is True
        def 变更(事件):
            '把请求的勾选态交给 onChange'
            改=属性.get('onChange')
            if 改 is not None:
                改(事件.target.checked is True)
        框.addEventListener('change',变更)
        字=文档.createElement('span')
        字.textContent='' if 属性.get('label') is None else str(属性['label'])
        根.appendChild(框)
        根.appendChild(字)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        return 自身.根

    def __call__(自身,属性=None):
        '再次调用时先换 props 再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
