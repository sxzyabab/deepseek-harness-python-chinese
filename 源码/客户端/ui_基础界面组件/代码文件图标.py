from ..模块.客户端.通告 import 取握手窗口
from .代码文件图标画稿 import 代码文件图标令牌,代码文件画稿

__all__=['代码文件图标']

序号=0

class 代码文件图标:
    '全彩代码文件方标。每个实例换掉画稿里的占位 id'
    def __init__(自身,属性=None):
        '记下类型和尺寸'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 渲染(自身):
        '把内层标记放进 20 视口的 svg'
        global 序号
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        序号=序号+1
        实例='dsh-code-icon-'+str(序号)
        类型=属性['type']
        内层=代码文件画稿[类型].replace(代码文件图标令牌,实例)
        尺寸=属性['size'] if 'size' in 属性 and 属性['size'] is not None else 20
        图=文档.createElement('svg')
        图.setAttribute('width',str(尺寸))
        图.setAttribute('height',str(尺寸))
        图.setAttribute('viewBox','0 0 20 20')
        图.setAttribute('xmlns','http://www.w3.org/2000/svg')
        图.setAttribute('aria-hidden','true')
        类名=属性.get('className')
        if isinstance(类名,str) and 类名!='':
            图.setAttribute('class',类名)
        图.innerHTML=内层
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(图)
        自身.根=图
        return 自身.根
