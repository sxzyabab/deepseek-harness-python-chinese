'宿主设置文档的客户端镜像。浏览器里只有这里读 settings.describe。'
from ...存储 import 创建快照存储

class 设置描述镜像:
    '串行化每一次 settings.describe。飞行中的再次加载只标一次重跑'
    def __init__(自身,上下文):
        '空闲快照。还没有答案，也没有错误'
        自身.上下文=上下文
        自身.仓=创建快照存储({
            'status':'idle',
            'view':None,
            'error':None,
        })
        自身.飞行中=None
        自身.需重跑=False
        自身.世代=0

    def getSnapshot(自身):
        '当前同步快照。引用保持到下一次变更'
        return 自身.仓.getSnapshot()

    def subscribe(自身,监听):
        '观察快照替换，返回退订'
        return 自身.仓.subscribe(监听)

    def 加载(自身):
        '从宿主刷新。飞行中的调用只标一次重跑，读完再决定要不要再读'
        if 自身.飞行中 is not None:
            自身.需重跑=True
            return
        自身.飞行中=True
        try:
            while True:
                先前=自身.仓.getSnapshot()
                if 先前['status']=='idle':
                    加载中=dict(先前)
                    加载中['status']='loading'
                    自身.仓.set(加载中)
                自身.需重跑=False#这次读覆盖此前标上的重跑
                自身.世代+=1
                世代=自身.世代
                try:
                    应答=自身.上下文.remote.settings.describe()
                    if 应答['ok'] is True:
                        结局={'view':应答['value']}
                    else:
                        结局={'failure':应答['error']['message']}
                except Exception as 错误:
                    结局={'failure':str(错误)}
                if 世代!=自身.世代:#写应答使这次读失效
                    continue
                if 'view' in 结局:
                    自身.仓.set({'status':'ready','view':结局['view'],'error':None})
                else:
                    持有=自身.仓.getSnapshot()
                    if 持有.get('view') is None:
                        状态='idle'
                    else:
                        状态='ready'
                    自身.仓.set({
                        'status':状态,
                        'view':持有.get('view'),
                        'error':结局['failure'],
                    })
                if 自身.需重跑 is not True:
                    break
        finally:
            自身.飞行中=None

    def 确保(自身):
        '已经持有答案就返回。只在 idle 时读取'
        if 自身.飞行中 is not None:
            return
        if 自身.getSnapshot()['status']=='idle':
            自身.加载()

    def 接纳视图(自身,视图):
        '不读导线，把一次写应答折进持有文档，并使还在读的那次失效'
        先前=自身.仓.getSnapshot()
        自身.世代+=1
        if 自身.飞行中 is not None:
            自身.需重跑=True
        if 先前.get('view') is None:
            return
        原表=先前['view']['namespaces']
        命中=False
        for 行 in 原表:
            if 行['ns']==视图['ns']:
                命中=True
                break
        if 命中 is True:
            新表=[]
            for 行 in 原表:
                if 行['ns']==视图['ns']:
                    新表.append(视图)
                else:
                    新表.append(行)
        else:
            新表=list(原表)
            新表.append(视图)
        新视图=dict(先前['view'])
        新视图['namespaces']=新表
        下一=dict(先前)
        下一['view']=新视图
        自身.仓.set(下一)

    def 命名空间(自身,ns):
        '在持有视图上按 ns 找一行。还没有答案或未登记时返回 None'
        视图=自身.仓.getSnapshot().get('view')
        if 视图 is None:
            return None
        for 行 in 视图['namespaces']:
            if 行['ns']==ns:
                return 行
        return None
