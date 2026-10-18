from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块

__all__=['快捷键']

样式模块='shortcut'

class 快捷键:
    '一串键帽。variant=tooltip 时带提示泡键帽样式，含加号则并成一组'
    def __init__(自身,属性=None):
        '记下键列表和变体'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '每个键一个 kbd。加号用分隔样式'
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '快捷键样式',
            os.path.join(os.path.dirname(__file__),'快捷键.module.css'),
            样式模块,
        )
        键列=属性['keys'] if 'keys' in 属性 and 属性['keys'] is not None else []
        变体=属性['variant'] if 'variant' in 属性 else 'plain'
        类名=['keys']
        if 变体=='tooltip':
            类名.append('tooltip')
        含加=False
        for 键 in 键列:
            if 键=='+':
                含加=True
        if 变体=='tooltip' and 含加:
            类名.append('joined')
        附加=属性.get('className')
        if isinstance(附加,str) and 附加!='':
            类名.append(附加)
        根=文档.createElement('span')
        根.className=' '.join(类名)
        标样式模块(根,样式模块)
        for 键 in 键列:
            帽=文档.createElement('kbd')
            if 键=='+':
                帽.className='separator'
            else:
                帽.className='key'
            标样式模块(帽,样式模块)
            帽.textContent=str(键)
            根.appendChild(帽)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        return 自身.根

    def __call__(自身,属性=None):
        '再次调用时先换 props 再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
