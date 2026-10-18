'侧栏自动化任务入口的时钟。共享图标集没有这枚，按上游路径自画'
from ...模块.客户端.通告 import 取握手窗口

__all__=['任务管理图标','画时钟']

def 画时钟(文档,尺寸=16,类名=None):
    '一像素描边时钟。颜色走 currentColor'
    图=文档.createElementNS('http://www.w3.org/2000/svg','svg')
    图.setAttribute('width',str(尺寸))
    图.setAttribute('height',str(尺寸))
    图.setAttribute('viewBox','0 0 16 16')
    图.setAttribute('fill','none')
    图.setAttribute('aria-hidden','true')
    图.setAttribute('stroke-width','1')
    if isinstance(类名,str) and 类名!='':
        图.setAttribute('class',类名)
    for 数据 in (
        'M8 14C11.3137 14 14 11.3137 14 8C14 4.68629 11.3137 2 8 2C4.68629 2 2 4.68629 2 8C2 11.3137 4.68629 14 8 14Z',
        'M8 4.31V8.46L11 10.08',
    ):
        路=文档.createElementNS('http://www.w3.org/2000/svg','path')
        路.setAttribute('d',数据)
        路.setAttribute('stroke','currentColor')
        图.appendChild(路)
    return 图

class 任务管理图标:
    '侧栏要的边长。无障碍名字由侧栏自己写'
    def __new__(类,属性=None):
        '每次按侧栏给的尺寸画一枚时钟'
        文档=属性['window'].document if isinstance(属性,dict) and 'window' in 属性 else 取握手窗口().document
        尺寸=16 if not isinstance(属性,dict) or 属性.get('size') is None else 属性['size']
        return 画时钟(文档,尺寸)
