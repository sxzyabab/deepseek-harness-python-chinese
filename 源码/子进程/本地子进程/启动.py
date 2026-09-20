import math,os,signal,socket,sys,time#有限数、路径、信号、双工套接字、平台与轮询
from threading import Event as 同步事件,Lock as 互斥锁,Thread as 线程,Timer as 定时器#结局广播、互斥、后台线程与宽限定时器
from subprocess import Popen,DEVNULL,PIPE,run as 同步跑#子进程与同步taskkill
from ...工具.超时 import 定时器延迟上限毫秒,已中止,若已中止则抛出,等待中止#定时器上限与中止入口
from ..子进程 import 擦洗父环境#清洗后的父环境
from ..子进程.控制 import 子进程控制描述符#控制通道 fd
from .进程检查 import 组内有活成员#Linux组内存活探针
from .终端 import 本地子进程错误#本包错误
from .输出 import 输出收集器,准备受管进程绑定#有界尾与溢出根
from .控制派生 import 控制环境,控制管道#控制管装配

__all__=('子环境','输出收集器','启动子进程','杀组','taskkill进程树','信号树','准备受管进程绑定')#仅中文公开名

def 节点平台():#把 sys.platform 粗映射到 Node 平台名
    """把 sys.platform 粗映射到 Node 平台名。"""
    名=sys.platform#本机
    if 名=='win32':#Windows
        return 'win32'#Node名
    if 名=='darwin':#macOS
        return 'darwin'#Node名
    if 名.startswith('linux'):#Linux
        return 'linux'#Node名
    return 名#原样

def 子环境(额外=None):#构造子环境
    """显式调用方条目按目标平台的环境键语义覆盖清洗后的父基线。字符串有意恢复或覆盖一条；显式 None 墓碑则删掉一条普通环境条目。额外是 dict。"""
    环境=擦洗父环境()#清洗后的父基线
    if 节点平台()!='win32':#POSIX：后写覆盖
        合并=dict(环境)#拷贝基线
        if 额外 is not None:#有显式条目
            for 键,值 in 额外.items():#逐条
                if 值 is None:#墓碑
                    合并.pop(键,None)#删掉
                else:#覆盖
                    合并[键]=值#写入
        return 合并#子环境
    条目=list(环境.items())#Windows：键大小写不敏感
    for 键,值 in ({} if 额外 is None else 额外).items():#每条显式条目
        规范=键.upper()#比较用大写
        条目=[(继承,继承值) for 继承,继承值 in 条目 if 继承.upper()!=规范]#丢掉同名继承
        条目.append((键,值))#按调用方大小写收下（含None墓碑）
    结果={}#重建对象
    for 键,值 in 条目:#逐条
        if 值 is not None:#非墓碑
            结果[键]=值#留下
    return 结果#子环境

def 短睡():#15ms一拍
    """树退出等待的存活轮询节拍。"""
    time.sleep(0.015)#短睡

def 杀组(pid,信号名):#POSIX组信号
    """向分离的 POSIX 进程组发送信号。永不抛出；非正 pid 是空操作。"""
    if pid<=0:#无效pid
        return#空操作
    try:#组可能已不在
        os.kill(-pid,getattr(signal,信号名))#负pid=整组
    except OSError:#投递失败；见上方约定
        pass掉

def taskkill进程树(pid):#Windows树终止
    """用 `taskkill /T /F` 终止一棵 Windows 进程树；失败可容忍。"""
    if pid<=0:#无效pid
        return#空操作
    同步跑(['taskkill','/PID',str(pid),'/T','/F'],stdout=DEVNULL,stderr=DEVNULL,check=False)#/T整树 /F强制

def 信号树(平台,pid,信号名,孩子,taskkill):#平台分发
    """按平台正确语义向分离进程树发信号。"""
    if 平台=='win32':#Windows：taskkill整树
        taskkill(pid)#任何信号都强制
        returnWindows
    if pid<=0:#无效pid
        return#空操作
    try:#先打组
        os.kill(-pid,getattr(signal,信号名))#负pid=整组
    except OSError:#组不在或无权
        try:#组失败则打直接孩子
            if 信号名=='SIGKILL':#强制
                孩子.kill()#立刻杀
            else:#温和
                孩子.terminate()#TERM
        except OSError:#直接孩子已退出；拆除仍幂等
            pass掉

def 是否收集模式(模式):#pipe/inherit以外即收集
    """输出模式是否为有界收集对象。"""
    return 模式!='pipe' and 模式!='inherit'#对象模式带maxBytes

