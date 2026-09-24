"""面向模型的 job_output、job_list、job_kill 工具，架在 jobs 服务上。"""
import json,weakref
from ...依赖.schemastery import 数字字段,枚举字段
from ...内核.工具 import 定义工具
from ...模型后端.llm import 截上下文摘要,创建用户消息
from ...工具.输出保留 import 文本保留器
from ..后台任务 import 任务标识
from .渲染 import 公开任务,状态行,渲染模型增量

公开任务模式={
    'type':'object',
    'additionalProperties':False,
    'properties':{
        'id':{'type':'string','required':True},
        'kind':{'type':'string','required':True},
        'label':{'type':'string','required':True},
        'status':{
            'type':'string',
            'required':True,
            'enum':['running','stopping','completed','killed','failed'],
        },
        'detail':{'type':'string'},
        'startedAt':{'type':'integer','required':True},
        'finishedAt':{'type':'integer'},
    },
}
配置={
    'waitTimeoutMs':数字字段(最小=1,默认值=30000),
    'maxWaitTimeoutMs':数字字段(最小=1,默认值=600000),
    'completionDelivery':枚举字段('quiet','wakeup',默认值='wakeup'),
    'maxConsecutiveWakes':数字字段(最小=1),
}
完成投递=('quiet','wakeup')

class 工具任务错误(Exception):
    """任务工具入参或配置非法。"""
    def __init__(自身,消息):
        """用原样英文消息构造。"""
        super().__init__(消息)

def 字节长(文本):
    """按 UTF-8 计字节长度。"""
    return len(文本.encode('utf-8'))

def 保留尾部(文本,最大字节):
    """按尾部策略压进字节上限。"""
    保留器=文本保留器({'kind':'tail','maxBytes':最大字节})
    保留器.推入(文本)
    return 保留器.收尾()['text']

def 保留头部(文本,最大字节):
    """按头部策略压进字节上限。"""
    保留器=文本保留器({'kind':'head','maxBytes':最大字节})
    保留器.推入(文本)
    return 保留器.收尾()['text']

def 后缀适配(正文,后缀,最大字节,省略标记):
    """在上限内拼接内容与后缀。"""
    全文=正文+后缀
    if 最大字节 is None or 字节长(全文)<=最大字节:
        return 全文
    固定=('' if 正文.endswith(省略标记.lstrip()) else 省略标记)+后缀
    固定字节=字节长(固定)
    if 固定字节>=最大字节:
        return 保留尾部(固定,最大字节)
    return 保留尾部(正文,最大字节-固定字节)+固定

def 完成摘要(任务):
    """notice 形态折叠行里，一条已结算任务的一行说明。"""
    return 截上下文摘要(任务['kind']+' '+任务['label']+' '+状态行(公开任务(任务)))

def 适配完成通知(任务):
    """把完成通知压进生产者输出上限。"""
    快照=公开任务(任务)
    前缀='background job '+str(快照['id'])
    细节=' ('+str(快照['kind'])+': '+str(快照['label'])+') finished '+状态行(快照)
    动作='\nDone; job_output.'
    全文=前缀+细节+'. Read its output with job_output.'
    最大字节=任务['outputLimitBytes'] if 'outputLimitBytes' in 任务 else None
    if 最大字节 is None or 字节长(全文)<=最大字节:
        return 全文
    省略='\n[notice truncated]'
    固定=前缀+省略+动作
    固定字节=字节长(固定)
    if 固定字节<=最大字节:
        if 固定字节==最大字节:
            return 固定
        return 前缀+保留头部(细节,最大字节-固定字节)+省略+动作
    紧凑=前缀+动作
    紧凑字节=字节长(紧凑)
    if 紧凑字节<=最大字节:
        return 紧凑
    动作字节=字节长(动作)
    if 动作字节>=最大字节:
        return 保留尾部(动作,最大字节)
    return 保留头部(前缀,最大字节-动作字节)+动作

def 单文本原文(内容):
    """恰好一块文本时抽出原文，否则为 None。"""
    if 内容 is None or len(内容)!=1:
        return None
    块=内容[0]
    if 块['type']!='text':
        return None
    return 块['text']

def 有界单文本(内容,最大字节):
    """把单文本块压进上限；非单文本则不动。"""
    文本=单文本原文(内容)
    if 文本 is None:
        return None
    return [{'type':'text','text':后缀适配(文本,'',最大字节,'\n[result truncated]')}]

