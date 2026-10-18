from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_基础界面组件.按钮 import 按钮
from ...ui_对话.异常 import 注入模块样式文件,挂上
from .文案 import 中文
from .引导模态 import 引导模态
from .编辑器页脚 import 清空子

__all__=['欢迎通知']

样式模块='欢迎通知'
样式标识='欢迎通知样式'

def 确保样式(文档):
    '欢迎通知样式按文档只插一次'
    注入模块样式文件(
        文档,
        样式标识,
        os.path.join(os.path.dirname(__file__),'欢迎通知.module.css'),
        样式模块,
    )

def 建(文档,标签,类名=None):
    '带欢迎通知类名的节点'
    确保样式(文档)
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    节点.setAttribute('data-dsh-css',样式模块)
    return 节点

class 欢迎通知:
    '当前文案版本还没确认时显示预览说明'
    def __init__(自身,属性):
        '记下完成回调。还没结束'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.已结束=False
        自身.根=None
        自身.模态=None
        自身.绘制中=False
        自身.待重画=False
        自身.已订=False
        自身.退订=None
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 结束(自身):
        '只完成一次'
        if 自身.已结束:
            return
        自身.已结束=True
        完成=自身.属性.get('complete')
        if 完成 is not None:
            完成()

    def 渲染(自身):
        '空闲先加载。已确认就完成并留空'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            自身.画出()
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

    def 画出(自身):
        '说明段落和继续按钮'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.style.display='contents'
            父=属性.get('parent')
            if 父 is not None:
                父.appendChild(自身.根)
        else:
            清空子(自身.根)
        钩=属性.get('useWelcome')
        控制器=属性.get('controller')
        if 钩 is None or 控制器 is None:
            return
        def 全量(快照):
            '整份欢迎快照'
            return 快照
        状态=钩(全量)
        if 状态.get('status')=='idle':
            控制器.加载()
            状态=钩(全量)
        if 状态.get('acknowledged') is True:
            自身.结束()
        if 状态.get('status') in ('idle','loading') or 状态.get('acknowledged') is True:
            自身.订上()
            return
        def 确认():
            '写上确认。宿主收下了才完成'
            if 控制器.确认():
                自身.结束()
                自身.渲染()
        段=中文['welcomeBody'].split('\n\n')
        文=建(文档,'div','copy')
        for 段文 in 段:
            段节=建(文档,'p')
            段节.textContent=段文
            文.appendChild(段节)
        子=[文]
        if 状态.get('error') is not None:
            错=建(文档,'p','error')
            错.setAttribute('role','alert')
            错.textContent=中文['welcomeError']
            子.append(错)
        动作=建(文档,'div','actions')
        钮=按钮({
            'window':窗口,
            'variant':'primary',
            'className':'primary',
            'disabled':状态.get('status')=='saving',
            'onClick':确认,
            'children':中文['welcomeContinue'],
        }).渲染()
        钮.setAttribute('data-dsh-css',样式模块)
        动作.appendChild(钮)
        子.append(动作)
        模态属性={
            'window':窗口,
            'title':中文['welcomeTitle'],
            'focusTitle':True,
            'children':子,
        }
        if 自身.模态 is None:
            自身.模态=引导模态(模态属性)
        else:
            自身.模态.更新(模态属性)
            自身.模态.渲染()
        挂上(自身.根,自身.模态)
        自身.订上()

    def 订上(自身):
        '欢迎快照变了就重画'
        if 自身.已订:
            return
        钩=自身.属性.get('useWelcome')
        订=getattr(钩,'_subscribe',None) if 钩 is not None else None
        if callable(订) is not True:
            return
        def 变更():
            '绘制中只记一笔'
            if 自身.绘制中:
                自身.待重画=True
                return
            if 自身.根 is None or 自身.根.parentNode is None:
                if 自身.退订 is not None:
                    退=自身.退订
                    自身.退订=None
                    自身.已订=False
                    退()
                return
            自身.渲染()
        自身.退订=订(变更)
        自身.已订=True
