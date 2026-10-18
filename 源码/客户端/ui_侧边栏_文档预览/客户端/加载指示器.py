from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,模块节点
from ...ui_基础界面组件.状态点 import 状态点
from .文案 import 中文

__all__=['加载指示器']

样式模块='document-loading'

class 加载指示器:
    '文档读取和绘制时的等待状态。inline 时是一行小转圈'
    def __init__(自身,属性=None):
        '记下标签和是否紧凑'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '居中的状态，或一行可访问的转圈'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '文档加载指示器样式',
            os.path.join(os.path.dirname(__file__),'加载指示器.module.css'),
            样式模块,
        )
        标签=属性['label'] if 'label' in 属性 and 属性['label'] is not None else 中文['loading']
        紧凑=属性.get('inline') is True
        根=模块节点(文档,'span',样式模块,'loading inline' if 紧凑 else 'loading')
        根.setAttribute('role','status')
        根.setAttribute('aria-label',标签)
        根.setAttribute('data-document-loading','')
        点=状态点({'window':窗口,'state':'ongoing','size':14 if 紧凑 else 28}).渲染()
        根.appendChild(点)
        if not 紧凑:
            文=文档.createElement('span')
            文.textContent=标签
            根.appendChild(文)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        return 自身.根

    def __call__(自身,属性=None):
        '再次调用时先换 props 再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
