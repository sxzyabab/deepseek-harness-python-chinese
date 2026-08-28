"""经一个已配置的 `ctx.subagents` 提供方做面向模型的委托。提供方生命周期控制工具登记和随上下文变化的模式措辞。前台调用在收集后总是释放该次运行。后台策略由本插件配置选择：一次性调用拥有普通 Task，可续接调用走 `ctx.subagents.startContinuable()`。"""
import threading#后台结算线程
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 路径上节点,字符串字段,布尔字段,数字字段,整数字段,列表字段,复合类型字段,常量字段,枚举字段,自然数字段#配置字段
聚合错误=cordis.聚合错误#多失败聚合
承诺=cordis.工具.承诺#承诺
是否thenable=cordis.工具.是否thenable#可等待判定
from ...内核.工具 import 定义工具#导入工具定义
from ..子智能体 import 断言子智能体最大深度,结算运行#深度断言与运行结算

名称='tool-subagent'#Cordis插件名
注入=['tools','subagents','systemPrompt']#依赖工具、子智能体与系统提示词
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
子智能体段落顺序=116.5#可续接委托指引段落顺序
安全整数上限=2**53-1#对齐 Number.MAX_SAFE_INTEGER
配置=路径上节点({#部署配置：委托到哪个提供方以及子体默认值
    'provider':字符串字段(可空=False),#必填提供方名
    'toolName':字符串字段(默认值='subagent'),#默认工具名
    'enableRunInBackground':布尔字段(默认值=True),#默认允许后台
    'backgroundMode':枚举字段('one-shot','continuable',默认值='one-shot'),#默认一次性
    # 阻止 Schemastery 把省略的 agentOptions 物化成 `{}`。
    'agentOptions':路径上节点({#智能体选项模式
        'provider':字符串字段(),#模型提供方
        'model':字符串字段(),#模型名
        'maxTokens':整数字段(步进=1,最小=1,最大=安全整数上限),#正整数token上限
    },默认值=None),#省略时保持未定义
    'persona':字符串字段(),#可选人格字符串
    # 保留省略；Schemastery 的 `{ allow: [] }` 默认会拒绝全部工具。
    'toolFilter':路径上节点({#工具过滤模式
        'allow':列表字段(字符串字段(),默认值=None),#省略allow时不物化空数组
        'deny':列表字段(字符串字段(),默认值=None),#省略deny时不物化空数组
    },默认值=None),#省略整个过滤
    'maxDepth':复合类型字段(自然数字段(最大=安全整数上限),常量字段('provider-managed'),默认值=3),#默认深度3
})#配置模式结束
Config=配置#Cordis配置模式

__all__=[#仅中文公开名；Cordis 槽英文别名不入表
    '名称','注入','配置','子智能体段落顺序','安全整数上限',
    '中止控制器','取字段','解开','应用','默认',
]#公开面结束

class 中止控制器:#发出中止的控制器
    """对应 AbortController：一对控制器与信号。"""
    def __init__(自身):#创建配套信号
        """创建配套信号。"""
        自身.信号=_中止信号()#本控制器的信号
        自身.signal=自身.信号#AbortController协议
    def 中止(自身,原因=None):#中止配套信号
        """中止配套信号。"""
        自身.信号.触发(原因)#触发一次
    def abort(自身,原因=None):#AbortController.abort
        """AbortController.abort。"""
        自身.中止(原因)#委托中文入口

class _中止信号:#一次中止信号
    """对应 AbortSignal。"""
    def __init__(自身):#初始未中止
        """初始未中止。"""
        自身.aborted=False#英文旗标
        自身.已中止=False#中文旗标
        自身.reason=None#英文原因
        自身.原因=None#中文原因
    def 触发(自身,原因=None):#触发一次中止
        """触发一次中止。"""
        if 自身.aborted:#已中止
            return#幂等
        自身.aborted=True#英文旗标
        自身.已中止=True#中文旗标
        自身.reason=原因#英文原因
        自身.原因=原因#中文原因

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 是否已中止(信号):#读中止旗标
    """对齐 signal.aborted。"""
    if 信号 is None:#无信号
        return False#未中止
    if getattr(信号,'aborted',False):#英文字段
        return True#已中止
    return bool(getattr(信号,'已中止',False))#中文字段

