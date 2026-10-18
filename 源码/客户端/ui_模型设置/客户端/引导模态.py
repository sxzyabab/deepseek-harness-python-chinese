from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_基础界面组件.模态 import 模态
from ...ui_对话.异常 import 注入模块样式文件,挂上
from .编辑器页脚 import 清空子

__all__=['引导模态','忽略隐式关闭']

样式模块='引导模态'
样式标识='引导模态样式'

def 忽略隐式关闭():
    '引导步不接受背景点击关掉'
    return None

def 确保样式(文档):
    '引导模态样式按文档只插一次'
    注入模块样式文件(
        文档,
        样式标识,
        os.path.join(os.path.dirname(__file__),'引导模态.module.css'),
        样式模块,
    )

def 建(文档,标签,类名=None):
    '带引导模态类名的节点'
    确保样式(文档)
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    节点.setAttribute('data-dsh-css',样式模块)
    return 节点

class 引导模态:
    '挡住后面的应用根。步骤自己放正文和动作'
    def __init__(自身,属性):
        '记下标题和正文，并让应用根 inert'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.先前惰性=None
        自身.已钉=False
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '无铬模态。需要时把标题做成可聚焦'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        确保样式(文档)
        if 自身.已钉 is False:
            应用根=文档.getElementById('root')
            if 应用根 is not None:
                自身.先前惰性=应用根.inert
                应用根.inert=True
                自身.已钉=True
        标题=属性.get('title')
        if isinstance(标题,str) is False:
            标题=''
        聚焦标题=属性.get('focusTitle') is True
        if 自身.根 is not None:
            清空子(自身.根)
        内容=建(文档,'div','content')
        题=建(文档,'h2','title')
        题.textContent=标题
        if 聚焦标题:
            题.tabIndex=-1
        内容.appendChild(题)
        体=建(文档,'div','body')
        子=属性.get('children')
        if 子 is not None:
            if isinstance(子,(list,tuple)):
                for 项 in 子:
                    挂上(体,项)
            else:
                挂上(体,子)
        内容.appendChild(体)
        罩=模态({
            'window':窗口,
            'open':True,
            'title':标题,
            'onClose':忽略隐式关闭,
            'headless':True,
            'className':'dialog',
            'children':内容,
        }).渲染()
        if 罩 is not None:
            卡=罩.querySelector('.dialog')
            if 卡 is not None:
                卡.setAttribute('data-dsh-css',样式模块)
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.style.display='contents'
            父=属性.get('parent')
            if 父 is not None:
                父.appendChild(自身.根)
        if 罩 is not None:
            自身.根.appendChild(罩)
        if 聚焦标题:
            题.focus()
        return 自身.根

    def 拆除(自身):
        '把应用根的 inert 放回去'
        if 自身.已钉 is False:
            return
        窗口=自身.属性['window'] if 'window' in 自身.属性 else 取握手窗口()
        应用根=窗口.document.getElementById('root')
        if 应用根 is not None:
            应用根.inert=自身.先前惰性
        自身.已钉=False
