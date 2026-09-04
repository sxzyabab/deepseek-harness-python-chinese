"""跨 worker 自有 shell 的 `node:child_process`。

浏览器 worker 不能 fork，故本模块即机器的进程层。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/child_process.ts`。
公开面中文名；Node 面经别名与 default 暴露英文名。
"""
from .buffer import Buffer#本包Buffer
from .events import 事件发射器#导入事件发射器
from ...未实现失败 import 未实现失败#导入未实现桩
from ...进程表 import 登记进程,释放进程,信号进程#导入进程表
from ....storage.路径 import dsh根#导入VFS根

__all__=[#中文与Node面
    '工作者子进程','启动','启动同步','执行','执行文件',
    'WorkerChildProcess','spawn','spawnSync','exec','execFile','execSync','execFileSync','fork',
    '__esModule','default',
]#公开结束

模块='node:child_process'#模块说明符

class 工作者可读(事件发射器):#可读管道半
    """管道可读半：携带 Buffer 的 data 事件、end，以及停止交付的 destroy。"""

    def __init__(自身):#构造
        """空可读半。"""
        super().__init__()#初始化
        自身._已毁=False#是否已销毁

    def 设编码(自身,*位置参数):#接受编码空操作
        """接受编码（块始终为以 Buffer 承载的 UTF-8 文本）。"""
        return 自身#链式

    def 暂停(自身):#暂停空操作
        """接受流控请求。"""
        return 自身#链式

    def 恢复(自身):#恢复空操作
        """恢复。"""
        return 自身#链式

    def 推送(自身,文本):#推送一块
        """向 data 监听器交付一块。"""
        if 自身._已毁 or 文本=='': return#已毁或空则跳过
        自身.发射('data',Buffer.from(文本,'utf8'))#发data事件

    def 结束流(自身):#结束流
        """发信号流结束。"""
        if 自身._已毁: return#已毁则跳过
        自身.发射('end')#发end

    def 销毁(自身):#销毁流
        """停止交付。"""
        自身._已毁=True#标记销毁
        自身.发射('close')#发close

    setEncoding=设编码#Node面
    pause=暂停#Node面
    resume=恢复#Node面
    push=推送#Node面
    finish=结束流#内部面
    destroy=销毁#Node面

class 工作者可写(事件发射器):#可写管道半
    """stdin 的可写半：子进程服务执行的批量写。"""

    def __init__(自身):#构造
        """空缓冲。"""
        super().__init__()#初始化
        自身._文本=''#已缓冲文本

    def 写入(自身,块):#缓冲写入
        """缓冲一次写。"""
        自身._文本+=块 if isinstance(块,str) else Buffer.from(块).toString('utf8')#追加文本
        return True#无背压

    def 结束(自身,块=None):#结束stdin
        """结束标准输入。"""
        if 块 is not None: 自身.写入(块)#可选最终写
        自身.发射('finish')#发finish

    def 内容(自身):#取缓冲内容
        """迄今写入的一切。"""
        return 自身._文本#返回文本

    write=写入#Node面
    end=结束#Node面
    contents=内容#内部面

class 工作者子进程(事件发射器):#子进程句柄
    """一条运行中的命令，穿着其消费者读取的 ChildProcess 部分。"""

    def __init__(自身,pid,stdio):#构造句柄
        """按 stdio 处置构造管道。"""
        super().__init__()#初始化发射器
        自身.pid=pid#记下pid
        自身.stdin=工作者可写() if stdio[0]=='pipe' else None#stdin管道
        自身.stdout=工作者可读() if stdio[1]=='pipe' else None#stdout管道
        自身.stderr=工作者可读() if stdio[2]=='pipe' else None#stderr管道
        自身.exitCode=None#退出码
        自身.signalCode=None#信号码

    def 杀死(自身,信号='SIGTERM'):#发信号
        """向本命令投递信号。"""
        return 信号进程(自身.pid,信号)#委托进程表

    kill=杀死#Node面

WorkerChildProcess=工作者子进程#Node面别名

def 规范化stdio(选项):#规范化stdio
    """将 stdio 选项规范为本 shim 读取的三元形式。"""
    if isinstance(选项,str): return [选项,选项,选项]#三流同值
    if 选项 is None: return ['pipe','pipe','pipe']#默认全管道
    return [选项[0] if len(选项)>0 and 选项[0] is not None else 'pipe',#stdin
        选项[1] if len(选项)>1 and 选项[1] is not None else 'pipe',#stdout
        选项[2] if len(选项)>2 and 选项[2] is not None else 'pipe']#stderr