def 单路结算(任务):#对齐单元素 Promise.allSettled
    """等一路落定并收成 fulfilled/rejected 观察。"""
    try:#等待成功
        return {'status':'fulfilled','value':解开(任务)}#兑现观察
    except BaseException as 错误:#失败
        return {'status':'rejected','reason':错误}#拒绝观察

def 输出值文本(值们):#抽出文本块并拼接
    """从权威JSON块数组渲染文本块，不信任任意值。"""
    文本们=[]#收集文本
    for 值 in 值们:#逐块
        if not isinstance(值,dict):#必须是对象
            continue#跳过
        if 取字段(值,'type')!='text':#只要文本块
            continue#跳过
        文本=取字段(值,'text')#取出文本
        if isinstance(文本,str):#带字符串的text
            文本们.append(文本)#收下
    return ''.join(文本们)#拼接

def 结算启动(启动,信号):#把启动承诺收成任务结局
    """结算尚未完成的启动，且不破坏任务生产者约定。"""
    结局承诺=承诺()#任务done
    def 盯结算():#等待启动再结算运行
        """把启动收成任务结局。"""
        try:#正常结算
            结局承诺.兑现(解开(结算运行(解开(启动))))#先得到运行再结算
        except BaseException as 错误:#启动失败
            if 是否已中止(信号):#若已中止则记为killed
                结局承诺.兑现({'status':'killed'})#中止结局
            else:#否则失败并带细节
                结局承诺.兑现({'status':'failed','detail':str(错误)})#失败结局
    工作=threading.Thread(target=盯结算)#后台结算线程
    工作.daemon=True#不挡住退出
    工作.start()#启动
    return 结局承诺#交给任务收集器

def 停止原因错误(结果):#把停止原因映射成错误文案
    """非 `completed` 的停止原因表示子体没有干净结束。"""
    原因=取字段(结果,'stopReason')#停止原因
    if 原因=='completed':#正常完成
        return None#不是错误
    if 原因=='aborted':#被取消
        return 'subagent run was cancelled'#取消文案（字面量不译）
    if 原因=='error':#运行失败
        return 'subagent run failed'#失败文案（字面量不译）
    if 原因=='max-tokens':#撞到token上限
        return 'subagent run hit its token limit before finishing'#上限文案（字面量不译）
    if 原因=='refusal':#拒绝任务
        return 'subagent declined the task'#拒绝文案（字面量不译）
    # 可合并扩展的联合：后端可能新增停止原因。把未知终端原因当失败，而不是把部分输出报成成功。
    return 'subagent run ended abnormally ('+str(原因)+')'#异常结束文案（字面量不译）

def 附带部分文本(错误,输出):#错误标题后附部分输出
    """把子体保留的部分回答追加到停止原因错误上，使截断或取消的子体真实文本仍到达父模型。"""
    文本们=[]#收集文本
    for 块 in 输出:#从输出块取文本
        if 取字段(块,'type')=='text':#只要文本块
            文本们.append(取字段(块,'text') or '')#取出文本
    文本=''.join(文本们)#拼接
    if len(文本)==0:#无文本则仅标题
        return 错误#仅标题
    return 错误+'\nPartial output before the run ended:\n'+文本#标题后附部分输出

