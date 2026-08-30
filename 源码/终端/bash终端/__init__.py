"""持久 shell PTY 后端，叠在子进程终端原语、共享沙盒策略、有界输出与提供方拥有的会话清理之上。"""
import threading,weakref#中止竞态与按所有者栅栏
from concurrent.futures import Future as _原生Future#单次操作结果
from ...依赖 import cordis#外部依赖胶水
from ..终端 import 终端后端清理错误#搭建清理双失败
from ...沙盒.沙盒策略 import 生效沙盒模式#有效沙盒模式
from .配置 import 配置,校验配置#配置模式与校验
from .会话 import 本地PTY会话#本地PTY会话
from .清洗 import 受控提示符#受控提示符

名称='terminal-bash'#Cordis插件名
注入=['terminals','sandboxPolicy','subprocess']#必需服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
Config=配置#Cordis配置模式
工作线程=threading.Thread#后台工作线程
沙盒模式栅栏=weakref.WeakKeyDictionary()#按所有者记住栅栏

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

def _是否thenable(值):#判定可等待对象
    if 值 is None:#空不是
        return False#不是
    if callable(getattr(值,'wait',None)):#Future 风格
        return True#可等待
    return callable(getattr(值,'等待',None))#外来 thenable

def _等待(值):#统一阻塞到结算
    if callable(getattr(值,'wait',None)):#Future 风格
        return 值.wait()#等待
    return 值.等待()#外来 thenable

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#可等待则等待否则原样
    """可等待则等待，否则原样返回。"""
    if _是否thenable(值):#可等待
        return _等待(值)#等待
    return 值#同步值

def 确保沙盒模式栅栏(上下文对象,所有者):#确保所有者已挂沙盒模式栅栏
    """有活动 PTY 时禁止改沙盒模式。"""
    已有=沙盒模式栅栏.get(所有者)#已有状态
    if 已有 is not None:#已挂过
        已有['pty']=上下文对象.terminals#刷新终端服务
        已有['sandboxPolicy']=上下文对象.sandboxPolicy#刷新沙盒策略
        return#不必再监听
    状态={'pty':上下文对象.terminals,'sandboxPolicy':上下文对象.sandboxPolicy}#新建状态
    沙盒模式栅栏[所有者]=状态#记下栅栏
    def 内部派发(_模式,事件名,参数,*其余):#拦截会话事件
        """拦截 session/event 上的 sandbox/mode。"""
        if 事件名!='session/event':#非会话事件则放过
            return#放过
        会话=参数[0]#会话
        事件=参数[1]#事件
        if 会话 is not 所有者.session or 取字段(事件,'type')!='sandbox/mode':#不是本所有者的模式事件
            return#放过
        当前模式=生效沙盒模式(会话.events)#当前有效模式
        if 当前模式 is None:#日志没有则用默认
            当前模式=状态['sandboxPolicy'].defaultMode#默认模式
        新模式=取字段(取字段(事件,'data'),'mode')#要改成的模式
        if 新模式==当前模式 or not 状态['pty'].hasOwnerActivity(所有者):#未改模式或无PTY活动
            return#放过
        raise Exception('cannot change sandbox mode from "'+str(当前模式)+'" to "'+str(新模式)+'" while persistent terminal sessions are open or being created; wait for creation to settle and close them first')#须先关闭会话
    所有者.ctx.on('internal/dispatch',内部派发,{'global':True})#全局监听

def 子环境(规格):#组装子进程环境
    """子进程提供方自带洗过的环境基底；这些是叠在其后的终端专用覆盖。"""
    return {#返回覆盖项
        'TERM':'dumb',#哑终端
        'PAGER':'cat',#分页器用cat
        'GIT_PAGER':'cat',#git分页器用cat
        'PS1':受控提示符,#受控提示符
        'PROMPT_COMMAND':'printf "\\033]133;D;%s\\007" "$?"',#退出码标记
        'BASH_SILENCE_DEPRECATION_WARNING':'1',#静音弃用警告
        'DSH_SHELL':'1',#标记为harness shell
        'DSH_SESSION_ID':取字段(取字段(规格,'owner'),'id'),#所有者会话id
        'DSH_PTY_SESSION_ID':取字段(规格,'sessionId'),#PTY会话id
    }#覆盖项结束

