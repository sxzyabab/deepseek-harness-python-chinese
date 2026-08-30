"""InputState.queue 投影的队列读面。

对齐上游 `ui-conversation/src/client/queue/store.ts`。公开面仅中文名。
纯投影——没有第二份 store，也不拷贝；会话快照在无关互换时保持队列数组引用稳定。
"""

__all__=['队列读面','队列读面自会话']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 队列读面:#裸可观察：getSnapshot / subscribe
    """把一份会话的瞬态收件箱行投影成可观察。"""

    def __init__(自身,会话面):#记下会话面
        """驻留会话面。"""
        自身.会话面=会话面#面

    def getSnapshot(自身):#读队列
        """返回会话快照里引用稳定的队列数组。"""
        快照=自身.会话面.getSnapshot()#快照
        return 取字段(快照,'queue') or []#队列

    def subscribe(自身,回调):#订阅
        """订阅会话面；队列随会话快照一起通知。"""
        return 自身.会话面.subscribe(回调)#退订器

def 队列读面自会话(会话面):#从会话面投影队列读面
    """接线层把它叠到 InputState.queue 上。"""
    return 队列读面(会话面)#读面