def 结算前台运行(运行):#收集结果并总是dispose
    """收集并释放一次前台运行，不让拆除替换一次独立的结果失败。"""
    def 映射结果():#结果到达后映射
        """把子结果收成前台成功值或抛错。"""
        结果=解开(取字段(运行,'result'))#等待结果
        错误=停止原因错误(结果)#非完成则得到错误文案
        if 错误 is not None:#非干净完成
            # 注册表把这次抛出转成 isError；部分输出不是成功，但保留的部分回答仍到达父级。
            raise Exception(附带部分文本(错误,取字段(结果,'output') or []))#带部分文本的错误
        return {#干净完成
            'kind':'foreground',#前台
            'runId':取字段(运行,'id'),#运行id
            # 内容块在别处已经跨过持久JSON边界；注册表在此做权威无损快照。
            'output':取字段(结果,'output'),#快照为JSON值
        }#成功值结束
    执行=单路结算(映射结果())#先等结果，失败也收下
    拆除=单路结算(取字段(运行,'dispose')())#无论结果如何都dispose
    if 取字段(执行,'status')=='rejected':#结果失败
        if 取字段(拆除,'status')=='rejected':#拆除也失败
            raise 聚合错误(#两条诊断都保留
                [取字段(执行,'reason'),取字段(拆除,'reason')],#结果失败与拆除失败
                'subagent run failed: '+str(取字段(执行,'reason'))+'; dispose failed: '+str(取字段(拆除,'reason')),#聚合文案（字面量不译）
            )#AggregateError结束
        raise 取字段(执行,'reason')#只抛结果失败
    if 取字段(拆除,'status')=='rejected':#完成后拆除失败仍报错
        raise 取字段(拆除,'reason')#抛拆除失败
    return 取字段(执行,'value')#返回前台成功值

def 提供方措辞(继承会话):#按是否继承会话选措辞
    """由提供方的会话历史描述符得到面向模型的措辞。全新子体需要独立提示；分叉子体已经看见会话的已完成轮次。"""
    if 继承会话:#分叉/继承会话
        return {#继承会话措辞
            'description':(#工具描述（字面量不译）
                'Delegate a task to a subagent that inherits this conversation: a child agent seeded with all '#继承会话：已完成轮次播种
                +'completed turns so far (it does not see the current in-flight turn). Use this when the subtask '#看不见当前进行中轮次
                +"builds on this conversation's context — a follow-up analysis, "#适合跟进分析/续作
                +'a review, a continuation — without consuming this conversation\'s context for the work itself. '#不占父会话上下文
                +'You receive its result, not its intermediate steps.'#只收结果不收中间步骤
            ),#描述结束
            'promptDescription':(#prompt参数说明（字面量不译）
                "The task for the subagent. It already sees this conversation's completed turns, so build on them "#已见已完成轮次
                +'freely and state only what is new.'#只写新增部分
            ),#说明结束
        }#继承分支结束
    return {#全新会话措辞
        'description':(#工具描述（字面量不译）
            'Delegate a self-contained task to a subagent (a separate agent that works in its own context) '#全新独立会话委托
            +'to offload focused, independent work — research, a scoped '#卸载聚焦独立工作
            +'implementation, an analysis — so it does not consume this conversation\'s context. The subagent '#不占父会话上下文
            +'returns its result, not its intermediate steps. Give it a '#只收结果
            +'complete, standalone prompt: it does not see this conversation.'#须给完整独立提示
        ),#描述结束
        'promptDescription':(#prompt参数说明（字面量不译）
            'The complete, self-contained task for the subagent. It does not share this '#完整自包含任务
            +"conversation's context, so include everything it needs."#须自带全部所需上下文
        ),#说明结束
    }#全新分支结束

def 解析委托运行(请求,选项):#解析前台或后台
    """把模型可选的调度请求解析成一条执行路线。"""
    if not 取字段(选项,'backgroundEnabled'):#本实例关闭后台
        # 校验器允许未声明键，因此模式省略还需要执行时强制。
        if 取字段(请求,'run_in_background') is True:#强制后台
            raise Exception('run_in_background is disabled for this tool instance (enableRunInBackground: false)')#拒绝强制后台（字面量不译）
        return {'runInBackground':False}#只能前台
    后台=取字段(请求,'run_in_background')#模型可选后台
    if 后台 is None:#省略时
        # 可续接工作默认独立调度，除非调用方明确要在下一步之前拿到结果。一次性策略保持前台默认，因为其后台结果需要 Task 收集。
        后台=取字段(选项,'continuable')#可续接默认后台，一次性默认前台
    return {'runInBackground':bool(后台)}#解析结束

