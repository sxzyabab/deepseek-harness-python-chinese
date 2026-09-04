"""`node:timers/promises`：基于 Worker 定时器全局的真实实现。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/timers/promises.ts`。
公开面中文名；Node 面经别名与 default 暴露英文名。
"""
__all__=[#中文公开名与Node英文挂名
    '设超时','设立即',
    'setTimeout','setImmediate','scheduler','__esModule','default',
]#公开结束

def 中止异常():#被中止的等待所报告的拒绝
    """按 Node 与 DOM 的拼写构造 AbortError。"""
    错误=Exception('The operation was aborted.')#基错误
    错误.name='AbortError'#DOM名
    return 错误#交回

def 设超时(延迟毫秒=None,值=None,选项=None):#延迟兑现
    """延迟后兑现；信号中止时拒绝。"""
    全局=globals()#宿主全局
    承诺类=全局.get('Promise')#Promise构造器

    def 执行(兑现,拒绝):#构造Promise体
        """武装定时器并监听中止。"""
        信号=None if 选项 is None else 选项.get('signal') if isinstance(选项,dict) else getattr(选项,'signal',None)#信号
        if 信号 is not None and getattr(信号,'aborted',False) is True:#已中止
            拒绝(中止异常())#立即拒绝
            return#结束
        定时器=全局['setTimeout'](lambda:兑现(值),延迟毫秒)#武装定时器

        def 中止时(*位置参数):#监听中止
            """清定时器并拒绝。"""
            全局['clearTimeout'](定时器)#清定时器
            拒绝(中止异常())#拒绝

        if 信号 is not None and hasattr(信号,'addEventListener'):#可监听
            信号.addEventListener('abort',中止时,{'once':True})#只听一次

    if callable(承诺类): return 承诺类(执行)#返回Promise
    raise Exception('web-preview: Promise is required for node:timers/promises')#无Promise

def 设立即(值=None):#下一宏任务兑现
    """在下一个宏任务兑现。"""
    return 设超时(0,值)#零延迟

def 等待(延迟毫秒=None,选项=None):#scheduler.wait
    """等待指定毫秒。"""
    return 设超时(延迟毫秒,None,选项)#委托设超时

def 让出():#scheduler.yield
    """让出一拍。"""
    return 设超时(0)#零延迟

setTimeout=设超时#Node面
setImmediate=设立即#Node面
scheduler={'wait':等待,'yield':让出}#调度辅助
__esModule=True#CJS互操作
default={'setTimeout':设超时,'setImmediate':设立即,'scheduler':scheduler}#默认导出
