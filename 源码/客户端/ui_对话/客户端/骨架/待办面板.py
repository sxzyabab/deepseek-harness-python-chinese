import os
from ....ui_基础界面组件.icons import 图标上chevron14,图标下chevron14,图标清单14
from ....ui_基础界面组件.状态点 import 处理状态点
from ...异常 import 注入模块样式文件,标样式模块
from ..文案 import 中文,填入,命名空间

__all__=['待办面板','待办停靠','待办停靠条目']

样式模块='todo-panel'

def 状态点态(状态):
    '待办状态对应共享状态点'
    if 状态=='completed':
        return 'done'
    if 状态=='in_progress':
        return 'ongoing'
    if 状态=='pending':
        return 'idle'
    raise Exception('unreachable todo status: '+str(状态))

def 状态文案(状态):
    '状态旁边读出来的中文'
    if 状态=='completed':
        return 中文['todo.status.completed']
    if 状态=='in_progress':
        return 中文['todo.status.inProgress']
    if 状态=='pending':
        return 中文['todo.status.pending']
    raise Exception('unreachable todo status: '+str(状态))

def 进度文案(待办列):
    '非零的完成、进行中、待处理，用间隔点连起来'
    完成=0
    进行=0
    for 项 in 待办列:
        if 项.get('status')=='completed':
            完成+=1
        elif 项.get('status')=='in_progress':
            进行+=1
    待=len(待办列)-完成-进行
    段=[]
    if 完成>0:
        段.append(填入(中文['todo.progress.done'],{'done':完成}))
    if 进行>0:
        段.append(填入(中文['todo.progress.active'],{'active':进行}))
    if 待>0:
        段.append(填入(中文['todo.progress.pending'],{'pending':待}))
    return '\u2002·\u2002'.join(段)

class 待办面板:
    '输入停靠里的任务条。空清单不画'
    def __init__(自身,属性):
        '默认收起'
        自身.属性=属性
        自身.根=None
        自身.收起=True
        自身.渲染()

    def 渲染(自身):
        '标题行可展开清单'
        属性=自身.属性
        待办列=属性.get('todos') or []
        if len(待办列)==0:
            if 自身.根 is not None:
                自身.根.remove()
                自身.根=None
            return None
        窗口=属性['window']
        文档=窗口.document
        注入模块样式文件(文档,'待办面板样式',os.path.join(os.path.dirname(__file__),'待办面板.module.css'),样式模块)
        父=None
        if 自身.根 is not None:
            父=自身.根.parentNode
            自身.根.remove()
        elif 'parent' in 属性:
            父=属性['parent']
        根=文档.createElement('section')
        根.className='root'
        标样式模块(根,样式模块)
        根.setAttribute('data-testid','todo-panel')
        根.setAttribute('aria-label','任务')
        体=文档.createElement('div')
        体.className='body'
        标样式模块(体,样式模块)
        头=文档.createElement('button')
        头.type='button'
        头.className='header'
        标样式模块(头,样式模块)
        头.setAttribute('aria-expanded','false' if 自身.收起 else 'true')
        def 切换(事件):
            '展开或收起'
            自身.收起=not 自身.收起
            自身.渲染()
        头.addEventListener('click',切换)
        前=文档.createElement('span')
        前.className='lead'
        标样式模块(前,样式模块)
        前.setAttribute('aria-hidden','true')
        前.appendChild(图标清单14({'window':窗口}))
        头.appendChild(前)
        题=文档.createElement('span')
        题.className='title'
        标样式模块(题,样式模块)
        题.textContent='任务'
        头.appendChild(题)
        进度=文档.createElement('span')
        进度.className='progress'
        标样式模块(进度,样式模块)
        进度.textContent=进度文案(待办列)
        头.appendChild(进度)
        箭盒=文档.createElement('span')
        箭盒.className='chevron'
        标样式模块(箭盒,样式模块)
        箭盒.setAttribute('aria-hidden','true')
        if 自身.收起:
            箭盒.appendChild(图标上chevron14({'window':窗口}))
        else:
            箭盒.appendChild(图标下chevron14({'window':窗口}))
        头.appendChild(箭盒)
        体.appendChild(头)
        if not 自身.收起:
            列=文档.createElement('ul')
            列.className='list'
            标样式模块(列,样式模块)
            for 项 in 待办列:
                行=文档.createElement('li')
                行.className='item'
                标样式模块(行,样式模块)
                行.setAttribute('data-status',项.get('status') or '')
                符=文档.createElement('span')
                符.className='glyph'
                标样式模块(符,样式模块)
                符.setAttribute('role','img')
                符.setAttribute('aria-label',状态文案(项.get('status')))
                点=处理状态点(窗口,{'state':状态点态(项.get('status'))})
                符.appendChild(点)
                行.appendChild(符)
                内容=文档.createElement('span')
                内容.className='content'
                标样式模块(内容,样式模块)
                内容.textContent=项.get('content') or ''
                行.appendChild(内容)
                列.appendChild(行)
            体.appendChild(列)
        根.appendChild(体)
        自身.根=根
        if 父 is not None:
            父.appendChild(自身.根)
        return 自身.根

class 待办停靠:
    '投影里的当前待办。没有就不画'
    def __init__(自身,属性):
        '包一层待办面板'
        自身.属性=属性
        自身.面板=None
        自身.根=None
        自身.渲染()

    def 渲染(自身):
        'todos 投影缺席当空表'
        属性=自身.属性
        待办=属性['useProjection']('todos')
        自身.面板=待办面板({'todos':待办 or [],'window':属性['window']})
        自身.根=自身.面板.根
        return 自身.根

待办停靠条目={
    'name':'conversation-todo-dock',
    'inject':['slots'],
    'apply':None,
}

def 应用待办(上下文):
    '登记到 conversation.input.dock，序 0'
    def 登记():
        '等停靠洞'
        return 上下文.slots.inject('conversation.input.dock',lambda: 上下文.slots.register({
            'name':'conversation.input.dock',
            'id':'todo',
            'order':0,
            'locale':命名空间,
        },待办停靠))
    return 登记()

待办停靠条目['apply']=应用待办
