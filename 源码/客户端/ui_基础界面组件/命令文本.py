from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块

__all__=['命令文本']

样式模块='command'

class 命令文本:
    '命令横向滚动区。放得下时不加 Tab 停点'
    def __init__(自身,属性=None):
        '记下文本和无障碍名'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.拆除=None

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '画出可横向滚动的命令文本，溢出后才能用键盘聚焦'
        if 自身.拆除 is not None:
            自身.拆除()
            自身.拆除=None
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '命令文本样式',
            os.path.join(os.path.dirname(__file__),'命令文本.module.css'),
            样式模块,
        )
        文本='' if 属性.get('text') is None else str(属性['text'])
        名='' if 属性.get('label') is None else str(属性['label'])
        根=文档.createElement('span')
        类名='text'
        附加=属性.get('className')
        if isinstance(附加,str) and 附加!='':
            类名=类名+' '+附加
        根.className=类名
        标样式模块(根,样式模块)
        根.setAttribute('data-command-text','')
        根.style.setProperty('--dsl-command-whitespace','var(--dsl-terminal-command-whitespace, pre)')
        根.style.color='var(--dsw-alias-label-primary)'
        根.textContent=文本
        def 测量():
            '溢出才挂 role、无障碍名和 tabIndex'
            溢出=根.scrollWidth>根.clientWidth
            if 溢出:
                根.tabIndex=0
                根.setAttribute('role','group')
                根.setAttribute('aria-label',名)
            else:
                根.removeAttribute('tabindex')
                根.removeAttribute('role')
                根.removeAttribute('aria-label')
        测量()
        观察=None
        构造=getattr(窗口,'ResizeObserver',None)
        if 构造 is not None:
            观察=构造(测量)
            观察.observe(根)
        字体=getattr(文档,'fonts',None)
        if 字体 is not None and hasattr(字体,'addEventListener'):
            字体.addEventListener('loadingdone',测量)
        def 拆除():
            '卸掉尺寸观察和字体加载'
            if 观察 is not None:
                观察.disconnect()
            if 字体 is not None and hasattr(字体,'removeEventListener'):
                字体.removeEventListener('loadingdone',测量)
        自身.拆除=拆除
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        return 自身.根

    def __call__(自身,属性=None):
        '再次调用时先换 props 再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