def 启动参数表(上下文对象,配置值,政策):#解析实际启动参数
    """解析实际启动参数；受限模式包进沙盒。"""
    参数表=[取字段(配置值,'shellPath'),*list(取字段(配置值,'shellArgs') or [])]#配置里的shell命令行
    if 取字段(政策,'mode')=='danger-full-access':#全权模式不包沙盒
        return 参数表#原样
    沙箱=上下文对象.get('sandbox')#取沙盒提供方
    if 沙箱 is None:#执行世界没有沙盒
        raise Exception('terminal-bash: sandbox mode "'+str(取字段(政策,'mode'))+'" requires a ctx.sandbox provider in the execution world')#拒绝缺提供方
    隔离政策=dict(政策) if isinstance(政策,dict) else {#拷贝政策
        'mode':取字段(政策,'mode'),#模式
        'workspaceRoot':取字段(政策,'workspaceRoot'),#工作区根
        'enforcement':取字段(政策,'enforcement'),#强制方式
        'denialSignatures':取字段(政策,'denialSignatures'),#拒绝特征
        'runnerFailureRules':取字段(政策,'runnerFailureRules'),#启动器失败规则
    }#对象政策收成映射
    隔离政策['mode']=取字段(政策,'mode')#钉死已收窄的模式
    return 取字段(沙箱.confine(参数表,隔离政策),'argv')#包进沙盒后的参数

def 初始化会话(会话,信号=None):#初始化会话并与取消竞态
    """初始化会话并与取消竞态。"""
    #TODO(pty-initialize-race-home):发送状态合并落地后，把这段外层取消竞态收进LocalPtySession.initialize
    if 信号 is None:#没有取消信号
        会话.初始化(信号)#直接初始化
        return#结束
    取消=操作任务()#取消拒绝器
    def 中止时(*位置参数):#取消时拒绝
        """取消时拒绝。"""
        原因=getattr(信号,'reason',None)#英文原因
        if 原因 is None:#没有英文原因
            原因=getattr(信号,'原因',None)#中文原因
        取消.拒绝(原因 if 原因 is not None else Exception('aborted'))#拒绝
    if hasattr(信号,'addEventListener'):#Web API
        信号.addEventListener('abort',中止时,{'once':True})#只听一次取消
    elif hasattr(信号,'加入监听'):#中文API
        信号.加入监听('abort',中止时,{'once':True})#只听一次取消
    try:#与初始化竞态
        if hasattr(信号,'throwIfAborted'):#英文API
            信号.throwIfAborted()#已经取消则立刻失败
        elif hasattr(信号,'抛若中止'):#中文API
            信号.抛若中止()#已经取消则立刻失败
        完成=操作任务()#初始化完成
        def 跑初始化():#跑初始化
            """跑初始化。"""
            try:#初始化
                会话.初始化(信号)#初始化
                完成.兑现(None)#成功
            except BaseException as 错误:#失败
                完成.拒绝(错误)#拒绝
        工作=工作线程(target=跑初始化)#初始化线程
        工作.daemon=True#不挡住退出
        工作.start()#立刻开跑
        胜出=操作任务()#竞态胜出
        def 等完成():#等初始化
            """等初始化完成。"""
            try:#等待
                解开(完成)#等待
                胜出.兑现(None)#初始化先到
            except BaseException as 错误:#失败
                胜出.拒绝(错误)#拒绝
        def 等取消():#等取消
            """等取消。"""
            try:#等待
                解开(取消)#等待取消
            except BaseException as 错误:#取消原因
                胜出.拒绝(错误)#取消先到
        工作线程(target=等完成,daemon=True).start()#等初始化
        工作线程(target=等取消,daemon=True).start()#等取消
        解开(胜出)#谁先到
    finally:#无论成败都摘监听
        if hasattr(信号,'removeEventListener'):#Web API
            信号.removeEventListener('abort',中止时)#摘掉取消监听
        elif hasattr(信号,'移除监听'):#中文API
            信号.移除监听('abort',中止时)#摘掉取消监听

