"""经共享沙箱 Node PTC 执行器的工作流编排。VM 提供脚本钩子；进程套用调用 Session 的文件政策。"""
import copy,os,re,threading,uuid#参数拷贝、并行度、元数据头、结束事件线程、运行标识
from ...依赖.schemastery import 字符串字段,自然数字段#配置字段
from ..工作流 import 工作流引擎,工作流错误,工作流运行标识#缝上引擎
from .宿主 import ptc工作流运行#持有者运行
from .元数据 import 校验元数据#元数据校验
from .领域 import 从领域物化,物化错误#再导出
from .类型 import (#再导出宾客类型字段
    工作者上限字段,#上限
    工作者初始化字段,#初始化
    子启动请求字段,#子启动
    子结果字段,#子结果
    子句柄,#句柄
    子端口,#端口
)#类型结束

__all__=[#仅中文公开名
    'ptc工作流引擎','校验元数据','从领域物化','物化错误',
    '工作者上限字段','工作者初始化字段','子启动请求字段','子结果字段','子句柄','子端口',
    '名称','依赖','配置',
]#公开面结束

名称='workflow-ptc'#Cordis 插件名
依赖=['subagents','ptcRuntime','sandboxPolicy']#所需服务
配置={#全部可选——Config 填默认
    'provider':字符串字段(默认值='spawn'),#agent() 使用的子提供方
    'maxConcurrentAgents':自然数字段(默认值=0),#并发上限；0 按核数解析
    'maxTotalAgents':自然数字段(最小=1,默认值=1000),#一次运行 agent() 总数
    'maxItemsPerCall':自然数字段(最小=1,默认值=4096),#一次 parallel/pipeline 条目
    'syncTimeoutMs':自然数字段(最小=1,默认值=5000),#最初同步片段 VM 超时
}#配置结束

元数据语句=re.compile(r'^\s*export\s+const\s+meta\b',re.ASCII)#Claude Code 风格 meta 头

def 断言正文可解析(正文,名称值):#发布前同步拒绝非法 JS 头
    """发布工作流运行前同步拒绝非法正文。宾客在自己的进程里编译同一异步包装。Python 宿主只拦 meta 头；JS 语法由宾客进程编译。"""
    if 元数据语句.search(正文) is not None:#正文里还有 export const meta
        raise 工作流错误('workflow meta rides the `meta` request field, not the script: remove the `export const meta = {...}` statement from the body','SCRIPT_PARSE')#解析

def 解析子提供方(上下文对象,已配置,覆盖):#发布前解析提供方路由
    """解析一次运行的子提供方路由。"""
    提供方=已配置 if 覆盖 is None else 覆盖#覆盖或配置
    if len(提供方)==0 or 提供方!=提供方.strip():#必须非空规范化
        raise 工作流错误('workflow subagentProvider must be a non-empty normalized string','INVALID_ARGUMENT')#参数
    if 上下文对象.subagents.取提供方(提供方) is None:#未登记
        raise 工作流错误('no subagent provider registered for "'+提供方+'"','AGENT_START')#启动
    return 提供方#路由

def 解析最大总智能体(请求值,天花板):#单次运行上限
    """相对引擎部署天花板解析一次运行的总子上限。"""
    if 请求值 is None:#用天花板
        return 天花板#部署上限
    if type(请求值) is bool or type(请求值) is not int or 请求值<1:#必须正整数
        raise 工作流错误('workflow maxTotalAgents must be a positive safe integer','INVALID_ARGUMENT')#参数
    if 请求值>天花板:#超过部署
        raise 工作流错误('workflow maxTotalAgents '+str(请求值)+' exceeds the engine ceiling '+str(天花板),'INVALID_ARGUMENT')#参数
    return 请求值#上限

def 可用并行度():#availableParallelism
    """可用 CPU 并行度，至少 1。"""
    核=os.cpu_count()#逻辑核
    if 核 is None or 核<1:#未知
        return 1#至少 1
    return 核#核数

