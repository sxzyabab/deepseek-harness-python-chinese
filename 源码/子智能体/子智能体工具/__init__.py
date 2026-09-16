import threading#后台结算线程
from concurrent.futures import Future as 原生结果#单次操作结果
from ...依赖.cordis import 聚合错误#多失败聚合
from ...依赖.schemastery import 字符串字段,布尔字段,整数字段,列表字段,复合类型字段,常量字段,枚举字段,字典字段,自然数字段#配置字段
from ...内核.工具 import 定义工具#导入工具定义
from ..子智能体 import 断言子智能体最大深度,结算运行#深度断言与运行结算
from ..子智能体.错误 import 子智能体错误#缝内失败

名称='tool-subagent'#Cordis插件名
注入=['tools','subagents','systemPrompt']#依赖工具、子智能体与系统提示词
子智能体段落顺序=116.5#可续接委托指引段落顺序
配置入口上限=2**53-1#外来 JSON 配置的深度上限校验
配置={#部署配置：委托到哪个提供方以及子体默认值
    'provider':字符串字段(可空=False),#必填提供方名
    'toolName':字符串字段(默认值='subagent'),#默认工具名
    'enableRunInBackground':布尔字段(默认值=True),#默认允许后台
    'backgroundMode':枚举字段('one-shot','continuable',默认值='one-shot'),#默认一次性
    'agentOptions':字典字段({#智能体选项模式
        'provider':字符串字段(),#模型提供方
        'model':字符串字段(),#模型名
        'maxTokens':整数字段(默认值=1),#正整数token上限
    },默认值=None),#省略时保持未定义
    'persona':字符串字段(),#可选人格字符串
    'toolFilter':字典字段({#工具过滤模式
        'allow':列表字段(字符串字段(),默认值=None),#省略allow时不物化空数组
        'deny':列表字段(字符串字段(),默认值=None),#省略deny时不物化空数组
    },默认值=None),#省略整个过滤
    'maxDepth':复合类型字段(自然数字段(最大=配置入口上限),常量字段('provider-managed'),默认值=3),#默认深度3
}#配置模式结束

__all__=['名称','注入','配置','子智能体段落顺序','应用']#仅中文公开名

class 操作任务:
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身._原生结果=原生结果()#底层 Future

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身._原生结果.done():#尚未结算
            自身._原生结果.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身._原生结果.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._原生结果.set_exception(错误)#原样拒绝
            else:#非异常
                自身._原生结果.set_exception(子智能体错误(str(错误),'ERROR'))#包装拒绝

    def 等待(自身,超时=None):
        """阻塞等到结算。"""
        return 自身._原生结果.result(timeout=超时)#取结果或抛错

class 中止信号:
    """threading.Event 取消通道。"""
    def __init__(自身):
        """创建一条取消通道。"""
        自身._事件=threading.Event()#中止标志
        自身._异常=None#中止时抛出的异常

    def 触发(自身,原因=None):
        """标记中止。"""
        if 自身._事件.is_set():#只触发一次
            return#已触发
        if isinstance(原因,BaseException):#已是异常
            自身._异常=原因#承载
        elif 原因 is not None:#非异常
            自身._异常=子智能体错误(str(原因),'CANCELLED')#包装
        else:#无原因
            自身._异常=子智能体错误('aborted','CANCELLED')#默认
        自身._事件.set()#置位

class 中止控制器:
    """发出中止的控制器。"""
    def __init__(自身):
        """创建配套信号。"""
        自身.信号=中止信号()#本控制器的信号

    def 中止(自身,原因=None):
        """中止配套信号。"""
        自身.信号.触发(原因)#触发一次

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号._事件.is_set()#Event 置位

def 单路结算(动作):
    """等一路落定并收成 fulfilled/rejected 观察。"""
    try:#等待成功
        return {'status':'fulfilled','value':动作()}#兑现观察
    except BaseException as 错误:#失败
        return {'status':'rejected','reason':错误}#拒绝观察

def 输出值文本(值列表):
    """从权威JSON块数组渲染文本块，不信任任意值。块为 dict。"""
    文本列表=[]#收集文本
    for 值 in 值列表:#逐块
        if not isinstance(值,dict):#必须是对象
            continue#跳过
        if 'type' not in 值 or 值['type']!='text':#只要文本块
            continue#跳过
        if 'text' in 值 and isinstance(值['text'],str):#带字符串的text
            文本列表.append(值['text'])#收下
    return ''.join(文本列表)#拼接