def 应用(上下文,配置值):#安装委托工具
    """安装委托工具：镜像提供方生命周期登记工具，并在可续接后台时挂指引。"""
    # 直接 apply() 会绕过 Schemastery 的数值约束。直接调用时省略保持无上限（模式默认只走加载器）。
    最大深度=取字段(配置值,'maxDepth')#读深度配置
    if 最大深度!='provider-managed':#数字上限当场校验
        断言子智能体最大深度(最大深度)#校验形态
    工具过滤=取字段(配置值,'toolFilter')#读过滤
    # 在加载时拒绝空的显式过滤，而不是让每次委托都失败。
    if 工具过滤 is not None and 取字段(工具过滤,'allow') is None and 取字段(工具过滤,'deny') is None:#空过滤
        raise Exception('tool-subagent: `toolFilter` is configured but names neither `allow` nor `deny` — remove the key or fill the filter')#空过滤失败（字面量不译）
    后台启用=取字段(配置值,'enableRunInBackground') is not False#未显式关闭则允许后台
    后台模式=取字段(配置值,'backgroundMode')#后台策略
    if 后台模式 is None:#省略
        后台模式='one-shot'#默认一次性
    可续接=后台模式=='continuable'#是否可续接策略
    工具名=取字段(配置值,'toolName')#工具名
    if 工具名 is None:#省略
        工具名='subagent'#默认subagent
    提供方名=取字段(配置值,'provider')#提供方名
    # 镜像提供方生命周期，因为兄弟加载顺序和 HMR 替换可能在本光纤仍活着时改变提供方是否存在。
    拆除工具=[None]#已登记工具的拆除（列表可变闭包）
    def 挂载(提供方):#按当前提供方登记工具
        """提供方出现时登记面向模型的委托工具。"""
        能力=取字段(提供方,'capabilities') or {}#提供方能力
        # 提供方无法执行的数字上限是错误配置——在挂载时失败（最早知道提供方能力的点），而不是第一次委托时。
        if isinstance(取字段(配置值,'maxDepth'),(int,float)) and not isinstance(取字段(配置值,'maxDepth'),bool) and not 取字段(能力,'depthLimit'):#数字上限但无能力
            raise Exception(#挂载失败
                'tool-subagent: provider "'+取字段(提供方,'name')+'" cannot enforce maxDepth (no depthLimit capability) — '#无 depthLimit 能力
                +"set maxDepth: 'provider-managed' to leave the recursion budget to the provider"#能力不足文案（字面量不译）
            )#Error结束
        措辞=提供方措辞(bool(取字段(提供方,'inheritsParentContext')))#按是否继承会话选措辞
        if 可续接 and 取字段(提供方,'prepareContinuable') is None:#可续接策略但提供方不能准备
            raise Exception(#挂载失败
                'tool-subagent: provider "'+取字段(提供方,'name')+'" does not support `backgroundMode: continuable`'#不支持可续接（字面量不译）
            )#Error结束
        if 后台启用:#基础描述加上后台策略后缀
            if 可续接:#可续接后缀
                # 完成通知是续接服务自身的行为，不是另装的能力，因此只要可续接后台路径可达，这条承诺就成立。
                描述后缀=' This tool runs in the background by default, immediately returns a durable subagent id, and keeps the child conversation available for later turns. When that run settles, the runtime sends the parent a notice containing its outcome and any final assistant message; `send_message` starts a later turn in the same child conversation. Set `run_in_background: false` only when your next action depends on receiving the result.'#可续接说明（字面量不译）
            else:#一次性后台
                描述后缀=' This call waits for the result by default. Set `run_in_background: true` to return a job id; collect with `job_output` and stop with `job_kill`.'#一次性后台说明（字面量不译）
        else:#关闭后台时的说明
            描述后缀=' This call waits for the subagent and returns its result.'#前台说明（字面量不译）
        参数表={#参数模式
            'description':{#短描述
                'type':'string',#字符串
                'required':True,#必填
                'description':'A short (3-5 word) description of the delegated task, for display.',#参数说明（字面量不译）
            },#description结束
            'prompt':{#任务提示
                'type':'string',#字符串
                'required':True,#必填
                'description':取字段(措辞,'promptDescription'),#随提供方变化的说明
            },#prompt结束
        }#参数骨架
        if 后台启用:#仅在允许后台时暴露该参数
            if 可续接:#可续接参数说明
                后台说明='Whether to run in the background and return a durable subagent id immediately. Defaults to true. Set false to wait for the result when your next action depends on it.'#可续接参数说明（字面量不译）
            else:#一次性参数说明
                后台说明='Whether to run as a background job and return its id. Defaults to false; collect with job_output or stop with job_kill.'#一次性参数说明（字面量不译）
            参数表['run_in_background']={#是否后台
                'type':'boolean',#布尔
                'description':后台说明,#按策略写说明
            }#run_in_background结束
        def 渲染(_参数,值):#渲染给模型的文本
            """按种类渲染委托结果。"""
            种类=取字段(值,'kind')#结果种类
            if 种类=='background':#一次性后台
                文本='started background subagent task '+str(取字段(值,'jobId'))#一次性后台（字面量不译）
            elif 种类=='continuable':#可续接
                文本='started subagent '+str(取字段(值,'subagentId'))#可续接后台（字面量不译）
            else:#前台抽出文本
                文本=输出值文本(取字段(值,'output') or [])#前台文本
            return [{'type':'text','text':文本}]#单个文本块
        def 可并行():#前后台都可并行
            """子体从不改父会话；唯一的父拥有写入（tasks.start）是同步可交换插入。"""
            return True#可并行
        def 执行(参数,执行元数据):#执行委托
            """按解析路线前台等待、一次性后台登记任务，或可续接立刻返回子体 id。"""
            父=取字段(执行元数据,'agent')#调用方智能体
            if 父 is None:#没有调用方
                # 非智能体调用方不能提供委托所有权的父。
                raise Exception('subagent tool requires a calling agent (exec.agent was undefined)')#缺父失败（字面量不译）
            配置深度=取字段(配置值,'maxDepth')#配置深度
            if isinstance(配置深度,(int,float)) and not isinstance(配置深度,bool):#仅数字上限才写入请求
                请求深度=配置深度#数字上限
            else:#交由提供方管理
                请求深度=None#不写入
            请求={#启动子体请求
                'label':取字段(参数,'description'),#展示用短描述
                'prompt':[{'type':'text','text':取字段(参数,'prompt')}],#任务提示块
                'parent':父,#父智能体
            }#request骨架
            智能体选项=取字段(配置值,'agentOptions')#子体智能体选项
            if 智能体选项 is not None:#有选项才展开
                请求['agentOptions']=智能体选项#写入
            人格=取字段(配置值,'persona')#可选人格
            if 人格 is not None:#有人格才展开
                请求['persona']=人格#写入
            if 工具过滤 is not None:#有过滤才展开
                请求['toolFilter']=工具过滤#写入
            if 请求深度 is not None:#有数字上限才展开
                请求['maxDepth']=请求深度#写入
            运行规格=解析委托运行(参数,{'backgroundEnabled':后台启用,'continuable':可续接})#解析执行路线
            if 取字段(运行规格,'runInBackground'):#走后台
                if 可续接:#可续接后台
                    # 在收件箱接受时决议：此后子体拥有自己的轮次，本调用既不等待也不收集结果。
                    已启动=解开(上下文.subagents.启动可续跑({#启动可续接子体
                        'provider':提供方名,#提供方名
                        'label':取字段(参数,'description'),#展示标签
                        'request':请求,#启动请求
                        'signal':取字段(执行元数据,'signal'),#工具中止信号
                    }))#startContinuable结束
                    return {'kind':'continuable','subagentId':取字段(已启动,'childId')}#立刻返回子体id
                任务们=上下文.get('jobs')#取任务运行时
                if 任务们 is None:#未装任务能力
                    raise Exception('background jobs unavailable: load @deepseek-ai/dsh-jobs and @deepseek-ai/dsh-tool-jobs')#缺任务运行时（字面量不译）
                # 一次性后台子体：任务预检在启动器能孵化之前完成，任务拥有的信号覆盖启动。
                def 任务体():#任务体
                    """在 ctx.jobs 下拉起一次性后台子体。"""
                    控制器=中止控制器()#任务拥有的中止
                    启动=上下文.subagents.启动(提供方名,{**请求,'signal':控制器.信号})#启动子运行
                    def 取消(原因=None):#取消
                        """中止启动/运行。"""
                        控制器.中止(原因 if 原因 is not None else 'background subagent task killed')#中止（字面量不译）
                    return {#任务句柄
                        'cancel':取消,#取消
                        'done':结算启动(启动,控制器.信号),#启动结算为任务结局
                        # 无 readOutput：中间细节由子会话拥有。
                    }#句柄结束
                编号=任务们.start({#登记父拥有的任务
                    'kind':'subagent',#任务种类
                    'label':取字段(参数,'description'),#展示标签
                    'owner':父,#父智能体
                    'run':任务体,#任务体
                })#jobs.start结束
                return {'kind':'background','jobId':编号}#立刻返回任务id
            运行=解开(上下文.subagents.启动(提供方名,{#前台启动并等待运行句柄
                **请求,#启动请求
                'signal':取字段(执行元数据,'signal'),#工具中止信号
            }))#start结束
            return 结算前台运行(运行)#收集结果并释放
        拆除工具[0]=上下文.tools.register(定义工具({#登记面向模型的委托工具
            'name':工具名,#工具名
            'description':取字段(措辞,'description')+描述后缀,#基础描述加上后台策略后缀
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
    # 先登记监听再检查是否已在，以免漏掉同步变化。
    # TODO(subagent-dup-toolname): two waiting one-shot fibers configured with the
    # same toolName collide when their provider appears, and the duplicate-name
    # throw rolls back the provider registration. Continuable instances reserve
    # their prompt-section name during apply() and fail earlier. Add an intent
    # registry if the late one-shot collision occurs in a shipped composition.
    def 提供方出现(提供方):#提供方出现
        """本提供方且尚未挂载则挂载。"""
        if 取字段(提供方,'name')==提供方名 and 拆除工具[0] is None:#本提供方且尚未挂载
            挂载(提供方)#挂载
    def 提供方消失(名):#提供方消失
        """不是本提供方或未挂载则忽略。"""
        if 名!=提供方名 or 拆除工具[0] is None:#不是本提供方或未挂载
            return#忽略
        拆除工具[0]()#拆除工具
        拆除工具[0]=None#清空拆除器
    上下文.on('subagent/provider-added',提供方出现)#provider-added结束
    上下文.on('subagent/provider-removed',提供方消失)#provider-removed结束
    现存=上下文.subagents.getProvider(提供方名)#当前是否已有该提供方
    if 现存 is not None:#已经在
        挂载(现存)#立刻挂载
    else:#还没有
        # 后端光纤可能稍后激活；拼错的提供方仍会出现在这条日志里。
        上下文.logger.info('subagent provider "'+提供方名+'" not registered yet; the "'+工具名+'" tool will register when it appears')#等待提供方（字面量不译）
    if 后台启用 and 可续接:#可续接且允许后台才挂指引
        # 该段落跟随提供方是否存在，无需自己的手工生命周期：工具不在时空文本会从渲染提示词省略，登记本身仍由本插件光纤拥有。
        def 段落文本(上下文元):#按工具是否可见生成指引
            """工具未挂或当前作用域看不见则空文本。"""
            if 拆除工具[0] is None:#工具未挂
                return ''#空文本，渲染时省略
            if 上下文.tools.get(工具名,取字段(上下文元,'scope')) is None:#当前作用域看不见
                return ''#空文本，渲染时省略
            return ('Use '+工具名+' in the background by default. Start independent delegations together in one assistant message and continue useful work while they run. Set `run_in_background: false` only when your next action depends on that subagent\'s result. When a background run settles, the runtime sends you a notice containing its outcome and any final assistant message.')#模型可见指引（字面量不译）
        上下文.systemPrompt.section({#登记可续接用法指引
            'name':'tool:'+工具名,#按工具名分段
            'order':子智能体段落顺序,#固定顺序
            'text':段落文本,#动态文本
        })#section结束

apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出
