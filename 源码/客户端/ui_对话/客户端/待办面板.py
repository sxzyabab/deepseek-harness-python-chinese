from .文案 import 命名空间

__all__=['待办面板','待办停靠','待办停靠条目','进度文案']

from nicegui import ui as 界面
from .文案 import 中文 as 对话文案
from ..异常 import 页面失败文案,贴出失败

def 恒等翻译(键,参数=None):
    '无宿主文案时用本包中文词典，没有则返回键本身。'
    if 键 not in 对话文案:#词典没有
        return 键#键
    文本=对话文案[键]#词条
    if 参数 is None:#无参数
        return 文本#原文
    for 名 in 参数:#替换占位
        文本=文本.replace('{'+名+'}',str(参数[名]))#替换
    return 文本#译完

def 进度文案(待办列表,翻译):
    '零计数段省略'
    完成=len([项 for 项 in 待办列表 if 'status' in 项 and 项['status']=='completed'])
    进行=len([项 for 项 in 待办列表 if 'status' in 项 and 项['status']=='in_progress'])
    待处理=len(待办列表)-完成-进行
    段=[]
    if 完成>0:
        段.append(翻译('todo.progress.done',{'done':完成}))
    if 进行>0:
        段.append(翻译('todo.progress.active',{'active':进行}))
    if 待处理>0:
        段.append(翻译('todo.progress.pending',{'pending':待处理}))
    return '\u2002·\u2002'.join(段)

class 待办面板:
    '空表不渲染；默认折叠'

    def __init__(自身,属性=None):
        '记下 props 与折叠'
        自身.属性=属性 if 属性 is not None else {}
        自身.已折叠=True
        自身.画面=None#可反复清空的画面

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}

    def 切换折叠(自身):
        '翻转折叠'
        自身.已折叠=not 自身.已折叠

    def 渲染(自身):
        '空返回 None'
        属性=自身.属性
        待办列表=属性['todos'] if 'todos' in 属性 and 属性['todos'] is not None else []
        翻译=属性['t'] if 't' in 属性 else 恒等翻译
        原译=翻译 if 翻译 is not 恒等翻译 else None
        def 取文案(键,参数=None):
            '属性上的 t 优先，否则用本包中文词典。'
            if 原译 is not None:#宿主
                if 参数 is None:#无参数
                    return 原译(键)#译
                return 原译(键,参数)#带参数
            if 键 not in 对话文案:#词典没有
                return 键#键
            文本=对话文案[键]#词条
            if 参数 is None:#无参数
                return 文本#原文
            for 名 in 参数:#替换占位
                文本=文本.replace('{'+名+'}',str(参数[名]))#替换
            return 文本#译完
        翻译=取文案#词典
        if len(待办列表)==0:#没有待办
            return#不画
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('root')#面板
        def 重画():
            '按折叠态重画任务。'
            自身.画面.clear()#清空
            with 自身.画面:#面板
                贴出失败(自身)
                进度=进度文案(待办列表,翻译)#进度
                def 点标题():
                    '翻转折叠。'
                    自身.切换折叠()#翻
                    重画()#重画
                界面.button(翻译('todo.title'),on_click=点标题)#标题
                if 进度=='':#零计数
                    pass#不另造句子
                else:#进度
                    界面.label(进度)#进度
                if 自身.已折叠 is False:#展开
                    for 项 in 待办列表:#逐条
                        内容=项['content'] if 'content' in 项 and 项['content'] is not None else ''#内容
                        状态=项['status'] if 'status' in 项 and 项['status'] is not None else ''#状态
                        if 内容=='' and 状态=='':#空行
                            continue#跳
                        if 状态=='':#只有内容
                            界面.label(内容)#内容
                        elif 内容=='':#只有状态
                            界面.label(状态)#状态
                        else:#都有
                            界面.label(内容+' · '+状态)#行
        重画()#画

class 待办停靠:
    '读 todos 投影'

    def __init__(自身,属性=None):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}
        自身.面板=待办面板()
        自身.画面=None#可反复清空的画面
        自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新并灌入面板'
        自身.属性=属性 if 属性 is not None else {}

    def 渲染(自身):
        '投影缺席当空表'
        属性=自身.属性
        用投影=属性['useProjection'] if 'useProjection' in 属性 else None
        待办=用投影('todos') if 用投影 is not None else None
        表=待办 if 待办 is not None else []
        翻译=属性['t'] if 't' in 属性 else None
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('待办停靠')#停靠
        自身.画面.clear()#清空
        with 自身.画面:#停靠
            贴出失败(自身)
            自身.面板.更新({'todos':表,'t':翻译})#灌入
            自身.面板.渲染()#自己画

def 待办停靠条目():
    '计划条停靠：order 0 的 input-dock 登记'
    def 应用(上下文):
        '登记 conversation.input.dock 条目'
        def 登记():
            '返回停靠组件登记'
            return 上下文.slots.register({
                'name':'conversation.input.dock',
                'id':'todo',
                'order':0,
                'locale':命名空间,
            },待办停靠)
        上下文.slots.inject('conversation.input.dock',登记)
    return {'name':'conversation-todo-dock','inject':['slots'],'apply':应用}
