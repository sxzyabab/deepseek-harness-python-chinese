import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点
from ...ui_基础界面组件.按钮 import 按钮
from .文案 import 中文

__all__=['文档动作']

样式模块='documentAction'

class 文档动作:
    '元数据确认有配置文件之后，才显示打开按钮'
    def __init__(自身,属性):
        '记下份额并画出。加载跟控制器走'
        自身.属性=属性
        自身.根=None
        自身.已加载=None
        自身.已订=False
        自身.退订=[]
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 更新(自身,属性):
        '换份额'
        自身.属性=属性

    def 拆订阅(自身):
        '退掉文档快照'
        for 退 in 自身.退订:
            退()
        自身.退订=[]
        自身.已订=False

    def 渲染(自身):
        '未就绪时不占位。错误只显示无法打开配置文件'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            注入模块样式文件(
                文档,
                '文档动作样式',
                os.path.join(os.path.dirname(__file__),'文档动作.module.css'),
                样式模块,
            )
            控制器=属性['controller']
            if 自身.已加载 is not 控制器:
                自身.已加载=控制器
                控制器.加载()
            def 全量(快照):
                '整份文档状态'
                return 快照
            状态=属性['useSnapshot'](全量)
            if 自身.根 is None:
                自身.根=文档.createElement('div')
                自身.根.style.display='contents'
            else:
                while 自身.根.firstChild is not None:
                    自身.根.firstChild.remove()
            if 状态['status']=='ready':
                盒=模块节点(文档,'div',样式模块,'action')
                if 状态['error'] is not None:
                    错=模块节点(文档,'span',样式模块,'error')
                    错.setAttribute('role','alert')
                    错.textContent=中文['openDocument.error']
                    盒.appendChild(错)
                def 点():
                    '打开宿主配置文件'
                    控制器.打开()
                盒.appendChild(按钮({
                    'window':窗口,
                    'variant':'outline',
                    'size':'sm',
                    'disabled':状态['opening'] is True,
                    'onClick':点,
                    'children':中文['openDocument'],
                }).渲染())
                自身.根.appendChild(盒)
            if 自身.已订 is False:
                自身.已订=True
                钩=属性['useSnapshot']
                if hasattr(钩,'_subscribe') and callable(钩._subscribe):
                    def 变更():
                        '快照变了就重画。已经不在页面上就退订'
                        if 自身.绘制中:
                            自身.待重画=True
                            return
                        if 自身.根 is None or 自身.根.parentNode is None:
                            自身.拆订阅()
                            return
                        自身.渲染()
                    退=钩._subscribe(变更)
                    if callable(退):
                        自身.退订.append(退)
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

    def 拆除(自身):
        '退掉文档快照'
        自身.拆订阅()
