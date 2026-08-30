"""本地子进程服务的进程管道：带每路 stdio 处置的分离进程树 spawn、带溢出文件的保尾收集、树范围发信号，以及 SIGTERM→SIGKILL 升级。

对齐上游 `subprocess-local/src/spawn.ts`。公开面仅中文名；无英文别名。
本层只对 abort 信号作出反应；截止、拆除阶梯和原因分类归调用方。
"""
import os,signal,tempfile,threading,time#路径、信号、溢出目录、收集线程与轮询
from concurrent.futures import Future as _原生Future#单次操作结果
from secrets import token_hex#溢出文件名随机后缀
from subprocess import Popen,DEVNULL,PIPE,run as 同步跑#子进程与同步taskkill
from ..子进程 import 擦洗父环境#清洗后的父环境
from ...工具.超时 import 定时器延迟上限毫秒#单次定时器可表示的最大延迟
from .进程检查 import 组内有活成员#Linux组内存活探针

__all__=('子环境','输出收集器','启动子进程','杀组','taskkill进程树','信号树')#仅中文公开名

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

溢出计数=0#本进程溢出文件序号
默认溢出目录=None#惰性私有溢出目录
溢出锁=threading.Lock()#保护溢出计数与默认目录

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 已中止(信号对象):#信号是否已中止
    """英文 aborted 或中文 已中止 任一为真则视为已中止。"""
    if 信号对象 is None:#无信号
        return False#无信号
    if getattr(信号对象,'aborted',False):#英文旗标
        return True#英文旗标
    if getattr(信号对象,'已中止',False):#中文旗标
        return True#中文旗标
    return False#未中止

def 中止原因(信号对象):#取出中止原因
    """取出中止原因。"""
    if 信号对象 is None:#无信号
        return None#无信号
    原因=getattr(信号对象,'reason',None)#英文原因
    if 原因 is not None:#有英文原因
        return 原因#英文原因
    return getattr(信号对象,'原因',None)#中文原因

def 听中止(信号对象,回调):#登记一次性abort回调
    """登记一次性 abort 回调。"""
    if 信号对象 is None:#无信号
        return#不登记
    if hasattr(信号对象,'addEventListener'):#Web API
        信号对象.addEventListener('abort',回调,{'once':True})#最多一次
        return#已登记
    if hasattr(信号对象,'加入监听'):#中文 API
        信号对象.加入监听('abort',回调,{'once':True})#最多一次

def 摘中止(信号对象,回调):#去掉abort回调
    """去掉 abort 回调。"""
    if 信号对象 is None:#无信号
        return#不摘
    if hasattr(信号对象,'removeEventListener'):#Web API
        信号对象.removeEventListener('abort',回调)#摘掉
        return#已摘
    if hasattr(信号对象,'移除监听'):#中文 API
        信号对象.移除监听('abort',回调)#摘掉

def 节点平台():#对齐Node process.platform
    """把 sys.platform 粗映射到 Node 平台名。"""
    import sys#取平台串
    名=sys.platform#本机
    if 名=='win32':#Windows
        return 'win32'#Node名
    if 名=='darwin':#macOS
        return 'darwin'#Node名
    if 名.startswith('linux'):#Linux
        return 'linux'#Node名
    return 名#原样

def 子环境(额外=None):#构造子环境
    """显式调用方条目按目标平台的环境键语义覆盖清洗后的父基线。字符串有意恢复或覆盖一条；显式 None 墓碑则删掉一条普通环境条目。"""
    环境=擦洗父环境()#清洗后的父基线
    if 节点平台()!='win32':#POSIX：后写覆盖
        合并=dict(环境)#拷贝基线
        if 额外 is not None:#有显式条目
            for 键,值 in (额外.items() if isinstance(额外,dict) else 额外):#逐条
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

def 私有溢出目录():#0700溢出根
    """默认溢出位置：OS tmpdir 下按进程私有的目录，惰性创建。"""
    global 默认溢出目录#惰性目录
    with 溢出锁:#保护创建
        if 默认溢出目录 is None:#首次创建
            默认溢出目录=tempfile.mkdtemp(prefix='dsh-subprocess-')#私有目录
            try:#尽量收紧权限
                os.chmod(默认溢出目录,0o700)#仅属主
            except Exception:#Windows等可能无chmod语义；目录仍在
                pass#保留已创建目录
        return 默认溢出目录#之后复用

