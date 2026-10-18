from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,模块节点
from .终端图标 import 终端图标

__all__=['终端标题']

样式路径=os.path.join(os.path.dirname(__file__),'终端标题.module.css')
样式模块='TerminalTitle'

class 终端标题:
    '双击停靠芯片就地改名'
    def __init__(自身,属性=None):
        '记下份额并画出'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.编辑中=False
        自身.已取消=False
        自身.标题文本=''
        自身.根=None
        自身.标签=None
        自身.输入=None
        自身.芯片=None
        自身.改名=None
        自身.代次=0
        自身.拆=[]
        自身.已订=None
        自身.渲染()

    def 更新(自身,属性):
        '换上一份份额'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 退订(自身):
        '摘掉状态订阅和双击'
        副本=list(自身.拆)
        自身.拆=[]
        自身.已订=None
        for 卸 in 副本:
            卸()
        if 自身.芯片 is not None and 自身.改名 is not None:
            自身.芯片.removeEventListener('dblclick',自身.改名)
        自身.芯片=None
        自身.改名=None

    def 当前标题(自身,标签):
        '优先模型标题，否则页签标题'
        def 取标题(状态):
            'info.title，否则状态上的 title'
            if not isinstance(状态,dict):
                return None
            信息=状态['info'] if isinstance(状态.get('info'),dict) else None
            if 信息 is not None and 信息.get('title') is not None:
                return 信息['title']
            if 状态.get('title') is not None:
                return 状态['title']
            return None
        名=自身.属性['useTerminal'](标签['id'],取标题)
        if 名 is None:
            return 标签['title'] if isinstance(标签.get('title'),str) else ''
        return 名

    def 渲染(自身):
        '图标加名称。编辑中是输入框'
        属性=自身.属性
        if isinstance(属性,dict) and 属性.get('window') is not None:
            窗=属性['window']
        else:
            窗=取握手窗口()
        文档=窗.document
        注入模块样式文件(文档,'终端标题样式',样式路径,样式模块)
        标签=属性['useTabInfo']()['tab']
        模型=属性['view'](标签['id'])
        if 自身.已订 is not 模型:
            自身.退订()
            def 变更(*参数):
                '标题变了就重画。节点已被摘掉则退订'
                if 自身.根 is not None and getattr(自身.根,'isConnected',True) is False:
                    自身.退订()
                    return
                自身.渲染()
            自身.拆.append(模型.状态.subscribe(变更))
            自身.已订=模型
        标题=自身.当前标题(标签)
        自身.标题文本=标题
        if 自身.根 is None:
            自身.根=文档.createElement('span')
            自身.根.style.display='contents'
        else:
            while 自身.根.firstChild is not None:
                自身.根.firstChild.remove()
        自身.根.appendChild(终端图标({'window':窗}).渲染())
        if 自身.编辑中:
            框=模块节点(文档,'input',样式模块,'name')
            框.defaultValue=标题
            框.setAttribute('maxlength','120')
            框.setAttribute('aria-label','终端名称')
            自身.输入=框

            def 停冒泡(事件):
                '拖动手柄不要吃掉输入'
                事件.stopPropagation()

            def 失焦(事件):
                '非空且不同才改名。Escape 之后丢弃'
                自身.编辑中=False
                下一=事件.currentTarget.value.strip()
                if 自身.已取消 is not True and 下一!='' and 下一!=自身.标题文本:
                    属性['view'](标签['id']).重命名(下一)
                自身.渲染()

            def 按键(事件):
                '组合输入先放过。Escape 取消，Enter 提交'
                事件.stopPropagation()
                if 事件.isComposing or 事件.keyCode==229:
                    return
                if 事件.key=='Escape':
                    自身.已取消=True
                    事件.currentTarget.blur()
                elif 事件.key=='Enter':
                    事件.currentTarget.blur()

            框.addEventListener('pointerdown',停冒泡)
            框.addEventListener('click',停冒泡)
            框.addEventListener('dblclick',停冒泡)
            框.addEventListener('blur',失焦)
            框.addEventListener('keydown',按键)
            自身.根.appendChild(框)
        else:
            字=模块节点(文档,'span',样式模块,'title')
            字.textContent=str(标题)
            自身.标签=字
            自身.输入=None
            自身.根.appendChild(字)
        父=属性.get('parent')
        if 父 is not None and getattr(自身.根,'parentNode',None) is None:
            父.appendChild(自身.根)

        自身.代次=自身.代次+1
        代=自身.代次

        def 稍后():
            '节点挂上之后再聚焦，或绑到停靠芯片的双击'
            if 代!=自身.代次:
                return
            if 自身.编辑中 and 自身.输入 is not None:
                自身.输入.focus()
                自身.输入.select()
                return
            if 自身.编辑中 or 自身.标签 is None:
                return
            芯片=自身.标签.closest('[data-dockkit-tab], [data-dockkit-float-grip]')
            if 芯片 is None:
                return

            def 开始(事件):
                '停掉拖动，进入改名'
                事件.stopPropagation()
                自身.已取消=False
                自身.编辑中=True
                自身.渲染()

            if 自身.芯片 is not None and 自身.改名 is not None:
                自身.芯片.removeEventListener('dblclick',自身.改名)
            芯片.addEventListener('dblclick',开始)
            自身.芯片=芯片
            自身.改名=开始

        窗.setTimeout(稍后,0)
        return 自身

    def __call__(自身,属性=None):
        '有新属性先更新，再画出'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
