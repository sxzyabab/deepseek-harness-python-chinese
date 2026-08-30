"""子进程 seam 的本地 PTY 终端进程实现。

对齐上游 `subprocess-local/src/terminal.ts`。公开面仅中文名；无英文别名。
本文件不规范路径、不调用 realpath：对照 TS terminal.ts，无 realpathSync.native；cwd/路径拼写由启动方规格原样持有，禁止在此加 TS 没有的路径回落。
"""
import signal,threading,time#信号名反查、拆除线程与宽限短睡
from concurrent.futures import Future as _原生Future#单次操作结果

__all__=('贯通流','本地终端句柄')#仅中文公开名

class 操作任务:#单次异步结果
    def __init__(自身):#构造未决任务
        自身._future=_原生Future()#底层 Future
    def 兑现(自身,值=None):#成功结算
        if not 自身._future.done():#尚未结算
            自身._future.set_result(值)#写入结果
        return 值#返回兑现值
    def 拒绝(自身,错误):#失败结算
        if not 自身._future.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._future.set_exception(错误)#原样拒绝
            else:#非异常
                自身._future.set_exception(Exception(错误))#包装拒绝
    def wait(自身,超时=None):#阻塞等待
        return 自身._future.result(timeout=超时)#取结果或抛错
    def 等待(自身,超时=None):#兼容外来调用
        return 自身.wait(超时)#转发

def 延迟(毫秒):#宽限内轮询用的短睡
    """阻塞睡指定毫秒。"""
    time.sleep(max(毫秒,0)/1000.0)#一次短睡

def 信号名(编号):#退出回调里的信号编号 → 名
    """把退出回调里的信号编号收成信号名；未死于信号则 None。"""
    if 编号 is None or 编号==0:#未死于信号
        return None#无信号
    for 名 in dir(signal):#扫 signal 模块公开名
        if not 名.startswith('SIG') or 名.startswith('SIG_'):#只要信号常量
            continue#跳过
        if getattr(signal,名)==编号:#对上编号
            return 名#信号名
    return None#未知编号

class 贯通流:#对齐 node:stream PassThrough 的用户可见输出面
    """用户可见输出流；本文件只用 写入/结束，与 TS PassThrough 用法对齐。"""
    def __init__(自身):#空流
        """构造尚未结束的贯通流。"""
        自身._块们=[]#已写入块
        自身._已结束=False#是否已 end

    def 写入(自身,数据):#写入一块
        """写入用户可见字节；已结束后为空操作。"""
        if 自身._已结束:#已关
            return False#不再写
        if isinstance(数据,str):#文本按 utf-8
            数据=数据.encode('utf-8')#转字节
        elif not isinstance(数据,bytes):#其它缓冲
            数据=bytes(数据)#收成 bytes
        自身._块们.append(数据)#收下
        return True#写出

    def 结束(自身):#关掉流
        """关掉用户可见流。"""
        自身._已结束=True#记下结束

