"""本地注册表的事件路由：订阅按过滤归档，每次提交向每个匹配监听器投递一次并包含错误。"""
from ...内核.作用域 import 匿名条目,获取作用域

class 任务层:
    """一层作用域的贡献：从它挂接的任务控制器，以及在那里注册的 {owners:scope} 订阅。"""
    def __init__(自身,_作用域=None):
        """建空层。"""
        自身.控制器=匿名条目()
        自身.作用域订阅=匿名条目()

    def 是否空(自身):
        """两表皆空才算空层。"""
        return 自身.控制器.是否空() and 自身.作用域订阅.是否空()

class 任务事件枢纽:
    """把事件路由到订阅。{owner} 与 {owners:all} 不论登记处；{owners:scope} 记入登记上下文的作用域层。"""
    def __init__(自身,层集,警告):
        """记下层集与监听失败汇。"""
        自身.层集=层集
        自身.警告=警告
        自身.无作用域=[]

    def 订阅(自身,上下文,过滤,监听器):
        """把一次监听登记为 ctx 的副作用。"""
        订阅项={'filter':过滤,'listener':监听器}
        if ('owners' in 过滤) and 过滤['owners']=='scope':
            def 追加(层):
                """记入本层作用域订阅。"""
                return 层.作用域订阅.追加(订阅项)
            return 自身.层集.副作用(上下文,追加,{'标签':'jobs.events.subscribe()'})
        def 执行体():
            """登记无作用域订阅。"""
            自身.无作用域.append(订阅项)
            def 拆除():
                """注销。"""
                if 订阅项 in 自身.无作用域:
                    自身.无作用域.remove(订阅项)
            return 拆除
        return 上下文.副作用(执行体,'jobs.events.subscribe()')

    def 发出(自身,事件,所有者):
        """向每个匹配订阅投递一次事件，包含监听失败。"""
        所有者标识=None if 所有者 is None else 所有者.id
        for 订阅项 in list(自身.无作用域):
            过滤=订阅项['filter']
            if ('owner' in 过滤) and 所有者标识 is not None and 所有者标识!=过滤['owner']:
                continue
            自身.投递(订阅项,事件)
        for 订阅项 in 自身.层集.全局.作用域订阅.诸值():
            自身.投递(订阅项,事件)
        作用域=None if 所有者 is None else 获取作用域(所有者.ctx)
        for 层 in 自身.层集.链上层(作用域):
            for 订阅项 in 层.作用域订阅.诸值():
                自身.投递(订阅项,事件)

    def 投递(自身,订阅项,事件):
        """包含一次回调。"""
        try:
            订阅项['listener'](事件)
        except BaseException as 错误:
            自身.警告('jobs: event listener threw on '+str(事件['type'])+': '+str(错误))

__all__=['任务层','任务事件枢纽']
