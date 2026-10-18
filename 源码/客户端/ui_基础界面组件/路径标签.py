from ..模块.客户端.通告 import 取握手窗口
import os
from ...工具.工作区路径 import 路径展示拆分
from ..ui_对话.异常 import 注入模块样式文件,标样式模块

__all__=['路径标签']

样式模块='path'

class 路径标签:
    '单行路径。目录用次要色，文件名用主要色，窄处保留末尾'
    def __init__(自身,属性=None):
        '记下路径'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.拆除=None

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '画出目录和文件名。溢出时在左缘淡出'
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
            '路径标签样式',
            os.path.join(os.path.dirname(__file__),'路径标签.module.css'),
            样式模块,
        )
        路径='' if 属性.get('path') is None else str(属性['path'])
        拆=路径展示拆分(路径)
        外=文档.createElement('span')
        类名='path'
        附加=属性.get('className')
        if isinstance(附加,str) and 附加!='':
            类名=类名+' '+附加
        外.className=类名
        标样式模块(外,样式模块)
        外.title=路径
        外.setAttribute('data-path-label','')
        内=文档.createElement('span')
        内.className='text'
        标样式模块(内,样式模块)
        if 拆['directory']!='':
            目录=文档.createElement('span')
            目录.className='directory'
            标样式模块(目录,样式模块)
            目录.textContent=拆['directory']
            内.appendChild(目录)
        名=文档.createElement('span')
        名.className='name'
        标样式模块(名,样式模块)
        名.textContent=拆['name']
        内.appendChild(名)
        外.appendChild(内)
        def 套裁切():
            '内层比外层宽就标 data-path-clipped'
            if 内.offsetWidth>外.clientWidth:
                外.setAttribute('data-path-clipped','')
            else:
                外.removeAttribute('data-path-clipped')
        套裁切()
        观察=None
        构造=getattr(窗口,'ResizeObserver',None)
        if 构造 is not None:
            观察=构造(套裁切)
            观察.observe(外)
            观察.observe(内)
        def 拆除():
            '卸掉尺寸观察'
            if 观察 is not None:
                观察.disconnect()
        自身.拆除=拆除
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(外)
        自身.根=外
        return 自身.根

    def __call__(自身,属性=None):
        '再次调用时先换 props 再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
