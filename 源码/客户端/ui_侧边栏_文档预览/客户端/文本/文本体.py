from ....模块.客户端.通告 import 取握手窗口
import os
from ....ui_对话.异常 import 注入模块样式文件,模块节点
from .行 import 行们

__all__=['文本体']

样式模块='text-preview'

class 文本体:
    '没有更具体渲染器时的纯文本。带导航目标行'
    def __init__(自身,属性=None):
        '记下文档正文 props'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if 'content' in 自身.属性 and 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '按页画出源行。不是文本内容则不画'
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
        属性=自身.属性
        内容=属性['content']
        if 内容['kind']!='text':
            return None
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '文本预览样式',
            os.path.join(os.path.dirname(__file__),'..','文本预览.module.css'),
            样式模块,
        )
        信息=属性['useTabInfo']()
        参数=信息['tab']['navigation']['params'] if 'navigation' in 信息['tab'] else None
        目标=参数['line'] if isinstance(参数,dict) and 'line' in 参数 else None
        根=模块节点(文档,'div',样式模块,'textDocument')
        根.setAttribute('data-textpreview-plain','')
        for 页 in 内容['pages']:
            预=模块节点(文档,'pre',样式模块,'page')
            预.setAttribute('data-textpreview-page',str(页['offset']))
            下标=0
            for 文 in 行们(页):
                号=页['offset']+下标
                下标=下标+1
                类名='line lineTarget' if 号==目标 else 'line'
                行=模块节点(文档,'div',样式模块,类名)
                行.setAttribute('data-textpreview-line',str(号))
                if 号==目标:
                    行.setAttribute('data-textpreview-target',str(号))
                行.textContent=文+'\n'
                预.appendChild(行)
            根.appendChild(预)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        return 自身.根

    def __call__(自身,属性=None):
        '再次调用时先换 props 再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
