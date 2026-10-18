from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.文件类型图标 import 分类文件类型,文件类型图标

__all__=['文本标题']

样式模块='text-preview'

class 文本标题:
    '芯片和浮动面板标题：类型图标加打开时记下的名字'
    def __init__(自身,属性=None):
        '记下标签读取'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if 'useTabInfo' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '16 像素类型图标，后面是标签标题'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '文本预览样式',
            os.path.join(os.path.dirname(__file__),'文本预览.module.css'),
            样式模块,
        )
        信息=属性['useTabInfo']()
        签=信息['tab']
        片=文档.createDocumentFragment()
        图=文件类型图标({
            'window':窗口,
            'kind':分类文件类型(签['title']),
            'size':16,
            'className':'titleIcon',
        }).渲染()
        标样式模块(图,样式模块)
        片.appendChild(图)
        片.appendChild(文档.createTextNode(签['title']))
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(片)
        自身.根=片
        return 自身.根

    def __call__(自身,属性=None):
        '再次调用时先换 props 再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