def 短睡():#15ms一拍
    """树退出等待的存活轮询节拍。"""
    time.sleep(0.015)#短睡

class 输出收集器:#一路流的有界尾+可选溢出
    """用有界内存尾收集一路流；有溢出上限时第一次溢出就创建溢出文件。"""
    def __init__(自身,最大字节,最大溢出字节,标签,溢出目录):#按是否配置溢出关掉溢出
        """构造有界收集器。"""
        自身.块们=[]#当前内存尾块
        自身.字节=0#当前尾合计字节
        自身.已丢=False#是否丢过更早字节
        自身.溢出fd=None#溢出文件描述符
        自身.溢出文件=None#溢出路径；不可靠时清掉
        自身.溢出已关=最大溢出字节 is None#未配置spill则永不写文件
        自身.总量=0#整路流总字节
        自身.最大字节=最大字节#内存尾上限
        自身.最大溢出字节=最大溢出字节#完整文件上限
        自身.标签=标签#stdout/stderr，写入文件名
        自身.溢出目录=溢出目录#溢出目录
        自身._锁=threading.Lock()#推入与读取互斥

    def 推入(自身,块):#吞下一块流数据
        """吞下一块流数据，计入整路流总量并维护内存尾/溢出。"""
        if isinstance(块,str):#文本则按utf-8
            块=块.encode('utf-8')#转字节
        elif not isinstance(块,bytes):#其它缓冲
            块=bytes(块)#收成bytes
        with 自身._锁:#互斥
            自身.总量+=len(块)#累计总量
            会撑破=自身.字节+len(块)>自身.最大字节#本块是否会撑破内存尾
            if not 自身.溢出已关 and (会撑破 or 自身.溢出fd is not None):#该写溢出则写
                自身._全部溢出(块)#写溢出
            自身.块们.append(块)#先整块收下
            自身.字节+=len(块)#尾合计增加
            while 自身.字节>自身.最大字节:#超内存尾则丢头
                头=自身.块们[0]#最旧一块
                超额=自身.字节-自身.最大字节#需要丢掉的字节
                if len(头)<=超额:#整块都在超额内
                    自身.块们.pop(0)#丢掉整块
                    自身.字节-=len(头)#尾合计减少
                else:#只切掉块头
                    自身.块们[0]=头[超额:]#保留块尾
                    自身.字节-=超额#刚好压到上限
                自身.已丢=True#记截断

    def _全部溢出(自身,块):#写溢出
        """惰性打开溢出文件并追加 chunk（以及此前各块，仅一次）。"""
        global 溢出计数#本进程序号
        if 自身.最大溢出字节 is not None and 自身.总量>自身.最大溢出字节:#整路流已超完整文件上限
            自身._作废溢出()#文件再也装不下完整流
            return#不再溢出
        if 自身.溢出fd is None:#第一次溢出
            with 溢出锁:#保护计数
                溢出计数+=1#递增
                序号=溢出计数#本文件序号
            自身.溢出文件=os.path.join(自身.溢出目录,'dsh-subprocess-'+str(os.getpid())+'-'+str(序号)+'-'+token_hex(6)+'-'+自身.标签+'.log')#私有文件名
            自身.溢出fd=os.open(自身.溢出文件,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)#O_EXCL创建，0600
            for 先前 in 自身.块们:#先把已收块写进去
                os.write(自身.溢出fd,先前)#写出
        os.write(自身.溢出fd,块)#追加本块

    def _作废溢出(自身):#作废溢出
        """一旦文件再也装不下完整流，就停止溢出并删掉文件。"""
        fd=自身.溢出fd#当前描述符
        文件=自身.溢出文件#当前路径
        自身.溢出fd=None#先摘掉
        自身.溢出文件=None#不再广告
        自身.溢出已关=True#从此只留内存尾
        if fd is not None:#曾经打开过
            try:#尝试关掉
                os.close(fd)#关描述符
            except Exception:#关掉失败；留给finalize再试
                自身.溢出fd=fd#还给字段
        if 文件 is not None:#曾经有路径
            try:#尝试删除
                os.unlink(文件)#删文件
            except Exception:#unlink失败；最多留下maxSpillBytes
                pass#容忍

    def 自偏移读取(自身,起始字节):#从偏移读尾
        """按整路流字节坐标做增量读取：返回自起始字节起推入的全部内容。"""
        with 自身._锁:#互斥
            窗口起点=自身.总量-自身.字节#尾起点在总流中的偏移
            缓冲=b''.join(自身.块们)#拼当前尾
            有损=起始字节<窗口起点#请求点已掉出内存尾
            切片=缓冲 if 有损 else 缓冲[起始字节-窗口起点:]#lossy则整段尾，否则从窗口内切
            结果={'text':切片.decode('utf-8','replace'),'nextOffset':自身.总量,'lossy':有损}#读取结果
            if 自身.溢出文件 is not None:#有完整溢出才广告路径
                结果['spillPath']=自身.溢出文件#带路径
            return 结果#结束返回

    def 封上(自身):#关溢出
        """流结束后关掉溢出文件；失败的 close 停止广告溢出路径。"""
        with 自身._锁:#互斥
            if 自身.溢出fd is None:#没打开过或已关
                return#空操作
            try:#尝试关掉
                os.close(自身.溢出fd)#关描述符
            except Exception:#延迟回写失败；保住内存结果
                自身.溢出文件=None#不再带spillPath
            自身.溢出fd=None#无论成败都摘掉fd

    def 结算(自身):#结算快照
        """封上溢出文件并返回最终输出。"""
        自身.封上()#先关文件
        with 自身._锁:#互斥
            结果={'text':b''.join(自身.块们).decode('utf-8','replace'),'truncated':自身.已丢}#最终输出
            if 自身.溢出文件 is not None:#完整溢出才带路径
                结果['spillPath']=自身.溢出文件#带路径
            return 结果#结束返回