def 结算启动(启动,信号):
    """结算尚未完成的启动，且不破坏任务生产者约定。启动为跑对象。"""
    结局任务=操作任务()#任务done
    def 监视结算():
        """把启动收成任务结局。"""
        try:#正常结算
            结局任务.兑现(结算运行(启动))#先得到运行再结算
        except BaseException as 错误:#启动失败
            if 已中止(信号) and not isinstance(错误,聚合错误):#中止且非聚合失败才记为killed
                结局任务.兑现({'status':'killed'})#中止结局
            else:#否则失败并带细节
                结局任务.兑现({'status':'failed','detail':str(错误)})#失败结局
    工作=threading.Thread(target=监视结算,daemon=True)#后台结算线程
    工作.start()#启动
    return 结局任务#交给任务收集器

def 停止原因错误(结果):
    """非 `completed` 的停止原因表示子体没有干净结束。结果为 dict。"""
    原因=结果['stopReason']#停止原因
    if 原因=='completed':#正常完成
        return None#不是错误
    if 原因=='aborted':#被取消
        return 'subagent run was cancelled'#取消文案
    if 原因=='error':#运行失败
        return 'subagent run failed'#失败文案
    if 原因=='max-tokens':#撞到token上限
        return 'subagent run hit its token limit before finishing'#上限文案
    if 原因=='refusal':#拒绝任务
        return 'subagent declined the task'#拒绝文案
    return 'subagent run ended abnormally ('+str(原因)+')'#异常结束文案

def 附带诊断与部分文本(错误,结果):
    """把提供方诊断与子体保留的部分回答追加到停止原因错误上。结果为 dict。"""
    if 'diagnostic' not in 结果 or 结果['diagnostic'] is None:#无诊断
        诊断=''#空诊断
    else:#有诊断
        诊断='\nDiagnostic: '+str(结果['diagnostic'])#诊断段
    输出=结果['output'] if 'output' in 结果 and 结果['output'] is not None else []#部分输出
    文本列表=[]#收集文本
    for 块 in 输出:#从输出块取文本
        if 'type' in 块 and 块['type']=='text':#只要文本块
            文本列表.append(块['text'] if 'text' in 块 and 块['text'] is not None else '')#取出文本
    文本=''.join(文本列表)#拼接
    if len(文本)==0:#无文本则无部分段
        部分=''#空部分
    else:#有文本
        部分='\nPartial output before the run ended:\n'+文本#部分输出段
    return 错误+诊断+部分#标题、诊断与部分文本

def 结算前台运行(运行):
    """收集并释放一次前台运行，不让拆除替换一次独立的结果失败。运行为对象。"""
    def 映射结果():
        """把子结果收成前台成功值或抛错。"""
        结果=运行.result.等待()#等待结果
        错误=停止原因错误(结果)#非完成则得到错误文案
        if 错误 is not None:#非干净完成
            raise 子智能体错误(附带诊断与部分文本(错误,结果),'RUN_FAILED')#带诊断与部分文本的错误
        return {#干净完成
            'kind':'foreground',#前台
            'runId':运行.id,#运行id
            'output':结果['output'],#快照为JSON值
        }#成功值结束
    执行=单路结算(映射结果)#先等结果，失败也收下
    拆除=单路结算(运行.销毁)#无论结果如何都销毁
    if 执行['status']=='rejected':#结果失败
        if 拆除['status']=='rejected':#拆除也失败
            raise 聚合错误(#两条诊断都保留
                [执行['reason'],拆除['reason']],#结果失败与拆除失败
                'subagent run failed: '+str(执行['reason'])+'; dispose failed: '+str(拆除['reason']),#聚合文案
            )#结束
        raise 执行['reason']#只抛结果失败
    if 拆除['status']=='rejected':#完成后拆除失败仍报错
        raise 拆除['reason']#抛拆除失败
    return 执行['value']#返回前台成功值

def 提供方措辞(继承会话):
    """由提供方的会话历史描述符得到面向模型的措辞。"""
    if 继承会话:#分叉/继承会话
        return {#继承会话措辞
            'description':(#工具描述
                'Delegate a task to a subagent that inherits this conversation: a child agent seeded with all '
                +'completed turns so far (it does not see the current in-flight turn). Use this when the subtask '
                +"builds on this conversation's context — a follow-up analysis, "
                +'a review, a continuation — without consuming this conversation\'s context for the work itself. '
                +'You receive its result, not its intermediate steps.'
            ),#描述结束
            'promptDescription':(#prompt参数说明
                "The task for the subagent. It already sees this conversation's completed turns, so build on them "
                +'freely and state only what is new.'
            ),#说明结束
        }#继承分支结束
    return {#全新会话措辞
        'description':(#工具描述
            'Delegate a self-contained task to a subagent (a separate agent that works in its own context) '
            +'to offload focused, independent work — research, a scoped '
            +'implementation, an analysis — so it does not consume this conversation\'s context. The subagent '
            +'returns its result, not its intermediate steps. Give it a '
            +'complete, standalone prompt: it does not see this conversation.'
        ),#描述结束
        'promptDescription':(#prompt参数说明
            'The complete, self-contained task for the subagent. It does not share this '
            +"conversation's context, so include everything it needs."
        ),#说明结束
    }#全新分支结束

