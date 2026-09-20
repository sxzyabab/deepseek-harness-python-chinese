"""登记持久 shell PTY 后端：叠在子进程终端原语上，配合共享沙盒策略、有界输出与提供方拥有的会话清理。"""
import weakref#按所有者记住沙盒模式栅栏
from ...工具.超时 import 若已中止则抛出#中止入口；信号来自超时库
from ..终端 import 终端后端清理错误#搭建清理双失败
from ...沙盒.沙盒策略 import 生效沙盒模式#有效沙盒模式
from .配置 import 配置,校验配置,终端bash错误#配置模式、校验与本包错误
from .会话 import 本地PTY会话#本地PTY会话
from .清洗 import 受控提示符#受控提示符

名称='terminal-bash'#Cordis插件名
依赖=['terminals','sandboxPolicy','subprocess']#必需服务
沙盒模式栅栏=weakref.WeakKeyDictionary()#按所有者记住栅栏

def 确保沙盒模式栅栏(上下文,所有者):#确保所有者已挂沙盒模式栅栏
    """有活动 PTY 时禁止改沙盒模式。"""
    已有=沙盒模式栅栏[所有者] if 所有者 in 沙盒模式栅栏 else None#已有状态
    if 已有 is not None:#已挂过
        已有['pty']=上下文.terminals#刷新终端服务
        已有['sandboxPolicy']=上下文.sandboxPolicy#刷新沙盒策略
        return#不必再监听
    状态={'pty':上下文.terminals,'sandboxPolicy':上下文.sandboxPolicy}#新建状态
    沙盒模式栅栏[所有者]=状态#记下栅栏
    def 内部派发(_模式,事件名,参数,*其余):#拦截会话事件
        """拦截 session/event 上的 sandbox/mode。"""
        if 事件名!='session/event':#非会话事件则放过
            return#放过
        会话=参数[0]#会话
        事件=参数[1]#事件
        if 会话 is not 所有者.session or 事件['type']!='sandbox/mode':#不是本所有者的模式事件
            return#放过
        当前模式=生效沙盒模式(会话.events)#当前有效模式
        if 当前模式 is None:#日志没有则用默认
            当前模式=状态['sandboxPolicy'].默认模式#默认模式
        事件数据=事件['data'] if 'data' in 事件 else None#事件载荷
        新模式=事件数据['mode'] if 事件数据 is not None and 'mode' in 事件数据 else None#要改成的模式
        if 新模式==当前模式 or not 状态['pty'].有所有者活动(所有者):#未改模式或无PTY活动
            return#放过
        raise 终端bash错误('cannot change sandbox mode from "'+str(当前模式)+'" to "'+str(新模式)+'" while persistent terminal sessions are open or being created; wait for creation to settle and close them first')#须先关闭会话
    所有者.ctx.监听('internal/dispatch',内部派发,{'全局':True})#全局监听

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
        'DSH_SESSION_ID':规格['owner'].id,#所有者会话id
        'DSH_PTY_SESSION_ID':规格['sessionId'],#PTY会话id
    }#覆盖项结束

def 启动参数表(上下文,配置值,政策):#解析实际启动参数
    """解析实际启动参数；受限模式包进沙盒。"""
    参数表=[配置值['shellPath'],*list(配置值['shellArgs'])]#配置里的shell命令行
    if 政策['mode']=='danger-full-access':#全权模式不包沙盒
        return 参数表#原样
    沙箱=上下文.获取服务('sandbox',False)#取沙盒提供方
    if 沙箱 is None:#执行世界没有沙盒
        raise 终端bash错误('terminal-bash: sandbox mode "'+str(政策['mode'])+'" requires a ctx.sandbox provider in the execution world')#拒绝缺提供方
    隔离=沙箱.隔离(参数表,政策)#包进沙盒
    return 隔离['argv']#包进沙盒后的参数