def 杀组(pid,信号名):#POSIX组信号
    """向分离的 POSIX 进程组发送信号。永不抛出；非正 pid 是空操作。"""
    if pid<=0:#无效pid
        return#空操作
    try:#组可能已不在
        os.kill(-pid,getattr(signal,信号名))#负pid=整组
    except Exception:#投递失败；见上方约定
        pass#吞掉

def taskkill进程树(pid):#Windows树终止
    """用 `taskkill /T /F` 终止一棵 Windows 进程树；失败可容忍。"""
    if pid<=0:#无效pid
        return#空操作
    同步跑(['taskkill','/PID',str(pid),'/T','/F'],stdout=DEVNULL,stderr=DEVNULL,check=False)#/T整树 /F强制

def 信号树(平台,pid,信号名,孩子,taskkill):#平台分发
    """按平台正确语义向分离进程树发信号。"""
    if 平台=='win32':#Windows：taskkill整树
        taskkill(pid)#任何信号都强制
        return#结束Windows
    if pid<=0:#无效pid
        return#空操作
    try:#先打组
        os.kill(-pid,getattr(signal,信号名))#负pid=整组
    except Exception:#组不在或无权
        try:#组失败则打直接孩子
            if 信号名=='SIGKILL':#强制
                孩子.kill()#立刻杀
            else:#温和
                孩子.terminate()#TERM
        except Exception:#直接孩子已退出；拆除仍幂等
            pass#吞掉

def 是否收集模式(模式):#pipe/inherit以外即收集
    """输出模式是否为有界收集对象。"""
    return 模式!='pipe' and 模式!='inherit'#对象模式带maxBytes

