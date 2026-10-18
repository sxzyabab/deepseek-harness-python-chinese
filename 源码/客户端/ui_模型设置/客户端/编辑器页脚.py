from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件
from .文案 import 中文

__all__=['编辑器页脚','确保样式','建','清空子','采集焦点','还原焦点','样式模块']

样式模块='模型分区'
样式标识='模型分区样式'

def 确保样式(文档):
    '模型页样式模块按文档只插一次'
    注入模块样式文件(
        文档,
        样式标识,
        os.path.join(os.path.dirname(__file__),'模型分区.module.css'),
        样式模块,
    )

def 建(文档,标签,类名=None):
    '带官方类名和样式模块的节点'
    确保样式(文档)
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    节点.setAttribute('data-dsh-css',样式模块)
    return 节点

def 清空子(节点):
    '拆掉节点下现有的子节点'
    while 节点 is not None and 节点.firstChild is not None:
        节点.removeChild(节点.firstChild)

def 采集焦点(文档,根):
    '重画前记下根里面的焦点和选区'
    活动=文档.activeElement
    if 活动 is None or 根 is None:
        return None
    节点=活动
    while 节点 is not None:
        if 节点==根:
            键=None
            if hasattr(活动,'getAttribute'):
                键=活动.getAttribute('data-dsh-focus')
            return (键,getattr(活动,'selectionStart',None),getattr(活动,'selectionEnd',None))
        节点=getattr(节点,'parentNode',None)
    return None

def 还原焦点(文档,快照):
    '按 data-dsh-focus 把焦点和选区放回去'
    if 快照 is None:
        return
    键,起,止=快照
    if isinstance(键,str) is False or 键=='':
        return
    框=文档.querySelector('[data-dsh-focus="'+键+'"]')
    if 框 is None:
        return
    框.focus()
    if isinstance(起,bool) or isinstance(止,bool):
        return
    if type(起) in (int,float) and type(止) in (int,float):
        框.setSelectionRange(int(起),int(止))

class 编辑器页脚:
    '卡片底部：左边取消，右边提交。取消只在提交进行中拒绝，只读也能关'
    def __init__(自身,属性):
        '记下 props 并画出动作行'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '取消和提交。文案用中文表原文'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        if 自身.根 is None:
            自身.根=建(文档,'div','editorActions')
            父=属性.get('parent')
            if 父 is not None:
                父.appendChild(自身.根)
        else:
            清空子(自身.根)
        取消文=中文['cancel']
        if 属性.get('cancelLabelKey') is not None:
            取消文=中文[属性['cancelLabelKey']]
        取消=建(文档,'button','secondaryButton')
        取消.type='button'
        取消.disabled=属性.get('busy') is True
        取消.textContent=取消文
        def 点取消(事件):
            '关闭卡片，不提交'
            属性['onCancel']()
        取消.addEventListener('click',点取消)
        提交=建(文档,'button','primaryButton')
        提交.type='button'
        提交.disabled=属性.get('submitDisabled') is True
        if 属性.get('busy') is True:
            提交.textContent=中文[属性['submitBusyLabelKey']]
        else:
            提交.textContent=中文[属性['submitLabelKey']]
        def 点提交(事件):
            '跑卡片自己的提交'
            属性['onSubmit']()
        提交.addEventListener('click',点提交)
        自身.根.appendChild(取消)
        自身.根.appendChild(提交)
        return 自身.根
