from ...内核.会话 import 会话#导入会话

def 播种描述符回合(子标识,种子,描述符):#建造含描述符的创建种子
    """建造子体创建种子：任何继承的父历史前缀，后面跟一条对模型隐藏、回合之间的 descriptor 事件。经 Session 暂存以分配序号，并强制耐久日志同一套无损 JSON 规则。"""
    暂存=会话.创建(子标识,种子)#用前缀暂存会话
    if hasattr(暂存,'追加'):#中文追加
        暂存.追加('subagent/descriptor',描述符)#追加隐藏描述符
    else:#英文append
        暂存.append('subagent/descriptor',描述符)#追加隐藏描述符
    事件列表=getattr(暂存,'events',None)#英文事件
    if 事件列表 is None:#中文属性
        事件列表=getattr(暂存,'事件列表',[])#中文事件列表
    return list(事件列表)#复制事件