def 规范化环境(选项):#规范化环境
    """命令运行时环境。"""
    进程=globals().get('process')#process
    继承={}#继承环境
    if 进程 is not None:#有process
        环境=进程.get('env') if isinstance(进程,dict) else getattr(进程,'env',None)#env
        if isinstance(环境,dict): 继承=环境#继承
    源=选项 if 选项 is not None else 继承#调用方或继承
    return {键:值 for 键,值 in 源.items() if 值 is not None}#去掉None

def 构造enoent(程序):#构造ENOENT
    """缺失程序按 Node 失败缺失二进制的方式失败。"""
    错误=Exception(f'spawn {程序} ENOENT')#基错误
    错误.code='ENOENT'#错误码
    错误.errno=-2#errno
    错误.path=程序#路径
    错误.syscall=f'spawn {程序}'#系统调用
    return 错误#返回

def 识别shell脚本(argv):#识别shell -c脚本
    """此 argv 是否为解释器应解析脚本的 shell 调用。"""
    if len(argv)<2: return None#过短
    程序=argv[0]#程序
    标志=argv[1]#标志
    if (程序!='bash' and 程序!='sh') or 标志!='-c': return None#非shell -c
    return argv[2] if len(argv)>2 else ''#脚本或空串

def _载入shell面():#惰性载入shell依赖
    """shell 层尚未全量汉化时按约定路径导入。"""
    from ....shell.process.宿主 import 启动进程#进程启动
    from ....shell.文件系统访问 import 宿主文件系统#宿主文件系统
    from ....shell.process.虚拟可执行 import 虚拟可执行#虚拟可执行
    from ....shell.programs.索引 import 标准程序们#标准命令表
    return 启动进程,宿主文件系统,虚拟可执行,标准程序们#交回

