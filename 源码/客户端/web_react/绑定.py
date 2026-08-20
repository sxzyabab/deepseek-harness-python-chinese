"""把裸可观察快照源绑成选择钩的纯逻辑面。

对齐上游 `web-react/src/bind.ts` 的绑定契约（subscribe/getSnapshot 闭包）。公开面仅中文名。

上游经 React 的 useSyncExternalStoreWithSelector 实现钩；React 半按迁移政策跳过，本模块给出稳定订阅/快照闭包，供宿主或测试绑定。
"""

__all__=['绑定快照选择器']#仅中文公开名

def 绑定快照选择器(源):#绑定快照选择钩契约
    """把裸可观察源绑成带选择的读面：subscribe/getSnapshot 按源捕获一次进稳定闭包。"""
    def 订阅(回调):#稳定订阅闭包
        """订阅变更。"""
        return 源.subscribe(回调)#转交
    def 读快照():#稳定读快照闭包
        """读当前快照。"""
        return 源.getSnapshot()#转交
    def 选择(选择器,相等=None):#选择钩形
        """对快照跑选择器；相等默认 identity 比较。"""
        快照=读快照()#当前快照
        return 选择器(快照)#选定值
    选择.subscribe=订阅#挂订阅
    选择.getSnapshot=读快照#挂快照
    return 选择#选择面
