from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块

__all__=['文字闪烁']

样式模块='shimmer'

class 文字闪烁:
    '活动时在文字上扫一层高光。嵌套时跟外层的活动态'
    def __init__(自身,属性=None):
        '记下文字和是否活动'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 渲染(自身):
        '真实文字留着可选。活动时再叠一层裁切高光'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(文档,'文字闪烁样式',os.path.join(os.path.dirname(__file__),'文字闪烁.module.css'),样式模块)
        活动=属性.get('active') is True
        子=属性.get('children')
        根=文档.createElement('span')
        类名='root'
        附加=属性.get('className')
        if isinstance(附加,str) and 附加!='':
            类名=类名+' '+附加
        根.className=类名
        标样式模块(根,样式模块)
        if 活动:
            根.setAttribute('data-shimmer','true')
        内容类='content'
        内容附加=属性.get('contentClassName')
        if isinstance(内容附加,str) and 内容附加!='':
            内容类=内容类+' '+内容附加
        内容=文档.createElement('span')
        内容.className=内容类
        标样式模块(内容,样式模块)
        if isinstance(子,str):
            字=文档.createElement('span')
            字.className='text'
            标样式模块(字,样式模块)
            字.textContent=子
            内容.appendChild(字)
        elif hasattr(子,'tagName'):
            内容.appendChild(子)
        根.appendChild(内容)
        if 活动 and isinstance(子,str):
            饰=文档.createElement('span')
            饰.className='decoration'
            标样式模块(饰,样式模块)
            饰.setAttribute('aria-hidden','true')
            饰.setAttribute('inert','')
            扫=文档.createElement('span')
            扫.className='sweep'
            标样式模块(扫,样式模块)
            亮=文档.createElement('span')
            亮.className=内容类+' highlight'
            标样式模块(亮,样式模块)
            亮字=文档.createElement('span')
            亮字.className='text'
            标样式模块(亮字,样式模块)
            亮字.setAttribute('data-shimmer-text',子)
            亮.appendChild(亮字)
            扫.appendChild(亮)
            饰.appendChild(扫)
            根.appendChild(饰)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        return 根
