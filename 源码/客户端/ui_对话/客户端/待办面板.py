from .文案 import 命名空间

__all__=['待办面板','待办停靠','待办停靠条目','进度文案']

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键

def 进度文案(待办列表,翻译):
    """零计数段省略。"""
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
    """空表不渲染；默认折叠。"""

    def __init__(自身,属性=None):
        """记下 props 与折叠。"""
        自身.属性=属性 if 属性 is not None else {}
        自身.已折叠=True

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}

    def 切换折叠(自身):
        """翻转折叠。"""
        自身.已折叠=not 自身.已折叠

    def 渲染(自身):
        """空返回 None。"""
        属性=自身.属性
        待办列表=属性['todos'] if 'todos' in 属性 and 属性['todos'] is not None else []
        翻译=属性['t'] if 't' in 属性 else 恒等翻译
        if len(待办列表)==0:
            return None
        列表=None
        if 自身.已折叠 is False:
            列表=[{
                'content':项['content'] if 'content' in 项 else None,
                'status':项['status'] if 'status' in 项 else None,
            } for 项 in 待办列表]
        return {
            'className':'root',
            'aria-label':翻译('todo.title'),
            'header':{
                'title':翻译('todo.title'),
                'progress':进度文案(待办列表,翻译),
                'expanded':自身.已折叠 is False,
                'onClick':自身.切换折叠,
            },
            'list':列表,
        }

class 待办停靠:
    """读 todos 投影。"""

    def __init__(自身,属性=None):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}
        自身.面板=待办面板()

    def 更新(自身,属性):
        """刷新并灌入面板。"""
        自身.属性=属性 if 属性 is not None else {}

    def 渲染(自身):
        """投影缺席当空表。"""
        属性=自身.属性
        用投影=属性['useProjection'] if 'useProjection' in 属性 else None
        待办=用投影('todos') if 用投影 is not None else None
        表=待办 if 待办 is not None else []
        翻译=属性['t'] if 't' in 属性 else None
        自身.面板.更新({'todos':表,'t':翻译})
        return 自身.面板.渲染()

def 待办停靠条目():
    """计划条停靠：order 0 的 input-dock 登记。"""
    def 应用(上下文):
        """登记 conversation.input.dock 条目。"""
        def 登记():
            """返回停靠组件登记。"""
            return 上下文.slots.register({
                'name':'conversation.input.dock',
                'id':'todo',
                'order':0,
                'locale':命名空间,
            },待办停靠)
        上下文.slots.inject('conversation.input.dock',登记)
    return {'name':'conversation-todo-dock','inject':['slots'],'apply':应用}
