import os
from ...ui_对话.异常 import 注入模块样式文件,模块节点
from .侧栏根 import 画描边图标,绑定提示,找快捷行,快捷面,新聊路径,左栏路径

__all__=['头部前置控件']

样式模块='leading'

class 头部前置控件:
    '窗框左上的打开侧栏和新建会话。框只在侧栏完全藏起时挂上这个席位'
    共享=None
    当前=None

    def __init__(自身,属性):
        '记下 props 并画出两个按钮'
        头部前置控件.当前=自身
        自身.属性=属性
        if 头部前置控件.共享 is None:
            头部前置控件.共享={
                '根':None,
                '已订':False,
                '提示拆除':[],
            }
        自身.状态=头部前置控件.共享
        自身.根=自身.状态['根']
        自身.渲染()

    def __call__(自身,属性=None):
        '父级再次渲染时刷新这两个按钮'
        if 属性 is not None:
            头部前置控件.当前=自身
            自身.属性=属性
        return 自身.渲染()

    def 渲染(自身):
        '两个图标按钮。不看平台，席位在不在由框决定'
        属性=自身.属性
        状态=自身.状态
        窗口=属性['window']
        文档=窗口.document
        def 找切换(行表):
            '打开侧栏的快捷键'
            return 找快捷行(行表,'sidebar.left.toggle')
        def 找新建(行表):
            '新建会话的快捷键'
            return 找快捷行(行表,'session.new')
        切换无障碍,切换键=快捷面(属性['useShortcuts'](找切换))
        新建无障碍,新建键=快捷面(属性['useShortcuts'](找新建))
        注入模块样式文件(
            文档,
            '头部前置控件样式',
            os.path.join(os.path.dirname(__file__),'头部前置控件.module.css'),
            样式模块,
        )
        根=状态['根']
        if 根 is None:
            根=模块节点(文档,'div',样式模块,'controls')
            状态['根']=根
        自身.根=根
        for 收提示 in list(状态['提示拆除']):
            收提示()
        状态['提示拆除'].clear()
        while 根.firstChild is not None:
            根.firstChild.remove()
        def 点切换(事件):
            '打开侧栏'
            属性['toggleSidebar']()
        def 点新建(事件):
            '开始新会话'
            属性['startSession']()
        打开=模块节点(文档,'button',样式模块,'iconButton')
        打开.type='button'
        打开.setAttribute('aria-label','打开侧边栏')
        if 切换无障碍 is not None:
            打开.setAttribute('aria-keyshortcuts',切换无障碍)
        打开.addEventListener('click',点切换)
        打开.appendChild(画描边图标(文档,左栏路径,16,1,None,None))
        状态['提示拆除'].append(绑定提示(打开,窗口,'打开侧边栏',切换键,'right',500))
        新建=模块节点(文档,'button',样式模块,'iconButton')
        新建.type='button'
        新建.setAttribute('aria-label','新建会话')
        if 新建无障碍 is not None:
            新建.setAttribute('aria-keyshortcuts',新建无障碍)
        新建.addEventListener('click',点新建)
        新建.appendChild(画描边图标(文档,新聊路径,16,1,None,None))
        状态['提示拆除'].append(绑定提示(新建,窗口,'新建会话',新建键,'right',500))
        根.appendChild(打开)
        根.appendChild(新建)
        if 状态['已订'] is not True:
            def 重画():
                '快捷键变了就重画'
                头部前置控件.当前.渲染()
            属性['useShortcuts']._subscribe(重画)
            状态['已订']=True
        父=属性['parent'] if 'parent' in 属性 else None
        if 父 is not None and 根.parentNode is not 父:
            父.appendChild(根)
        return 根
