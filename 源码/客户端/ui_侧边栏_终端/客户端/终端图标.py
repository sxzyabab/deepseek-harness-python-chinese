from ...模块.客户端.通告 import 取握手窗口

__all__=['终端图标','终端作品']

class 终端图标:
    '十六像素装饰线条字形'
    def __init__(自身,属性=None):
        '记下窗口。构造不画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 渲染(自身):
        '返回标题用终端图标'
        if isinstance(自身.属性,dict) and 自身.属性.get('window') is not None:
            窗=自身.属性['window']
        else:
            窗=取握手窗口()
        文档=窗.document
        图=文档.createElementNS('http://www.w3.org/2000/svg','svg')
        图.setAttribute('width','16')
        图.setAttribute('height','16')
        图.setAttribute('viewBox','0 0 16 16')
        图.setAttribute('fill','none')
        图.setAttribute('aria-hidden','true')
        for 路径 in ('M3 4L7 8L3 12','M9 12H13'):
            笔=文档.createElementNS('http://www.w3.org/2000/svg','path')
            笔.setAttribute('d',路径)
            笔.setAttribute('stroke','currentColor')
            图.appendChild(笔)
        自身.根=图
        return 图

    def __call__(自身,属性=None):
        '有新属性先更新，再画出'
        if isinstance(属性,dict):
            自身.属性=属性
        return 自身.渲染()

def 终端作品(窗口,尺寸,类名):
    '引导卡片上的终端字形。向导按窗口、尺寸、类名调用'
    文档=窗口.document
    图=文档.createElementNS('http://www.w3.org/2000/svg','svg')
    图.setAttribute('xmlns','http://www.w3.org/2000/svg')
    图.setAttribute('width',str(尺寸))
    图.setAttribute('height',str(尺寸))
    图.setAttribute('viewBox','0 0 36 36')
    图.setAttribute('fill','none')
    if isinstance(类名,str) and 类名!='':
        图.setAttribute('class',类名)
    for 路径 in (
        'M10 11L16.606 17.606C16.6841 17.6841 16.6841 17.8107 16.606 17.8888L10 24.4948',
        'M20.1211 24.4946H26.8685',
    ):
        笔=文档.createElementNS('http://www.w3.org/2000/svg','path')
        笔.setAttribute('d',路径)
        笔.setAttribute('stroke','#679EFE')
        笔.setAttribute('stroke-width','3.5')
        图.appendChild(笔)
    return 图