def 启动子进程(规格,内部=None):#本地spawn
    """按规格的每路 stdio 处置 spawn 一棵隔离的分离进程树。规格与内部覆盖都是 dict。"""
    if 内部 is None:#缺省空覆盖
        内部={}#测试覆盖
    宽限=规格['graceMs']#杀进程宽限
    if isinstance(宽限,bool) or not isinstance(宽限,(int,float)) or not math.isfinite(宽限) or 宽限<=0 or 宽限>定时器延迟上限毫秒:#宽限必须可表示
        raise 本地子进程错误('subprocess graceMs must be a positive finite number no greater than '+str(定时器延迟上限毫秒))#与E2B提供方同一句
    溢出目录=准备受管进程绑定(内部)['spillDir']#溢出根
    平台=内部['platform'] if 'platform' in 内部 else None#测试覆盖平台
    if 平台 is None:#缺省本机
        平台=节点平台()#本机平台
    taskkill=内部['taskkill'] if 'taskkill' in 内部 else None#测试覆盖taskkill
    if taskkill is None:#缺省真实taskkill
        taskkill=taskkill进程树#Windows终止
    组探针=内部['linuxProcessGroupHasLiveMembers'] if 'linuxProcessGroupHasLiveMembers' in 内部 else None#测试覆盖组探针
    if 组探针 is None:#缺省/proc检查
        组探针=组内有活成员#组探针
    中止信号=规格['signal'] if 'signal' in 规格 else None#取消信号
    if 已中止(中止信号):#spawn前已取消
        try:#取出原因
            若已中止则抛出(中止信号)#抛原因异常
            原因='aborted'#无抛出则占位
        except BaseException as 错误:#原因异常
            原因=str(错误)#带取消原因
        raise 本地子进程错误('aborted before spawn: '+原因)#带取消原因
    参数表=list(规格['argv']) if 'argv' in 规格 and 规格['argv'] is not None else []#argv
    if len(参数表)==0 or 参数表[0] is None or len(str(参数表[0]))==0:#必须有非空程序名
        raise 本地子进程错误('invalid argv: expected a non-empty program name at argv[0]')#加载/调用失败
    程序=参数表[0]#argv[0]是程序
    参数=参数表[1:]#其余参数
    标准流=规格['stdio']#三路处置
    出模式=标准流['stdout']#stdout处置
    错模式=标准流['stderr']#stderr处置
    入模式=标准流['stdin']#stdin处置
    控制请求=标准流['control'] if 'control' in 标准流 else None#可选控制管
    环境=控制环境(子环境(规格['env'] if 'env' in 规格 else None),控制请求)#合并后的子环境
    入管道=PIPE if 入模式!='ignore' else DEVNULL#ignore或可写管道
    出管道=None if 出模式=='inherit' else PIPE#inherit或可读管道
    错管道=None if 错模式=='inherit' else PIPE#同上
    启动参数={'args':[程序]+参数,'cwd':规格['cwd'] if 'cwd' in 规格 else None,'env':环境,'stdin':入管道,'stdout':出管道,'stderr':错管道}#Popen参数
    控制父=None#父端双工
    控制子=None#子端套接字
    if 控制请求=='pipe':#显式控制通道
        控制父,控制子=socket.socketpair()#一对双工套接字
        if 平台!='win32':#POSIX 才能把套接字放到 fd 7
            def 放到控制描述符():#子进程把套接字放到 fd 7
                """把继承套接字放到保留控制描述符。"""
                os.dup2(控制子.fileno(),子进程控制描述符)#占 fd 7
            启动参数['pass_fds']=(控制子.fileno(),)#继承子端
            启动参数['preexec_fn']=放到控制描述符#放到 7
    if 平台!='win32':#仅POSIX分离
        启动参数['start_new_session']=True#自己的进程组
    孩子=Popen(**启动参数)#启动；spawn级失败原样抛给调用方
    if 控制子 is not None:#父进程关掉子端
        控制子.close()#只留父端
    孩子.控制=控制父#挂到孩子上供控制管道读取
    标准输出收集=None#stdout收集器
    标准误收集=None#stderr收集器
    if 是否收集模式(出模式) and 孩子.stdout is not None:#挂stdout收集
        溢出=出模式['spill'] if 'spill' in 出模式 else None#溢出配置
        标准输出收集=输出收集器(出模式['maxBytes'],溢出['maxBytes'] if 溢出 is not None else None,'stdout',溢出目录)#有界尾
    if 是否收集模式(错模式) and 孩子.stderr is not None:#挂stderr收集
        溢出=错模式['spill'] if 'spill' in 错模式 else None#溢出配置
        标准误收集=输出收集器(错模式['maxBytes'],溢出['maxBytes'] if 溢出 is not None else None,'stderr',溢出目录)#有界尾

    状态={
        'graceTimer':None,#SIGKILL升级定时器
        'observing':False,#整树退出观察线程是否已起
        'settled':False,#直接孩子结局已结算
        'pipeDrainTimer':None,#close等待上限
    }#可变状态
    pid=孩子.pid if 孩子.pid is not None else -1#同步可读pid
    树静止=同步事件()#整树已确认缺席，广播给等待者
    观察锁=互斥锁()#保住观察线程单例
    结局=None#直接孩子退出事实
    已结局=同步事件()#直接孩子结局已写好，广播给等待者

    def 树仍活():#存活探针
        """分离树的根（或 POSIX 组）是否仍活着。"""
        if 树静止.is_set():#已确认缺席
            return False#不活
        if pid<=0:#从未启动
            return False#不活
        if 平台=='win32':#Windows没有组存活探针
            return 孩子.poll() is None#孩子仍在跑
        try:#POSIX：kill(0)探组
            os.kill(-pid,0)#组是否仍在
            if 状态['settled'] and 平台=='linux' and 组探针(pid) is False:#只剩僵尸
                return False#不活
            return True#组仍在
        except OSError as 错误:#kill(0)失败
            码=错误.errno if 错误.errno is not None else None#errno
            if 码==getattr(os,'ESRCH',3):#组不在
                return False#不活
            if 码==getattr(os,'EPERM',1):#无权不等于不在
                return True#仍当活
            return 孩子.poll() is None#其余：退到直接孩子

    def 观察树退出():#单例观察者
        """起一次整树退出观察线程；已起过则空操作。"""
        with 观察锁:#单例
            if 状态['observing']:#已起
                return#空操作
            状态['observing']=True#记下已起
        def 轮询():#后台轮询
            """活着就继续轮询，缺席后取消升级定时器。"""
            while 树仍活():#活着
                短睡()#一拍
            树静止.set()#记下缺席并唤醒等待者
            定时=状态['graceTimer']#挂起的SIGKILL
            if 定时 is not None:#有定时器
                定时.cancel()#取消
            状态['graceTimer']=None#摘掉
        工作=线程(target=轮询)#观察线程
        工作.daemon=True#不挡住退出
        工作.start()

    def 发信号(信号名):#向仍活的树发信号
        """以树存活为门向树发信号。"""
        if not 树仍活():#已死则不打
            return#空操作
        信号树(平台,pid,信号名,孩子,taskkill)#按平台投递

    def 终止():#TERM再在宽限后KILL
        """面向消费方的终止动词。"""
        if 树静止.is_set() or 状态['graceTimer'] is not None:#已死或已在升级
            return#空操作
        观察树退出()#启动观察
        if 树静止.is_set():#启动观察时已经死了
            return#空操作
        发信号('SIGTERM')#先TERM
        def 升级():#宽限后KILL
            """宽限到期后强制杀死。"""
            发信号('SIGKILL')#KILL
        定时=定时器(宽限/1000.0,升级)#宽限后KILL
        定时.daemon=True#保持承诺语义
        定时.start()
        状态['graceTimer']=定时#记下

    def 为宿主退出终止():#宿主退出：立刻KILL
        """同步强制终止当前树，不启动定时器或等待。"""
        发信号('SIGKILL')#不等宽限

    已摘中止=[False]#结算后不再响应取消
    if 中止信号 is not None:#有取消信号
        def 盯中止():#等到中止再终止
            """等到信号中止再终止这棵树。"""
            等待中止(中止信号)#阻塞到中止
            if not 已摘中止[0]:#仍挂着才终止
                终止()#终止
        盯线程=线程(target=盯中止)#监听线程
        盯线程.daemon=True#不挡住退出
        盯线程.start()#立刻开跑

    if isinstance(入模式,dict) and 孩子.stdin is not None:#有stdin数据块
        数据=入模式['data'] if 'data' in 入模式 and 入模式['data'] is not None else b''#批数据
        if isinstance(数据,str):#文本
            数据=数据.encode('utf-8')#转字节
        try:#写出尽力而为
            孩子.stdin.write(数据)#写出
            孩子.stdin.close()#关闭
        except OSError:#EPIPE等；结局跟退出/输出走
            try:#尽量关
                孩子.stdin.close()#关
            except OSError:#关失败
                pass掉

    def 挂收集(流,收集器):#把管道读进收集器
        """后台读管道直到 EOF。"""
        def 读():#读线程
            """逐块推入收集器。"""
            try:#读可能因destroy提前结束
                while True:#直到EOF
                    块=流.read(65536)#一块
                    if not 块:#EOF
                        break
                    收集器.推入(块)#推入
            except OSError:#管道被毁；结算路径会seal
                pass掉
            finally:#确保关
                try:#关管道
                    流.close()#关
                except OSError:#已关
                    pass掉
        工作=线程(target=读)#收集线程
        工作.daemon=True#不挡住退出
        工作.start()
        return 工作#返回线程

    出线程=挂收集(孩子.stdout,标准输出收集) if 标准输出收集 is not None else None#stdout收集线程
    错线程=挂收集(孩子.stderr,标准误收集) if 标准误收集 is not None else None#stderr收集线程

    def 清理():#卸一次性监听
        """卸 abort 与排空定时器；有意不清 graceTimer。"""
        定时=状态['pipeDrainTimer']#排空等待
        if 定时 is not None:#有定时器
            定时.cancel()#取消
        状态['pipeDrainTimer']=None#摘掉
        已摘中止[0]=True#不再响应取消

    def 结算(退出码,信号名):#只结算一次
        """结算直接孩子结局。"""
        nonlocal 结局#写外层结局
        if 状态['settled']:#已经结算
            return#空操作
        状态['settled']=True#记下
        if 标准输出收集 is not None and 孩子.stdout is not None:#打断仍挂着的收集管道
            try:#destroy
                孩子.stdout.close()#关
            except OSError:#已关
                pass掉
        if 标准误收集 is not None and 孩子.stderr is not None:#同上
            try:#destroy
                孩子.stderr.close()#关
            except OSError:#已关
                pass掉
        if 标准输出收集 is not None:#封stdout溢出
            标准输出收集.封上()#封
        if 标准误收集 is not None:#封stderr溢出
            标准误收集.封上()#封
        清理()#卸abort与排空定时器
        结局={'exitCode':退出码,'signal':信号名}#写下结局
        已结局.set()#唤醒等结局的调用方

    def 盯退出():#孩子退出与管道排空
        """等进程结束，再以宽限等待收集管道排空后结算。"""
        码=孩子.wait()#等直接孩子
        退出码=码#默认退出码
        信号名=None#默认无信号
        if 码 is not None and 码<0:#POSIX负码表示信号
            退出码=None#死于信号则退出码为null
            try:#反查信号名
                信号名=signal.Signals(-码).name#信号名
            except ValueError:#未知编号
                信号名=None#未知
        def 强制结算():#宽限到仍未close则强制结算
            """用 exit 的码强制结算。"""
            结算(退出码,信号名)#结算
        定时=定时器(宽限/1000.0,强制结算)#与杀死同一宽限
        定时.daemon=True#不挡住退出
        定时.start()
        状态['pipeDrainTimer']=定时#记下
        if 出线程 is not None:#等stdout排空
            出线程.join()#等收集线程
        if 错线程 is not None:#等stderr排空
            错线程.join()#等收集线程
        结算(退出码,信号名)#管道关完则立刻结算

    盯线程=线程(target=盯退出)#退出监视线程
    盯线程.daemon=True#不挡住退出
    盯线程.start()

    def 等待结局():#等到直接孩子结局
        """阻塞到直接孩子退出，返回其退出事实。"""
        已结局.wait()#等结算
        return 结局#退出事实

    def 等待退出(等待信号=None):#等到树静止或调用方取消
        """等到整树静止；调用方取消则返回 False。"""
        观察树退出()#起观察
        if 树静止.is_set():#已经静止
            return True#静止
        if 已中止(等待信号):#调用方已取消
            return False#取消
        if 等待信号 is None:#无取消则死等
            树静止.wait()#等到缺席
            return True#静止
        while not 树静止.wait(0.015):#与中止赛跑，一拍一查
            if 已中止(等待信号):#取消
                return False#取消
        return True#静止

    已收集={}#collect模式读取器
    if 标准输出收集 is not None:#有stdout收集器才带
        已收集['stdout']=标准输出收集#带上
    if 标准误收集 is not None:#有stderr收集器才带
        已收集['stderr']=标准误收集#带上

    class 本地句柄:#活句柄
        """本地扩展句柄：含宿主退出同步强制终止。方法仅中文：等待结局、终止、等待退出、为宿主退出终止。"""
        def __init__(自身):#钉字段
            """保存管道与控制面。"""
            自身.pid=pid#同步可读
            自身.stdin=孩子.stdin if 入模式=='pipe' else None#仅pipe暴露
            自身.stdout=孩子.stdout if 出模式=='pipe' else None#仅pipe暴露
            自身.stderr=孩子.stderr if 错模式=='pipe' else None#仅pipe暴露
            自身.control=控制管道(孩子,控制请求)#可选控制通道
            自身.collected=已收集#collect模式读取器
            自身.等待结局=等待结局#等孩子结局
            自身.终止=终止#TERM→KILL
            自身.为宿主退出终止=为宿主退出终止#立刻KILL
            自身.等待退出=等待退出#等树静止

    return 本地句柄()#活句柄
