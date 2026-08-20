"""工作流能力缝的服务定义。服务提供方执行编排脚本；仅观察的生命周期事件从不暴露运行控制。"""
import threading#异步监听拒绝的后台观察
from cordis import 服务#Cordis 服务基类
from cordis.工具 import 是否thenable#可等待判定
from llm import 装备错误#智能体错误基类
from .类型 import (#再导出工作流公开类型
    工作流运行标识,#运行标识品牌工厂
    工作流阶段,#阶段声明
    工作流元数据,#脚本元数据
    工作流停止原因,#停止原因
    工作流结果,#完整运行结果
    工作流运行信息,#运行身份快照
    工作流智能体信息,#智能体调用身份
    工作流智能体结局,#智能体调用结局
    工作流智能体结束信息,#智能体调用结束信息
    工作流结果信息,#对外结果摘要
)#来自类型模块
from .运行时类型 import (#再导出运行句柄与启动请求
    工作流启动请求,#启动请求
    工作流运行,#存活运行句柄协议
)#来自运行时类型模块

工作流事件名=(#工作流生命周期事件名联合
    'workflow/start',#运行开始
    'workflow/phase',#进入阶段
    'workflow/log',#叙述日志
    'workflow/agent-start',#智能体调用开始
    'workflow/agent-end',#智能体调用结束
    'workflow/end',#运行结束
)#事件名结束

工作流错误码=(#工作流致命错误码联合
    'SCRIPT_PARSE',#脚本解析失败
    'META_INVALID',#元数据无效
    'INVALID_ARGUMENT',#参数无效
    'UNSUPPORTED_OPTION',#不支持的选项
    'UNSUPPORTED_SCHEMA',#不支持的模式
    'AGENT_CAP',#智能体数量上限
    'ITEM_CAP',#条目数量上限
    'AGENT_START',#智能体启动失败
    'AGENT_RESULT',#智能体结果失败
    'RESULT_UNSERIALIZABLE',#结果不可序列化
    'CANCELLED',#已取消
)#错误码结束

class 工作流错误(装备错误):#工作流缝的带类型错误
    """工作流缝失败的带类型错误。继承装备错误，因此 code 是可机器路由的分类。fatal 决定组合子纪律：parallel()/pipeline() 会再抛出致命错误（写错的选项或触顶的上限必须大声杀掉脚本），并把每项的 null 留给子运行失败和阶段内普通脚本错误。每一个工作流错误码都是致命的；该标志存在是为了让每个 catch 点显式区分，而不是靠暗示。"""
    def __init__(自身,消息,码,选项=None):#构造工作流错误
        """记下稳定 code、链式 cause，以及 fatal 标志（未指定时视为致命）。"""
        装备错误.__init__(自身,消息,码,选项)#交给智能体错误基类
        自身.name='WorkflowError'#固定错误名
        致命=True#默认致命
        if isinstance(选项,dict) and 'fatal' in 选项:#选项给出 fatal
            致命=选项['fatal']#取显式值
            if 致命 is None:#显式 None 仍按默认
                致命=True#未指定时视为致命
        自身.fatal=致命#英文致命标志
        自身.致命=致命#中文致命标志

def 是否致命工作流错误(错误):#判断是否为致命工作流错误
    """组合子是否必须再抛出 error，而不是把该项映射为 null。任意抛出值；是否致命由宿主 isinstance 判定（脚本领域无法伪造）。当且仅当 error 是 fatal 已置位的工作流错误时返回真。"""
    return isinstance(错误,工作流错误) and 错误.fatal#类型匹配且致命标志为真

def 渲染监听错误(错误):#把抛出值渲染成可记录字符串
    """在不破坏监听器收容的前提下渲染任意抛出值。返回 str(error)；连强制转换都抛错时返回固定标签。"""
    try:#尝试强制转为字符串
        return str(错误)#返回字符串形式
    except Exception:#字符串强制转换本身也可能抛错
        # 字符串强制转换本身也可能抛错。
        return '[unrenderable thrown value]'#转换失败时返回固定标签

class 工作流引擎(服务):#工作流引擎服务定义
    """工作流服务定义约定。无效请求在发布前抛出；存活运行由持有者所有，其结果永不拒绝，取消与销毁有界，销毁会在该界限内等待子清理。生命周期监听器失败会被收容，且 workflow/end 在结果结算时恰好发出一次。"""
    def __init__(自身,ctx):#用 Cordis 上下文构造引擎
        """向宿主注册名为 workflowEngine 的服务。"""
        服务.__init__(自身,ctx,'workflowEngine')#向宿主注册名为 workflowEngine 的服务

    def 启动(自身,请求):#启动一次工作流运行
        """解析并执行一份工作流脚本。请求含脚本、其 args、父智能体、以及可选的取消信号。返回存活运行；其 result 在脚本结算时兑现。"""
        raise NotImplementedError('WorkflowEngine.start')#子类必须实现

    def 发出工作流事件(自身,名称,*参数):#派发工作流事件并收容监听器失败
        """发出生命周期事件，同时收容并记录每个监听器的失败。名称是要派发的 workflow/* 事件；参数须匹配其声明签名。"""
        派发参数=[名称,*参数]#组装 emit 派发参数
        for 监听器 in 自身.ctx.events.dispatch('emit',派发参数):#遍历该事件的全部监听器
            try:#执行单个监听器
                返回=监听器(*参数)#调用监听器并取得返回值
                if 是否thenable(返回):#返回值像承诺则接管拒绝
                    def 盯住(任务=返回,事件名=名称):#把异步拒绝接到诊断
                        """把异步拒绝接到诊断。"""
                        try:#等待承诺
                            任务.等待()#等待承诺
                        except Exception as 错误:#异步拒绝
                            自身.ctx.logger.warn('workflow: '+事件名+' listener rejected: '+渲染监听错误(错误))#记录监听器 Promise 拒绝
                    线程=threading.Thread(target=盯住)#后台观察
                    线程.daemon=True#不挡住退出
                    线程.start()#启动
            except Exception as 错误:#监听器同步抛错
                自身.ctx.logger.warn('workflow: '+名称+' listener threw: '+渲染监听错误(错误))#记录监听器同步抛错

默认=工作流引擎#默认导出工作流引擎服务定义
default=工作流引擎#Cordis 默认导出
