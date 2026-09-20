from ...node.builtin_modules.implemented.async_hooks import (
    绑定异步上下文,
    捕获异步上下文,
    在异步上下文运行,
)

__all__=['安装异步上下文钩子']

_已安装=False

def 绑定槽(处理器,快照):
    """包装一个处理器槽，非可调用槽原样留下。"""
    if not callable(处理器):
        return 处理器
    def 包装(值):
        """在捕获的快照下调用处理器。"""
        def 调用处理器():
            """把值交给原处理器。"""
            return 处理器(值)
        return 在异步上下文运行(快照,调用处理器)
    return 包装

def 安装异步上下文钩子():
    """给平台注册点打补丁。幂等；在宿主树启动前从 worker 入口调用一次。"""
    global _已安装
    if _已安装:
        return
    _已安装=True
    全局=globals()
    承诺类=全局['Promise'] if 'Promise' in 全局 else None
    if 承诺类 is not None and hasattr(承诺类,'prototype'):
        原型=承诺类.prototype
        原生then=getattr(原型,'then',None)
        def 补丁then(自身,onFulfilled=None,onRejected=None):
            """在注册点捕获快照，包装处理器槽后调用原生 then。"""
            快照=捕获异步上下文()
            if 快照 is None:
                return 原生then(自身,onFulfilled,onRejected)
            return 原生then(自身,绑定槽(onFulfilled,快照),绑定槽(onRejected,快照))
        原型.then=补丁then
    原生微任务=全局['queueMicrotask'] if 'queueMicrotask' in 全局 else None
    if callable(原生微任务):
        def 补丁微任务(回调):
            """绑定后排队微任务。"""
            原生微任务(绑定异步上下文(回调))
        全局['queueMicrotask']=补丁微任务
    原生fetch=全局['fetch'] if 'fetch' in 全局 else None
    if callable(原生fetch):
        def 补丁fetch(输入,初始化=None):
            """把响应续体绑到调用点，供在附加处理器前转交 promise 的消费者。"""
            快照=捕获异步上下文()
            if 快照 is None:
                return 原生fetch(输入,初始化)
            承诺=原生fetch(输入,初始化)
            def 兑现(响应):
                """在快照下返回响应。"""
                def 交响应():
                    """原样返回响应。"""
                    return 响应
                return 在异步上下文运行(快照,交响应)
            def 拒绝(原因):
                """在快照下重抛。"""
                def 重抛():
                    """抛出原因。"""
                    raise 原因
                return 在异步上下文运行(快照,重抛)
            then面=getattr(承诺,'then',None)
            if callable(then面):
                return then面(兑现,拒绝)
            return 承诺
        全局['fetch']=补丁fetch
