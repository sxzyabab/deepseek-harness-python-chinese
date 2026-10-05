from ....基础设施.通用工具 import 观察者集合

__all__=['创建语言行存储']#仅中文公开名

def 创建语言行存储():
    '返回语言行存储句柄（纯映射 + sync 动作）'
    状态={'active':'','options':[],'revision':-1}#空选项，修订 -1
    监听者=观察者集合()#变更订阅

    def 取快照():
        '返回当前状态映射'
        return 状态#当前状态

    def 订阅(回调):
        '登记变更回调，返回退订'
        return 监听者.订阅(回调)#退订器

    def 同步(当前,选项,修订):
        '旧修订丢弃；否则写入并通知'
        if 修订<=状态['revision']:#旧修订
            return#丢弃
        状态['active']=当前#当前语言
        状态['options']=list(选项)#选项
        状态['revision']=修订#记下修订
        监听者.通知()#触发

    def 初始态():
        '规格 init：当前状态引用'
        return 状态#状态

    return {#存储句柄；getSnapshot/subscribe/actions 是槽位存储协议键
        'getSnapshot':取快照,#读快照
        'subscribe':订阅,#订阅
        'actions':{'sync':同步},#写入面
        'spec':{'init':初始态},#规格形
    }#句柄结束