class ptc工作流引擎(工作流引擎):#PTC 后端工作流引擎
    """start() 预先校验脚本（元数据 + 宿主侧正文检查）并返回结果永不拒绝的工作流运行。"""
    def __init__(自身,上下文对象,配置):#记下已解析配置
        """加载时拒绝非 TypeScript 的 PTC 提供方。"""
        super().__init__(上下文对象)#登记 workflowEngine
        if 上下文对象.ptcRuntime.语言()!='typescript':#必须 Node TS
            raise RuntimeError('workflow-ptc requires the Node TypeScript PTC runtime')#拒绝
        自身.配置=配置#schemastery 已填默认

    def 启动(自身,请求):#校验并执行
        """在沙箱 Node 进程中校验并执行工作流脚本。不能开始的请求同步抛工作流错误；一旦返回运行，失败都经 result.stopReason 兑现。"""
        元数据=校验元数据(请求['meta'])#元数据
        断言正文可解析(请求['script'],元数据['name'])#正文
        覆盖=请求['subagentProvider'] if 'subagentProvider' in 请求 else None#覆盖
        子提供方=解析子提供方(自身.ctx,自身.配置['provider'],覆盖)#路由
        请求上限=请求['maxTotalAgents'] if 'maxTotalAgents' in 请求 else None#单次上限
        总上限=解析最大总智能体(请求上限,自身.配置['maxTotalAgents'])#上限
        标识=工作流运行标识(str(uuid.uuid4()))#运行 id
        信息={'id':标识,'meta':元数据}#运行信息
        if 自身.配置['maxConcurrentAgents']==0:#按核数
            并发=min(16,max(1,可用并行度()-2))#自动
        else:#显式
            并发=自身.配置['maxConcurrentAgents']#配置
        上限={'maxConcurrentAgents':并发,'maxTotalAgents':总上限,'maxItemsPerCall':自身.配置['maxItemsPerCall'],'syncTimeoutMs':自身.配置['syncTimeoutMs']}#钩子上限
        初始化={'meta':元数据,'body':请求['script'],'limits':上限}#boot
        if 'args' in 请求 and 请求['args'] is not None:#有 args
            初始化['args']=copy.deepcopy(请求['args'])#拷贝
        运行上下文=自身.ctx#捕获服务，卸载后仍可用
        class 观察器:#生命周期观察
            """把执行进度投影成 workflow/* 事件。"""
            def 阶段(自身,标题):#phase
                """发出 workflow/phase。"""
                引擎.发出工作流事件('workflow/phase',信息,标题)#阶段
            def 日志(自身,消息):#log
                """发出 workflow/log。"""
                引擎.发出工作流事件('workflow/log',信息,消息)#日志
            def 智能体开始(自身,智能体):#agent-start
                """发出 workflow/agent-start。"""
                引擎.发出工作流事件('workflow/agent-start',信息,智能体)#开始
            def 智能体结束(自身,智能体):#agent-end
                """发出 workflow/agent-end。"""
                引擎.发出工作流事件('workflow/agent-end',信息,智能体)#结束
        引擎=自身#观察器闭包用
        信号=请求['signal'] if 'signal' in 请求 else None#可选取消
        运行=ptc工作流运行(
            运行上下文,#上下文
            运行上下文.subagents,#子智能体
            运行上下文.ptcRuntime,#PTC
            标识,#id
            元数据,#meta
            请求['parent'],#父
            初始化,#boot
            子提供方,#提供方
            运行上下文.sandboxPolicy.解析({'session':请求['parent'].session}),#政策
            观察器(),#观察
            信号,#信号
        )#运行
        自身.发出工作流事件('workflow/start',信息)#开始
        def 发结束():#结果落定时发 end
            """workflow/end 只带结局数据，不含结果值。"""
            已结算=运行.结果.等待()#永不拒绝
            结局={'stopReason':已结算['stopReason'],'agentsStarted':已结算['agentsStarted']}#摘要
            if 'error' in 已结算 and 已结算['error'] is not None:#有错误
                结局['error']=已结算['error']#带上
            自身.发出工作流事件('workflow/end',信息,结局)#结束
        threading.Thread(target=发结束,daemon=True).start()#后台
        return 运行#存活运行

default=ptc工作流引擎#Cordis 默认导出
name=名称#Cordis 插件名
inject=依赖#Cordis 依赖槽
Config=配置#Cordis 配置槽
