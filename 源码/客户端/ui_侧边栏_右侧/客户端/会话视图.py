import threading

__all__=['侧栏会话视图']

def 已中止(信号):
    if 信号 is None:
        return False
    return 信号.is_set()

class 侧栏会话视图:
    """一份侧栏视图的会话引用、保留正文与已提交挂载寿命。"""
    def __init__(自身,会话标识,会话面,拆除时,标签释放时):
        自身.会话标识=会话标识
        自身.拆除时=拆除时
        自身.标签释放时=标签释放时
        自身.引用=会话面.retain(会话标识,{'source':'sidebarView'})
        自身.标签表={}
        自身.挂载数=0
        自身.已退役=False
        自身.已拆除=False
        就绪=getattr(自身.引用,'ready',None)
        if 就绪 is not None:
            def 报错():
                try:
                    if hasattr(就绪,'等待'):
                        就绪.等待()
                except Exception as 错误:
                    print('Sidebar Session opening failed:',错误)
            threading.Thread(target=报错,daemon=True).start()

    def 有保留标签(自身):
        return len(自身.标签表)>0

    def 挂载(自身):
        自身.挂载数+=1
        def 卸():
            自身.挂载数-=1
            if 自身.已退役 and 自身.挂载数==0:
                自身.拆除()
        return 卸

    def 保留标签(自身,标签标识,信号):
        if 已中止(信号) or 自身.已拆除:
            return lambda:None
        自身.标签表[标签标识]=自身.标签表.get(标签标识,0)+1
        持有=[True]
        def 释放():
            if not 持有[0]:
                return
            持有[0]=False
            计数=自身.标签表.get(标签标识,0)
            if 计数<=1:
                if 标签标识 in 自身.标签表:
                    del 自身.标签表[标签标识]
            else:
                自身.标签表[标签标识]=计数-1
            自身.标签释放时(自身)
        if 信号 is not None:
            def 盯():
                信号.wait()
                释放()
            threading.Thread(target=盯,daemon=True).start()
        return 释放

    def 退役(自身):
        自身.已退役=True
        if 自身.挂载数==0:
            自身.拆除()

    def 拆除(自身):
        if 自身.已拆除:
            return
        自身.已拆除=True
        自身.已退役=True
        自身.拆除时(自身)
        自身.引用.release()
