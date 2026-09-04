"""任何 VFS 模块运行前 Worker 所需的 `process` 全局。Cordis 在构造 Loader 时
会读 `process.env` 与 `process.versions.node`，且 `cordis.yml` 保留其
`!!js process.*` 表达式，因此配置字节与 Node 部署保持一致。第三方 Node
包用是否存在 `process.title` 来避开仅浏览器全局。

对齐上游 `webworker-runtime/src/node/globals/process.ts`。公开面仅中文名。
"""
import time#高分辨率起点
from ...module_system.模块加载器 import 要求活动模块加载器#导入活动加载器
from ..进程表 import 进程存活,信号进程#导入进程表操作

__all__=['安装进程全局']#仅中文公开名

def 安装进程全局(选项):#安装process全局
    """发布 `globalThis.process`。

    `versions.node` 故意为 `0.0.0`：使 Cordis 的
    `ModuleLoader.fromInternal()` 返回 undefined 而不去碰 Node 内部，
    从而让 Worker 能安装自己的模块 seam。
    """
    起点=time.perf_counter()*1000#启动时刻（毫秒，对齐 performance.now）

    def 写(目标):#构造写函数
        """去尾换行后打印。"""
        def 写出(块):#写出一块
            """写到控制台。"""
            文本=块[:-1] if isinstance(块,str) and 块.endswith('\n') else 块#去尾换行
            print(文本)#打印（对齐 console.log/error）
            return True#恒成功
        return 写出#交回写函数

    def 取内置模块(标识):#解析内置模块
        """Node 22 `process.getBuiltinModule`。"""
        try:#尝试解析
            解析结果=要求活动模块加载器().解析(标识,'/')#经活动加载器
        except Exception:#解析失败
            #尚未挂上加载器，或 id 无处可解析：Node 对非内置返回 undefined 而不抛错。
            return None#非内置
        if isinstance(解析结果,dict) and 解析结果.get('kind')=='static':#静态工厂
            return 解析结果['factory']()#调用工厂
        return None#非静态

    def 杀(pid,信号='SIGTERM'):#发信号
        """向经 child_process 启动的命令发信号；0 为存活探测。"""
        if 信号==0:#存活探测
            if 进程存活(pid): return True#仍在表中
            错误=Exception('kill ESRCH')#构造ESRCH
            错误.code='ESRCH'#错误码
            错误.syscall='kill'#系统调用名
            raise 错误#抛出
        return 信号进程(pid,信号)#投递信号

    def 下一滴答(回调,*参数):#微任务调度
        """queueMicrotask 形态。"""
        def 运行():#微任务体
            """调用回调。"""
            回调(*参数)#调用
        globals()['queueMicrotask'](运行)#微任务

    def 高分辨纳秒():#纳秒差
        """自启动起的纳秒差。"""
        return int(round((time.perf_counter()*1000-起点)*1e6))#纳秒

    def 运行秒数():#运行秒数
        """自启动起的秒数。"""
        return (time.perf_counter()*1000-起点)/1000#秒

    def 退出(码=None):#请求退出
        """仅告警；worker 继续运行。"""
        print(f'webworker process: exit({码 if 码 is not None else 0}) requested; the worker keeps running')#告警

    垫片={#构造垫片对象
        'env':dict(选项.get('env') or {}),#可写环境副本
        'argv':list(选项.get('argv') or ['node','dsh-webworker']),#参数向量
        'execArgv':[],#无执行参数
        'title':'dsh-webworker',#进程标题
        'platform':'linux',#报告linux
        'arch':'x64',#报告x64
        'pid':1,#宿主pid
        'version':'v0.0.0',#版本串
        'versions':{'node':'0.0.0'},#故意零版本
        'getBuiltinModule':取内置模块,#取内置
        'kill':杀,#发信号
        'nextTick':下一滴答,#微任务
        'stdout':{'write':写('log')},#标准输出写
        'stderr':{'write':写('error')},#标准错误写
        'hrtime':{'bigint':高分辨纳秒},#高分辨率时间
        'uptime':运行秒数,#运行秒数
        'exit':退出,#仅告警
    }#垫片字段结束

    def 当前目录():#返回虚拟根
        """cwd()。"""
        return 选项['cwd']#虚拟根

    垫片['cwd']=当前目录#挂cwd

    def 空链(*位置参数,**关键字参数):#空事件注册
        """空事件面：返回垫片自身。"""
        return 垫片#链式

    def 空列表(*位置参数,**关键字参数):#空监听列表
        """恒返回空列表。"""
        return []#空列表

    def 零数量(*位置参数,**关键字参数):#监听数量
        """恒返回 0。"""
        return 0#零数量

    def 空发射(*位置参数,**关键字参数):#空发射
        """恒返回 false。"""
        return False#空发射

    垫片['on']=空链#空on
    垫片['off']=空链#空off
    垫片['once']=空链#空once
    垫片['prependListener']=空链#空前置
    垫片['prependOnceListener']=空链#空前置once
    垫片['removeListener']=空链#空移除
    垫片['removeAllListeners']=空链#空清除
    垫片['listeners']=空列表#空列表
    垫片['listenerCount']=零数量#零数量
    垫片['setMaxListeners']=空链#空旋钮
    垫片['emit']=空发射#空发射
    全局=globals()#宿主全局
    全局['process']=垫片#挂到全局
    return 垫片#返回垫片
