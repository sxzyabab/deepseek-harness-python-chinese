"""面向模型的 job_output、job_list、job_kill 工具，架在 ctx.jobs 上。加载本插件会挂接生产者所需的控制器。它还把未报告的完成投递给所属智能体：忙着的所有者注入其下一步，空闲的在默认 wakeup 投递下开一个回合，并按所有者设上限。"""
import json,weakref#JSON片段与弱键字典
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 路径上节点,数字字段,枚举字段#配置字段
已兑现=cordis.工具.已兑现#立刻兑现
是否thenable=cordis.工具.是否thenable#可等待判定
from ..工具 import 定义工具#定义面向模型的工具
from ..llm import 截上下文摘要,创建用户消息#摘要与用户消息
from ..输出保留 import 文本保留器#头尾文本保留器
from ..任务 import 任务标识#任务id品牌化

名称='tool-jobs'#Cordis插件名
注入=['tools','jobs','systemPrompt']#依赖工具、任务、系统提示
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
配置=路径上节点({#有界等待与完成投递配置
    'waitTimeoutMs':数字字段(最小=1,默认值=30000),#默认等待30秒
    'maxWaitTimeoutMs':数字字段(最小=1,默认值=600000),#硬上限10分钟
    'completionDelivery':枚举字段('quiet','wakeup',默认值='wakeup'),#默认唤醒
    'maxConsecutiveWakes':数字字段(最小=1,默认值=3),#默认连续3次
})#配置模式结束
Config=配置#Cordis配置模式
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

