'浅色和深色各一张装饰图'
from ...模块.客户端.通告 import 取握手窗口
import base64
import os
from ...ui_对话.异常 import 注入模块样式文件

__all__=['上手引导插图','图地址']

样式模块='桌面上手引导'

def 图地址(文件名):
    '把静态图读成数据地址'
    路径=os.path.join(os.path.dirname(__file__),'静态资产',文件名)
    句柄=open(路径,'rb')
    数据=句柄.read()
    句柄.close()
    if 文件名.endswith('.svg'):
        类型='image/svg+xml'
    elif 文件名.endswith('.webp'):
        类型='image/webp'
    else:
        类型='application/octet-stream'
    return 'data:'+类型+';base64,'+base64.b64encode(数据).decode('ascii')

class 上手引导插图:
    '浅色图和深色图叠在一起，由主题选择器决定显示哪张'
    def __init__(自身,属性):
        '记下两张图的地址'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '画出不读屏的两张图'
        窗口=自身.属性['window'] if 'window' in 自身.属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '桌面上手引导样式',
            os.path.join(os.path.dirname(__file__),'桌面上手引导.module.css'),
            样式模块,
        )
        if 自身.根 is not None:
            自身.根.remove()
        盒=文档.createElement('div')
        类名='illustration'
        附加=自身.属性.get('className')
        if isinstance(附加,str) and 附加!='':
            类名=类名+' '+附加
        盒.className=类名
        盒.setAttribute('aria-hidden','true')
        盒.setAttribute('data-dsh-css',样式模块)
        浅=文档.createElement('img')
        浅.className='lightIllustration'
        浅.setAttribute('data-dsh-css',样式模块)
        浅.src=自身.属性.get('src') or ''
        浅.alt=''
        深=文档.createElement('img')
        深.className='darkIllustration'
        深.setAttribute('data-dsh-css',样式模块)
        深.src=自身.属性.get('darkSrc') or ''
        深.alt=''
        盒.appendChild(浅)
        盒.appendChild(深)
        自身.根=盒
        return 自身.根
