import time
from ...module_system.模块加载器 import 要求活动模块加载器
from ..进程表 import 进程存活,信号进程

__all__=['安装进程全局']

def 安装进程全局(选项):
    """发布 `globalThis.process`。

    `versions.node` 故意为 `0.0.0`：使 Cordis 的
    `ModuleLoader.fromInternal()` 返回 undefined 而不去碰 Node 内部，
    从而让 Worker 能安装自己的模块 seam。
    """
    起点=time.perf_counter_ns()

    def 写(目标):
        """去尾换行后打印。"""
        def 写出(块):
            """写到控制台。"""
            文本=块[:-1] if isinstance(块,str) and 块.endswith('\n') else 块
            print(文本)
            return True
        return 写出

    def 取内置模块(标识):
        """Node 22 `process.getBuiltinModule`。"""
        try:
            解析结果=要求活动模块加载器().解析(标识,'/')
        except Exception:#加载器.resolve 对非内置与未挂载什么都可能抛，Node 要 undefined，契约未定所以收不窄
            #尚未挂上加载器，或 id 无处可解析：Node 对非内置返回 undefined 而不抛错。
            return None
        if isinstance(解析结果,dict) and 'kind' in 解析结果 and 解析结果['kind']=='static':
            return 解析结果['factory']()
        return None

    def 杀(pid,信号='SIGTERM'):
        """向经 child_process 启动的命令发信号；0 为存活探测。"""
        if 信号==0:
            if 进程存活(pid): return True
            错误=Exception('kill ESRCH')
            错误.code='ESRCH'
            错误.syscall='kill'
            raise 错误
        return 信号进程(pid,信号)

    def 下一滴答(回调,*参数):
        """queueMicrotask 形态。"""
        def 运行():
            """调用回调。"""
            回调(*参数)
        globals()['queueMicrotask'](运行)

    def 高分辨纳秒():
        """自启动起的纳秒差。"""
        return time.perf_counter_ns()-起点

    def 运行秒数():
        """自启动起的秒数。"""
        return (time.perf_counter_ns()-起点)/1e9

    def 退出(码=None):
        """仅告警；worker 继续运行。"""
        print(f'webworker process: exit({码 if 码 is not None else 0}) requested; the worker keeps running')

    垫片={
        'env':dict({} if 'env' not in 选项 else 选项['env']),
        'argv':list(['node','dsh-webworker'] if 'argv' not in 选项 else 选项['argv']),#??默认 argv，空列表合法
        'execArgv':[],
        'title':'dsh-webworker',
        'platform':'linux',
        'arch':'x64',
        'pid':1,
        'version':'v0.0.0',
        'versions':{'node':'0.0.0'},
        'getBuiltinModule':取内置模块,
        'kill':杀,
        'nextTick':下一滴答,
        'stdout':{'write':写('log')},
        'stderr':{'write':写('error')},
        'hrtime':{'bigint':高分辨纳秒},
        'uptime':运行秒数,
        'exit':退出,
    }

    def 当前目录():
        """cwd()。"""
        return 选项['cwd']

    垫片['cwd']=当前目录

    def 空链(*位置参数,**关键字参数):
        """空事件面：返回垫片自身。"""
        return 垫片

    def 空列表(*位置参数,**关键字参数):
        """恒返回空列表。"""
        return []

    def 零数量(*位置参数,**关键字参数):
        """恒返回 0。"""
        return 0

    def 空发射(*位置参数,**关键字参数):
        """恒返回 false。"""
        return False

    垫片['on']=空链
    垫片['off']=空链
    垫片['once']=空链
    垫片['prependListener']=空链
    垫片['prependOnceListener']=空链
    垫片['removeListener']=空链
    垫片['removeAllListeners']=空链
    垫片['listeners']=空列表
    垫片['listenerCount']=零数量
    垫片['setMaxListeners']=空链
    垫片['emit']=空发射
    全局=globals()
    全局['process']=垫片
    return 垫片
