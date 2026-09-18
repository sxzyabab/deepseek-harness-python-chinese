import signal,time#信号名反查与宽限短睡
from threading import Event as 同步事件,Lock as 互斥锁,Thread as 线程#退出广播、拆除互斥与后台观察

__all__=('贯通流','本地终端句柄','本地子进程错误')#仅中文公开名

class 本地子进程错误(Exception):#本包终端与子进程失败
    """本地子进程或终端句柄失败。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

def 延迟(毫秒):#宽限内轮询用的短睡
    """阻塞睡指定毫秒。"""
    time.sleep(max(毫秒,0)/1000.0)#一次短睡

def 与延迟赛跑(操作等待,毫秒,超时值):#对齐 raceWithDelay
    """等操作等待兑现，或宽限到期返回超时值。操作等待是有等待() 的任务。"""
    截止=time.time()+毫秒/1000.0#截止
    while time.time()<截止:#未到期
        if 操作等待.已完成():#已兑现或拒绝
            return 操作等待.取值()#结果或抛错
        延迟(min(25,max(1,(截止-time.time())*1000.0)))#短睡
    return 超时值#超时

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
    """用户可见输出流：写入、结束，以及 data/end/error/drain 监听。"""
    def __init__(自身):#空流
        """构造尚未结束的贯通流。"""
        自身.块列表=[]#已写入块
        自身.已结束=False#是否已 end
        自身.监听表={}#事件名到回调列表
        自身.高水位=65536#背压阈值
        自身.缓冲字节=0#未排空字节

    def 监听(自身,事件,回调):#登记持续监听
        """登记持续监听。事件名是 data/end/error/drain。"""
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
        """写入用户可见字节；已结束后为空操作；超高水位返回 False。"""
        if 自身.已结束:#已关
            return False#不再写
        if isinstance(数据,str):#文本按 utf-8
            数据=数据.encode('utf-8')#转字节
        elif not isinstance(数据,bytes):#其它缓冲
            数据=bytes(数据)#收成 bytes
        自身.块列表.append(数据)#收下
        自身.缓冲字节+=len(数据)#累加
        自身.派发('data',数据)#通知监听者
        return True#同步消费面不模拟背压

    def 排空(自身):#消费方读走后降水位
        """清空已缓冲字节并派发 drain。"""
        自身.缓冲字节=0#清零
        自身.派发('drain')#可再写

    def 结束(自身):#关掉流
        """关掉用户可见流并派发 end。"""
        if 自身.已结束:#已关
            return#幂等
        自身.已结束=True#记下结束
        自身.派发('end')#通知结束
        自身.派发('close')#对齐 close

class 结局任务:#对齐 Promise.withResolvers
    """可兑现/拒绝的结局等待。"""
    def __init__(自身):#未结算
        """构造未结算任务。"""
        自身._事件=同步事件()#广播
        自身._值=None#兑现值
        自身._错=None#拒绝

    def 兑现(自身,值):#成功结算
        """兑现一次。"""
        if 自身._事件.is_set():#已结算
            return#幂等
        自身._值=值#记下
        自身._事件.set()#广播

    def 拒绝(自身,错误):#失败结算
        """拒绝一次。"""
        if 自身._事件.is_set():#已结算
            return#幂等
        自身._错=错误#记下
        自身._事件.set()#广播

    def 已完成(自身):#是否结算
        """是否已兑现或拒绝。"""
        return 自身._事件.is_set()#已结算

    def 取值(自身):#取结果或抛错
        """阻塞到结算后返回值；拒绝则抛。"""
        自身._事件.wait()#等
        if 自身._错 is not None:#拒绝
            raise 自身._错#抛
        return 自身._值#兑现值

    def 等待(自身,超时秒=None):#可选超时等待
        """等结算；超时返回 False。"""
        return 自身._事件.wait(超时秒)#广播

class 拆除任务:#对齐 terminate() 返回的 Promise
    """拆除完成等待；失败可重试。"""
    def __init__(自身):#未完成
        """构造未完成拆除。"""
        自身._事件=同步事件()#广播
        自身._错=None#失败

    def 完成(自身):#成功
        """标记拆除完成。"""
        自身._错=None#清错
        自身._事件.set()#广播

    def 失败(自身,错误):#失败
        """记下失败并广播。"""
        自身._错=错误#记下
        自身._事件.set()#广播

    def 等待(自身):#阻塞到完成或失败
        """等到拆除结束；失败则抛。"""
        自身._事件.wait()#等
        if 自身._错 is not None:#失败
            raise 自身._错#抛

class 本地终端句柄:#本地 PTY 会话
    """进程会话所有权留在 PTY 后端之下的本地终端。终止() 返回时没有进行中的写入、检查或信号：每条句柄调用在底层都同步做完（PTY 写入、基于 ps 的检查），拆除自己也在调用线程里跑完。

    公开方法仅中文：写入、调整尺寸、等待结局、检查前台、检查活动、发信号前台、终止、为宿主退出终止。
    """
    def __init__(自身,终端,检查器,宽限毫秒,平台=None,托管所有者=None,结算托管结局=None,命令活动=None,静止回调=None,观察壳退出=False):#钉 pid、身份、输出与退出
        """用已分配的 PTY、平台检查器与宽限构造句柄。"""
        import sys as 系统#平台缺省
        自身.终端=终端#PTY 后端
        自身.检查器=检查器#进程表
        自身.宽限毫秒=宽限毫秒#宽限毫秒
        自身.平台=平台 if 平台 is not None else ('win32' if 系统.platform=='win32' else 系统.platform)#平台
        自身.托管所有者=托管所有者#可选受管范围所有者
        自身.结算托管结局=结算托管结局#可选结局改写
        自身.命令活动=命令活动#可选 shell 活动
        自身.静止回调=静止回调#静止后回调
        自身.观察壳退出=观察壳退出#是否观察托管范围空
        自身.pid=终端.pid#顶层 shell pid
        自身.输出=贯通流()#用户可见输出
        自身.结局任务=结局任务()#顶层退出任务
        自身.已退出=同步事件()#exit 回调是否已到
        自身.已静止=False#拆除是否已完整跑完一次
        自身.托管范围已空=False#托管范围是否已空
        自身.托管所有者已清理=False#cleanup 是否已跑
        自身.输出已暂停=False#背压 pause
        自身.活动键=''#活动观测键
        自身.活动修订=0#活动修订
        自身.拆除锁=互斥锁()#串行化并发拆除
        自身.拆除中=None#进行中的拆除任务
        自身.已跟踪子孙=[]#已收养的子孙身份
        自身.根身份=None#启动时钉死的根身份
        try:#钉根身份
            for 成员 in 检查器.快照().树(自身.pid):#扫启动树
                if 成员.pid==自身.pid:#钉启动身份
                    自身.根身份=成员#记下
                    break#已找到
        except Exception:#不可观察
            自身.根身份=None#无
        def 恢复写出():#drain 后 resume
            """背压解除后恢复 PTY。"""
            if not 自身.输出已暂停:#未暂停
                return#空操作
            自身.输出已暂停=False#清
            if not 自身.已退出.is_set():#仍活
                恢复=getattr(终端,'resume',None)#可选 resume
                if 恢复 is not None:#有
                    恢复()#恢复
        自身.输出.监听('drain',恢复写出)#背压解除
        自身.输出.一次('close',lambda:自身.输出.取消监听('drain',恢复写出))#卸
        def 在数据时(数据):#PTY 文本 → 字节
            """把 PTY 回调文本写入用户可见流；背压则 pause。"""
            if isinstance(数据,bytes):#已是字节
                写出=自身.输出.写入(数据)#原样写
            else:#文本
                写出=自身.输出.写入(数据.encode('utf-8'))#utf-8 字节
            if (not 写出) and 自身.拆除中 is None and (not 自身.输出已暂停):#背压
                自身.输出已暂停=True#记下
                暂停=getattr(终端,'pause',None)#可选 pause
                if 暂停 is not None:#有
                    暂停()#暂停
        def 在退出时(退出事实):#进程退出
            """只收一次退出；关流、记下结局再广播。"""
            if 自身.已退出.is_set():#只收一次
                return#忽略
            自身.已退出.set()#先记退出
            if 自身.托管所有者 is not None and 自身.观察壳退出:#观察范围空
                def 观察范围():#后台等范围空
                    """等托管范围退出后授权空闲。"""
                    try:#观察
                        自身.托管所有者.等待退出()#等空
                        自身.托管范围已空=True#授权
                    except Exception:#失败不得授权空闲回收
                        pass#吞掉
                线程(target=观察范围,daemon=True).start()#后台
            自身.输出.结束()#关掉用户可见流
            退出码=退出事实['exitCode'] if 'exitCode' in 退出事实 else None#退出码
            退出信号=退出事实['signal'] if 'signal' in 退出事实 else None#信号编号
            结局={'exitCode':退出码 if 退出信号 is None or 退出信号==0 else None,#死于信号则退出码为 null
                'signal':信号名(退出信号),}#信号名或 null
            try:#可改写结局
                if 自身.结算托管结局 is not None:#有改写
                    结局=自身.结算托管结局(结局)#改写
                自身.结局任务.兑现(结局)#兑现
            except Exception as 错误:#改写失败
                自身.结局任务.拒绝(错误)#拒绝
        自身.数据拆除=终端.onData(在数据时)#onData 监听
        自身.退出拆除=终端.onExit(在退出时)#onExit 监听

    @property
    def 运行中(自身):#node-pty 尚未发布顶层退出
        """顶层退出事件是否尚未到达。"""
        return not 自身.已退出.is_set()#仍运行

    def 写入(自身,数据):#往 PTY 写用户输入
        """往 PTY 写用户输入；已退出则拒绝。本地 PTY 写出是同步的。"""
        if 自身.已退出.is_set():#已退出则拒绝
            raise 本地子进程错误('terminal process has exited')#已退出
        if 自身.命令活动 is not None:#有活动
            自身.命令活动.失效()#失效
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
        return 自身.结局任务.取值()#退出事实

    def 检查前台(自身):#读前台进程组
        """读前台进程组快照；无法解析则 None。本地检查是同步的。"""
        自身.子孙列表(自身.检查器.快照())#顺带刷新已收养子孙
        进程组号=自身.检查器.前台进程组(自身.pid)#前台 pgid
        if 进程组号 is None:#无法解析
            return None#无前台
        return {#前台快照
            'processGroupId':进程组号,#进程组 id
            'inputWaiting':自身.检查器.是否在等标准输入(进程组号,自身.pid),#是否在等 stdin
        }#结束返回

    def 检查活动(自身):#观测命令活动
        """观测命令活动，不解释输出；返回 state 与 revision。"""
        状态='idle' if 自身.已静止 else 'unknown'#初态
        修订=0#修订
        if not 自身.已静止:#未静止
            try:#观测
                if 自身.命令活动 is not None:#有 shell
                    shell观测=自身.命令活动.检查(自身.pid)#观测
                else:#无
                    shell观测={'state':'unknown','revision':0}#未知
                修订=shell观测['revision']#修订
                观察=自身.检查器.快照()#一次表
                子孙=自身.子孙列表(观察)#后代
                根=None#根条目
                for 成员 in 观察.树(自身.pid):#找根
                    if 成员.pid==自身.pid:#命中
                        根=成员#记下
                        break#已找到
                if 自身.已退出.is_set() and 自身.托管范围已空:#范围空
                    状态='idle'#空闲
                elif len(子孙)>0:#有后代
                    状态='busy'#忙
                elif 自身.已退出.is_set() and 自身.托管所有者 is None and 自身.平台=='linux' and 观察.complete is True and 根 is None:#Linux 回落会话
                    状态='busy' if any(观察.存活(成员) for 成员 in 观察.会话(自身.pid)) else 'idle'#会话活则忙
                elif 观察.complete is True and 根 is not None and 自身.根身份 is not None and 根.started==自身.根身份.started:#根仍是原 shell
                    前台=自身.检查器.前台进程组(自身.pid)#前台
                    if 前台 is None:#无法解析
                        状态='unknown'#未知
                    elif 前台==自身.pid:#前台即 shell
                        状态=shell观测['state']#壳态
                    else:#前台是别人
                        状态='busy'#忙
                    if 状态=='idle' and 自身.托管所有者 is not None:#托管再核任务数
                        查任务=getattr(自身.托管所有者,'检查任务数',None)#可选
                        任务=查任务() if 查任务 is not None else None#任务数
                        if 任务 is None or 任务<1:#不可观察或空
                            状态='unknown'#未知
                        elif 任务==1:#仅壳
                            状态='idle'#空闲
                        else:#有额外任务
                            状态='busy'#忙
            except Exception:#不完整
                状态='unknown'#未知
        键=str(修订)+':'+状态#键
        if 键!=自身.活动键:#变化
            自身.活动键=键#记下
            自身.活动修订+=1#推进
        return {'state':状态,'revision':自身.活动修订}#观测

    def 发信号前台(自身,信号):#向前台组投递信号
        """向前台组投递信号；返回打到的 pgid。"""
        if 自身.命令活动 is not None:#有活动
            自身.命令活动.失效()#失效
        前台=自身.检查前台()#先解析前台
        if 前台 is None:#没有前台组
            raise 本地子进程错误('cannot resolve foreground process group for terminal '+str(自身.pid))#诊断带 pid
        if 信号=='SIGKILL' and 前台['processGroupId']==自身.pid:#KILL 打到 shell 本身
            raise 本地子进程错误('refusing to SIGKILL the terminal shell; terminate the terminal session instead')#必须走 terminate
        if 自身.平台=='win32':#Windows 无组信号
            if 信号=='SIGINT':#Ctrl-C
                自身.终端.write('\x03')#写入 ETX
                return 前台['processGroupId']#返回 pgid
            if 信号=='SIGTSTP' or 信号=='SIGHUP':#不支持
                raise 本地子进程错误('signal '+信号+' is unsupported on Windows; only SIGINT, SIGTERM, and SIGKILL are available')#拒
        自身.检查器.信号组(前台['processGroupId'],信号)#向组投递
        return 前台['processGroupId']#返回打到的 pgid

    def 终止(自身):#TERM→KILL 整棵会话；幂等
        """同步做完一次完整拆除；已静止或进行中则复用；失败原样抛出且允许重试。"""
        with 自身.拆除锁:#并发调用排队
            if 自身.拆除中 is not None:#已有拆除
                任务=自身.拆除中#复用
            else:#首次
                if 自身.输出已暂停:#解除背压
                    自身.输出已暂停=False#清
                    恢复=getattr(自身.终端,'resume',None)#可选
                    if 恢复 is not None:#有
                        恢复()#恢复
                任务=拆除任务()#新建
                自身.拆除中=任务#记下
                try:#完整拆除
                    自身.关闭一次()#拆除
                    自身.已静止=True#记下静止
                    if 自身.命令活动 is not None:#有活动
                        自身.命令活动.拆除()#拆
                    if 自身.静止回调 is not None:#有回调
                        自身.静止回调()#回调
                    任务.完成()#成功
                except Exception as 错误:#失败可重试
                    自身.拆除中=None#允许重试
                    任务.失败(错误)#广播失败
                    raise#原样
            #锁外等待同一任务
        任务.等待()#等到完成或失败
        return 任务#可再等

    def 为宿主退出终止(自身):#宿主退出路径：立刻 KILL
        """在宿主 exit 期间同步强制终止可观察会话。不声称静止，也不替代 终止()。"""
        自身.强制停子孙()#先杀已跟踪子孙
        自身.强制停壳()#再杀 shell
        自身.强制停子孙()#shell 死后可能新冒出的子孙
        if 自身.托管所有者 is not None:#有托管
            自身.托管所有者.为宿主退出终止()#强制停范围

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

    def 仍活(自身,成员列表,观察=None):#仍非静止的成员
        """按精确身份探活。"""
        if 观察 is None:#现取
            观察=自身.检查器.快照()#快照
        return [成员 for 成员 in 成员列表 if 观察.存活(成员)]#仍活

    def 子孙列表(自身,观察=None):#刷新已收养子孙
        """仅当数字根 pid 仍可证明携带已 spawn shell 的启动身份时，才收养新扫到的成员。"""
        if 观察 is None:#现取
            观察=自身.检查器.快照()#快照
        树=观察.树(自身.pid)#当前树
        根=None#根条目
        for 成员 in 树:#找根
            if 成员.pid==自身.pid:#命中根 pid
                根=成员#记下
                break#已找到
        根已核=自身.根身份 is not None and 根 is not None and 根.started==自身.根身份.started#根仍是原 shell
        组列表=[自身.已跟踪子孙]#已收养
        if 根已核:#根仍是原 shell 才并入树与会话
            组列表.append(树)#当前树
            组列表.append(观察.会话(自身.pid))#会话成员
        并集=自身.并集成员(*组列表)#去重并集
        自身.已跟踪子孙=自身.仍活([成员 for 成员 in 并集 if 成员.pid!=自身.pid],观察)#并集后只留活着的非根
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
        观察=自身.检查器.快照()#最终观察
        return 自身.仍活(自身.并集成员(存活,自身.子孙列表(观察)),观察)#最终仍活的

    def 停壳(自身):#TERM 再 KILL 顶层 PTY
        """TERM 再 KILL 顶层 PTY；仍活则抛错。"""
        if 自身.平台=='win32':#Windows 专用路径
            自身.停壳Windows()#走 taskkill/身份
            return#结束
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

    def 停壳Windows(自身):#Windows 拆除
        """身份 fenced 的 TERM/KILL；无身份则裸 kill。"""
        def 壳已走():#壳是否已不在
            """退出回调或身份探死。"""
            if 自身.已退出.is_set():#已退
                return True#走了
            if 自身.根身份 is not None and (not 自身.检查器.是否存活(自身.根身份)):#身份死
                return True#走了
            return False#仍在
        if (not 壳已走()) and 自身.根身份 is not None:#有身份则 TERM
            自身.检查器.信号进程(自身.根身份,'SIGTERM')#TERM
            自身.等Windows壳退出()#等
        if (not 壳已走()) and 自身.根身份 is None:#无身份则裸 kill
            try:#裸 kill
                自身.终端.kill()#无信号
            except OSError:#退出回调才是权威
                pass#退出回调才是权威
            自身.已退出.wait(自身.宽限毫秒/1000.0)#等
        if (not 壳已走()) and 自身.根身份 is not None:#再 KILL
            自身.检查器.信号进程(自身.根身份,'SIGKILL')#KILL
            自身.等Windows壳退出()#等
        if not 壳已走():#仍活
            raise 本地子进程错误('terminal cleanup failed; surviving pid: '+str(自身.pid))#失败

    def 等Windows壳退出(自身):#宽限内等壳死
        """宽限内轮询身份或退出回调。"""
        截止=time.time()+自身.宽限毫秒/1000.0#截止
        while (not 自身.已退出.is_set()) and time.time()<截止:#未退且未到期
            if 自身.根身份 is not None and (not 自身.检查器.是否存活(自身.根身份)):#身份死
                return#结束
            延迟(min(25,max(1,(截止-time.time())*1000.0)))#短睡

    def 关闭一次(自身):#一次完整拆除
        """一次完整拆除：托管范围或子孙→壳→二次子孙，最后卸监听。"""
        if 自身.托管所有者 is not None:#走托管路径
            try:#关范围
                自身.关闭托管范围(自身.托管所有者)#TERM→KILL 范围
                自身.数据拆除.dispose()#卸 onData
                自身.退出拆除.dispose()#卸 onExit
            finally:#结局后再 cleanup
                def 清所有者():#等结局后清
                    """结算后再释放所有者私有物。"""
                    try:#等结局
                        自身.结局任务.取值()#等
                    except Exception:#结局拒绝仍清
                        pass#仍清
                    自身.清理托管所有者(自身.托管所有者)#cleanup
                线程(target=清所有者,daemon=True).start()#后台
            return#托管路径结束
        存活=自身.停子孙()#先清子孙
        if len(存活)>0:#还有活的
            raise 本地子进程错误('terminal cleanup failed; surviving pids: '+', '.join(str(成员.pid) for 成员 in 存活))#带仍活 pid
        自身.停壳()#再清 shell
        存活=自身.停子孙()#shell 死后可能新冒出的
        if len(存活)>0:#仍有活的
            raise 本地子进程错误('terminal cleanup failed; surviving pids: '+', '.join(str(成员.pid) for 成员 in 存活))#带仍活 pid
        自身.若已走则结算退出()#Windows 可能缺 exit 事件
        自身.数据拆除.dispose()#卸 onData
        自身.退出拆除.dispose()#卸 onExit

    def 清理托管所有者(自身,所有者):#释放私有物
        """只清一次。"""
        if 自身.托管所有者已清理:#已清
            return#空操作
        自身.托管所有者已清理=True#记下
        清理=getattr(所有者,'清理',None)#可选
        if 清理 is not None:#有
            清理()#清

    def 关闭托管范围(自身,所有者):#TERM→KILL 托管范围
        """先 TERM 等宽限，超时再 KILL。"""
        所有者.发信号('SIGTERM')#先 TERM
        观察=结局任务()#包装 waitForExit
        def 跑观察():#后台观察
            """把等待退出收成任务。"""
            try:#等
                所有者.等待退出()#等空
                观察.兑现({'kind':'stopped'})#停了
            except Exception as 错误:#失败
                观察.兑现({'kind':'failed','error':错误})#失败
        线程(target=跑观察,daemon=True).start()#启动
        首轮=与延迟赛跑(观察,自身.宽限毫秒,{'kind':'timeout'})#赛跑
        if 首轮['kind']!='stopped':#未停
            所有者.发信号('SIGKILL')#KILL
            if 首轮['kind']=='failed':#观察失败仍要最终观察
                try:#再等
                    所有者.等待退出()#最终
                except Exception as 最终错:#再失败
                    raise Exception('terminal managed-range cleanup failed') from 最终错#聚合语义简化
                raise 首轮['error']#抛首次
            观察.取值()#等 timeout 路径上的观察兑现
        if not 自身.已退出.is_set():#壳退出事件可能滞后
            自身.已退出.wait(自身.宽限毫秒/1000.0)#再等宽限
        if not 自身.已退出.is_set():#仍活
            raise 本地子进程错误('terminal cleanup failed; surviving pid: '+str(自身.pid))#失败

    def 若已走则结算退出(自身):#Windows 缺 exit 时补结算
        """外部 taskkill 可能不触发 node-pty 退出通知。"""
        if 自身.平台!='win32':#仅 Windows
            return#结束
        if 自身.已退出.is_set():#已有事件
            return#结束
        if 自身.根身份 is not None and 自身.检查器.是否存活(自身.根身份):#仍活
            return#不结算
        自身.已退出.set()#补记
        自身.输出.结束()#关流
        自身.结局任务.兑现({'exitCode':None,'signal':None})#补结局
