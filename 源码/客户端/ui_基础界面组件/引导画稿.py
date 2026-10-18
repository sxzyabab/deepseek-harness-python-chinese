from ..模块.客户端.通告 import 取握手窗口

__all__=['引导画稿浏览器','引导画稿文件']

def 建画(文档,尺寸,类名,路径列):
    '固定调色板的装饰 svg，辅助技术不读'
    图=文档.createElement('svg')
    图.setAttribute('width',str(尺寸))
    图.setAttribute('height',str(尺寸))
    图.setAttribute('viewBox','0 0 36 36')
    图.setAttribute('fill','none')
    图.setAttribute('xmlns','http://www.w3.org/2000/svg')
    图.setAttribute('aria-hidden','true')
    if isinstance(类名,str) and 类名!='':
        图.setAttribute('class',类名)
    for 项 in 路径列:
        路=文档.createElement('path')
        路.setAttribute('d',项['d'])
        if 'stroke' in 项:
            路.setAttribute('stroke',项['stroke'])
        if 'strokeWidth' in 项:
            路.setAttribute('stroke-width',项['strokeWidth'])
        if 'strokeLinecap' in 项:
            路.setAttribute('stroke-linecap',项['strokeLinecap'])
        if 'fill' in 项:
            路.setAttribute('fill',项['fill'])
        图.appendChild(路)
    return 图

class 引导画稿浏览器:
    '侧栏引导里的浏览器画稿'
    def __init__(自身,属性=None):
        '记下尺寸和类名'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 渲染(自身):
        '画出浏览器圆环画稿'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        尺寸=属性['size'] if 'size' in 属性 else 36
        图=建画(窗口.document,尺寸,属性.get('className'),[
            {'d':'M17.9995 28.1465C23.6034 28.1465 28.1461 23.6038 28.1461 18C28.1461 12.3963 23.6034 7.85352 17.9995 7.85352C12.3958 7.85352 7.85303 12.3963 7.85303 18C7.85303 23.6038 12.3958 28.1465 17.9995 28.1465Z','stroke':'#539CFA','strokeWidth':'2'},
            {'d':'M8.57764 18H27.4211','stroke':'#539CFA','strokeWidth':'2','strokeLinecap':'square'},
            {'d':'M17.999 28.1467C20.0576 28.1467 21.6228 23.6039 21.6228 18C21.6228 12.3963 20.0576 7.85352 17.999 7.85352','stroke':'#539CFA','strokeWidth':'2'},
            {'d':'M17.9992 28.1467C15.9407 28.1467 14.3755 23.6039 14.3755 18C14.3755 12.3963 15.9407 7.85352 17.9992 7.85352','stroke':'#539CFA','strokeWidth':'2'},
        ])
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(图)
        自身.根=图
        return 自身.根

class 引导画稿文件:
    '侧栏引导里的文件画稿'
    def __init__(自身,属性=None):
        '记下尺寸和类名'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 渲染(自身):
        '画出文件夹画稿'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        尺寸=属性['size'] if 'size' in 属性 else 36
        图=建画(窗口.document,尺寸,属性.get('className'),[
            {'d':'M10.7603 27.922H24.6817C26.3441 27.922 27.1753 27.922 27.8102 27.5984C28.3687 27.3139 28.8228 26.8598 29.1074 26.3012C29.4309 25.6663 29.4309 24.8351 29.4309 23.1727V15.4936','stroke':'#FFCD78','strokeWidth':'1.97886'},
            {'d':'M13.1597 8.07812C13.4182 8.07818 13.6727 8.14336 13.8989 8.26855L16.7554 9.84961C16.9817 9.97485 17.2369 10.041 17.4956 10.041H26.106C26.9492 10.0412 27.6323 10.7251 27.6323 11.5684V24.5371C27.6323 25.3805 26.9483 26.0645 26.105 26.0645H8.09619C7.25281 26.0645 6.56884 25.3805 6.56885 24.5371V9.60449C6.56909 8.76133 7.25297 8.07812 8.09619 8.07812H13.1597ZM9.81592 14.5508V16.5293H24.3999V14.5508H9.81592Z','fill':'#FFBC4D'},
        ])
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(图)
        自身.根=图
        return 自身.根
