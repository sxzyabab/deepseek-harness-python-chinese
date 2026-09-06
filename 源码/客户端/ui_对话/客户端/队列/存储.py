"""InputState.queue 投影的队列读面。

对齐上游 `ui-conversation/src/client/queue/store.ts`。公开面仅中文名。
纯投影——没有第二份存储，也不拷贝；会话快照在无关互换时保持队列数组引用稳定。
快照为 dict。
"""

__all__=['队列读面','队列读面自会话']#仅中文公开名

class 队列读面:
    """把一份会话的瞬态收件箱行投影成可观察。"""

    def __init__(自身,会话面):
        """驻留会话面。"""
        自身.会话面=会话面#面

    def getSnapshot(自身):
        """返回会话快照里引用稳定的队列数组。"""
        快照=自身.会话面.getSnapshot()#快照
        队列=快照['queue'] if 快照 is not None and 'queue' in 快照 else None#队列
        return 队列 if 队列 is not None else []#空容器仍返回

    def subscribe(自身,回调):
        """订阅会话面；队列随会话快照一起通知。"""
        return 自身.会话面.subscribe(回调)#退订器

def 队列读面自会话(会话面):
    """接线层把它叠到 InputState.queue 上。"""
    return 队列读面(会话面)#读面
