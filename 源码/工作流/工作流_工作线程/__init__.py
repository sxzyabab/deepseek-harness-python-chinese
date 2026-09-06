"""worker-thread 工作流引擎。每次运行在全新 worker 上的可逃离领域上下文中执行模型写的脚本，并把 agent() 调用桥到宿主子智能体。该线程防止同步脚本工作阻塞宿主，并允许强制终止，但这是收容而不是安全边界。"""
import os,re,threading,uuid#并行度、meta 语句检测、后台观察与 UUID
from ...依赖.schemastery import 字符串字段,自然数字段#配置字段
from ..工作流 import (#导入工作流引擎、错误与运行标识
    工作流引擎,#引擎服务定义
    工作流错误,#工作流错误
    工作流运行标识,#运行标识工厂
)#来自工作流服务定义
from .元数据 import 校验元数据#导入元数据校验
from .领域 import 从领域物化,物化错误#再导出领域物化
from .宿主 import 工作线程运行#导入宿主侧存活运行
from .运行时 import 编译脚本正文#宿主侧与 worker 共用包装编译
from .类型 import (#再导出 worker 侧端口词汇
    子句柄,#子句柄
    子端口,#子端口
    子结果,#子结果
    子启动请求,#子启动请求
    工作线程初始化,#初始化载荷
    工作线程上限,#上限
)#来自类型模块
__all__=(#仅中文公开名；Cordis 英文槽不入表
    '元数据语句','配置模式','可用并行度','断言正文可解析',
    '工作线程工作流引擎','默认',
    '子句柄','子端口','子结果','子启动请求','工作线程初始化','工作线程上限',
    '校验元数据','从领域物化','物化错误','工作线程运行',
)#公开面结束

元数据语句=re.compile(r'^\s*export\s+const\s+meta\b',re.ASCII)#检测 export const meta 语句；JS 标识符为 ASCII

配置模式={#静态配置模式
    'provider':字符串字段(默认值='spawn'),#默认 spawn 提供方
    'maxConcurrentAgents':自然数字段(默认值=0),#0 表示自动解析并发
    'maxTotalAgents':自然数字段(最小=1,默认值=1000),#默认总数上限 1000
    'maxItemsPerCall':自然数字段(最小=1,默认值=4096),#默认组合子条目上限
    'syncTimeoutMs':自然数字段(最小=1,默认值=5000),#默认同步超时 5000ms
    'disposeGraceMs':自然数字段(默认值=5000),#默认销毁宽限 5000ms
}#结束配置模式

def 可用并行度():#对齐 os.availableParallelism
    """返回可用 CPU 并行度估计。"""
    核=os.cpu_count()#CPU 核数
    return 核 if 核 is not None and 核>0 else 1#至少 1

def 断言正文可解析(正文,名称):#宿主侧解析检查脚本正文
    """用 worker 侧运行时编译的同一包装做正文解析检查，让 start() 保住缝的同步 SCRIPT_PARSE 抛出。以 export const meta 开头的正文给出针对性消息。"""
    if 元数据语句.search(正文) is not None:#正文里还写了 export const meta
        raise 工作流错误('workflow meta rides the `meta` request field, not the script: remove the `export const meta = {...}` statement from the body','SCRIPT_PARSE')#指出 meta 应走请求字段
    try:#尝试按 worker 包装编译
        编译脚本正文(正文,名称)#只解析——脚本对象丢弃，什么都不执行
    except 工作流错误:#已是 SCRIPT_PARSE
        raise#原样抛出
    except SyntaxError as 错误:#包装编译失败
        raise 工作流错误('workflow script does not parse: '+str(错误),'SCRIPT_PARSE',{'cause':错误})#映射为 SCRIPT_PARSE

def 解析子智能体提供方(上下文,已配置,覆盖):#解析子智能体提供方名
    """在发布工作前解析一次运行的提供方路由。"""
    提供方=覆盖 if 覆盖 is not None else 已配置#请求覆盖优先于引擎配置
    if not isinstance(提供方,str) or len(提供方)==0 or 提供方!=提供方.strip():#空或未归一化；判 length
        raise 工作流错误('workflow subagentProvider must be a non-empty normalized string','INVALID_ARGUMENT')#参数无效
    if 上下文.subagents.取提供方(提供方) is None:#未登记该提供方
        raise 工作流错误('no subagent provider registered for "'+提供方+'"','AGENT_START')#启动前就找不到提供方
    return 提供方#返回已解析提供方名

def 解析最大总智能体(请求值,上限):#解析子智能体总数上限
    """按引擎部署上限解析一次运行的子总数上限。外来 JSON 在此校验安全整数。"""
    if 请求值 is None:#未请求则用部署上限
        return 上限#返回部署上限
    if isinstance(请求值,bool) or (not isinstance(请求值,int)) or 请求值<1 or abs(请求值)>9007199254740991:#不是从 1 起的安全整数
        raise 工作流错误('workflow maxTotalAgents must be a positive safe integer','INVALID_ARGUMENT')#参数无效
    if 请求值>上限:#超过引擎上限
        raise 工作流错误('workflow maxTotalAgents '+str(请求值)+' exceeds the engine ceiling '+str(上限),'INVALID_ARGUMENT')#说明超限
    return 请求值#返回请求值

