"""面向模型的 job_output、job_list、job_kill 工具，架在 jobs 服务上。

加载本插件会挂接生产者所需的控制器，并把未报告的完成投递给所属智能体：忙着的所有者注入其下一步，空闲的在默认 wakeup 投递下开一个回合，并按所有者设上限。
"""
import json,weakref#JSON片段与弱键字典
from ...依赖.schemastery import 数字字段,枚举字段#配置字段
from ...内核.工具 import 定义工具#定义面向模型的工具
from ...模型后端.llm import 截上下文摘要,创建用户消息#摘要与用户消息
from ...工具.输出保留 import 文本保留器#头尾文本保留器
from ..后台任务 import 任务标识#任务id品牌化

公开任务模式={#公开快照JSON Schema
    'type':'object',#对象
    'additionalProperties':False,#禁止额外字段
    'properties':{#字段
        'id':{'type':'string','required':True},#任务id
        'kind':{'type':'string','required':True},#种类
        'label':{'type':'string','required':True},#标签
        'status':{#生命周期状态
            'type':'string',#字符串
            'required':True,#必填
            'enum':['running','stopping','completed','killed','failed'],#五种状态
        },#status结束
        'detail':{'type':'string'},#可选细节
        'startedAt':{'type':'integer','required':True},#开始时间
        'finishedAt':{'type':'integer'},#可选结束时间
    },#properties结束
}#公开任务模式结束
配置={#有界等待与完成投递配置
    'waitTimeoutMs':数字字段(最小=1,默认值=30000),#默认等待30秒
    'maxWaitTimeoutMs':数字字段(最小=1,默认值=600000),#硬上限10分钟
    'completionDelivery':枚举字段('quiet','wakeup',默认值='wakeup'),#默认唤醒
    'maxConsecutiveWakes':数字字段(最小=1,默认值=3),#默认连续3次
}#配置模式结束
完成投递=('quiet','wakeup')#完成投递策略联合