class Bash终端后端:#本地bash后端
    """以配置的类型注册的本地 shell 后端。"""
    def __init__(自身,上下文对象,配置值,搭建终端=None,创建会话=None):#注入上下文、配置与可替换的搭建钩子
        """注入上下文、配置与可替换的搭建钩子。"""
        自身.上下文=上下文对象#插件上下文
        自身.配置=配置值#已解析配置
        自身.type=取字段(配置值,'backendType')#记下注册类型
        if 搭建终端 is None:#默认走subprocess
            def 默认搭建(规格):#默认搭建
                """默认走 subprocess.spawnTerminal。"""
                return 上下文对象.subprocess.spawnTerminal(规格)#默认
            自身.搭建终端=默认搭建#默认
        else:#可替换钩子
            自身.搭建终端=搭建终端#钩子
        if 创建会话 is None:#默认构造会话
            def 默认创建(终端句柄,配置项):#默认创建
                """默认构造本地会话。"""
                return 本地PTY会话(终端句柄,配置项)#默认
            自身.创建会话=默认创建#默认
        else:#可替换钩子
            自身.创建会话=创建会话#钩子

    def 搭建(自身,规格):#搭建一次会话
        """搭建一次会话并等到首个提示符。"""
        信号=取字段(规格,'signal')#取消
        if 信号 is not None:#有取消信号
            if hasattr(信号,'throwIfAborted'):#英文API
                信号.throwIfAborted()#已取消则失败
            elif hasattr(信号,'抛若中止'):#中文API
                信号.抛若中止()#已取消则失败
        确保沙盒模式栅栏(自身.上下文,取字段(规格,'owner'))#挂上沙盒模式栅栏
        政策=自身.上下文.sandboxPolicy.resolve({'session':取字段(取字段(规格,'owner'),'session')})#解析沙盒策略
        参数表=启动参数表(自身.上下文,自身.配置,政策)#得到启动参数
        if len(参数表)==0 or 参数表[0] is None:#拒绝空参数
            raise Exception('terminal-bash: sandbox returned empty argv')#拒绝空参数
        工作目录=取字段(规格,'cwd')#请求工作目录
        if 工作目录 is None:#缺省
            工作目录=取字段(政策,'workspaceRoot')#策略根
        终端规格={#子进程终端规格
            'argv':参数表,#命令行
            'cwd':工作目录,#工作目录
            'env':子环境(规格),#环境覆盖
            'rows':取字段(自身.配置,'rows'),#行数
            'cols':取字段(自身.配置,'cols'),#列数
            'graceMs':取字段(自身.配置,'disposeGraceMs'),#拆除宽限
        }#规格骨架
        if 信号 is not None:#有取消
            终端规格['signal']=信号#带上
        终端句柄=解开(自身.搭建终端(终端规格))#拉起子进程终端
        会话=自身.创建会话(终端句柄,自身.配置)#包成本地会话
        try:#走启动就绪
            初始化会话(会话,信号)#等到首个提示符
            return 会话#交给注册表
        except BaseException as 错误:#启动失败则关闭
            try:#关闭刚建的会话
                解开(会话.关闭('PTY startup failed'))#按启动失败关闭
            except BaseException as 关闭错误:#关闭也失败
                raise 终端后端清理错误(错误,关闭错误)#搭建成清理双失败
            raise 错误#只把启动失败抛出

def 应用(上下文对象,配置值):#注册本地PTY后端
    """注册本地 PTY 后端。"""
    校验配置(配置值)#校验配置
    上下文对象.terminals.registerBackend(Bash终端后端(上下文对象,配置值))#挂上bash后端

apply=应用#Cordis插件入口
default=应用#默认导出

__all__=['名称','注入','应用','配置','Config','name','inject','apply','default']#公开面
