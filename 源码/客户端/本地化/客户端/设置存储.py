from ....基础设施.通用工具 import 观察者集合

__all__=['创建语言行存储']#仅中文公开名

class 语言行存储:
    '语言行镜像。钩子源是带 getSnapshot 与 subscribe 的对象，槽位按 create 取这一份'
    def __init__(自身):
        '空选项，修订 -1，这样修订 0 仍算变更'
        自身.状态={'active':'','options':[],'revision':-1}#独立状态
        自身.监听者=观察者集合()#变更订阅
        自身.actions={'sync':自身.同步}#写入面
        自身.spec={'init':自身.初始态}#规格形

    def getSnapshot(自身):
        '返回当前状态映射'
        return 自身.状态#当前状态

    def subscribe(自身,回调):
        '登记变更回调，返回退订'
        return 自身.监听者.订阅(回调)#退订器

    def 同步(自身,当前,选项,修订):
        '旧修订丢弃；否则写入并通知'
        if 修订<=自身.状态['revision']:#旧修订
            return#丢弃
        自身.状态['active']=当前#当前语言
        自身.状态['options']=list(选项)#选项
        自身.状态['revision']=修订#记下修订
        自身.监听者.通知()#触发

    def 初始态(自身):
        '规格 init：当前状态引用'
        return 自身.状态#状态

    def create(自身,键=None):
        '根作用域交回这一份'
        return 自身#共享

def 创建语言行存储():
    '返回语言行存储句柄'
    return 语言行存储()#句柄
