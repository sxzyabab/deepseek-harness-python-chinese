"""计划条：composer 上方待办整表快照。

对齐上游 `ui-conversation/src/client/skeleton/TodoPanel.tsx`。公开面仅中文名。
"""

__all__=['待办面板','待办停靠','待办停靠条目','进度文案']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或对象。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 进度文案(待办们,翻译):#头摘要
    """零计数段省略；En 空格分隔。"""
    完成=len([项 for 项 in 待办们 if 取字段(项,'status')=='completed'])#完成
    进行=len([项 for 项 in 待办们 if 取字段(项,'status')=='in_progress'])#进行
    待处理=len(待办们)-完成-进行#待
    段=[]#段
    if 完成>0:#完成
        段.append(翻译('todo.progress.done',{'done':完成}))#段
    if 进行>0:#进行
        段.append(翻译('todo.progress.active',{'active':进行}))#段
    if 待处理>0:#待
        段.append(翻译('todo.progress.pending',{'pending':待处理}))#段
    return '\u2002·\u2002'.join(段)#拼

class 待办面板:#计划条
    """空表不渲染；默认折叠。"""

    def __init__(自身,属性=None):#记下
        """记下 props 与折叠。"""
        自身.属性=属性 or {}#合成
        自身.已折叠=True#折叠

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 切换折叠(自身):#开合
        """翻转。"""
        自身.已折叠=not 自身.已折叠#翻

    def 渲染(自身):#结构
        """空返回 None。"""
        属性=自身.属性#props
        待办们=取字段(属性,'todos') or []#表
        翻译=取字段(属性,'t',lambda 键,**_:键)#文案
        if len(待办们)==0:#空
            return None#不画
        列表=None#列表
        if not 自身.已折叠:#展开
            列表=[{#项
                'content':取字段(项,'content'),#正文
                'status':取字段(项,'status'),#态
            } for 项 in 待办们]#项
        return {#根
            'className':'root',#类
            'aria-label':翻译('todo.title'),#aria
            'header':{#头
                'title':翻译('todo.title'),#标题
                'progress':进度文案(待办们,翻译),#进度
                'expanded':not 自身.已折叠,#展开
                'onClick':自身.切换折叠,#切换
            },#结束头
            'list':列表,#列表
        }#结束根

class 待办停靠:#input.dock 适配
    """读 todos 投影。"""

    def __init__(自身,属性=None):#记下
        """记下 props。"""
        自身.属性=属性 or {}#合成
        自身.面板=待办面板()#面板

    def 更新(自身,属性):#刷新
        """刷新并灌入面板。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构
        """投影缺席当空表。"""
        属性=自身.属性#props
        用投影=取字段(属性,'useProjection')#投影
        待办=用投影('todos') if callable(用投影) else None#todos
        自身.面板.更新({'todos':待办 or [],'t':取字段(属性,'t')})#灌
        return 自身.面板.渲染()#面板

def 待办停靠条目():#登记插件形
    """对齐 todoDockEntry：计划条 plain registrant。"""
    from .文案 import 命名空间#词典 NS
    def 应用(上下文):#登记计划停靠
        """input-dock 条目（order 0）。"""
        def 登记():#等停靠槽
            """register。"""
            return 上下文.slots.register({#条目
                'name':'conversation.input.dock',#停靠
                'id':'todo',#id
                'order':0,#序
                'locale':命名空间,#文案
            },待办停靠)#组件
        上下文.slots.inject('conversation.input.dock',登记)#等槽
    return {'name':'conversation-todo-dock','inject':['slots'],'apply':应用}#插件