def 启动(程序,参数=None,选项=None):#异步启动命令
    """在 worker 中运行一条命令。"""
    if 参数 is None: 参数=[]#缺省参数
    if 选项 is None: 选项={}#缺省选项
    if not isinstance(程序,str) or 程序=='':#非法程序名
        非法=TypeError(f'The "file" argument must be a non-empty string. Received {程序}')#类型错误
        非法.code='ERR_INVALID_ARG_TYPE'#错误码
        raise 非法#抛出
    argv=[程序,*参数]#完整argv
    stdio=规范化stdio(选项.get('stdio'))#规范化stdio
    表项=登记进程()#预留pid
    子=工作者子进程(表项['pid'],stdio)#构造句柄
    已结算=[False]#是否已结算

    def 投递(流,文本):#输出投递
        """管道或继承流输出。"""
        if 文本=='': return#空跳过
        管道=子.stdout if 流=='stdout' else 子.stderr#取管道
        if 管道 is not None:#有管道
            管道.推送(文本)#推入管道
            return#结束
        下标=1 if 流=='stdout' else 2#流下标
        if stdio[下标]=='inherit':#继承流
            print(文本[:-1] if 文本.endswith('\n') else 文本)#打到控制台

    def 结算(退出码):#正常结算
        """正常结算。"""
        if 已结算[0]: return#防重入
        已结算[0]=True#标记结算
        释放进程(表项['pid'])#释放表项
        信号=表项.get('signal')#取出信号
        子.exitCode=None if 信号 is not None else 退出码#信号则无退出码
        子.signalCode=信号#记下信号
        if 子.stdout is not None: 子.stdout.结束流()#结束stdout
        if 子.stderr is not None: 子.stderr.结束流()#结束stderr
        子.发射('exit',子.exitCode,信号)#发exit
        子.发射('close',子.exitCode,信号)#发close

    def 启动失败(错误):#启动失败
        """启动失败。"""
        if 已结算[0]: return#防重入
        已结算[0]=True#标记结算
        释放进程(表项['pid'])#释放表项
        子.发射('error',错误)#发error

    微任务=globals().get('queueMicrotask')#微任务

    def 启动体():#微任务启动体
        """异步启动命令。"""
        try:#尝试
            启动进程,宿主文件系统,虚拟可执行,标准程序们=_载入shell面()#载入shell
            cwd=选项.get('cwd') or dsh根#工作目录
            命令argv=argv#待运行argv
            文件系统=None#可选文件系统
            缺失可执行=None#缺失可执行退出
            可执行=虚拟可执行(程序)#查虚拟可执行
            if 可执行 is not None:#有虚拟包装
                准备=可执行.prepare(参数,{'cwd':cwd,'filesystem':宿主文件系统()})#准备（可能thenable）
                def 处理准备(prepared):#处理准备结果
                    """处理虚拟包装准备结果。"""
                    nonlocal 命令argv,文件系统,缺失可执行#外层
                    种类=prepared.get('kind') if isinstance(prepared,dict) else getattr(prepared,'kind',None)#种类
                    if 种类=='exit':#立即退出
                        投递('stdout',prepared.get('stdout','') if isinstance(prepared,dict) else prepared.stdout)#stdout
                        投递('stderr',prepared.get('stderr','') if isinstance(prepared,dict) else prepared.stderr)#stderr
                        结算(prepared.get('exitCode') if isinstance(prepared,dict) else prepared.exitCode)#结算
                        return#结束
                    命令argv=prepared.get('argv') if isinstance(prepared,dict) else prepared.argv#替换argv
                    文件系统=prepared.get('filesystem') if isinstance(prepared,dict) else getattr(prepared,'filesystem',None)#可选fs
                    缺失可执行=prepared.get('missingExecutable') if isinstance(prepared,dict) else getattr(prepared,'missingExecutable',None)#缺失
                    续跑()#继续
                def 续跑():#已知性检查与启动
                    """已知性检查与启动。"""
                    命令=命令argv[0]#命令名
                    脚本=识别shell脚本(命令argv)#shell脚本
                    已知=脚本 is not None or 命令 in 标准程序们()#是否已知
                    if not 已知:#未知程序
                        if 缺失可执行 is not None:#有缺失退出
                            投递('stdout',缺失可执行.get('stdout','') if isinstance(缺失可执行,dict) else 缺失可执行.stdout)#stdout
                            投递('stderr',缺失可执行.get('stderr','') if isinstance(缺失可执行,dict) else 缺失可执行.stderr)#stderr
                            结算(缺失可执行.get('exitCode') if isinstance(缺失可执行,dict) else 缺失可执行.exitCode)#结算
                        else: 启动失败(构造enoent(程序))#ENOENT
                        return#结束
                    参数表={#启动参数
                        'script':脚本,'argv':命令argv,'cwd':cwd,#基本
                        'env':规范化环境(选项.get('env')),#环境
                        'stdin':子.stdin.内容() if 子.stdin is not None else '',#stdin
                        'onOutput':投递,'onExit':结算,#回调
                    }#参数结束
                    if 文件系统 is not None: 参数表['fs']=文件系统#可选fs
                    表项['process']=启动进程(参数表)#启动进程
                    if 表项.get('signal') is not None:#已有待投信号
                        if 表项['signal']=='SIGKILL': 表项['process'].destroy()#强杀
                        else: 表项['process'].interrupt()#软中断
                if hasattr(准备,'then') and callable(准备.then):#thenable
                    准备.then(处理准备,lambda e:启动失败(e if isinstance(e,Exception) else Exception(str(e))))#异步
                else: 处理准备(准备)#同步
            else:#无虚拟包装
                命令argv=argv#原argv
                文件系统=None#无
                缺失可执行=None#无
                命令=命令argv[0]#命令名
                脚本=识别shell脚本(命令argv)#shell脚本
                已知=脚本 is not None or 命令 in 标准程序们()#是否已知
                if not 已知:#未知
                    启动失败(构造enoent(程序))#ENOENT
                    return#结束
                参数表={#启动参数
                    'script':脚本,'argv':命令argv,'cwd':cwd,#基本
                    'env':规范化环境(选项.get('env')),#环境
                    'stdin':子.stdin.内容() if 子.stdin is not None else '',#stdin
                    'onOutput':投递,'onExit':结算,#回调
                }#参数结束
                表项['process']=启动进程(参数表)#启动进程
                if 表项.get('signal') is not None:#已有待投信号
                    if 表项['signal']=='SIGKILL': 表项['process'].destroy()#强杀
                    else: 表项['process'].interrupt()#软中断
        except Exception as 错误:#异步失败
            启动失败(错误 if isinstance(错误,Exception) else Exception(str(错误)))#转为Error

    if callable(微任务): 微任务(启动体)#排队
    else: 启动体()#同步
    return 子#立即返回句柄