__all__=[#仅中文公开名；Cordis 槽英文别名不入表
    '名称','注入','配置','公开任务模式','取字段','解开','应用','默认',
]#公开面结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 缺席(对象,键):#字段是否缺席
    """对齐字段 === undefined。"""
    if 对象 is None:#空对象
        return True#缺席
    if isinstance(对象,dict):#映射
        return 键 not in 对象#无键则缺席
    return not hasattr(对象,键)#无属性则缺席

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 是否安全整数(值):#对齐JS Number.isSafeInteger
    """对齐 JS Number.isSafeInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是安全整数
    if isinstance(值,int):#整数
        return -(2**53)<值<(2**53)#在安全整数范围内
    if isinstance(值,float):#浮点
        return 值.is_integer() and abs(值)<=(2**53-1)#整值且在范围内
    return False#其它类型

def 字节长(文本):#UTF-8字节长度
    """对齐 TextEncoder.encode(...).byteLength。"""
    return len(文本.encode('utf-8'))#按utf8计

def 公开任务(快照):#投影公开快照
    """从注册表快照去掉任务所有权与通知记账。"""
    结果={#面向模型的字段
        'id':取字段(快照,'id'),#任务id
        'kind':取字段(快照,'kind'),#种类
        'label':取字段(快照,'label'),#标签
        'status':取字段(快照,'status'),#状态
        'startedAt':取字段(快照,'startedAt'),#开始时间
    }#骨架
    if not 缺席(快照,'detail'):#有细节才带
        结果['detail']=取字段(快照,'detail')#细节
    if not 缺席(快照,'finishedAt'):#有结束才带
        结果['finishedAt']=取字段(快照,'finishedAt')#结束时间
    return 结果#公开快照

def 状态行(快照):#方括号状态行
    """渲染通用状态，可带生产者细节。"""
    if not 缺席(快照,'detail'):#有细节
        return '[status: '+str(取字段(快照,'status'))+', '+str(取字段(快照,'detail'))+']'#状态加细节
    return '[status: '+str(取字段(快照,'status'))+']'#只有状态

def 保留尾部(文本,最大字节):#保留尾部
    """按尾部策略压进字节上限。"""
    保留器=文本保留器({'kind':'tail','maxBytes':最大字节})#尾部保留器
    保留器.推入(文本)#喂入全文
    return 取字段(保留器.收尾(),'text')#截好的尾部

def 保留头部(文本,最大字节):#保留头部
    """按头部策略压进字节上限。"""
    保留器=文本保留器({'kind':'head','maxBytes':最大字节})#头部保留器
    保留器.推入(文本)#喂入全文
    return 取字段(保留器.收尾(),'text')#截好的头部

def 后缀适配(正文,后缀,最大字节,省略标记):#在上限内拼接内容与后缀
    """在上限内拼接内容与后缀。"""
    全文=正文+后缀#未截断全文
    if 最大字节 is None or 字节长(全文)<=最大字节:#未超上限则原样
        return 全文#原样
    固定=(('' if 正文.endswith(省略标记.lstrip()) else 省略标记)+后缀)#标记加后缀
    固定字节=字节长(固定)#固定部分字节
    if 固定字节>=最大字节:#固定部分已超则只留尾
        return 保留尾部(固定,最大字节)#只留尾
    return 保留尾部(正文,最大字节-固定字节)+固定#正文留尾再拼固定部分

def 完成摘要(快照):#完成摘要
    """notice 形态折叠行里，一条已结算任务的一行说明。"""
    return 截上下文摘要(取字段(快照,'kind')+' '+取字段(快照,'label')+' '+状态行(快照))#种类、标签、状态

def 适配完成通知(快照):#把完成通知压进上限
    """把完成通知压进生产者输出上限。"""
    前缀='background job '+str(取字段(快照,'id'))#通知前缀
    细节=' ('+str(取字段(快照,'kind'))+': '+str(取字段(快照,'label'))+') finished '+状态行(快照)#细节段
    动作='\nDone; job_output.'#动作提示
    全文=前缀+细节+'. Read its output with job_output.'#未截断全文
    最大字节=取字段(快照,'outputLimitBytes')#生产者上限
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
    """恰好一块文本时抽出原文，否则缺席。"""
    if 内容 is None or len(内容)!=1:#不是恰好一块
        return None#缺席
    块=内容[0]#那一块
    if 取字段(块,'type')!='text':#不是文本
        return None#缺席
    return 取字段(块,'text')#文本原文

def 有界单文本(内容,最大字节):#把单文本压进上限
    """把单文本块压进上限；非单文本则不动。"""
    文本=单文本原文(内容)#抽出原文
    if 文本 is None:#不是单文本则不动
        return None#不动
    return [{'type':'text','text':后缀适配(文本,'',最大字节,'\n[result truncated]')}]#截断后的文本块

def 可见输出上限(上下文,执行):#该次调用可见的输出上限
    """只约束 job_output 与 job_kill，按任务 id 查生产者上限。"""
    工具名=取字段(执行,'name')#工具名
    if 工具名!='job_output' and 工具名!='job_kill':#只约束这两工具
        return None#无上限
    参数=取字段(执行,'arguments')#参数
    任务号=取字段(参数,'job_id')#参数里的任务id
    if (not isinstance(任务号,str)) or len(任务号)==0:#没有合法id
        return None#无上限
    for 快照 in 上下文.jobs.列出(取字段(执行,'agent')):#可见任务
        if 取字段(快照,'id')==任务号:#命中
            return 取字段(快照,'outputLimitBytes')#该任务的上限
    return None#未找到

def 校验任务号(值):#校验并品牌化任务id
    """校验 ParameterSchemaSpec 表达不了的非空约束。"""
    if len(值)==0:#空字符串
        raise Exception('invalid job_id: expected a non-empty string, got '+json.dumps(值,ensure_ascii=False))#拒绝空id
    return 任务标识(值)#品牌化

def 呈现任务调用(标题,种类,原始输入=None):#通用卡片
    """三个通用任务控制共用的待决展示。"""
    视图={'card':'generic','title':标题,'kind':种类}#标题与种类
    if 原始输入 is not None:#有原文
        视图['rawInput']=原始输入#带上原文
    return 视图#通用卡片

def 应用(上下文,配置值):#注册工具与完成投递
    """挂接控制器、完成投递、系统提示，并登记三个面向模型的任务工具。"""
    等待缺省=取字段(配置值,'waitTimeoutMs')#默认等待
    if 等待缺省 is None:#未给出
        等待缺省=30000#默认30秒
    等待上限=取字段(配置值,'maxWaitTimeoutMs')#等待硬上限
    if 等待上限 is None:#未给出
        等待上限=600000#默认10分钟
    投递=取字段(配置值,'completionDelivery')#投递策略
    if 投递 is None:#未给出
        投递='wakeup'#默认唤醒
    唤醒预算=取字段(配置值,'maxConsecutiveWakes')#连续唤醒预算
    if 唤醒预算 is None:#未给出
        唤醒预算=3#默认3次
    已花唤醒=weakref.WeakKeyDictionary()#按精确Agent记已花唤醒
    if 等待缺省>等待上限:#默认大于硬上限
        raise Exception('tool-jobs: waitTimeoutMs ('+str(等待缺省)+') exceeds maxWaitTimeoutMs ('+str(等待上限)+')')#配置自相矛盾
    if not 是否安全整数(唤醒预算):#不是整数回合
        raise Exception('tool-jobs: maxConsecutiveWakes ('+str(唤醒预算)+') must be a whole number of turns')#必须是整数
    if 投递=='wakeup':#只有唤醒才记账
        def 认领收件箱(载荷,*剩余):#认领收件箱
            """用户输入重置连续唤醒预算；插件通知不得回填。"""
            智能体=取字段(载荷,'agent')#所有者
            消息=取字段(载荷,'message')#认领消息
            if 取字段(取字段(消息,'source'),'kind')=='user':#用户输入
                已花唤醒.pop(智能体,None)#重置预算
        上下文.on('agent/inbox/claimed',认领收件箱)#结束认领监听
    输出上限表=weakref.WeakKeyDictionary()#按执行记下上限
    def 预执行(执行,下一步,*剩余):#执行前记下可见上限
        """插到 tools/pre-execute 链前，记下本次可见上限。"""
        最大字节=可见输出上限(上下文,执行)#该次调用的上限
        if 最大字节 is not None:#有则记账
            输出上限表[执行]=最大字节#记下
        return 下一步()#继续瀑布
    上下文.on('tools/pre-execute',预执行,{'prepend':True})#插到链前
    def 收口任务内容(执行,结果):#按上限收口内容
        """按记下的或现查的上限收口工具可见内容。"""
        最大字节=输出上限表.get(执行)#记下的上限
        if 最大字节 is None:#没有记下
            最大字节=可见输出上限(上下文,执行)#现查
        输出上限表.pop(执行,None)#用过即丢
        if 最大字节 is None:#没有上限则不动
            return None#不动
        if 取字段(执行,'name')=='job_output' and (not 取字段(结果,'isError')):#成功的job_output
            值=取字段(结果,'value')#规范输出
            文本=取字段(值,'text')#输出文本
            正文=文本 if len(文本)>0 else '(no new output)'#正文或占位
            if 正文.endswith('\n'):#末尾换行
                内容=正文[0:-1]#去掉末尾换行
            else:#无末尾换行
                内容=正文#原样
            后缀='\n'+状态行(取字段(值,'job'))#状态行后缀
            if 单文本原文(取字段(结果,'content'))==(内容+后缀):#仍是默认渲染
                return [{'type':'text','text':后缀适配(内容,后缀,最大字节,'\n[output truncated]')}]#按上限重切
        return 有界单文本(取字段(结果,'content'),最大字节)#其余按单文本截断
    上下文.jobs.挂接控制器('tool-jobs')#挂接本插件控制器
    上下文.systemPrompt.段落({#系统提示段
        'name':'tool:jobs',#段名
        'order':106,#排在bash之后
        'text':'Track every background job id you start. You are notified in-session when a job finishes — do not busy-poll or sleep on one; keep working on independent steps and do not duplicate a running job\'s work. Before giving a final answer, collect every still-relevant job with job_output (set wait: true only when you are genuinely blocked on it), and job_kill jobs that stopped mattering.',#面向模型的用法
    })#系统提示段结束
    def 任务完成(快照,所有者):#完成投递
        """未报告的完成投递给所有者：空闲且预算未尽则唤醒，否则注入。"""
        if 取字段(快照,'reported') or 所有者 is None:#已报告或无主则不投
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
        已花=已花唤醒.get(所有者,0)#已花唤醒次数
        if 投递=='wakeup' and 取字段(所有者,'status')=='idle' and 已花<唤醒预算:#空闲且预算未尽
            已花唤醒[所有者]=已花+1#花一次唤醒
            所有者.后续(消息)#开一个回合
            return#已唤醒则不再注入
        所有者.注入(消息)#注入下一步
    上下文.jobs.任务完成时(任务完成)#结束完成投递
    def 渲染输出(_参数,值):#渲染给模型
        """正文加状态行。"""
        文本=取字段(值,'text')#输出文本
        正文=文本 if len(文本)>0 else '(no new output)'#正文或占位
        分隔='' if 正文.endswith('\n') else '\n'#避免双换行
        return [{'type':'text','text':正文+分隔+状态行(取字段(值,'job'))}]#正文加状态行
    def 执行输出(参数,执行上下文):#执行读取
        """校验后可选等待，再读输出。"""
        标识=校验任务号(取字段(参数,'job_id'))#校验任务id
        if 取字段(参数,'wait') is True:#请求等待
            超时毫秒=取字段(参数,'timeout_ms')#模型给的超时
            if 超时毫秒 is None:#未给
                超时毫秒=等待缺省#用默认
            超时=min(超时毫秒,等待上限)#钳到硬上限
            解开(上下文.jobs.等待(标识,超时,取字段(执行上下文,'agent'),取字段(执行上下文,'signal')))#等到结算或超时
        读取=上下文.jobs.读取(标识,取字段(执行上下文,'agent'))#读取输出
        return 已兑现({'text':取字段(读取,'text'),'job':公开任务(取字段(读取,'snapshot'))})#文本加公开快照
    def 呈现输出(参数):#读卡片
        """job_output 待决卡片。"""
        return 呈现任务调用('Read output from background job '+str(取字段(参数,'job_id')),'read',取字段(参数,'job_id'))#读卡片
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
    def 渲染列表(_参数,任务们):#渲染给模型
        """空列表占位或一行一条。"""
        if len(任务们)==0:#没有任务
            文本='(no background jobs)'#空列表占位
        else:#有任务
            行们=[]#行缓冲
            for 条 in 任务们:#逐条
                行们.append(str(取字段(条,'id'))+' ['+str(取字段(条,'kind'))+'] '+str(取字段(条,'status'))+' — '+str(取字段(条,'label')))#一行一条
            文本='\n'.join(行们)#拼行
        return [{'type':'text','text':文本}]#文本块
    def 执行列表(_参数,执行上下文):#执行列表
        """列出可见任务并投影公开快照。"""
        任务们=上下文.jobs.列出(取字段(执行上下文,'agent'))#可见任务
        投影=[]#公开快照列表
        for 条 in 任务们:#逐条
            投影.append(公开任务(条))#投影
        return 已兑现(投影)#投影公开快照
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
        if 取字段(值,'outcome')=='already-finished':#已经结束
            文本='job '+str(取字段(取字段(值,'job'),'id'))+' had already finished '+状态行(取字段(值,'job'))#已结束文案
        else:#已请求取消
            文本='requested cancellation of job '+str(取字段(取字段(值,'job'),'id'))#已请求取消
        return [{'type':'text','text':文本}]#文本块
    def 执行终止(参数,执行上下文):#执行取消
        """请求取消并返回非消费公开快照。"""
        标识=校验任务号(取字段(参数,'job_id'))#校验任务id
        结果=上下文.jobs.终止(标识,取字段(执行上下文,'agent'),取字段(参数,'reason'))#请求取消
        快照=公开任务(上下文.jobs.获取(标识,取字段(执行上下文,'agent')))#非消费快照
        if 结果=='already-finished':#已经结束
            结局='already-finished'#已结束
        else:#已请求取消
            结局='cancellation-requested'#已请求
        return 已兑现({'outcome':结局,'job':快照})#工具结果
    def 呈现终止(参数):#取消卡片
        """job_kill 待决卡片。"""
        return 呈现任务调用('Kill background job '+str(取字段(参数,'job_id')),'execute',取字段(参数,'job_id'))#取消卡片
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

apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出
完成投递=('quiet','wakeup')#完成投递策略联合