class 本地终端句柄:#本地 PTY 会话
    """进程会话所有权留在 PTY 后端之下的本地终端。seam 的 终止() 承诺——结算后没有进行中的写入、检查或信号——在这里不需要操作跟踪就能站住，只因为每条句柄调用在底层都同步完成（PTY 写入、基于 ps 的检查）。任何句柄调用里出现第一个真正异步的步骤时，必须补上远端提供方所需的跟踪。

    公开方法仅中文：写入、检查前台、发信号前台、终止、为宿主退出终止。
    """
    def __init__(自身,终端,检查器,宽限毫秒):#钉 pid、身份、输出与退出
        """用已分配的 PTY、平台检查器与宽限构造句柄。"""
        自身.终端=终端#PTY 后端
        自身.检查器=检查器#进程表
        自身.宽限毫秒=宽限毫秒#宽限毫秒
        自身.pid=终端.pid#顶层 shell pid
        自身.输出=贯通流()#用户可见输出
        自身.结局=操作任务()#内部结局通知
        自身.done=自身.结局#对外暴露承诺
        自身.清理=None#进行中的 terminate；失败则清空以允许重试
        自身.已退出=False#exit 回调是否已到
        自身.已跟踪子孙=[]#已收养的子孙身份
        自身.根身份=None#启动时钉死的根身份
        for 成员 in 检查器.进程树(自身.pid):#扫启动树
            if 成员.pid==自身.pid:#钉启动身份
                自身.根身份=成员#记下
                break#已找到
        def 在数据时(数据):#PTY 文本 → 字节
            """把 PTY 回调文本写入用户可见流。"""
            if isinstance(数据,bytes):#已是字节
                自身.输出.写入(数据)#原样写
            else:#文本
                自身.输出.写入(数据.encode('utf-8'))#utf-8 字节
        def 在退出时(事件):#进程退出
            """只收一次退出；关流并兑现结局。"""
            if 自身.已退出:#只收一次
                return#忽略
            自身.已退出=True#记下
            自身.输出.结束()#关掉用户可见流
            if isinstance(事件,dict):#映射事件
                退出码=事件.get('exitCode')#退出码
                退出信号=事件.get('signal')#信号编号
            else:#对象事件
                退出码=getattr(事件,'exitCode',None)#退出码
                退出信号=getattr(事件,'signal',None)#信号编号
            自身.结局.兑现({#交出结局
                'exitCode':退出码 if 退出信号 is None or 退出信号==0 else None,#死于信号则退出码为 null
                'signal':信号名(退出信号),#信号名或 null
            })#结束兑现
        自身.数据拆除=终端.onData(在数据时)#onData 监听
        自身.退出拆除=终端.onExit(在退出时)#onExit 监听

    def 写入(自身,数据):#往 PTY 写用户输入
        """往 PTY 写用户输入；已退出则拒绝。本地同步写出；seam 返回承诺是为了远端传输。"""
        if 自身.已退出:#已退出则拒绝
            raise Exception('terminal process has exited')#已退出
        自身.终端.write(数据)#同步写出
        return None#对齐 void

    def 检查前台(自身):#读前台进程组
        """读前台进程组快照；无法解析则 None。本地检查是同步的。"""
        自身.子孙们()#顺带刷新已收养子孙
        进程组号=自身.检查器.前台进程组(自身.pid)#前台 pgid
        if 进程组号 is None:#无法解析
            return None#无前台
        return {#前台快照
            'processGroupId':进程组号,#进程组 id
            'inputWaiting':自身.检查器.是否在等标准输入(进程组号),#是否在等 stdin
        }#结束返回

    def 发信号前台(自身,信号):#向前台组投递信号
        """向前台组投递信号；返回打到的 pgid。"""
        前台=自身.检查前台()#先解析前台
        if 前台 is None:#没有前台组
            raise Exception('cannot resolve foreground process group for terminal '+str(自身.pid))#诊断带 pid
        if 信号=='SIGKILL' and 前台['processGroupId']==自身.pid:#KILL 打到 shell 本身
            raise Exception('refusing to SIGKILL the terminal shell; terminate the terminal session instead')#必须走 terminate
        自身.检查器.信号组(前台['processGroupId'],信号)#向组投递
        return 前台['processGroupId']#返回打到的 pgid

    def 终止(自身):#TERM→KILL 整棵会话；幂等
        """启动一次拆除并返回清理承诺；失败则允许重试。"""
        if 自身.清理 is not None:#已有进行中的清理
            return 自身.清理#复用
        清理=操作任务()#本次清理
        自身.清理=清理#记下
        def 跑一次():#后台跑 closeOnce
            """一次完整拆除；失败清空 cleanup 以允许重试。"""
            try:#拆除可能失败
                自身._关闭一次()#完整拆除
                清理.兑现(None)#静止
            except Exception as 错误:#拆除失败
                自身.清理=None#允许重试
                清理.拒绝(错误)#拒绝清理
        工作=threading.Thread(target=跑一次)#拆除线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        return 清理#调用方等静止或失败

    def 为宿主退出终止(自身):#宿主退出路径：立刻 KILL
        """在宿主 exit 期间同步强制终止可观察会话。不声称静止，也不替代 终止()。"""
        自身._强制停子孙()#先杀已跟踪子孙
        自身._强制停壳()#再杀 shell
        自身._强制停子孙()#shell 死后可能新冒出的子孙

    def _强制停壳(自身):#同步 KILL 顶层 shell
        """同步 KILL 顶层 shell。"""
        if 自身.已退出:#已经退了
            return#空操作
        if 自身.根身份 is not None:#有启动身份则按身份打
            try:#身份信号可能碰上退出竞态
                自身.检查器.信号进程(自身.根身份,'SIGKILL')#精确身份 KILL
            except Exception:#退出竞态与 PID 复用都由精确身份收住
                pass#精确身份发信号同时收住退出竞态与 PID 复用
            return#不再走 PTY
        try:#没有钉住的身份，只能靠 PTY
            自身.终端.kill('SIGKILL')#后端杀根
        except Exception:#没有捕获身份时，PTY 是唯一的根杀原语
            pass#没有捕获身份时，PTY 是唯一的根杀原语

    def _仍活(自身,成员们):#仍非静止的成员
        """按精确身份探活。"""
        return [成员 for 成员 in 成员们 if 自身.检查器.是否存活(成员)]#仍活

    def 子孙们(自身):#刷新已收养子孙
        """仅当数字根 pid 仍可证明携带已 spawn shell 的启动身份时，才收养新扫到的成员：shell 死后，回收 pid 的树和会话不得把无关进程的孩子捐给本会话的发信号。已经收养的成员保留各自的启动身份，每次发信号都会再核对。"""
        树=自身.检查器.进程树(自身.pid)#当前树
        根=None#根条目
        for 成员 in 树:#找根
            if 成员.pid==自身.pid:#命中根 pid
                根=成员#记下
                break#已找到
        根已核=自身.根身份 is not None and 根 is not None and 根.started==自身.根身份.started#根仍是原 shell
        组们=[自身.已跟踪子孙]#已收养
        if 根已核:#根仍是原 shell 才并入树与会话
            组们.append(树)#当前树
            组们.append(自身.检查器.进程会话(自身.pid))#会话成员
        并集=自身._并集成员(*组们)#去重并集
        自身.已跟踪子孙=自身._仍活([成员 for 成员 in 并集 if 成员.pid!=自身.pid])#并集后只留活着的非根
        return 自身.已跟踪子孙#当前跟踪集

    def _等成员(自身,成员们):#宽限内等这批退出
        """宽限内轮询探活；返回到期后仍活的。"""
        截止=time.time()+自身.宽限毫秒/1000.0#截止时刻
        存活=自身._仍活(成员们)#当前仍活
        while len(存活)>0 and time.time()<截止:#还有活的且未到期
            剩余=截止-time.time()#剩余秒
            延迟(min(25,max(1,剩余*1000.0)))#最多睡 25ms，至少 1ms
            存活=自身._仍活(成员们)#再探
        return 存活#到期后仍活的

    def _信号成员(自身,成员们,信号):#按精确身份逐个发信号
        """按精确身份逐个发信号；同刻退出算成功。"""
        for 成员 in 成员们:#每个身份
            try:#同刻退出算成功
                自身.检查器.信号进程(成员,信号)#活着才 kill
            except Exception:#精确进程身份会再核对；同刻退出即成功
                pass#精确进程身份会再核对；同刻退出即成功

    def _强制停子孙(自身):#宿主退出：KILL 已跟踪子孙
        """宿主退出：KILL 已跟踪子孙。"""
        成员们=自身.已跟踪子孙#先用已捕获身份
        try:#最后一次扫进程表可能失败
            成员们=自身.子孙们()#尽量刷新
        except Exception:#最终进程表扫描失败时保住已捕获身份
            pass#最终进程表扫描失败时保住已捕获身份
        自身._信号成员(成员们,'SIGKILL')#一律 KILL

    def _并集成员(自身,*组们):#按 pid+started 去重并集
        """按 pid+started 去重并集。"""
        成员们=[]#结果
        已见=set()#已见键
        for 组 in 组们:#每组
            for 成员 in 组:#每个身份
                键=str(成员.pid)+':'+str(成员.started)#启动身份键
                if 键 in 已见:#已收过
                    continue#跳过
                已见.add(键)#记下
                成员们.append(成员)#收下
        return 成员们#去重后的并集

    def _停子孙(自身):#TERM 再 KILL 子孙
        """TERM 再 KILL 子孙；返回最终仍活的（含新扫到的）。"""
        已捕获=自身.子孙们()#先快照
        自身._信号成员(已捕获,'SIGTERM')#先 TERM
        捕获存活=自身._等成员(已捕获)#等宽限
        成员们=自身._并集成员(捕获存活,自身.子孙们())#并入宽限内新出现的
        自身._信号成员(成员们,'SIGKILL')#再 KILL
        存活=自身._等成员(成员们)#再等
        return 自身._仍活(自身._并集成员(存活,自身.子孙们()))#最终仍活的（含新扫到的）

    def _等退出或宽限(自身):#等退出回调或宽限到期
        """等退出回调或宽限到期。"""
        截止=time.time()+自身.宽限毫秒/1000.0#截止时刻
        存活=not 自身.已退出#当前是否未退
        while 存活 and time.time()<截止:#未退且未到期
            剩余=截止-time.time()#剩余秒
            延迟(min(25,max(1,剩余*1000.0)))#短睡
            存活=not 自身.已退出#再看

    def _停壳(自身):#TERM 再 KILL 顶层 PTY
        """TERM 再 KILL 顶层 PTY；仍活则抛错。"""
        if not 自身.已退出:#还没退
            try:#TERM 可能碰上已退出
                自身.终端.kill('SIGTERM')#先 TERM
            except Exception:#退出回调才是权威
                pass#退出回调才是权威
            自身._等退出或宽限()#等退出或宽限
        if not 自身.已退出:#宽限后仍活
            try:#KILL 同样可能碰上已退出
                自身.终端.kill('SIGKILL')#强制
            except Exception:#退出回调才是权威
                pass#退出回调才是权威
            自身._等退出或宽限()#再等
        if not 自身.已退出:#shell 仍活
            raise Exception('terminal cleanup failed; surviving pid: '+str(自身.pid))#shell 仍活

    def _关闭一次(自身):#一次完整拆除
        """一次完整拆除：先清子孙，再清 shell，再清二次子孙，最后卸监听。"""
        存活=自身._停子孙()#先清子孙
        if len(存活)>0:#还有活的
            raise Exception('terminal cleanup failed; surviving pids: '+', '.join(str(成员.pid) for 成员 in 存活))#带仍活 pid
        自身._停壳()#再清 shell
        存活=自身._停子孙()#shell 死后可能新冒出的
        if len(存活)>0:#仍有活的
            raise Exception('terminal cleanup failed; surviving pids: '+', '.join(str(成员.pid) for 成员 in 存活))#带仍活 pid
        自身.数据拆除.dispose()#卸 onData
        自身.退出拆除.dispose()#卸 onExit
