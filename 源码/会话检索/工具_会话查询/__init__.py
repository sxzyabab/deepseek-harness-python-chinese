"""面向模型、且经工作区授权的会话历史检索与读取工具。"""
from ...依赖.schemastery import 整数字段
from ...内核.工具 import 定义工具#定义面向模型的工具
from ...工具.超时 import 定时器延迟上限毫秒#定时器延迟上限
from .入参 import 工具入参#工具入参面
from .操作 import 操作#工具执行
from .呈现 import 呈现#工具呈现

包名='@deepseek-ai/dsh-tool-session-query'
名称='tool-session-query'
依赖=['tools','systemPrompt','sessionQuery']#依赖工具、系统提示词与会话检索

默认最大搜索结果数=100#默认最大命中数
默认搜索超时毫秒=30000#默认检索超时毫秒

配置={
    'maxSearchResults':整数字段(默认值=默认最大搜索结果数),#命中上限
    'searchTimeoutMs':整数字段(默认值=默认搜索超时毫秒),#超时毫秒
}

提示词文本=(
    'Use session_search to find relevant work from prior sessions, or session_event_search to search earlier '
    'events in one session. Search results are cursor-free and workspace-scoped. Follow a useful hit with '
    'session_trace, session_event_trace, or session_event_read when you need lineage, relationships, or exact data.'
)#系统提示词段落

def 渲染文本输出(参数,值):
    """字符串工具输出。"""
    return [{'type':'text','text':值}]#文本块

文本输出={'schema':{'type':'string'},'render':渲染文本输出}#字符串输出

__all__=['包名','名称','依赖','应用','默认','配置','默认最大搜索结果数','默认搜索超时毫秒']

def 解析配置(配置值):
    """解析运行时配置。"""
    最大结果数=配置值['maxSearchResults'] if 'maxSearchResults' in 配置值 else 默认最大搜索结果数#命中上限
    超时毫秒=配置值['searchTimeoutMs'] if 'searchTimeoutMs' in 配置值 else 默认搜索超时毫秒#超时
    if isinstance(最大结果数,bool) or (not isinstance(最大结果数,int)) or 最大结果数<1:#非法命中
        raise TypeError('tool-session-query: maxSearchResults must be a positive safe integer')#拒绝
    if isinstance(超时毫秒,bool) or (not isinstance(超时毫秒,int)) or 超时毫秒<1 or 超时毫秒>定时器延迟上限毫秒:#非法超时
        raise TypeError('tool-session-query: searchTimeoutMs must be a positive integer no greater than '+str(定时器延迟上限毫秒))#拒绝
    return {'maxSearchResults':最大结果数,'searchTimeoutMs':超时毫秒}#解析结果

def 并发安全():
    """只读工具并发安全。"""
    return True#安全

def 应用(上下文,配置值):
    """登记全部五个工具及其共享的模型指引。"""
    已解析=解析配置(配置值)#解析配置
    上下文.systemPrompt.section({'name':'tool:session-query','order':113,'text':提示词文本})#系统提示词
    def 执行会话搜索(参数,执行):
        """session_search。"""
        return 操作['executeSessionSearch'](上下文,参数,执行,已解析['maxSearchResults'])#执行
    def 执行事件搜索(参数,执行):
        """session_event_search。"""
        return 操作['executeEventSearch'](上下文,参数,执行,已解析['maxSearchResults'])#执行
    def 执行谱系(参数,执行):
        """session_trace。"""
        return 操作['executeSessionTrace'](上下文,参数,执行)#执行
    def 执行事件追踪(参数,执行):
        """session_event_trace。"""
        return 操作['executeEventTrace'](上下文,参数,执行)#执行
    def 呈现事件追踪(参数):
        """追踪卡。"""
        return 呈现['presentEventTargetCall']('Trace event',参数)#卡
    def 执行事件读取(参数,执行):
        """session_event_read。"""
        return 操作['executeEventRead'](上下文,参数,执行)#执行
    def 呈现事件读取(参数):
        """读取卡。"""
        return 呈现['presentEventTargetCall']('Read event',参数)#卡
    上下文.tools.register(定义工具({
        'name':'session_search','description':'Search prior sessions in the caller workspace and return the strongest matching event from each session.',
        'parameters':工具入参['sessionSearchParameters'],'output':文本输出,'timeoutMs':已解析['searchTimeoutMs'],
        'execute':执行会话搜索,
        'presentCall':呈现['presentSessionSearchCall'],
    }))#session_search
    上下文.tools.register(定义工具({
        'name':'session_event_search','description':'Search prior events in one authorized session; the current session excludes the step performing this call.',
        'parameters':工具入参['eventSearchParameters'],'output':文本输出,'timeoutMs':已解析['searchTimeoutMs'],
        'execute':执行事件搜索,
        'presentCall':呈现['presentEventSearchCall'],
    }))#session_event_search
    上下文.tools.register(定义工具({
        'name':'session_trace','description':'Read the authorized session lineage around one session, including complete visible ancestor and descendant relationships.',
        'parameters':工具入参['targetSessionParameter'],'output':文本输出,'isConcurrencySafe':并发安全,
        'execute':执行谱系,
        'presentCall':呈现['presentSessionTraceCall'],
    }))#session_trace
    上下文.tools.register(定义工具({
        'name':'session_event_trace','description':'Read every direct replacement and relationship to a cited source event for one event in an authorized session.',
        'parameters':{**工具入参['targetSessionParameter'],'seq':{'type':'integer','required':True,'description':'Target event sequence number.'}},
        'output':文本输出,'isConcurrencySafe':并发安全,
        'execute':执行事件追踪,
        'presentCall':呈现事件追踪,
    }))#session_event_trace
    上下文.tools.register(定义工具({
        'name':'session_event_read','description':'Read one full unabridged event and optional neighboring raw-event summaries from an authorized session.',
        'parameters':{
            **工具入参['targetSessionParameter'],
            'seq':{'type':'integer','required':True,'description':'Target event sequence number.'},
            'before':{'type':'integer','description':'Number of preceding raw events to summarize. Omit for none.'},
            'after':{'type':'integer','description':'Number of following raw events to summarize. Omit for none.'},
        },'output':文本输出,'isConcurrencySafe':并发安全,
        'execute':执行事件读取,
        'presentCall':呈现事件读取,
    }))#session_event_read

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=默认#框架槽
