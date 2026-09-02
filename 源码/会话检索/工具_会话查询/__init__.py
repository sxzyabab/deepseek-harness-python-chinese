"""面向模型、且经工作区授权的会话历史检索与读取工具。对齐上游 `@deepseek-ai/dsh-tool-session-query`。"""
from ...依赖.schemastery import 整数字段#配置字段
from ...内核.工具 import 定义工具#定义面向模型的工具
from ...工具.超时 import 定时器延迟上限毫秒#定时器延迟上限
from .入参 import 工具入参#工具入参面
from .操作 import 操作#工具执行
from .展示 import 展示#工具展示

名称='tool-session-query'#Cordis插件名（字面量）
注入=['tools','systemPrompt','sessionQuery']#依赖工具、系统提示词与会话检索

默认最大搜索结果数=100#默认最大命中数
默认搜索超时毫秒=30000#默认检索超时毫秒

配置={#插件配置模式
    'maxSearchResults':整数字段(默认值=默认最大搜索结果数),#命中上限
    'searchTimeoutMs':整数字段(默认值=默认搜索超时毫秒),#超时毫秒
}#配置结束

提示词文本=(
    'Use session_search to find relevant work from prior sessions, or session_event_search to search earlier '
    'events in one session. Search results are cursor-free and workspace-scoped. Follow a useful hit with '
    'session_trace, session_event_trace, or session_event_read when you need lineage, relationships, or exact data.'
)#系统提示词段落

文本输出={'schema':{'type':'string'},'render':lambda 参数,值:[{'type':'text','text':值}]}#字符串输出

__all__=['名称','注入','配置','应用','默认最大搜索结果数','默认搜索超时毫秒']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解析配置(配置值):#把配置收成运行时规格
    """解析运行时配置。"""
    最大结果数=取字段(配置值,'maxSearchResults',默认最大搜索结果数)#命中上限
    超时毫秒=取字段(配置值,'searchTimeoutMs',默认搜索超时毫秒)#超时
    if (not isinstance(最大结果数,int)) or 最大结果数<1:#非法命中
        raise TypeError('tool-session-query: maxSearchResults must be a positive safe integer')#拒绝
    if (not isinstance(超时毫秒,int)) or 超时毫秒<1 or 超时毫秒>定时器延迟上限毫秒:#非法超时
        raise TypeError(f'tool-session-query: searchTimeoutMs must be a positive integer no greater than {定时器延迟上限毫秒}')#拒绝
    return {'maxSearchResults':最大结果数,'searchTimeoutMs':超时毫秒}#解析结果

def 应用(上下文,配置值):#安装工具消费方
    """登记全部五个工具及其共享的模型指引。"""
    已解析=解析配置(配置值)#解析配置
    上下文.systemPrompt.section({'name':'tool:session-query','order':113,'text':提示词文本})#系统提示词
    上下文.tools.register(定义工具({
        'name':'session_search','description':'Search prior sessions in the caller workspace and return the strongest matching event from each session.',
        'parameters':工具入参['sessionSearchParameters'],'output':文本输出,'timeoutMs':已解析['searchTimeoutMs'],
        'execute':lambda 参数,执行:操作['executeSessionSearch'](上下文,参数,执行,已解析['maxSearchResults']),
        'presentCall':展示['presentSessionSearchCall'],
    }))#session_search
    上下文.tools.register(定义工具({
        'name':'session_event_search','description':'Search prior events in one authorized session; the current session excludes the step performing this call.',
        'parameters':工具入参['eventSearchParameters'],'output':文本输出,'timeoutMs':已解析['searchTimeoutMs'],
        'execute':lambda 参数,执行:操作['executeEventSearch'](上下文,参数,执行,已解析['maxSearchResults']),
        'presentCall':展示['presentEventSearchCall'],
    }))#session_event_search
    上下文.tools.register(定义工具({
        'name':'session_trace','description':'Read the authorized session lineage around one session, including complete visible ancestor and descendant relationships.',
        'parameters':工具入参['targetSessionParameter'],'output':文本输出,'isConcurrencySafe':lambda:True,
        'execute':lambda 参数,执行:操作['executeSessionTrace'](上下文,参数,执行),
        'presentCall':展示['presentSessionTraceCall'],
    }))#session_trace
    上下文.tools.register(定义工具({
        'name':'session_event_trace','description':'Read every direct replacement and relationship to a cited source event for one event in an authorized session.',
        'parameters':{**工具入参['targetSessionParameter'],'seq':{'type':'integer','required':True,'description':'Target event sequence number.'}},
        'output':文本输出,'isConcurrencySafe':lambda:True,
        'execute':lambda 参数,执行:操作['executeEventTrace'](上下文,参数,执行),
        'presentCall':lambda 参数:展示['presentEventTargetCall']('Trace event',参数),
    }))#session_event_trace
    上下文.tools.register(定义工具({
        'name':'session_event_read','description':'Read one full unabridged event and optional neighboring raw-event summaries from an authorized session.',
        'parameters':{
            **工具入参['targetSessionParameter'],
            'seq':{'type':'integer','required':True,'description':'Target event sequence number.'},
            'before':{'type':'integer','description':'Number of preceding raw events to summarize. Omit for none.'},
            'after':{'type':'integer','description':'Number of following raw events to summarize. Omit for none.'},
        },'output':文本输出,'isConcurrencySafe':lambda:True,
        'execute':lambda 参数,执行:操作['executeEventRead'](上下文,参数,执行),
        'presentCall':lambda 参数:展示['presentEventTargetCall']('Read event',参数),
    }))#session_event_read

apply=应用#Cordis插件入口