def 调用方标识(执行):
    """工具执行所属智能体的会话标识。"""
    智能体=执行['agent'] if isinstance(执行,dict) and 'agent' in 执行 else getattr(执行,'agent',None)
    if 智能体 is None:
        return None
    return 智能体.id

def 可见输出上限(上下文,执行):
    """job_output 与 job_kill 所点名任务的生产者上限。"""
    工具名=执行['name'] if isinstance(执行,dict) else 执行.name
    if 工具名!='job_output' and 工具名!='job_kill':
        return None
    参数=执行['arguments'] if isinstance(执行,dict) else 执行.arguments
    任务号=参数['job_id'] if 参数 is not None and 'job_id' in 参数 else None
    if (not isinstance(任务号,str)) or len(任务号)==0:
        return None
    for 快照 in 上下文.jobs.列出(调用方标识(执行)):
        if 快照['id']==任务号:
            return 快照['outputLimitBytes'] if 'outputLimitBytes' in 快照 else None
    return None

def 校验任务号(值):
    """校验 ParameterSchemaSpec 表达不了的非空约束。"""
    if len(值)==0:
        raise 工具任务错误('invalid job_id: expected a non-empty string, got '+json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False))
    return 任务标识(值)

def 呈现任务调用(标题,种类,原始输入=None):
    """三个通用任务控制共用的待决呈现。"""
    视图={'card':'generic','title':标题,'kind':种类}
    if 原始输入 is not None:
        视图['rawInput']=原始输入
    return 视图

def 读取正文(读取):
    """消费增量、一次结果、再加状态行。"""
    溢出=读取['job']['output']['spillPaths'] if 'spillPaths' in 读取['job']['output'] else []
    增量=渲染模型增量(读取['chunks'],读取['lossy'],溢出)
    结果=读取['result'] if 'result' in 读取 else None
    if 结果 is None:
        文本=增量
    else:
        连接='\n' if len(增量)>0 and (not 增量.endswith('\n')) else ''
        文本=增量+连接+结果
    return {'text':文本,'job':公开任务(读取['job'])}

