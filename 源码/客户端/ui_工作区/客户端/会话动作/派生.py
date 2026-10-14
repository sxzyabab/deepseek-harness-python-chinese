__all__=['派生','投影源']

class 投影源:
    '源快照身份变化才重算；钩子要 getSnapshot/subscribe 方法'

    def __init__(自身,源,投影):
        '记下源与投影'
        自身.源=源#可观察源
        自身.投影=投影#纯函数
        自身.见过=None#上次快照
        自身.值=None#投影值
        自身.就绪=False#是否已算

    def getSnapshot(自身):
        '身份未变复用'
        快照=自身.源.getSnapshot()#读源
        if (not 自身.就绪) or (快照 is not 自身.见过):#变了
            自身.见过=快照
            自身.值=自身.投影(快照)#重算
            自身.就绪=True#已算
        return 自身.值#值

    def subscribe(自身,监听):
        '透传源订阅'
        return 自身.源.subscribe(监听)#退订

def 派生(源,投影):
    '返回带方法的投影源，不返回字典'
    return 投影源(源,投影)#对象
