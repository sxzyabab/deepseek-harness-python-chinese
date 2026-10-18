from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.文件类型图标 import 文件类型图标
from .文件体 import 样式模块

__all__=['文件标题','挂上文件标题']

class 文件标题:
    '芯片和浮动面板头部：文件夹图标加标签标题'
    def __init__(自身,属性):
        '记下 props。槽位入口再调用渲染'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.节点=[]

    def 更新(自身,属性):
        '换上一份 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 卸下(自身):
        '拆掉上次挂上的图标和标题'
        for 节点 in 自身.节点:
            节点.remove()
        自身.节点=[]

    def 渲染(自身):
        '返回文档片段。图标和标题文本直接进芯片'
        属性=自身.属性
        窗=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗.document
        注入模块样式文件(
            文档,
            '文件体样式',
            os.path.join(os.path.dirname(__file__),'文件体.module.css'),
            样式模块,
        )
        自身.卸下()
        信息=属性['useTabInfo']()
        签=信息['tab']
        标题=签['title'] if isinstance(签,dict) else 签.title
        图标=文件类型图标({
            'window':窗,
            'kind':'folder',
            'size':16,
            'className':'titleIcon',
        }).渲染()
        片=文档.createDocumentFragment()
        if 图标 is not None:
            标样式模块(图标,样式模块)
            片.appendChild(图标)
            自身.节点.append(图标)
        字=文档.createTextNode('' if 标题 is None else str(标题))
        片.appendChild(字)
        自身.节点.append(字)
        if 'parent' in 属性:
            属性['parent'].appendChild(片)
        return 片

    def __call__(自身,属性=None):
        '有新属性先更新，再画出'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

def 挂上文件标题(属性):
    '槽位入口。返回这一次画出的片段'
    return 文件标题(属性).渲染()
