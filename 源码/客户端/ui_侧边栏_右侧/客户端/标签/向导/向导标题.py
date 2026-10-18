'向导签的标题：罗盘加上类型的字'
from .....模块.客户端.通告 import 取握手窗口
from .....ui_对话.异常 import 标样式模块

__all__=['罗盘字形','立方字形','向导标题']

样式模块='sidebar-right-guide'


def _窗口(属性):
    '调用方带来的窗口，否则用桥上的窗口'
    if isinstance(属性,dict) and 属性.get('window') is not None:
        return 属性['window']
    return 取握手窗口()


class 罗盘字形:
    '圆环和指向东北的针。颜色跟 currentColor'

    def __init__(自身,窗口,尺寸=16,类名=None):
        '记下大小'
        自身.窗口=窗口
        自身.尺寸=尺寸
        自身.类名=类名
        自身.属性={'window':窗口}
        自身.根=None

    def 渲染(自身):
        '画出 svg'
        文档=自身.窗口.document
        图=文档.createElementNS('http://www.w3.org/2000/svg','svg')
        图.setAttribute('width',str(自身.尺寸))
        图.setAttribute('height',str(自身.尺寸))
        图.setAttribute('viewBox','0 0 16 16')
        图.setAttribute('fill','none')
        图.setAttribute('aria-hidden','true')
        if 自身.类名:
            图.setAttribute('class',自身.类名)
            标样式模块(图,样式模块)
        环=文档.createElementNS('http://www.w3.org/2000/svg','path')
        环.setAttribute('d','M8 14C11.3137 14 14 11.3137 14 8C14 4.68629 11.3137 2 8 2C4.68629 2 2 4.68629 2 8C2 11.3137 4.68629 14 8 14Z')
        环.setAttribute('stroke','currentColor')
        针=文档.createElementNS('http://www.w3.org/2000/svg','path')
        针.setAttribute('d','M10.6101 5.39014L8.99014 8.99014L5.39014 10.6101L7.01014 7.01014L10.6101 5.39014Z')
        针.setAttribute('fill','currentColor')
        图.appendChild(环)
        图.appendChild(针)
        自身.根=图
        return 图


class 立方字形:
    '等轴方块。没有自己图标的入口用它'

    def __init__(自身,窗口,尺寸=16,类名=None):
        '记下大小'
        自身.窗口=窗口
        自身.尺寸=尺寸
        自身.类名=类名
        自身.属性={'window':窗口}
        自身.根=None

    def 渲染(自身):
        '画出 svg'
        文档=自身.窗口.document
        图=文档.createElementNS('http://www.w3.org/2000/svg','svg')
        图.setAttribute('width',str(自身.尺寸))
        图.setAttribute('height',str(自身.尺寸))
        图.setAttribute('viewBox','0 0 16 16')
        图.setAttribute('fill','none')
        图.setAttribute('aria-hidden','true')
        if 自身.类名:
            图.setAttribute('class',自身.类名)
            标样式模块(图,样式模块)
        廓=文档.createElementNS('http://www.w3.org/2000/svg','path')
        廓.setAttribute('d','M7.99998 2.5L12.9 5.2V10.8L7.99998 13.5L3.09998 10.8V5.2L7.99998 2.5Z')
        廓.setAttribute('stroke','currentColor')
        廓.setAttribute('stroke-linejoin','round')
        缝=文档.createElementNS('http://www.w3.org/2000/svg','path')
        缝.setAttribute('d','M3.09998 5.19995L7.99998 7.89995M7.99998 7.89995L12.9 5.19995M7.99998 7.89995V13.5')
        缝.setAttribute('stroke','currentColor')
        缝.setAttribute('stroke-linecap','round')
        缝.setAttribute('stroke-linejoin','round')
        图.appendChild(廓)
        图.appendChild(缝)
        自身.根=图
        return 图


class 向导标题:
    '芯片上的罗盘和标题字'

    def __init__(自身,属性=None):
        '记下份额'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.渲染()

    def __call__(自身,属性=None):
        '再次绘制'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

    def 渲染(自身):
        '罗盘在前，字在后'
        窗口=_窗口(自身.属性)
        文档=窗口.document
        根=文档.createElement('span')
        图=罗盘字形(窗口,16,'titleIcon').渲染()
        根.appendChild(图)
        用=自身.属性.get('useTabInfo')
        字=''
        if callable(用):
            信息=用()
            签=信息.get('tab') if isinstance(信息,dict) else None
            if isinstance(签,dict):
                字=签.get('title') or ''
        根.appendChild(文档.createTextNode(str(字)))
        自身.根=根
        父=自身.属性.get('parent')
        if 父 is not None and getattr(根,'parentNode',None) is None:
            父.appendChild(根)
        return 自身