class 工具任务错误(Exception):#本包校验与配置失败
    """任务工具入参或配置非法。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

def 字节长(文本):#UTF-8字节长度
    """对齐 TextEncoder.encode(...).byteLength。"""
    return len(文本.encode('utf-8'))#按utf8计

def 公开任务(快照):#投影公开快照
    """从注册表快照去掉任务所有权与通知记账。快照是 dict。"""
    结果={#面向模型的字段
        'id':快照['id'],#任务id
        'kind':快照['kind'],#种类
        'label':快照['label'],#标签
        'status':快照['status'],#状态
        'startedAt':快照['startedAt'],#开始时间
    }#骨架
    if 'detail' in 快照:#有细节才带
        结果['detail']=快照['detail']#细节
    if 'finishedAt' in 快照:#有结束才带
        结果['finishedAt']=快照['finishedAt']#结束时间
    return 结果#公开快照

def 状态行(快照):#方括号状态行
    """渲染通用状态，可带生产者细节。"""
    if 'detail' in 快照:#有细节
        return '[status: '+str(快照['status'])+', '+str(快照['detail'])+']'#状态加细节
    return '[status: '+str(快照['status'])+']'#只有状态

def 保留尾部(文本,最大字节):#保留尾部
    """按尾部策略压进字节上限。"""
    保留器=文本保留器({'kind':'tail','maxBytes':最大字节})#尾部保留器
    保留器.推入(文本)#喂入全文
    return 保留器.收尾()['text']#截好的尾部

def 保留头部(文本,最大字节):#保留头部
    """按头部策略压进字节上限。"""
    保留器=文本保留器({'kind':'head','maxBytes':最大字节})#头部保留器
    保留器.推入(文本)#喂入全文
    return 保留器.收尾()['text']#截好的头部

def 后缀适配(正文,后缀,最大字节,省略标记):#在上限内拼接内容与后缀
    """在上限内拼接内容与后缀。"""
    全文=正文+后缀#未截断全文
    if 最大字节 is None or 字节长(全文)<=最大字节:#未超上限则原样
        return 全文#原样
    固定=('' if 正文.endswith(省略标记.lstrip()) else 省略标记)+后缀#标记加后缀
    固定字节=字节长(固定)#固定部分字节
    if 固定字节>=最大字节:#固定部分已超则只留尾
        return 保留尾部(固定,最大字节)#只留尾
    return 保留尾部(正文,最大字节-固定字节)+固定#正文留尾再拼固定部分

def 完成摘要(快照):#完成摘要
    """notice 形态折叠行里，一条已结算任务的一行说明。"""
    return 截上下文摘要(快照['kind']+' '+快照['label']+' '+状态行(快照))#种类、标签、状态

def 适配完成通知(快照):#把完成通知压进上限
    """把完成通知压进生产者输出上限。"""
    前缀='background job '+str(快照['id'])#通知前缀
    细节=' ('+str(快照['kind'])+': '+str(快照['label'])+') finished '+状态行(快照)#细节段
    动作='\nDone; job_output.'#动作提示
    全文=前缀+细节+'. Read its output with job_output.'#未截断全文
    最大字节=快照['outputLimitBytes'] if 'outputLimitBytes' in 快照 else None#生产者上限
    if 最大字节 is None or 字节长(全文)<=最大字节:#未超上限则原样
        return 全文#原样
    省略='\n[notice truncated]'#截断标记
    固定=前缀+省略+动作#前缀加标记加动作
    固定字节=字节长(固定)#该形态字节
    if 固定字节<=最大字节:#固定形态仍装得下
        if 固定字节==最大字节:#刚好用尽
            return 固定#用固定形态
        return 前缀+保留头部(细节,最大字节-固定字节)+省略+动作#细节留头
    紧凑=前缀+动作#丢掉细节
    紧凑字节=字节长(紧凑)#紧凑形态字节
    if 紧凑字节<=最大字节:#紧凑形态装得下
        return 紧凑#紧凑形态
    动作字节=字节长(动作)#动作段字节
    if 动作字节>=最大字节:#动作已超则只留尾
        return 保留尾部(动作,最大字节)#只留尾
    return 保留头部(前缀,最大字节-动作字节)+动作#前缀留头再拼动作

def 单文本原文(内容):#单文本块原文
    """恰好一块文本时抽出原文，否则为 None。"""
    if 内容 is None or len(内容)!=1:#不是恰好一块
        return None#不是单文本
    块=内容[0]#那一块
    if 块['type']!='text':#不是文本
        return None#不是单文本
    return 块['text']#文本原文

def 有界单文本(内容,最大字节):#把单文本压进上限
    """把单文本块压进上限；非单文本则不动。"""
    文本=单文本原文(内容)#抽出原文
    if 文本 is None:#不是单文本则不动
        return None#不动
    return [{'type':'text','text':后缀适配(文本,'',最大字节,'\n[result truncated]')}]#截断后的文本块

def 可见输出上限(上下文,执行):#该次调用可见的输出上限
    """只约束 job_output 与 job_kill，按任务 id 查生产者上限。执行是 dict。"""
    工具名=执行['name']#工具名
    if 工具名!='job_output' and 工具名!='job_kill':#只约束这两工具
        return None#无上限
    参数=执行['arguments']#参数
    任务号=参数['job_id'] if 参数 is not None and 'job_id' in 参数 else None#参数里的任务id
    if (not isinstance(任务号,str)) or len(任务号)==0:#没有合法id
        return None#无上限
    智能体=执行['agent'] if 'agent' in 执行 else None#调用方智能体
    for 快照 in 上下文.jobs.列出(智能体):#可见任务
        if 快照['id']==任务号:#命中
            return 快照['outputLimitBytes'] if 'outputLimitBytes' in 快照 else None#该任务的上限
    return None#未找到

def 校验任务号(值):#校验并品牌化任务id
    """校验 ParameterSchemaSpec 表达不了的非空约束。"""
    if len(值)==0:#空字符串
        raise 工具任务错误('invalid job_id: expected a non-empty string, got '+json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False))#拒绝空id
    return 任务标识(值)#品牌化

def 呈现任务调用(标题,种类,原始输入=None):#通用卡片
    """三个通用任务控制共用的待决呈现。"""
    视图={'card':'generic','title':标题,'kind':种类}#标题与种类
    if 原始输入 is not None:#有原文
        视图['rawInput']=原始输入#带上原文
    return 视图#通用卡片

def 应用(上下文,配置值):#注册工具与完成投递
    """挂接控制器、完成投递、系统提示，并登记三个面向模型的任务工具。配置是 dict。"""
    等待缺省=配置值['waitTimeoutMs'] if 'waitTimeoutMs' in 配置值 else 30000#默认等待
    等待上限=配置值['maxWaitTimeoutMs'] if 'maxWaitTimeoutMs' in 配置值 else 600000#等待硬上限
    投递=配置值['completionDelivery'] if 'completionDelivery' in 配置值 else 'wakeup'#投递策略
    唤醒预算=配置值['maxConsecutiveWakes'] if 'maxConsecutiveWakes' in 配置值 else 3#连续唤醒预算
    已花唤醒=weakref.WeakKeyDictionary()#按精确Agent记已花唤醒
    if 等待缺省>等待上限:#默认大于硬上限
        raise 工具任务错误('tool-jobs: waitTimeoutMs ('+str(等待缺省)+') exceeds maxWaitTimeoutMs ('+str(等待上限)+')')#配置自相矛盾
    if isinstance(唤醒预算,bool):#布尔不是数字
        整数预算=False#非法
    elif isinstance(唤醒预算,int):#整数
        整数预算=True#合法形态
    elif isinstance(唤醒预算,float) and 唤醒预算.is_integer():#整值浮点
        整数预算=True#合法形态
    else:#其它类型
        整数预算=False#非法
    if not 整数预算:#不是整数回合
        raise 工具任务错误('tool-jobs: maxConsecutiveWakes ('+str(唤醒预算)+') must be a whole number of turns')#必须是整数
    唤醒预算=int(唤醒预算)#收窄为整型
    if 投递=='wakeup':#只有唤醒才记账
        def 认领收件箱(载荷,*位置参数):#认领收件箱
            """用户输入重置连续唤醒预算；插件通知不得回填。载荷是 dict。"""
            智能体=载荷['agent']#所有者
            消息=载荷['message']#认领消息
            来源=消息['source'] if 消息 is not None and 'source' in 消息 else None#消息来源
            if 来源 is not None and 来源['kind']=='user':#用户输入
                已花唤醒.pop(智能体,None)#重置预算
        上下文.监听('agent/inbox/claimed',认领收件箱)#结束认领监听
    输出上限表=weakref.WeakKeyDictionary()#按执行记下上限
    def 预执行(执行,下一步,*位置参数):#执行前记下可见上限
        """插到 tools/pre-execute 链前，记下本次可见上限。"""
        最大字节=可见输出上限(上下文,执行)#该次调用的上限
        if 最大字节 is not None:#有则记账
            输出上限表[执行]=最大字节#记下
        return 下一步()#继续瀑布
    上下文.监听('tools/pre-execute',预执行,{'前置':True})#插到链前
    def 收口任务内容(执行,结果):#按上限收口内容
        """按记下的或现查的上限收口工具可见内容。执行与结果都是 dict。"""
        最大字节=输出上限表[执行] if 执行 in 输出上限表 else None#记下的上限
        if 最大字节 is None:#没有记下
            最大字节=可见输出上限(上下文,执行)#现查
        if 执行 in 输出上限表:#用过即丢
            del 输出上限表[执行]#丢掉
        if 最大字节 is None:#没有上限则不动
            return None#不动
        if 执行['name']=='job_output' and (not 结果['isError']):#成功的job_output
            值=结果['value']#规范输出
            文本=值['text']#输出文本
            正文=文本 if len(文本)>0 else '(no new output)'#正文或占位
            if 正文.endswith('\n'):#末尾换行
                内容=正文[0:-1]#去掉末尾换行
            else:#无末尾换行
                内容=正文#原样
            后缀='\n'+状态行(值['job'])#状态行后缀
            if 单文本原文(结果['content'] if 'content' in 结果 else None)==(内容+后缀):#仍是默认渲染
                return [{'type':'text','text':后缀适配(内容,后缀,最大字节,'\n[output truncated]')}]#按上限重切
        return 有界单文本(结果['content'] if 'content' in 结果 else None,最大字节)#其余按单文本截断
    上下文.jobs.挂接控制器('tool-jobs')#挂接本插件控制器
    上下文.systemPrompt.段落({#系统提示段
        'name':'tool:jobs',#段名
        'order':106,#排在bash之后
        'text':'Track every background job id you start. You are notified in-session when a job finishes — do not busy-poll or sleep on one; keep working on independent steps and do not duplicate a running job\'s work. Before giving a final answer, collect every still-relevant job with job_output (set wait: true only when you are genuinely blocked on it), and job_kill jobs that stopped mattering.',#面向模型的用法
    })#系统提示段结束
    def 任务完成(快照,所有者):#完成投递
        """未报告的完成投递给所有者：空闲且预算未尽则唤醒，否则注入。快照是 dict，所有者是智能体对象。"""
        if 快照['reported'] or 所有者 is None:#已报告或无主则不投
            return#不投
        消息=创建用户消息({#插件通知消息
            'content':[{#文本块
                'type':'text',#文本
                'text':适配完成通知(快照),#压进上限的通知
            }],#内容结束
            'source':{#来源
                'kind':'plugin',#插件
                'plugin':'tool-jobs',#本插件
                'form':'notice',#通知形态
                'summary':完成摘要(快照),#折叠行摘要
            },#来源结束
        })#消息结束
        已花=已花唤醒[所有者] if 所有者 in 已花唤醒 else 0#已花唤醒次数
        if 投递=='wakeup' and 所有者.status=='idle' and 已花<唤醒预算:#空闲且预算未尽
            已花唤醒[所有者]=已花+1#花一次唤醒
            所有者.后续(消息)#开一个回合
            return#已唤醒则不再注入
        所有者.注入(消息)#注入下一步
    上下文.jobs.任务完成时(任务完成)#结束完成投递
    def 渲染输出(_参数,值):#渲染给模型
        """正文加状态行。值是 dict。"""
        文本=值['text']#输出文本
        正文=文本 if len(文本)>0 else '(no new output)'#正文或占位
        分隔='' if 正文.endswith('\n') else '\n'#避免双换行
        return [{'type':'text','text':正文+分隔+状态行(值['job'])}]#正文加状态行
    def 执行输出(参数,执行):#执行读取
        """校验后可选等待，再读输出。参数与执行都是 dict。"""
        标识=校验任务号(参数['job_id'])#校验任务id
        智能体=执行['agent'] if 'agent' in 执行 else None#调用方
        if 'wait' in 参数 and 参数['wait'] is True:#请求等待
            超时毫秒=参数['timeout_ms'] if 'timeout_ms' in 参数 else None#模型给的超时
            if 超时毫秒 is None:#未给
                超时毫秒=等待缺省#用默认
            超时=min(超时毫秒,等待上限)#钳到硬上限
            信号=执行['signal'] if 'signal' in 执行 else None#工具取消
            上下文.jobs.等待(标识,超时,智能体,信号)#等到结算或超时
        读取=上下文.jobs.读取(标识,智能体)#读取输出
        return {'text':读取['text'],'job':公开任务(读取['snapshot'])}#文本加公开快照
    def 呈现输出(参数):#读卡片
        """job_output 待决卡片。"""
        return 呈现任务调用('Read output from background job '+str(参数['job_id']),'read',参数['job_id'])#读卡片
    公开任务必填=dict(公开任务模式)#拷贝公开模式
    公开任务必填['required']=True#必填标记
    上下文.tools.登记(定义工具({#注册job_output
        'name':'job_output',#工具名
        'description':('Read a background job. Stream jobs return only output since the previous read; '#读后台任务
            +'final-output jobs return their result after settlement. Every response ends with '#结算后给最终输出
            +'`[status: ...]`. Reads are non-blocking unless `wait: true`, which waits up to the configured cap.'),#wait才阻塞
        'parameters':{#参数
            'job_id':{'type':'string','required':True,'description':'Job id returned by the tool that started the background work.'},#任务id
            'wait':{'type':'boolean','description':'Block until the job reaches a terminal status or the timeout expires. A timed-out wait returns [status: running] and leaves the job alive.'},#是否等待
            'timeout_ms':{'type':'number','description':'Max wait in milliseconds (only meaningful with wait: true). Defaults to the configured wait timeout; capped by the configured maximum.'},#等待毫秒
        },#parameters结束
        'finalizeContent':收口任务内容,#按上限收口
        'output':{#输出
            'schema':{#输出模式
                'type':'object',#对象
                'additionalProperties':False,#禁止额外字段
                'properties':{#字段
                    'text':{'type':'string','required':True},#输出文本
                    'job':公开任务必填,#公开快照
                },#properties结束
            },#schema结束
            'render':渲染输出,#渲染给模型
        },#output结束
        'execute':执行输出,#执行读取
        'presentCall':呈现输出,#读卡片
    }))#job_output结束
    def 渲染列表(_参数,任务列表):#渲染给模型
        """空列表占位或一行一条。"""
        if len(任务列表)==0:#没有任务
            文本='(no background jobs)'#空列表占位
        else:#有任务
            行列表=[]#行缓冲
            for 条 in 任务列表:#逐条
                行列表.append(str(条['id'])+' ['+str(条['kind'])+'] '+str(条['status'])+' — '+str(条['label']))#一行一条
            文本='\n'.join(行列表)#拼行
        return [{'type':'text','text':文本}]#文本块
    def 执行列表(_参数,执行):#执行列表
        """列出可见任务并投影公开快照。"""
        智能体=执行['agent'] if 'agent' in 执行 else None#调用方
        任务列表=上下文.jobs.列出(智能体)#可见任务
        投影=[]#公开快照列表
        for 条 in 任务列表:#逐条
            投影.append(公开任务(条))#投影
        return 投影#投影公开快照
    def 呈现列表(_参数=None):#列表卡片
        """job_list 待决卡片。"""
        return 呈现任务调用('List background jobs','read')#列表卡片
    上下文.tools.登记(定义工具({#注册job_list
        'name':'job_list',#工具名
        'description':'List your background jobs (running and finished) with their ids, kinds, and statuses.',#列后台任务
        'parameters':{},#无参数
        'output':{#输出
            'schema':{'type':'array','items':公开任务模式},#公开快照数组
            'render':渲染列表,#渲染给模型
        },#output结束
        'execute':执行列表,#执行列表
        'presentCall':呈现列表,#列表卡片
    }))#job_list结束
    def 渲染终止(_参数,值):#渲染给模型
        """已结束或已请求取消文案。"""
        if 值['outcome']=='already-finished':#已经结束
            文本='job '+str(值['job']['id'])+' had already finished '+状态行(值['job'])#已结束文案
        else:#已请求取消
            文本='requested cancellation of job '+str(值['job']['id'])#已请求取消
        return [{'type':'text','text':文本}]#文本块
    def 执行终止(参数,执行):#执行取消
        """请求取消并返回非消费公开快照。"""
        标识=校验任务号(参数['job_id'])#校验任务id
        智能体=执行['agent'] if 'agent' in 执行 else None#调用方
        原因=参数['reason'] if 'reason' in 参数 else None#可选原因
        结果=上下文.jobs.终止(标识,智能体,原因)#请求取消
        快照=公开任务(上下文.jobs.获取(标识,智能体))#非消费快照
        if 结果=='already-finished':#已经结束
            结局='already-finished'#已结束
        else:#已请求取消
            结局='cancellation-requested'#已请求
        return {'outcome':结局,'job':快照}#工具结果
    def 呈现终止(参数):#取消卡片
        """job_kill 待决卡片。"""
        return 呈现任务调用('Kill background job '+str(参数['job_id']),'execute',参数['job_id'])#取消卡片
    上下文.tools.登记(定义工具({#注册job_kill
        'name':'job_kill',#工具名
        'description':'Request cancellation of a running background job by job id. Returns immediately; the job settles as killed once its work actually stops.',#请求取消
        'parameters':{#参数
            'job_id':{'type':'string','required':True,'description':'Job id returned by the tool that started the background work.'},#任务id
            'reason':{'type':'string','description':'Optional short reason, recorded in the log and forwarded to the job.'},#可选原因
        },#parameters结束
        'finalizeContent':收口任务内容,#按上限收口
        'output':{#输出
            'schema':{#输出模式
                'type':'object',#对象
                'additionalProperties':False,#禁止额外字段
                'properties':{#字段
                    'outcome':{#取消结果
                        'type':'string',#字符串
                        'required':True,#必填
                        'enum':['cancellation-requested','already-finished'],#两种结局
                    },#outcome结束
                    'job':公开任务必填,#公开快照
                },#properties结束
            },#schema结束
            'render':渲染终止,#渲染给模型
        },#output结束
        'execute':执行终止,#执行取消
        'presentCall':呈现终止,#取消卡片
    }))#job_kill结束

__all__=[#仅中文公开名
    '公开任务模式','配置','完成投递','工具任务错误','应用',
]#公开面结束
name='tool-jobs'#框架插件名
inject=['tools','jobs','systemPrompt']#依赖工具、任务、系统提示
Config=配置#框架配置模式
apply=应用#框架插件入口
default=应用#框架默认导出