def 启动子进程(规格,内部=None):#本地spawn
    """按规格的每路 stdio 处置 spawn 一棵隔离的分离进程树。"""
    if 内部 is None:#缺省空覆盖
        内部={}#测试覆盖
    宽限=取字段(规格,'graceMs')#杀进程宽限
    if isinstance(宽限,bool) or not isinstance(宽限,(int,float)) or not (宽限==宽限) or 宽限<=0 or 宽限>定时器延迟上限毫秒:#宽限必须可表示
        raise Exception('subprocess graceMs must be a positive finite number no greater than '+str(定时器延迟上限毫秒))#与E2B提供方同一句
    溢出目录=取字段(内部,'spillDir')#测试覆盖溢出根
    if 溢出目录 is None:#缺省私有目录
        溢出目录=私有溢出目录()#惰性创建
    平台=取字段(内部,'platform')#测试覆盖平台
    if 平台 is None:#缺省本机
        平台=节点平台()#对齐Node
    taskkill=取字段(内部,'taskkill')#测试覆盖taskkill
    if taskkill is None:#缺省真实taskkill
        taskkill=taskkill进程树#Windows终止
    组探针=取字段(内部,'linuxProcessGroupHasLiveMembers')#测试覆盖组探针
    if 组探针 is None:#缺省/proc检查
        组探针=组内有活成员#组探针
    信号对象=取字段(规格,'signal')#取消信号
    if 已中止(信号对象):#spawn前已取消
        raise Exception('aborted before spawn: '+str(中止原因(信号对象) if 中止原因(信号对象) is not None else 'aborted'))#带取消原因
    参数表=list(取字段(规格,'argv') or [])#argv
    if len(参数表)==0 or 参数表[0] is None or len(str(参数表[0]))==0:#必须有非空程序名
        raise Exception('invalid argv: expected a non-empty program name at argv[0]')#加载/调用失败
    程序=参数表[0]#argv[0]是程序
    参数=参数表[1:]#其余参数
    标准流=取字段(规格,'stdio')#三路处置
    出模式=取字段(标准流,'stdout')#stdout处置
    错模式=取字段(标准流,'stderr')#stderr处置
    入模式=取字段(标准流,'stdin')#stdin处置
    环境=子环境(取字段(规格,'env'))#合并后的子环境
    入管道=PIPE if 入模式!='ignore' else DEVNULL#ignore或可写管道
    出管道=None if 出模式=='inherit' else PIPE#inherit或可读管道
    错管道=None if 错模式=='inherit' else PIPE#同上
    启动参数={'args':[程序]+参数,'cwd':取字段(规格,'cwd'),'env':环境,'stdin':入管道,'stdout':出管道,'stderr':错管道}#Popen参数
    if 平台!='win32':#仅POSIX分离
        启动参数['start_new_session']=True#自己的进程组
    try:#spawn可能失败
        孩子=Popen(**启动参数)#启动
    except Exception as 错误:#spawn失败
        完成=操作任务()#拒绝done
        完成.拒绝(错误)#spawn级失败
        raise 错误#调用方立即看见；与Node同步抛错不同处：Node把失败放进done——此处对齐同步失败+句柄路径由上层捕获
    #注：Node的spawn失败走child.on('error')拒绝done且仍返回句柄；Python Popen构造失败同步抛。下面成功路径对齐。
    标准输出收集=None#stdout收集器
    标准误收集=None#stderr收集器
    if 是否收集模式(出模式) and 孩子.stdout is not None:#挂stdout收集
        溢出=取字段(出模式,'spill')#溢出配置
        标准输出收集=输出收集器(取字段(出模式,'maxBytes'),取字段(溢出,'maxBytes') if 溢出 is not None else None,'stdout',溢出目录)#有界尾
    if 是否收集模式(错模式) and 孩子.stderr is not None:#挂stderr收集
        溢出=取字段(错模式,'spill')#溢出配置
        标准误收集=输出收集器(取字段(错模式,'maxBytes'),取字段(溢出,'maxBytes') if 溢出 is not None else None,'stderr',溢出目录)#有界尾

    状态={
        'graceTimer':None,#SIGKILL升级定时器
        'treeExitObserved':False,#树已确认缺席
        'treeExitObservation':None,#整树退出观察者
        'settled':False,#直接孩子结局已结算
        'pipeDrainTimer':None,#close等待上限
    }#可变状态
    pid=孩子.pid if 孩子.pid is not None else -1#同步可读pid
    完成=操作任务()#直接孩子结局

    def 树仍活():#存活探针
        """分离树的根（或 POSIX 组）是否仍活着。"""
        if 状态['treeExitObserved']:#已确认缺席
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
            码=getattr(错误,'errno',None)#errno
            if 码==getattr(os,'ESRCH',3):#组不在
                return False#不活
            if 码==getattr(os,'EPERM',1):#无权不等于不在
                return True#仍当活
            return 孩子.poll() is None#其余：退到直接孩子

    def 观察树退出():#单例观察者
        """启动或复用句柄上唯一的整树退出观察者。"""
        if 状态['treeExitObservation'] is not None:#已建
            return 状态['treeExitObservation']#复用
        观察=操作任务()#观察任务
        def 轮询():#后台轮询
            """活着就继续轮询，缺席后取消升级定时器。"""
            while 树仍活():#活着
                短睡()#一拍
            状态['treeExitObserved']=True#记下缺席
            定时=状态['graceTimer']#挂起的SIGKILL
            if 定时 is not None:#有定时器
                定时.cancel()#取消
            状态['graceTimer']=None#摘掉
            观察.兑现(None)#观察完成
        工作=threading.Thread(target=轮询)#观察线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        状态['treeExitObservation']=观察#记下
        return 观察#返回

    def 发信号(信号名):#向仍活的树发信号
        """以树存活为门向树发信号。"""
        if not 树仍活():#已死则不打
            return#空操作
        信号树(平台,pid,信号名,孩子,taskkill)#按平台投递

    def 终止():#TERM再在宽限后KILL
        """面向消费方的终止动词。"""
        if 状态['treeExitObserved'] or 状态['graceTimer'] is not None:#已死或已在升级
            return#空操作
        观察树退出()#启动观察
        if 状态['treeExitObserved']:#启动观察时已经死了
            return#空操作
        发信号('SIGTERM')#先TERM
        def 升级():#宽限后KILL
            """宽限到期后强制杀死。"""
            发信号('SIGKILL')#KILL
        定时=threading.Timer(宽限/1000.0,升级)#宽限后KILL
        定时.daemon=True#保持承诺语义
        定时.start()#启动
        状态['graceTimer']=定时#记下

    def 为宿主退出终止():#宿主退出：立刻KILL
        """同步强制终止当前树，不启动定时器或等待。"""
        发信号('SIGKILL')#不等宽限

    def 在中止时():#signal abort→终止
        """abort 监听回调。"""
        终止()#终止

    听中止(信号对象,在中止时)#最多一次

    if isinstance(入模式,dict) and 孩子.stdin is not None:#有stdin数据块
        数据=取字段(入模式,'data')#批数据
        if 数据 is None:#没有数据
            数据=''#空
        if isinstance(数据,str):#文本
            数据=数据.encode('utf-8')#转字节
        try:#写出尽力而为
            孩子.stdin.write(数据)#写出
            孩子.stdin.close()#关闭
        except Exception:#EPIPE等；结局跟退出/输出走
            try:#尽量关
                孩子.stdin.close()#关
            except Exception:#关失败
                pass#吞掉

    def 挂收集(流,收集器):#把管道读进收集器
        """后台读管道直到 EOF。"""
        def 读():#读线程
            """逐块推入收集器。"""
            try:#读可能因destroy提前结束
                while True:#直到EOF
                    块=流.read(65536)#一块
                    if not 块:#EOF
                        break#结束
                    收集器.推入(块)#推入
            except Exception:#管道被毁；结算路径会seal
                pass#吞掉
            finally:#确保关
                try:#关管道
                    流.close()#关
                except Exception:#已关
                    pass#吞掉
        工作=threading.Thread(target=读)#收集线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        return 工作#返回线程

    出线程=挂收集(孩子.stdout,标准输出收集) if 标准输出收集 is not None else None#stdout收集线程
    错线程=挂收集(孩子.stderr,标准误收集) if 标准误收集 is not None else None#stderr收集线程

    def 清理():#卸一次性监听
        """卸 abort 与排空定时器；有意不清 graceTimer。"""
        定时=状态['pipeDrainTimer']#排空等待
        if 定时 is not None:#有定时器
            定时.cancel()#取消
        状态['pipeDrainTimer']=None#摘掉
        摘中止(信号对象,在中止时)#卸abort

    def 结算(退出码,信号名):#只结算一次
        """结算直接孩子结局。"""
        if 状态['settled']:#已经结算
            return#空操作
        状态['settled']=True#记下
        if 标准输出收集 is not None and 孩子.stdout is not None:#打断仍挂着的收集管道
            try:#destroy
                孩子.stdout.close()#关
            except Exception:#已关
                pass#吞掉
        if 标准误收集 is not None and 孩子.stderr is not None:#同上
            try:#destroy
                孩子.stderr.close()#关
            except Exception:#已关
                pass#吞掉
        if 标准输出收集 is not None:#封stdout溢出
            标准输出收集.封上()#封
        if 标准误收集 is not None:#封stderr溢出
            标准误收集.封上()#封
        清理()#卸abort与排空定时器
        完成.兑现({'exitCode':退出码,'signal':信号名})#交出结局

    def 盯退出():#孩子退出与管道排空
        """等进程结束，再以宽限等待收集管道排空后结算。"""
        码=孩子.wait()#等直接孩子
        退出码=码#默认退出码
        信号名=None#默认无信号
        if 码 is not None and 码<0:#POSIX负码表示信号
            退出码=None#死于信号则退出码为null
            try:#反查信号名
                信号名=signal.Signals(-码).name#信号名
            except Exception:#未知编号
                信号名=None#未知
        def 强制结算():#宽限到仍未close则强制结算
            """用 exit 的码强制结算。"""
            结算(退出码,信号名)#结算
        定时=threading.Timer(宽限/1000.0,强制结算)#与杀死同一宽限
        定时.daemon=True#不挡住退出
        定时.start()#启动
        状态['pipeDrainTimer']=定时#记下
        if 出线程 is not None:#等stdout排空
            出线程.join()#等收集线程
        if 错线程 is not None:#等stderr排空
            错线程.join()#等收集线程
        结算(退出码,信号名)#管道关完则立刻结算

    盯线程=threading.Thread(target=盯退出)#退出监视线程
    盯线程.daemon=True#不挡住退出
    盯线程.start()#启动

    def 等待退出(等待信号=None):#等到树静止或调用方取消
        """等到整树静止；调用方取消则返回 False。"""
        观察=观察树退出()#启动/复用观察
        if 状态['treeExitObserved']:#已经静止
            return True#静止
        if 已中止(等待信号):#调用方已取消
            return False#取消
        if 等待信号 is None:#无取消则死等
            观察.等待()#等到缺席
            return True#静止
        取消=操作任务()#取消通道
        def 在取消时():#abort→False
            """取消回调。"""
            取消.兑现(False)#取消
        听中止(等待信号,在取消时)#最多一次
        if 已中止(等待信号):#登记时已取消
            在取消时()#立刻兑现
        try:#两路赛跑
            静止=操作任务()#静止通道
            def 在静止时():#观察完成
                """静止回调。"""
                静止.兑现(True)#静止
            def 跟观察():#等观察
                """等观察线程。"""
                try:#观察可能已兑现
                    观察.等待()#等
                except Exception:#观察失败仍当静止尝试结束
                    pass#吞掉
                在静止时()#兑现
            threading.Thread(target=跟观察,daemon=True).start()#跟观察
            #简化：轮询两路
            while True:#赛跑
                if 状态['treeExitObserved']:#静止
                    return True#静止
                if 已中止(等待信号):#取消
                    return False#取消
                短睡()#一拍
        finally:#无论哪路
            摘中止(等待信号,在取消时)#卸监听

    已收集={}#collect模式读取器
    if 标准输出收集 is not None:#有stdout收集器才带
        已收集['stdout']=标准输出收集#带上
    if 标准误收集 is not None:#有stderr收集器才带
        已收集['stderr']=标准误收集#带上

    class 本地句柄:#活句柄
        """本地扩展句柄：含宿主退出同步强制终止。方法仅中文：终止、等待退出、为宿主退出终止。"""
        def __init__(自身):#钉字段
            """保存管道与控制面。"""
            自身.pid=pid#同步可读
            自身.stdin=孩子.stdin if 入模式=='pipe' else None#仅pipe暴露
            自身.stdout=孩子.stdout if 出模式=='pipe' else None#仅pipe暴露
            自身.stderr=孩子.stderr if 错模式=='pipe' else None#仅pipe暴露
            自身.collected=已收集#collect模式读取器
            自身.done=完成#孩子结局
            自身.终止=终止#TERM→KILL
            自身.为宿主退出终止=为宿主退出终止#立刻KILL
            自身.等待退出=等待退出#等树静止

    return 本地句柄()#活句柄
