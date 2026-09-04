"""Runtime 后端发出的、与界域无关的 Console 事件。

对齐上游 `shared/cdp/console.ts`。公开面仅中文名。
"""
__all__=['运行时控制台类型','运行时控制台事件','运行时异常事件','运行时控制台后端事件']#仅中文公开名

运行时控制台类型=(#Console类别
    'log','debug','info','error','warning','dir','dirxml','table','trace','clear',#常用
    'startGroup','startGroupCollapsed','endGroup','assert','profile','profileEnd','count','timeEnd',#组与计时
)#类型结束

class 运行时控制台事件:#Console事件
    """关联到单个被检查界域的一条 Console 事件。"""
    def __init__(自身,type,arguments,timestamp,contextId=None,stackTrace=None):#构造
        """保存 Console 事件字段。"""
        自身.type=type#类别
        自身.arguments=tuple(arguments)#参数
        自身.timestamp=timestamp#时间戳
        自身.contextId=contextId#上下文id
        自身.stackTrace=stackTrace#栈跟踪

class 运行时异常事件:#异常事件
    """在被检查界域中观察到的一条未捕获异常。"""
    def __init__(自身,timestamp,details,contextId=None):#构造
        """保存异常事件字段。"""
        自身.timestamp=timestamp#时间戳
        自身.contextId=contextId#上下文id
        自身.details=details#异常详情

def 运行时控制台后端事件(类型,事件):#Console后端事件
    """界域后端发出的 Console 域事件。"""
    return {'type':类型,'event':事件}#判别联合
