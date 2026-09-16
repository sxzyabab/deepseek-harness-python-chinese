import signal,time#信号名反查与宽限短睡
from threading import Event as 同步事件,Lock as 互斥锁#退出广播与拆除互斥

__all__=('贯通流','本地终端句柄','本地子进程错误')#仅中文公开名

class 本地子进程错误(Exception):#本包终端与子进程失败
    """本地子进程或终端句柄失败。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

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
    """用户可见输出流：写入、结束，以及 data/end/error 监听。"""
    def __init__(自身):#空流
        """构造尚未结束的贯通流。"""
        自身.块列表=[]#已写入块
        自身.已结束=False#是否已 end
        自身.监听表={}#事件名到回调列表

    def 监听(自身,事件,回调):#登记持续监听
        """登记持续监听。事件名是 data/end/error。"""
        if 事件 not in 自身.监听表:#尚无列表
            自身.监听表[事件]=[]#新建
        自身.监听表[事件].append(回调)#追加

    def 一次(自身,事件,回调):#只听一次
        """只听一次，触发后自动摘掉。"""
        def 包装(*位置参数):#触发后自摘
            """触发后自摘再转发。"""
            自身.取消监听(事件,包装)#自摘
            回调(*位置参数)#转发
        自身.监听(事件,包装)#挂上包装

    def 取消监听(自身,事件,回调):#摘掉一次监听
        """摘掉一次监听；未挂过则忽略。"""
        if 事件 not in 自身.监听表:#没有该事件
            return#结束
        try:#去掉这条
            自身.监听表[事件].remove(回调)#去掉
        except ValueError:#已不在列表
            return#结束

    def 派发(自身,事件,*位置参数):#派发给当前监听者
        """派发给当前监听者的副本，避免回调里改表。"""
        列表=自身.监听表[事件] if 事件 in 自身.监听表 else []#当前列表
        for 回调 in list(列表):#副本
            回调(*位置参数)#调用

    def 写入(自身,数据):#写入一块
        """写入用户可见字节；已结束后为空操作。"""
        if 自身.已结束:#已关
            return False#不再写
        if isinstance(数据,str):#文本按 utf-8
            数据=数据.encode('utf-8')#转字节
        elif not isinstance(数据,bytes):#其它缓冲
            数据=bytes(数据)#收成 bytes
        自身.块列表.append(数据)#收下
        自身.派发('data',数据)#通知监听者
        return True#写出

    def 结束(自身):#关掉流
        """关掉用户可见流并派发 end。"""
        if 自身.已结束:#已关
            return#幂等
        自身.已结束=True#记下结束
        自身.派发('end')#通知结束

class 本地终端句柄:#本地 PTY 会话
    """进程会话所有权留在 PTY 后端之下的本地终端。终止() 返回时没有进行中的写入、检查或信号：每条句柄调用在底层都同步做完（PTY 写入、基于 ps 的检查），拆除自己也在调用线程里跑完。

    公开方法仅中文：写入、等待结局、检查前台、发信号前台、终止、为宿主退出终止。
    """
    def __init__(自身,终端,检查器,宽限毫秒):#钉 pid、身份、输出与退出
        """用已分配的 PTY、平台检查器与宽限构造句柄。"""
        自身.终端=终端#PTY 后端
        自身.检查器=检查器#进程表
        自身.宽限毫秒=宽限毫秒#宽限毫秒
        自身.pid=终端.pid#顶层 shell pid
        自身.输出=贯通流()#用户可见输出
        自身.结局=None#顶层进程退出事实；退出回调到达后才有
        自身.已退出=同步事件()#exit 回调是否已到，同时广播给等待者
        自身.已静止=False#拆除是否已完整跑完一次
        自身.拆除锁=互斥锁()#串行化并发拆除
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
        def 在退出时(退出事实):#进程退出
            """只收一次退出；关流、记下结局再广播。"""
            if 自身.已退出.is_set():#只收一次
                return#忽略
            自身.输出.结束()#关掉用户可见流
            退出码=退出事实['exitCode'] if 'exitCode' in 退出事实 else None#退出码
            退出信号=退出事实['signal'] if 'signal' in 退出事实 else None#信号编号
            自身.结局={'exitCode':退出码 if 退出信号 is None or 退出信号==0 else None,#死于信号则退出码为 null
                'signal':信号名(退出信号),}#信号名或 null
            自身.已退出.set()#广播给等待结局的调用方
        自身.数据拆除=终端.onData(在数据时)#onData 监听
        自身.退出拆除=终端.onExit(在退出时)#onExit 监听

    def 写入(自身,数据):#往 PTY 写用户输入
        """往 PTY 写用户输入；已退出则拒绝。本地 PTY 写出是同步的。"""
        if 自身.已退出.is_set():#已退出则拒绝
            raise 本地子进程错误('terminal process has exited')#已退出
        自身.终端.write(数据)#同步写出
        return None#对齐 void

    def 调整尺寸(自身,列,行):#改终端尺寸
        """改终端尺寸并通知前台应用；已退出则拒绝。"""
        if 自身.已退出.is_set():#已退出则拒绝
            raise 本地子进程错误('terminal process has exited')#已退出
        自身.终端.resize(列,行)#同步改尺寸
        return None#对齐 void

    def 等待结局(自身):#阻塞到顶层进程退出
        """阻塞到顶层进程退出，返回其退出事实。"""
        自身.已退出.wait()#等退出回调
        return 自身.结局#退出事实

    def 检查前台(自身):#读前台进程组
        """读前台进程组快照；无法解析则 None。本地检查是同步的。"""
        自身.子孙列表()#顺带刷新已收养子孙
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
            raise 本地子进程错误('cannot resolve foreground process group for terminal '+str(自身.pid))#诊断带 pid
        if 信号=='SIGKILL' and 前台['processGroupId']==自身.pid:#KILL 打到 shell 本身
            raise 本地子进程错误('refusing to SIGKILL the terminal shell; terminate the terminal session instead')#必须走 terminate
        自身.检查器.信号组(前台['processGroupId'],信号)#向组投递
        return 前台['processGroupId']#返回打到的 pgid

    def 终止(自身):#TERM→KILL 整棵会话；幂等
        """同步做完一次完整拆除；已静止则空操作，失败原样抛出且允许重试。"""
        with 自身.拆除锁:#并发调用排队，只有第一个真正拆
            if 自身.已静止:#已经静止
                return#空操作
            自身.关闭一次()#完整拆除；失败原样抛给调用方
            自身.已静止=True#记下静止

    def 为宿主退出终止(自身):#宿主退出路径：立刻 KILL
        """在宿主 exit 期间同步强制终止可观察会话。不声称静止，也不替代 终止()。"""
        自身.强制停子孙()#先杀已跟踪子孙
        自身.强制停壳()#再杀 shell
        自身.强制停子孙()#shell 死后可能新冒出的子孙

    def 强制停壳(自身):#同步 KILL 顶层 shell
        """同步 KILL 顶层 shell。"""
        if 自身.已退出.is_set():#已经退了
            return#空操作
        if 自身.根身份 is not None:#有启动身份则按身份打
            try:#身份信号可能碰上退出竞态
                自身.检查器.信号进程(自身.根身份,'SIGKILL')#精确身份 KILL
            except OSError:#退出竞态与 PID 复用都由精确身份收住
                pass#精确身份发信号同时收住退出竞态与 PID 复用
            return#不再走 PTY
        try:#没有钉住的身份，只能靠 PTY
            自身.终端.kill('SIGKILL')#后端杀根
        except OSError:#没有捕获身份时，PTY 是唯一的根杀原语
            pass#没有捕获身份时，PTY 是唯一的根杀原语

    def 仍活(自身,成员列表):#仍非静止的成员
        """按精确身份探活。"""
        return [成员 for 成员 in 成员列表 if 自身.检查器.是否存活(成员)]#仍活

    def 子孙列表(自身):#刷新已收养子孙
        """仅当数字根 pid 仍可证明携带已 spawn shell 的启动身份时，才收养新扫到的成员：shell 死后，回收 pid 的树和会话不得把无关进程的孩子捐给本会话的发信号。已经收养的成员保留各自的启动身份，每次发信号都会再核对。"""
        树=自身.检查器.进程树(自身.pid)#当前树
        根=None#根条目
        for 成员 in 树:#找根
            if 成员.pid==自身.pid:#命中根 pid
                根=成员#记下
                break#已找到
        根已核=自身.根身份 is not None and 根 is not None and 根.started==自身.根身份.started#根仍是原 shell
        组列表=[自身.已跟踪子孙]#已收养
        if 根已核:#根仍是原 shell 才并入树与会话
            组列表.append(树)#当前树
            组列表.append(自身.检查器.进程会话(自身.pid))#会话成员
        并集=自身.并集成员(*组列表)#去重并集
        自身.已跟踪子孙=自身.仍活([成员 for 成员 in 并集 if 成员.pid!=自身.pid])#并集后只留活着的非根
        return 自身.已跟踪子孙#当前跟踪集

    def 等成员(自身,成员列表):#宽限内等这批退出
        """宽限内轮询探活；返回到期后仍活的。"""
        截止=time.time()+自身.宽限毫秒/1000.0#截止时刻
        存活=自身.仍活(成员列表)#当前仍活
        while len(存活)>0 and time.time()<截止:#还有活的且未到期
            剩余=截止-time.time()#剩余秒
            延迟(min(25,max(1,剩余*1000.0)))#最多睡 25ms，至少 1ms
            存活=自身.仍活(成员列表)#再探
        return 存活#到期后仍活的

    def 信号成员(自身,成员列表,信号):#按精确身份逐个发信号
        """按精确身份逐个发信号；同刻退出算成功。"""
        for 成员 in 成员列表:#每个身份
            try:#同刻退出算成功
                自身.检查器.信号进程(成员,信号)#活着才 kill
            except OSError:#精确进程身份会再核对；同刻退出即成功
                pass#精确进程身份会再核对；同刻退出即成功

    def 强制停子孙(自身):#宿主退出：KILL 已跟踪子孙
        """宿主退出：KILL 已跟踪子孙。"""
        成员列表=自身.已跟踪子孙#先用已捕获身份
        try:#最后一次扫进程表可能失败
            成员列表=自身.子孙列表()#尽量刷新
        except OSError:#最终进程表扫描失败时保住已捕获身份
            pass#最终进程表扫描失败时保住已捕获身份
        自身.信号成员(成员列表,'SIGKILL')#一律 KILL

    def 并集成员(自身,*组列表):#按 pid+started 去重并集
        """按 pid+started 去重并集。"""
        成员列表=[]#结果
        已见=set()#已见键
        for 组 in 组列表:#每组
            for 成员 in 组:#每个身份
                键=str(成员.pid)+':'+str(成员.started)#启动身份键
                if 键 in 已见:#已收过
                    continue#跳过
                已见.add(键)#记下
                成员列表.append(成员)#收下
        return 成员列表#去重后的并集

    def 停子孙(自身):#TERM 再 KILL 子孙
        """TERM 再 KILL 子孙；返回最终仍活的（含新扫到的）。"""
        已捕获=自身.子孙列表()#先快照
        自身.信号成员(已捕获,'SIGTERM')#先 TERM
        捕获存活=自身.等成员(已捕获)#等宽限
        成员列表=自身.并集成员(捕获存活,自身.子孙列表())#并入宽限内新出现的
        自身.信号成员(成员列表,'SIGKILL')#再 KILL
        存活=自身.等成员(成员列表)#再等
        return 自身.仍活(自身.并集成员(存活,自身.子孙列表()))#最终仍活的（含新扫到的）

    def 停壳(自身):#TERM 再 KILL 顶层 PTY
        """TERM 再 KILL 顶层 PTY；仍活则抛错。"""
        if not 自身.已退出.is_set():#还没退
            try:#TERM 可能碰上已退出
                自身.终端.kill('SIGTERM')#先 TERM
            except OSError:#退出回调才是权威
                pass#退出回调才是权威
            自身.已退出.wait(自身.宽限毫秒/1000.0)#等退出回调或宽限到期
        if not 自身.已退出.is_set():#宽限后仍活
            try:#KILL 同样可能碰上已退出
                自身.终端.kill('SIGKILL')#强制
            except OSError:#退出回调才是权威
                pass#退出回调才是权威
            自身.已退出.wait(自身.宽限毫秒/1000.0)#再等一个宽限
        if not 自身.已退出.is_set():#shell 仍活
            raise 本地子进程错误('terminal cleanup failed; surviving pid: '+str(自身.pid))#shell 仍活

    def 关闭一次(自身):#一次完整拆除
        """一次完整拆除：先清子孙，再清 shell，再清二次子孙，最后卸监听。"""
        存活=自身.停子孙()#先清子孙
        if len(存活)>0:#还有活的
            raise 本地子进程错误('terminal cleanup failed; surviving pids: '+', '.join(str(成员.pid) for 成员 in 存活))#带仍活 pid
        自身.停壳()#再清 shell
        存活=自身.停子孙()#shell 死后可能新冒出的
        if len(存活)>0:#仍有活的
            raise 本地子进程错误('terminal cleanup failed; surviving pids: '+', '.join(str(成员.pid) for 成员 in 存活))#带仍活 pid
        自身.数据拆除.dispose()#卸 onData
        自身.退出拆除.dispose()#卸 onExit