def 应用(上下文,配置值):
    """挂接控制器、完成投递、系统提示，并登记三个面向模型的任务工具。"""
    等待缺省=配置值['waitTimeoutMs'] if 'waitTimeoutMs' in 配置值 else 30000
    等待上限=配置值['maxWaitTimeoutMs'] if 'maxWaitTimeoutMs' in 配置值 else 600000
    投递=配置值['completionDelivery'] if 'completionDelivery' in 配置值 else 'wakeup'
    唤醒预算=配置值['maxConsecutiveWakes'] if 'maxConsecutiveWakes' in 配置值 else None
    已花唤醒=weakref.WeakKeyDictionary()
    if 等待缺省>等待上限:
        raise 工具任务错误('tool-jobs: waitTimeoutMs ('+str(等待缺省)+') exceeds maxWaitTimeoutMs ('+str(等待上限)+')')
    if 唤醒预算 is not None:
        if isinstance(唤醒预算,bool):
            整数预算=False
        elif isinstance(唤醒预算,int):
            整数预算=True
        elif isinstance(唤醒预算,float) and 唤醒预算.is_integer():
            整数预算=True
        else:
            整数预算=False
        if not 整数预算:
            raise 工具任务错误('tool-jobs: maxConsecutiveWakes ('+str(唤醒预算)+') must be a whole number of turns')
        唤醒预算=int(唤醒预算)
    if 投递=='wakeup' and 唤醒预算 is not None:
        def 认领收件箱(载荷,*位置参数):
            """用户输入重置连续唤醒预算。"""
            智能体=载荷['agent']
            消息=载荷['message']
            来源=消息['source'] if 消息 is not None and 'source' in 消息 else None
            if 来源 is not None and 来源['kind']=='user':
                已花唤醒.pop(智能体,None)
        上下文.监听('agent/inbox/claimed',认领收件箱)
    输出上限表=weakref.WeakKeyDictionary()
    def 预执行(执行,下一步,*位置参数):
        """插到 tools/pre-execute 链前，记下本次可见上限。"""
        最大字节=可见输出上限(上下文,执行)
        if 最大字节 is not None:
            输出上限表[执行]=最大字节
        return 下一步()
    上下文.监听('tools/pre-execute',预执行,{'前置':True})
    def 收口任务内容(执行,结果):
        """按记下的或现查的上限收口工具可见内容。"""
        最大字节=输出上限表[执行] if 执行 in 输出上限表 else None
        if 最大字节 is None:
            最大字节=可见输出上限(上下文,执行)
        if 执行 in 输出上限表:
            del 输出上限表[执行]
        if 最大字节 is None:
            return None
        名=执行['name'] if isinstance(执行,dict) else 执行.name
        是否错误=结果['isError'] if isinstance(结果,dict) else 结果.isError
        if 名=='job_output' and (not 是否错误):
            值=结果['value']
            文本=值['text']
            正文=文本 if len(文本)>0 else '(no new output)'
            if 正文.endswith('\n'):
                内容=正文[0:-1]
            else:
                内容=正文
            后缀='\n'+状态行(值['job'])
            内容块=结果['content'] if 'content' in 结果 else None
            if 单文本原文(内容块)==(内容+后缀):
                return [{'type':'text','text':后缀适配(内容,后缀,最大字节,'\n[output truncated]')}]
        return 有界单文本(结果['content'] if 'content' in 结果 else None,最大字节)
    上下文.jobs.挂接控制器('tool-jobs')
    段顺序=上下文.systemPrompt.获取段落顺序('TOOL_JOBS') if hasattr(上下文.systemPrompt,'获取段落顺序') else 上下文.systemPrompt.getSectionOrder('TOOL_JOBS')
    上下文.systemPrompt.段落({
        'name':'tool:jobs',
        'order':段顺序,
        'text':'Track every background job id you start. You are notified in-session when a job finishes — do not busy-poll or sleep on one; keep working on independent steps and do not duplicate a running job\'s work. Before giving a final answer, collect every still-relevant job with job_output (set wait: true only when you are genuinely blocked on it), and job_kill jobs that stopped mattering.',
    })
    模型已杀=set()
    def 收结算(事件):
        """把未收集的完成投递给所属智能体。"""
        if 事件['type']=='removed':
            模型已杀.discard(事件['job']['id'])
            return
        if 事件['type']!='settled':
            return
        已送达=(事件['job']['id'] in 模型已杀) or 事件['awaited']
        模型已杀.discard(事件['job']['id'])
        if 已送达 or 事件['cause']=='teardown' or ('owner' not in 事件['job']):
            return
        智能体表=上下文.获取服务('agents',False)
        if 智能体表 is None:
            return
        所有者=智能体表.获取(事件['job']['owner']) if hasattr(智能体表,'获取') else 智能体表.get(事件['job']['owner'])
        if 所有者 is None:
            return
        消息=创建用户消息({
            'content':[{'type':'text','text':适配完成通知(事件['job'])}],
            'source':{'kind':'tool-jobs','form':'notice','summary':完成摘要(事件['job'])},
        })
        if 投递=='wakeup' and 所有者.status=='idle':
            if 唤醒预算 is None:
                所有者.后续(消息)
                return
            已花=已花唤醒[所有者] if 所有者 in 已花唤醒 else 0
            if 已花<唤醒预算:
                已花唤醒[所有者]=已花+1
                所有者.后续(消息)
                return
        所有者.注入(消息)
    上下文.jobs.事件.订阅({'owners':'scope'},收结算)
    def 渲染输出(_参数,值):
        """正文加状态行。"""
        文本=值['text']
        正文=文本 if len(文本)>0 else '(no new output)'
        分隔='' if 正文.endswith('\n') else '\n'
        return [{'type':'text','text':正文+分隔+状态行(值['job'])}]
    def 执行输出(参数,执行):
        """校验后可选等待，再读输出。"""
        标识=校验任务号(参数['job_id'])
        会话=调用方标识(执行)
        if 'wait' in 参数 and 参数['wait'] is True:
            超时毫秒=参数['timeout_ms'] if 'timeout_ms' in 参数 else None
            if 超时毫秒 is None:
                超时毫秒=等待缺省
            超时=min(超时毫秒,等待上限)
            信号=执行['signal'] if isinstance(执行,dict) and 'signal' in 执行 else getattr(执行,'signal',None)
            上下文.jobs.等待(标识,超时,会话,信号)
        return 读取正文(上下文.jobs.读取(标识,会话))
    def 呈现输出(参数):
        """job_output 待决卡片。"""
        return 呈现任务调用('Read output from background job '+str(参数['job_id']),'read',参数['job_id'])
    公开任务必填=dict(公开任务模式)
    公开任务必填['required']=True
    上下文.tools.登记(定义工具({
        'name':'job_output',
        'description':('Read a background job. Stream jobs return only output since the previous read; '
            +'final-output jobs return their result after settlement. Every response ends with '
            +'`[status: ...]`. Reads are non-blocking unless `wait: true`, which waits up to the configured cap.'),
        'parameters':{
            'job_id':{'type':'string','required':True,'description':'Job id returned by the tool that started the background work.'},
            'wait':{'type':'boolean','description':'Block until the job reaches a terminal status or the timeout expires. A timed-out wait returns [status: running] and leaves the job alive.'},
            'timeout_ms':{'type':'number','description':'Max wait in milliseconds (only meaningful with wait: true). Defaults to the configured wait timeout; capped by the configured maximum.'},
        },
        'finalizeContent':收口任务内容,
        'output':{
            'schema':{
                'type':'object',
                'additionalProperties':False,
                'properties':{
                    'text':{'type':'string','required':True},
                    'job':公开任务必填,
                },
            },
            'render':渲染输出,
        },
        'execute':执行输出,
        'presentCall':呈现输出,
    }))
    def 渲染列表(_参数,任务列表):
        """空列表占位或一行一条。"""
        if len(任务列表)==0:
            文本='(no background jobs)'
        else:
            行列表=[]
            for 条 in 任务列表:
                行列表.append(str(条['id'])+' ['+str(条['kind'])+'] '+str(条['status'])+' — '+str(条['label']))
            文本='\n'.join(行列表)
        return [{'type':'text','text':文本}]
    def 执行列表(_参数,执行):
        """列出可见任务并投影公开快照。"""
        任务列表=上下文.jobs.列出(调用方标识(执行))
        return [公开任务(条) for 条 in 任务列表]
    def 呈现列表(_参数=None):
        """job_list 待决卡片。"""
        return 呈现任务调用('List background jobs','read')
    上下文.tools.登记(定义工具({
        'name':'job_list',
        'description':'List your background jobs (running and finished) with their ids, kinds, and statuses.',
        'parameters':{},
        'output':{
            'schema':{'type':'array','items':公开任务模式},
            'render':渲染列表,
        },
        'execute':执行列表,
        'presentCall':呈现列表,
    }))
    def 渲染终止(_参数,值):
        """已结束或已请求取消文案。"""
        if 值['outcome']=='already-finished':
            文本='job '+str(值['job']['id'])+' had already finished '+状态行(值['job'])
        else:
            文本='requested cancellation of job '+str(值['job']['id'])
        return [{'type':'text','text':文本}]
    def 执行终止(参数,执行):
        """请求取消并返回非消费公开快照。"""
        标识=校验任务号(参数['job_id'])
        会话=调用方标识(执行)
        原因=参数['reason'] if 'reason' in 参数 else None
        结果=上下文.jobs.终止(标识,会话,原因)
        if 结果=='requested':
            模型已杀.add(标识)
        快照=公开任务(上下文.jobs.获取(标识,会话))
        结局='already-finished' if 结果=='already-finished' else 'cancellation-requested'
        return {'outcome':结局,'job':快照}
    def 呈现终止(参数):
        """job_kill 待决卡片。"""
        return 呈现任务调用('Kill background job '+str(参数['job_id']),'execute',参数['job_id'])
    上下文.tools.登记(定义工具({
        'name':'job_kill',
        'description':'Request cancellation of a running background job by job id. Returns immediately; the job settles as killed once its work actually stops.',
        'parameters':{
            'job_id':{'type':'string','required':True,'description':'Job id returned by the tool that started the background work.'},
            'reason':{'type':'string','description':'Optional short reason, recorded in the log and forwarded to the job.'},
        },
        'finalizeContent':收口任务内容,
        'output':{
            'schema':{
                'type':'object',
                'additionalProperties':False,
                'properties':{
                    'outcome':{
                        'type':'string',
                        'required':True,
                        'enum':['cancellation-requested','already-finished'],
                    },
                    'job':公开任务必填,
                },
            },
            'render':渲染终止,
        },
        'execute':执行终止,
        'presentCall':呈现终止,
    }))

__all__=[
    '公开任务模式','配置','完成投递','工具任务错误','应用',
]
name='tool-jobs'
inject=['tools','jobs','systemPrompt']
Config=配置
apply=应用
default=应用
