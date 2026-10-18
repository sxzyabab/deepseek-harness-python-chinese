from ...模块.客户端.通告 import 取握手窗口

__all__=['浏览器种类','浏览器标识','浏览器向导图']

浏览器种类='browser'
浏览器标识='@deepseek-ai/dsh-client-ui-sidebar-browser'


def 浏览器向导图(尺寸=36):
    '固定配色的浏览器向导图。向导按像素尺寸调用，也可以传入带 size 的字典'
    类名=None
    if isinstance(尺寸,dict):
        类名=尺寸.get('className')
        尺寸=尺寸.get('size',36)
    文档=取握手窗口().document
    图=文档.createElementNS('http://www.w3.org/2000/svg','svg')
    图.setAttribute('width',str(尺寸))
    图.setAttribute('height',str(尺寸))
    图.setAttribute('viewBox','0 0 36 36')
    图.setAttribute('fill','none')
    图.setAttribute('xmlns','http://www.w3.org/2000/svg')
    图.setAttribute('aria-hidden','true')
    if isinstance(类名,str) and 类名!='':
        图.setAttribute('class',类名)
    圆=文档.createElementNS('http://www.w3.org/2000/svg','path')
    圆.setAttribute('d','M17.9995 28.1465C23.6034 28.1465 28.1461 23.6038 28.1461 18C28.1461 12.3963 23.6034 7.85352 17.9995 7.85352C12.3958 7.85352 7.85303 12.3963 7.85303 18C7.85303 23.6038 12.3958 28.1465 17.9995 28.1465Z')
    圆.setAttribute('stroke','#539CFA')
    圆.setAttribute('stroke-width','2')
    纬=文档.createElementNS('http://www.w3.org/2000/svg','path')
    纬.setAttribute('d','M8.57764 18H27.4211')
    纬.setAttribute('stroke','#539CFA')
    纬.setAttribute('stroke-width','2')
    纬.setAttribute('stroke-linecap','square')
    左经=文档.createElementNS('http://www.w3.org/2000/svg','path')
    左经.setAttribute('d','M17.999 28.1467C20.0576 28.1467 21.6228 23.6039 21.6228 18C21.6228 12.3963 20.0576 7.85352 17.999 7.85352')
    左经.setAttribute('stroke','#539CFA')
    左经.setAttribute('stroke-width','2')
    右经=文档.createElementNS('http://www.w3.org/2000/svg','path')
    右经.setAttribute('d','M17.9992 28.1467C15.9407 28.1467 14.3755 23.6039 14.3755 18C14.3755 12.3963 15.9407 7.85352 17.9992 7.85352')
    右经.setAttribute('stroke','#539CFA')
    右经.setAttribute('stroke-width','2')
    图.appendChild(圆)
    图.appendChild(纬)
    图.appendChild(左经)
    图.appendChild(右经)
    return 图
