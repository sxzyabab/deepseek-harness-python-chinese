'标签关掉或插件拆掉时，放开还留着的查看状态'

__all__=['保留文档标签']

def 保留文档标签(上下文):
    '同一个信号重复拿住时共用一个监听。插件拆掉时忘掉还留着的'
    留着={}
    def 拆光():
        '插件拆掉时忘掉还留着的标签'
        def 拆():
            '逐个忘掉'
            for 忘掉 in list(留着.values()):
                忘掉()
        return 拆
    上下文.副作用(拆光)
    def 拿住(标签标识,信号,忘掉标签):
        '信号已经中止就立刻忘掉。否则等到 abort'
        if getattr(信号,'aborted',False):
            忘掉标签(标签标识)
            return
        if 信号 in 留着:
            return
        def 忘掉():
            '摘掉监听并忘掉这一标签'
            信号.removeEventListener('abort',忘掉)
            if 信号 in 留着:
                del 留着[信号]
            忘掉标签(标签标识)
        留着[信号]=忘掉
        信号.addEventListener('abort',忘掉,{'once':True})
    return 拿住