def 初始化会话(会话,信号=None):#初始化会话并与取消竞态
    """初始化会话；取消已在发送路径上监听，此处只做入口检查。"""
    若已中止则抛出(信号)#已经取消则立刻失败
    会话.初始化(信号)#等到首个提示符

class Bash终端后端:#本地bash后端
    """以配置的类型注册的本地 shell 后端。"""
    def __init__(自身,上下文,配置值,搭建终端=None,创建会话=None):#注入上下文、配置与可替换的搭建钩子
        """注入上下文、配置与可替换的搭建钩子。"""
        自身.上下文=上下文#插件上下文
        自身.配置=配置值#已解析配置
        自身.type=配置值['backendType']#记下注册类型
        自身.搭建终端=搭建终端#可替换钩子
        自身.创建会话=创建会话#可替换钩子

    def 默认搭建终端(自身,规格):#默认走子进程终端
        """默认走 subprocess.启动终端。"""
        return 自身.上下文.subprocess.启动终端(规格)#拉起子进程终端

    def 默认创建会话(自身,终端句柄,配置项):#默认构造会话
        """默认构造本地会话。"""
        return 本地PTY会话(终端句柄,配置项)#本地会话

    def 搭建(自身,规格):#搭建一次会话
        """搭建一次会话并等到首个提示符。"""
        信号=规格['signal'] if 'signal' in 规格 else None#取消
        若已中止则抛出(信号)#已取消则失败
        确保沙盒模式栅栏(自身.上下文,规格['owner'])#挂上沙盒模式栅栏
        政策=自身.上下文.sandboxPolicy.解析({'session':规格['owner'].session})#解析沙盒策略
        参数表=启动参数表(自身.上下文,自身.配置,政策)#得到启动参数
        if len(参数表)==0 or 参数表[0] is None:#拒绝空参数
            raise 终端bash错误('terminal-bash: sandbox returned empty argv')#拒绝空参数
        工作目录=规格['cwd'] if 'cwd' in 规格 else None#请求工作目录
        if 工作目录 is None:#缺省
            工作目录=政策['workspaceRoot']#策略根
        终端规格={#子进程终端规格
            'argv':参数表,#命令行
            'cwd':工作目录,#工作目录
            'env':子环境(规格),#环境覆盖
            'rows':自身.配置['rows'],#行数
            'cols':自身.配置['cols'],#列数
            'graceMs':自身.配置['disposeGraceMs'],#拆除宽限
        }#规格骨架
        if 信号 is not None:#有取消
            终端规格['signal']=信号#带上
        if 自身.搭建终端 is None:#默认搭建
            终端句柄=自身.默认搭建终端(终端规格)#拉起子进程终端
        else:#可替换钩子
            终端句柄=自身.搭建终端(终端规格)#钩子
        if 自身.创建会话 is None:#默认会话
            会话=自身.默认创建会话(终端句柄,自身.配置)#包成本地会话
        else:#可替换钩子
            会话=自身.创建会话(终端句柄,自身.配置)#钩子
        try:#走启动就绪
            初始化会话(会话,信号)#等到首个提示符
            return 会话#交给注册表
        except BaseException as 错误:#启动失败则关闭
            try:#关闭刚建的会话
                会话.关闭('PTY startup failed').等待()#按启动失败关闭
            except BaseException as 关闭错误:#关闭也失败
                raise 终端后端清理错误(错误,关闭错误)#搭建成清理双失败
            raise 错误#只把启动失败抛出

def 应用(上下文,配置值):#注册本地PTY后端
    """注册本地 PTY 后端。"""
    校验配置(配置值)#校验配置
    上下文.terminals.登记后端(Bash终端后端(上下文,配置值))#挂上bash后端

__all__=['名称','依赖','应用','配置','Bash终端后端','终端bash错误']#公开面
name=名称#Cordis插件名
inject=依赖#Cordis依赖声明
Config=配置#Cordis配置模式
apply=应用#Cordis插件入口
default=应用#框架槽