class 生命周期观察者:#生命周期回调，转成工作流事件
    """生命周期回调表。"""
    def __init__(自身,转发):#记住转发函数
        """记住转发函数。"""
        自身.转发=转发#转发

    def 阶段(自身,标题):#阶段
        """阶段。"""
        自身.转发('workflow/phase',标题)#转发

    def 日志(自身,消息):#日志
        """日志。"""
        自身.转发('workflow/log',消息)#转发

    def 智能体开始(自身,智能体):#开始
        """开始。智能体是 dict。"""
        自身.转发('workflow/agent-start',智能体)#转发

    def 智能体结束(自身,智能体):#结束
        """结束。智能体是 dict。"""
        自身.转发('workflow/agent-end',智能体)#转发

class 工作线程工作流引擎(工作流引擎):#worker-thread 工作流引擎
    """worker-thread 引擎服务。start() 预先校验脚本（meta + 宿主侧正文解析）并返回工作流运行，其 结果 永不拒绝；workflow/* 事件按缝约定围绕该运行发出。"""
    注入=['subagents']#依赖子智能体服务

    def __init__(自身,ctx,config=None):#用上下文与配置构造引擎
        """用上下文与配置构造引擎。配置是 dict。"""
        工作流引擎.__init__(自身,ctx)#登记为 workflowEngine 服务
        自身.配置=config if config is not None else {}#保存已解析配置

    def 启动(自身,请求):#启动一次 worker-thread 运行
        """在全新 worker 线程中校验并执行工作流脚本。无法开始的请求同步抛出工作流错误；一旦返回运行，此后每次失败都经 结果.stopReason 兑现。请求是 dict。"""
        元数据=校验元数据(请求['meta'])#校验并规范化 meta
        断言正文可解析(请求['script'],元数据['name'])#宿主侧解析正文
        覆盖=请求['subagentProvider'] if 'subagentProvider' in 请求 else None#可选提供方覆盖
        子提供方=解析子智能体提供方(自身.ctx,自身.配置['provider'] if 'provider' in 自身.配置 else 'spawn',覆盖)#解析提供方
        请求上限=请求['maxTotalAgents'] if 'maxTotalAgents' in 请求 else None#可选总数上限
        最大总=解析最大总智能体(请求上限,自身.配置['maxTotalAgents'] if 'maxTotalAgents' in 自身.配置 else 1000)#解析总数上限
        标识=工作流运行标识(str(uuid.uuid4()))#铸造运行标识
        信息={'id':标识,'meta':元数据}#事件用身份快照
        并发=自身.配置['maxConcurrentAgents'] if 'maxConcurrentAgents' in 自身.配置 else 0#并发配置
        if 并发==0:#0 表示按机器自动解析
            并发=min(16,max(1,可用并行度()-2))#留两核给宿主，上限 16
        上限={#组装 worker 侧上限
            'maxConcurrentAgents':并发,#并发上限
            'maxTotalAgents':最大总,#本次运行总数上限
            'maxItemsPerCall':自身.配置['maxItemsPerCall'] if 'maxItemsPerCall' in 自身.配置 else 4096,#组合子条目上限
            'syncTimeoutMs':自身.配置['syncTimeoutMs'] if 'syncTimeoutMs' in 自身.配置 else 5000,#同步切片超时
        }#结束上限
        初始化={'meta':元数据,'body':请求['script'],'limits':上限}#组装 workerData
        if 'args' in 请求 and 请求['args'] is not None:#有 args 才放入
            初始化['args']=请求['args']#写入
        运行上下文=自身.ctx#捕获启动时上下文
        子智能体=运行上下文.subagents#捕获子智能体服务
        def 转发(事件名,*其余):#把观察者回调转成工作流事件
            """把观察者回调转成工作流事件。"""
            自身.发出工作流事件(事件名,信息,*其余)#转发
        工作线程运行实例=工作线程运行(#创建宿主侧存活运行
            运行上下文,#启动时上下文
            子智能体,#子智能体服务
            标识,#运行标识
            元数据,#元数据
            请求['parent'],#父智能体
            初始化,#worker 初始化
            子提供方,#提供方名
            自身.配置['disposeGraceMs'] if 'disposeGraceMs' in 自身.配置 else 5000,#销毁宽限
            生命周期观察者(转发),#生命周期回调
            请求['signal'] if 'signal' in 请求 else None,#可选取消信号
        )#结束工作线程运行构造
        自身.发出工作流事件('workflow/start',信息)#发出运行开始
        def 监视结束():#结果兑现后发结束事件
            """结果兑现后发结束事件。"""
            try:#等待结果
                已结算=工作线程运行实例.结果.等待()#等待结算
            except Exception:#永不拒绝约定下不应到达
                return#忽略
            摘要={'stopReason':已结算['stopReason'],'agentsStarted':已结算['agentsStarted']}#组装对外结果摘要
            if 'error' in 已结算:#有错误键才带 error
                摘要['error']=已结算['error']#写入
            自身.发出工作流事件('workflow/end',信息,摘要)#发出结束
        线程=threading.Thread(target=监视结束)#后台
        线程.daemon=True#不挡住退出
        线程.start()#启动
        return 工作线程运行实例#返回存活运行

工作线程工作流引擎.inject=工作线程工作流引擎.注入#Cordis 依赖槽
工作线程工作流引擎.Config=配置模式#Cordis 配置槽
默认=工作线程工作流引擎#默认导出 worker-thread 引擎
Config=配置模式#Cordis 配置槽
apply=工作线程工作流引擎#Cordis 入口槽
default=工作线程工作流引擎#Cordis 默认导出槽