def 解析委托运行(请求,选项):
    """把模型可选的调度请求解析成一条执行路线。请求与选项为 dict。"""
    if not 选项['backgroundEnabled']:#本实例关闭后台
        if 'run_in_background' in 请求 and 请求['run_in_background'] is True:#强制后台
            raise 子智能体错误('run_in_background is disabled for this tool instance (enableRunInBackground: false)','BACKGROUND_DISABLED')#拒绝强制后台
        return {'runInBackground':False}#只能前台
    if 'run_in_background' not in 请求 or 请求['run_in_background'] is None:#省略时
        后台=选项['continuable']#可续接默认后台，一次性默认前台
    else:#模型给出
        后台=请求['run_in_background']#模型可选后台
    return {'runInBackground':bool(后台)}#解析结束

def 应用(上下文,配置值,会话=None):
    """安装委托工具：镜像提供方生命周期登记工具，并在可续接后台时挂指引。

    配置为 dict。会话为直接 Agent 装配供给的未发布 Session（常驻组合省略）；
    本 Python 面尚未移植 modelSelectionSettings 路径，会话参数保留签名对齐。
    """
    _=会话#签名对齐；模型选择设置路径未移植时未使用
    最大深度=配置值['maxDepth'] if 'maxDepth' in 配置值 else None#读深度配置
    if 最大深度!='provider-managed':#数字上限当场校验
        断言子智能体最大深度(最大深度)#校验形态
    工具过滤=配置值['toolFilter'] if 'toolFilter' in 配置值 else None#读过滤
    if 工具过滤 is not None and ('allow' not in 工具过滤 or 工具过滤['allow'] is None) and ('deny' not in 工具过滤 or 工具过滤['deny'] is None):#空过滤
        raise 子智能体错误('tool-subagent: `toolFilter` is configured but names neither `allow` nor `deny` — remove the key or fill the filter','EMPTY_TOOL_FILTER')#空过滤失败
    后台启用=True#默认允许
    if 'enableRunInBackground' in 配置值 and 配置值['enableRunInBackground'] is False:#显式关闭
        后台启用=False#关闭后台
    后台模式=配置值['backgroundMode'] if 'backgroundMode' in 配置值 and 配置值['backgroundMode'] is not None else 'one-shot'#后台策略
    可续接=后台模式=='continuable'#是否可续接策略
    工具名=配置值['toolName'] if 'toolName' in 配置值 and 配置值['toolName'] is not None else 'subagent'#工具名
    提供方名=配置值['provider']#提供方名
    拆除工具=[None]#已登记工具的拆除
    def 挂载(提供方):
        """提供方出现时登记面向模型的委托工具。提供方为对象。"""
        能力=提供方.能力 if 提供方.能力 is not None else {}#提供方能力
        配置深度=配置值['maxDepth'] if 'maxDepth' in 配置值 else None#配置深度
        if (配置深度 is not None and 配置深度!='provider-managed'
            and ('depthLimit' not in 能力 or not 能力['depthLimit'])):#数字上限但无能力
            raise 子智能体错误(#挂载失败
                'tool-subagent: provider "'+提供方.名称+'" cannot enforce maxDepth (no depthLimit capability) — '
                +"set maxDepth: 'provider-managed' to leave the recursion budget to the provider",#文案
                'UNSUPPORTED_CAPABILITY',#码
            )#结束
        措辞=提供方措辞(bool(提供方.继承父上下文))#按是否继承会话选措辞
        if 可续接 and not hasattr(提供方,'准备可续跑'):#可续接策略但提供方不能准备
            raise 子智能体错误(#挂载失败
                'tool-subagent: provider "'+提供方.名称+'" does not support `backgroundMode: continuable`',#文案
                'UNSUPPORTED_CAPABILITY',#码
            )#结束
        if 后台启用:#基础描述加上后台策略后缀
            if 可续接:#可续接后缀
                描述后缀=' This tool runs in the background by default, immediately returns a durable subagent id, and keeps the child conversation available for later turns. When that run settles, the runtime sends the parent a notice containing its outcome and any final assistant message; `send_message` steers the child\'s nearest step while it is running and starts a turn while it is idle. Set `run_in_background: false` only when your next action depends on receiving the result.'#可续接说明
            else:#一次性后台
                描述后缀=' This call waits for the result by default. Set `run_in_background: true` to return a job id; collect with `job_output` and stop with `job_kill`.'#一次性后台说明
        else:#关闭后台时的说明
            描述后缀=' This call waits for the subagent and returns its result.'#前台说明
        参数表={#参数模式
            'description':{#短描述
                'type':'string',#字符串
                'required':True,#必填
                'description':'A short (3-5 word) description of the delegated task, for display.',#参数说明
            },#description结束
            'prompt':{#任务提示
                'type':'string',#字符串
                'required':True,#必填
                'description':措辞['promptDescription'],#随提供方变化的说明
            },#prompt结束
        }#参数骨架
        if 后台启用:#仅在允许后台时暴露该参数
            if 可续接:#可续接参数说明
                后台说明='Whether to run in the background and return a durable subagent id immediately. Defaults to true. Set false to wait for the result when your next action depends on it.'#可续接参数说明
            else:#一次性参数说明
                后台说明='Whether to run as a background job and return its id. Defaults to false; collect with job_output or stop with job_kill.'#一次性参数说明
            参数表['run_in_background']={#是否后台
                'type':'boolean',#布尔
                'description':后台说明,#按策略写说明
            }#run_in_background结束
        def 渲染(_参数,值):
            """按种类渲染委托结果。值为 dict。"""
            种类=值['kind']#结果种类
            if 种类=='background':#一次性后台
                文本='started background subagent job '+str(值['jobId'])#一次性后台
            elif 种类=='continuable':#可续接
                文本='started subagent '+str(值['subagentId'])#可续接后台
            else:#前台抽出文本
                文本=输出值文本(值['output'] if 'output' in 值 and 值['output'] is not None else [])#前台文本
            return [{'type':'text','text':文本}]#单个文本块
        def 可并行():
            """子体从不改父会话；唯一的父拥有写入是同步可交换插入。"""
            return True#可并行
        def 执行(参数,执行元数据):
            """按解析路线前台等待、一次性后台登记任务，或可续接立刻返回子体 id。参数与执行为 dict；父为智能体对象。"""
            if 'agent' not in 执行元数据 or 执行元数据['agent'] is None:#没有调用方
                raise 子智能体错误('subagent tool requires a calling agent (exec.agent was undefined)','NO_AGENT')#缺父失败
            父=执行元数据['agent']#调用方智能体
            配置深度=配置值['maxDepth'] if 'maxDepth' in 配置值 else None#配置深度
            请求={#启动子体请求
                'label':参数['description'],#展示用短描述
                'prompt':[{'type':'text','text':参数['prompt']}],#任务提示块
                'parent':父,#父智能体
            }#request骨架
            if 配置深度 is not None and 配置深度!='provider-managed':#有数字上限才写入
                请求['maxDepth']=配置深度#写入
            if 'agentOptions' in 配置值 and 配置值['agentOptions'] is not None:#有选项才展开
                请求['agentOptions']=配置值['agentOptions']#写入
            if 'persona' in 配置值 and 配置值['persona'] is not None:#有人格才展开
                请求['persona']=配置值['persona']#写入
            if 工具过滤 is not None:#有过滤才展开
                请求['toolFilter']=工具过滤#写入
            运行规格=解析委托运行(参数,{'backgroundEnabled':后台启用,'continuable':可续接})#解析执行路线
            if 运行规格['runInBackground']:#走后台
                if 可续接:#可续接后台
                    可续跑请求={#启动可续接子体
                        'provider':提供方名,#提供方名
                        'label':参数['description'],#展示标签
                        'request':请求,#启动请求
                    }#规格
                    if 'signal' in 执行元数据:#有信号
                        可续跑请求['signal']=执行元数据['signal']#写入
                    已启动=上下文.subagents.启动可续跑(可续跑请求)#启动
                    return {'kind':'continuable','subagentId':已启动['childId']}#立刻返回子体id
                任务服务=上下文.获取服务('jobs')#取任务运行时
                if 任务服务 is None:#未装任务能力
                    raise 子智能体错误('background jobs unavailable: load @deepseek-ai/dsh-jobs and @deepseek-ai/dsh-tool-jobs','JOBS_UNAVAILABLE')#缺任务运行时
                def 任务体():
                    """在 ctx.jobs 下拉起一次性后台子体。"""
                    控制器=中止控制器()#任务拥有的中止
                    启动请求=dict(请求)#复制启动请求
                    启动请求['signal']=控制器.信号#任务信号
                    启动=上下文.subagents.启动(提供方名,启动请求)#启动子运行
                    def 取消(原因=None):
                        """中止启动/运行。"""
                        控制器.中止(原因 if 原因 is not None else 'background subagent task killed')#中止
                    return {#任务句柄
                        'cancel':取消,#取消
                        'done':结算启动(启动,控制器.信号),#启动结算为任务结局
                    }#句柄结束
                编号=任务服务.启动({#登记父拥有的任务
                    'kind':'subagent',#任务种类
                    'label':参数['description'],#展示标签
                    'owner':父,#父智能体
                    'run':任务体,#任务体
                })#jobs.启动结束
                return {'kind':'background','jobId':编号}#立刻返回任务id
            前台请求=dict(请求)#复制
            if 'signal' in 执行元数据:#有信号
                前台请求['signal']=执行元数据['signal']#写入
            运行=上下文.subagents.启动(提供方名,前台请求)#前台启动并等待运行句柄
            return 结算前台运行(运行)#收集结果并释放
        拆除工具[0]=上下文.tools.登记(定义工具({#登记面向模型的委托工具
            'name':工具名,#工具名
            'description':措辞['description']+描述后缀,#基础描述加上后台策略后缀
            'parameters':参数表,#参数模式
            'output':{#返回值
                'schema':{#返回模式
                    'oneOf':[#三种成功形态
                        {#一次性后台
                            'type':'object',#对象
                            'additionalProperties':False,#禁止多余键
                            'properties':{#字段
                                'kind':{'type':'string','required':True,'const':'background'},#种类
                                'jobId':{'type':'string','required':True},#任务id
                            },#properties结束
                        },#background形态结束
                        {#可续接后台
                            'type':'object',#对象
                            'additionalProperties':False,#禁止多余键
                            'properties':{#字段
                                'kind':{'type':'string','required':True,'const':'continuable'},#种类
                                'subagentId':{'type':'string','required':True},#子体id
                            },#properties结束
                        },#continuable形态结束
                        {#前台
                            'type':'object',#对象
                            'additionalProperties':False,#禁止多余键
                            'properties':{#字段
                                'kind':{'type':'string','required':True,'const':'foreground'},#种类
                                'runId':{'type':'string','required':True},#运行id
                                'output':{'type':'array','required':True,'items':{'type':'json'}},#输出数组
                            },#properties结束
                        },#foreground形态结束
                    ],#oneOf结束
                },#schema结束
                'render':渲染,#渲染给模型的文本
            },#output结束
            'isConcurrencySafe':可并行,#前后台都可并行
            'execute':执行,#执行委托
        }))#register结束
    def 提供方出现(提供方):
        """本提供方且尚未挂载则挂载。提供方为对象。"""
        if 提供方.名称==提供方名 and 拆除工具[0] is None:#本提供方且尚未挂载
            挂载(提供方)#挂载
    def 提供方消失(名):
        """不是本提供方或未挂载则忽略。"""
        if 名!=提供方名 or 拆除工具[0] is None:#不是本提供方或未挂载
            return#忽略
        拆除工具[0]()#拆除工具
        拆除工具[0]=None#清空拆除器
    上下文.监听('subagent/provider-added',提供方出现)#provider-added结束
    上下文.监听('subagent/provider-removed',提供方消失)#provider-removed结束
    现存=上下文.subagents.取提供方(提供方名)#当前是否已有该提供方
    if 现存 is not None:#已经在
        挂载(现存)#立刻挂载
    else:#还没有
        上下文.日志.信息('subagent provider "'+提供方名+'" not registered yet; the "'+工具名+'" tool will register when it appears')#等待提供方
    if 后台启用 and 可续接:#可续接且允许后台才挂指引
        def 段落文本(上下文元):
            """工具未挂或当前作用域看不见则空文本。上下文元为 dict。"""
            if 拆除工具[0] is None:#工具未挂
                return ''#空文本，渲染时省略
            作用域=上下文元['scope'] if 'scope' in 上下文元 else None#作用域
            if 上下文.tools.获取(工具名,作用域) is None:#当前作用域看不见
                return ''#空文本，渲染时省略
            return ('Use '+工具名+' in the background by default. Start independent delegations together in one assistant message and continue useful work while they run. Set `run_in_background: false` only when your next action depends on that subagent\'s result. When a background run settles, the runtime sends you a notice containing its outcome and any final assistant message.')#模型可见指引
        上下文.systemPrompt.段落({#登记可续接用法指引
            'name':'tool:'+工具名,#按工具名分段
            'order':子智能体段落顺序,#固定顺序
            'text':段落文本,#动态文本
        })#section结束

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=应用#框架槽
