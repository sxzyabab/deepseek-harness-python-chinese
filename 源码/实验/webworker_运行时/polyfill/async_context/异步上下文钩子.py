"""ALS shim 的全局钩子层：在回调被注册处捕获异步上下文，
在回调运行处恢复。配合 async_hooks 的折叠栈，
给 worker 两种覆盖——边界内的 await 因边界栈条目仍开着
而保持其存储，交给平台的工作（then、queueMicrotask、定时器、
fetch）因注册时已捕获而保持其存储。

此处打补丁：Promise.prototype.then、queueMicrotask 与 fetch。
补丁保持的两个性质：
- 值仍是原生 promise——包装的是处理器，从不包装链；
- 空处理器槽保持空。

对齐上游 `webworker-runtime/src/polyfill/async-context/async-context-hooks.ts`。公开面仅中文名。
"""
from ...node.builtin_modules.implemented.async_hooks import (
    绑定异步上下文,#bindAsyncContext
    捕获异步上下文,#captureAsyncContext
    在异步上下文运行,#runWithAsyncContext
)#ALS绑定面

__all__=['安装异步上下文钩子']#仅中文公开名

_已安装=False#是否已打补丁

def 绑定槽(处理器,快照):#绑定槽
    """包装一个处理器槽，非可调用槽原样留下。"""
    if not callable(处理器):#非函数原样
        return 处理器#原样
    def 包装(值):#恢复后调用
        """在捕获的快照下调用处理器。"""
        return 在异步上下文运行(快照,lambda:处理器(值))#恢复后调用
    return 包装#绑定后处理器

def 安装异步上下文钩子():#安装钩子
    """给平台注册点打补丁。幂等；在宿主树启动前从 worker 入口调用一次。"""
    global _已安装#安装标志
    if _已安装:#幂等
        return#已安装
    _已安装=True#置位
    全局=globals()#宿主全局命名空间面
    承诺类=全局.get('Promise')#Promise构造器（浏览器宿主）
    if 承诺类 is not None and hasattr(承诺类,'prototype'):#有原型
        原型=承诺类.prototype#原型对象
        原生then=getattr(原型,'then',None)#原生then
        def 补丁then(自身,onFulfilled=None,onRejected=None):#补丁then
            """在注册点捕获快照，包装处理器槽后调用原生 then。"""
            快照=捕获异步上下文()#注册点快照
            if 快照 is None:#无上下文直通
                return 原生then(自身,onFulfilled,onRejected)#直通
            return 原生then(自身,绑定槽(onFulfilled,快照),绑定槽(onRejected,快照))#绑定后调用
        原型.then=补丁then#挂补丁
    原生微任务=全局.get('queueMicrotask')#原生微任务
    if callable(原生微任务):#可补丁
        def 补丁微任务(回调):#补丁微任务
            """绑定后排队微任务。"""
            原生微任务(绑定异步上下文(回调))#绑定后排队
        全局['queueMicrotask']=补丁微任务#挂补丁
    原生fetch=全局.get('fetch')#原生fetch
    if callable(原生fetch):#可补丁
        def 补丁fetch(输入,初始化=None):#补丁fetch
            """把响应续体绑到调用点，供在附加处理器前转交 promise 的消费者。"""
            快照=捕获异步上下文()#调用点快照
            if 快照 is None:#无上下文直通
                return 原生fetch(输入,初始化)#直通
            承诺=原生fetch(输入,初始化)#真实请求
            def 兑现(响应):#兑现恢复
                """在快照下返回响应。"""
                return 在异步上下文运行(快照,lambda:响应)#恢复
            def 拒绝(原因):#拒绝恢复
                """在快照下重抛。"""
                def 重抛():#重抛体
                    """抛出原因。"""
                    raise 原因#重抛
                return 在异步上下文运行(快照,重抛)#恢复并抛
            then面=getattr(承诺,'then',None)#then方法
            if callable(then面):#有then
                return then面(兑现,拒绝)#挂续体
            return 承诺#无then则原样
        全局['fetch']=补丁fetch#挂补丁
