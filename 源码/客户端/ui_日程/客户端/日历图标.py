'日期行用的 14 像素日历轮廓。共享图标集里没有这枚'
from ...模块.客户端.通告 import 取握手窗口

__all__=['日历图标']

class 日历图标:
    '一像素描边的日历。颜色走 currentColor'
    def __init__(自身,属性=None):
        '记下类名'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 渲染(自身):
        '画出矩形和两根钉'
        文档=自身.属性['window'].document if 'window' in 自身.属性 else 取握手窗口().document
        图=文档.createElementNS('http://www.w3.org/2000/svg','svg')
        图.setAttribute('width','14')
        图.setAttribute('height','14')
        图.setAttribute('viewBox','0 0 14 14')
        图.setAttribute('fill','none')
        图.setAttribute('aria-hidden','true')
        图.setAttribute('stroke-width','1')
        类名=自身.属性.get('className')
        if isinstance(类名,str) and 类名!='':
            图.setAttribute('class',类名)
        矩形=文档.createElementNS('http://www.w3.org/2000/svg','rect')
        矩形.setAttribute('x','1.4')
        矩形.setAttribute('y','2.6')
        矩形.setAttribute('width','11.2')
        矩形.setAttribute('height','10')
        矩形.setAttribute('rx','1.6')
        矩形.setAttribute('stroke','currentColor')
        图.appendChild(矩形)
        for 数据 in ('M1.4 5.6H12.6','M4.4 1.4V3.6M9.6 1.4V3.6'):
            路=文档.createElementNS('http://www.w3.org/2000/svg','path')
            路.setAttribute('d',数据)
            路.setAttribute('stroke','currentColor')
            图.appendChild(路)
        自身.根=图
        return 图

    def __call__(自身,属性=None):
        '再画一次'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

def 日历图标节点(文档,类名=None):
    '给行上直接挂的日历'
    return 日历图标({'window':文档.defaultView,'className':类名}).渲染()