def 启动同步(程序,参数=None):#同步spawn
    """报告命令无法同步运行（或虚拟可执行的同步探测结果）。"""
    if 参数 is None: 参数=[]#缺省
    空=Buffer.alloc(0) if hasattr(Buffer,'alloc') else b''#空缓冲
    try:#尝试载入shell
        _,_,虚拟可执行,标准程序们=_载入shell面()#载入
    except Exception:#shell未就绪
        错误=构造enoent(程序)#ENOENT
        return {'pid':-1,'status':None,'signal':None,'stdout':空,'stderr':空,'output':[None,空,空],'error':错误}#失败
    可执行=虚拟可执行(程序)#查虚拟可执行
    if 可执行 is not None:#有虚拟包装
        结果=可执行.runSync(参数)#同步探测
        种类=结果.get('kind') if isinstance(结果,dict) else getattr(结果,'kind',None)#种类
        if 种类=='asynchronous':#仅异步可跑
            错误=Exception(f'{模块}.spawnSync cannot run {程序} in the worker host: commands run asynchronously')#异步错误
            return {'pid':-1,'status':None,'signal':None,'stdout':空,'stderr':空,'output':[None,空,空],'error':错误}#失败结果
        stdout=Buffer.from(结果.get('stdout','') if isinstance(结果,dict) else 结果.stdout)#stdout缓冲
        stderr=Buffer.from(结果.get('stderr','') if isinstance(结果,dict) else 结果.stderr)#stderr缓冲
        码=结果.get('exitCode') if isinstance(结果,dict) else 结果.exitCode#退出码
        return {'pid':-1,'status':码,'signal':None,'stdout':stdout,'stderr':stderr,'output':[None,stdout,stderr]}#同步结果
    if 程序 in 标准程序们():#已知程序
        错误=Exception(f'{模块}.spawnSync cannot run {程序} in the worker host: commands run asynchronously')#异步错误
    else: 错误=构造enoent(程序)#ENOENT
    return {'pid':-1,'status':None,'signal':None,'stdout':空,'stderr':空,'output':[None,空,空],'error':错误}#失败结果

def 拆分执行参数(选项,回调):#拆分选项与回调
    """将可选选项参数与回调分开。"""
    if callable(选项): return {'options':{},'callback':选项}#选项实为回调
    return {'options':选项 or {},'callback':回调}#原样配对

def 共享执行(argv,选项,回调):#共享执行体
    """exec 与 execFile 的共享体。"""
    子=启动(argv[0],list(argv[1:]),{**选项,'stdio':'pipe'})#强制管道spawn
    stdout=['']#收集stdout
    stderr=['']#收集stderr
    if 子.stdout is not None: 子.stdout.监听('data',lambda chunk: stdout.__setitem__(0,stdout[0]+str(chunk)))#累加stdout
    if 子.stderr is not None: 子.stderr.监听('data',lambda chunk: stderr.__setitem__(0,stderr[0]+str(chunk)))#累加stderr
    子.监听('error',lambda error: 回调(error if isinstance(error,Exception) else Exception(str(error)),stdout[0],stderr[0]) if 回调 else None)#错误回调
    def 关闭时(码,*其余):#关闭回调
        """关闭回调。"""
        if 回调 is None: return#无回调
        状态=码 if isinstance(码,int) else 1#状态码
        回调(None if 状态==0 else Exception(f"Command failed: {' '.join(argv)}"),stdout[0],stderr[0])#成功或失败
    子.监听('close',关闭时)#close结束
    return 子#返回句柄

def 执行(命令,选项=None,回调=None):#运行命令行
    """运行命令行并经回调报告其输出。"""
    已拆=拆分执行参数(选项,回调)#拆分参数
    return 共享执行(['bash','-c',命令],已拆['options'],已拆['callback'])#经bash -c

def 执行文件(程序,参数=None,选项=None,回调=None):#运行显式argv
    """以显式 argv 运行一程序并经回调报告其输出。"""
    if isinstance(参数,(list,tuple)):#显式参数
        argv=[程序,*参数]#拼argv
        移位=选项#选项
        回调值=回调 if not callable(选项) else 选项#回调
    else:#args实为选项或回调
        argv=[程序]#仅程序
        移位=参数#移位选项
        回调值=选项 if callable(选项) else 回调#回调
    已拆=拆分执行参数(移位,回调值)#拆分
    return 共享执行(argv,已拆['options'],已拆['callback'])#执行

spawn=启动#Node面
spawnSync=启动同步#Node面
exec=执行#Node面
execFile=执行文件#Node面
execSync=未实现失败(模块,'execSync')#execSync拒绝
execFileSync=未实现失败(模块,'execFileSync')#execFileSync拒绝
fork=未实现失败(模块,'fork')#fork拒绝
__esModule=True#CJS互操作标记
default={#默认导出
    'spawn':启动,'spawnSync':启动同步,'exec':执行,'execFile':执行文件,#启动器
    'execFileSync':execFileSync,'execSync':execSync,'fork':fork,#不可用
}#默认导出结束
