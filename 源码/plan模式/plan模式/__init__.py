"""计划模式是按智能体记录的协作状态：激活时，每次模型请求都会带上部署方拥有的指导段落，`exit_plan_mode` 把完成的计划交给用户审阅，`/plan off` 则让用户直接离开。沙箱模式与审批策略各自独立执行限制，不读不写计划状态。

当前生效状态由会话日志折叠而来（`plan/mode`，最后一条胜出），因此恢复与分叉无需实时镜像即可还原。用户选择保持待定，直到下一个被接受的回合内 pre-step。服务把所选状态纳入提议的步骤组装，再仅在步骤被接受时从 `agent/pre-step` 追加 `plan/mode`。同一步的请求重试复用其组装。

退出工具在计划模式未激活时仍保持注册，因此进入或离开计划模式只改提示词段落，不改请求的工具目录。
"""
import re,weakref#标题匹配与会话弱表
from cordis import 服务#Cordis 服务基类
from cordis.工具 import 已兑现,是否thenable#立刻兑现与可等待判定
from llm import 创建用户消息#铸造用户消息
from tools import 定义工具#定义工具
from user_questions import 用户提问错误#用户提问通道错误
from .类型 import 计划投影字段,计划投影#再导出计划域纯类型

退出计划模式='exit_plan_mode'#退出计划模式的工具名
审阅标识='plan-review'#审阅问题的 id
批准标签='Approve'#审阅问题的批准选项标签
继续规划标签='Keep planning'#审阅问题的继续规划选项标签
退出说明=('Use only in plan mode. Present your plan for the user\'s review and, on approval, leave plan mode. '#仅计划模式可用；批准后离开
    +'Send the COMPLETE plan as markdown, starting with a # heading that names it. '#完整 markdown，以标题起头
    +'The user may approve (carry out the plan from your next step) or keep '#用户可批准或继续规划
    +'planning — their feedback comes back in the tool result; revise and present again.')#反馈经工具结果回来
标题行=re.compile(r'^#{1,6}\s+(.+?)\s*$')#匹配 ATX 标题
首级标题起头=re.compile(r'^#\s+\S')#必须以非空 # 标题起头
计划投影模式={#`plan` 投影的线上载荷模式
    'type':'object',#对象
    'additionalProperties':False,#禁多余键
    'properties':{#字段
        'active':{'type':'boolean'},#已提交状态
        'pending':{'type':'boolean'},#是否有未决选择
    },#字段结束
    'required':['active','pending'],#两字段必填
}#模式结束

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

def 配置键列表(配置):#对齐 Object.keys
    """列出配置自有键。"""
    if isinstance(配置,dict):#映射
        return list(配置.keys())#映射键
    字典=getattr(配置,'__dict__',None)#实例字典
    if 字典 is None:#没有字典
        return []#无键
    return [键 for 键 in 字典 if not str(键).startswith('_')]#自有非私有键

def 首条标题(计划):#抽出第一条标题文本
    """计划的第一条 markdown 标题（任意级别）；没有则 None。"""
    for 行 in 计划.split('\n'):#逐行扫
        匹配=标题行.match(行)#匹配 ATX 标题
        if 匹配 is not None:#命中
            return 匹配.group(1)#捕获组是标题文本
    return None#没有标题

def 解析配置(配置):#加载时校验配置
    """校验部署方拥有的计划指导。缺失、空白、非字符串或未知字段在插件加载时失败，而不是被忽略。"""
    段落=取字段(配置,'section')#可能缺席的 section
    if not isinstance(段落,str):#必须是字符串
        raise Exception('PlanModeConfig needs a string `section`')#缺或非字符串
    if 段落.strip()=='':#空白也不行
        raise Exception('PlanModeConfig needs a non-empty `section`')#空指导
    未知=[键 for 键 in 配置键列表(配置) if 键!='section']#除 section 以外的键
    if len(未知)>0:#有未知键
        raise Exception('PlanModeConfig has unknown key(s) '+', '.join(未知)+' — config is { section }')#大声失败
    return {'section':段落}#已校验的脱离副本

def 折叠计划模式(事件们,终点=None):#折叠已记录计划模式
    """折叠 `events[0, end)` 之后计划模式是否激活。最后一条 `plan/mode` 胜出；前缀里一条都没有则为未激活。"""
    if 终点 is None:#默认整份日志
        终点=len(事件们)#整份
    激活=False#第一条之前视为未激活
    下标=0#已消费下标
    for 事件 in 事件们:#按日志顺序
        if 下标>=终点:#到达折叠终点
            break#停
        下标+=1#计入本条
        if 取字段(事件,'type')=='plan/mode':#本包事件
            激活=取字段(取字段(事件,'data'),'active')#最后一条胜出
    return 激活#折叠结果

def 有打开回合(事件们):#空闲信号：有无打开回合
    """日志是否持有一个尚未对应 `turn/end` 的已打开回合。"""
    打开=False#当前是否在回合内
    for 事件 in 事件们:#按日志顺序
        种类=取字段(事件,'type')#事件类型
        if 种类=='turn/start':#打开回合
            打开=True#打开
        elif 种类=='turn/end':#关闭回合
            打开=False#关闭
    return 打开#仍打开则为回合中

def 上次请求头处计划模式(事件们):#上次请求组装时告诉模型的模式
    """最近一条已记录请求头处的计划状态；第一条头之前为 None。"""
    最近头=-1#最近 request/header 下标
    下标=0#扫描下标
    for 事件 in 事件们:#按日志顺序
        if 取字段(事件,'type')=='request/header':#请求头
            最近头=下标#记下头位置
        下标+=1#前进
    if 最近头<0:#还没有请求头
        return None#尚无
    return 折叠计划模式(事件们,最近头+1)#头及之前的折叠结果

class 计划模式控制器(服务):#计划模式控制器服务
    """`ctx.planMode`：拥有已记录的计划状态，在步骤开始时应用并叙述所选状态，以及 `plan:policy` 段落、`/plan` 命令和稳定的退出工具。UI 通过 `session/event` 观察已提交的翻转；没有实时镜像。"""
    inject=['tools','systemPrompt']#注册工具与系统提示词段落所需
    注入=inject#中文别名

    def __init__(自身,上下文,配置=None):#加载插件：校验配置并挂生命周期
        """加载插件：校验配置并挂生命周期。"""
        if 配置 is None:#缺省空配置
            配置={'section':''}#空指导会在解析时失败
        super().__init__(上下文,'planMode')#以 planMode 名注册服务
        自身.段落=解析配置(配置)['section']#加载时校验指导
        自身.未决意图=weakref.WeakKeyDictionary()#会话 → 未决选择
        自身.已拆除=False#插件纤维是否已拆除
        def 步骤前(载荷,下一步):#步骤被接受时提交未决选择
            """步骤被接受时提交未决选择；可附加叙述消息。"""
            判定=解开(下一步())#先让下游判定
            智能体=取字段(载荷,'agent')#本步智能体
            信号=取字段(载荷,'signal')#取消信号
            未决=自身.未决意图.get(取字段(智能体,'session'))#本会话未决选择
            if 取字段(判定,'kind')=='reject' or 取字段(信号,'aborted') or 未决 is None:#拒绝、取消或无选择则原样
                return 判定#原样
            叙述=自身.叙述(取字段(智能体,'session'),取字段(未决,'active'))#切换通知（若上次请求头是另一模式）
            try:#追加 plan/mode；失败则仍待定
                自身.在边界(取字段(智能体,'session'))#边界提交
            except Exception as 错误:#持久写入失败
                上下文.logger.warn('dsh-plan-mode: failed to append selected plan mode at step start: %o',错误)#留下待定以便重试
                return 判定#不挡步骤
            if (not 取字段(未决,'narrate')) or 叙述 is None:#退出工具已叙述，或无需通知
                return 判定#原样判定
            下一判定=dict(判定)#脱离副本
            下一判定['messages']=list(取字段(判定,'messages') or [])+[叙述]#附上用户切换通知
            return 下一判定#带叙述的判定
        上下文.on('agent/pre-step',步骤前)#挂 pre-step
        def 装寿命():#拆除时标记 disposed
            """拆除时标记 disposed。"""
            def 拆寿命():#标记已拆除
                """标记已拆除。"""
                自身.已拆除=True#已拆除
            return 拆寿命#拆除器
        上下文.effect(装寿命,'dsh-plan-mode: close service lifetime')#拆除时标记 disposed
        def 政策文本(上下文块):#按当前（含未决）状态决定是否渲染
            """按当前（含未决）状态决定是否渲染。"""
            智能体=取字段(上下文块,'agent')#组装上下文里的智能体
            if 智能体 is None:#无智能体则空
                return ''#空
            未决=自身.未决意图.get(取字段(智能体,'session'))#未决选择优先
            if 未决 is not None:#有未决
                激活=取字段(未决,'active')#未决目标
            else:#无未决
                激活=折叠计划模式(取字段(取字段(智能体,'session'),'events'))#日志折叠
            if 激活:#激活才给指导
                return 自身.段落#指导正文
            return ''#未激活则空
        上下文.systemPrompt.section({#注册 plan:policy 段落
            'name':'plan:policy',#段落名
            'order':50,#排序
            'text':政策文本,#按状态渲染
        })#结束 section 注册
        def 投影安装(投影上下文,*其余):#有投影注册表才挂单元
            """计划投影单元：纯双事件折叠，向客户端提供完整 {active, pending}。"""
            def 初始():#默认未激活、无未决
                """默认未激活、无未决。"""
                return {'active':False,'wanted':None}#内部状态
            def 折叠(状态,事件):#按事件折叠
                """按事件折叠。"""
                种类=取字段(事件,'type')#事件类型
                数据=取字段(事件,'data')#事件载荷
                if 种类=='command/run' and 取字段(数据,'name')=='plan':#已记录 /plan
                    参数=取字段(数据,'args')#命令参数
                    if 参数 is None:#无参则不变
                        return 状态#不变
                    想要=参数.strip()!='off'#off 以外都是进入
                    if 想要==取字段(状态,'wanted'):#目标未变则复用
                        return 状态#复用
                    return {'active':取字段(状态,'active'),'wanted':想要}#记下目标
                if 种类=='plan/mode':#已提交选择
                    return {'active':取字段(数据,'active'),'wanted':None}#记下并清除未决
                return 状态#其他事件忽略
            def 视图(状态):#内部状态 → 线上值
                """内部状态 → 线上值。"""
                想要=取字段(状态,'wanted')#未决目标
                激活=取字段(状态,'active')#已提交
                return {#线上值
                    'active':激活,#已提交
                    'pending':想要 is not None and 想要!=激活,#未决且与已提交不同
                }#视图结束
            投影上下文.sessionProjections.register({#登记 plan 键
                'key':'plan',#投影键
                'schema':计划投影模式,#线上值模式
                'init':初始,#初始
                'apply':折叠,#折叠
                'view':视图,#视图
                'stateVersion':1,#内部状态版本
            })#登记结束
        上下文.inject(['sessionProjections'],投影安装)#等到投影缝
        def 命令安装(命令上下文,*其余):#有命令注册表才挂 /plan
            """仅当组合了命令注册表时命令子插件才激活。"""
            def 处理(调用):#处理 /plan
                """处理 /plan。"""
                智能体=取字段(调用,'agent')#调用方智能体
                原文=取字段(调用,'rawInput')#原始输入
                if 原文 is None:#缺席
                    原文=''#空
                消息=原文.strip()#去掉首尾空白
                if 消息=='off':#离开
                    结果=自身.设置(智能体,False)#选择未激活
                    if 结果=='committed':#已立刻写入日志
                        return {'kind':'success','text':'Plan mode off.'}#已关闭
                    if 结果=='queued':#等下一被接受的 pre-step
                        return {'kind':'success','text':'Leaving plan mode (applies from the next step).'}#下一步生效
                    if 结果=='cancelled':#清掉相反的未决进入
                        return {'kind':'success','text':'Plan mode entry cancelled.'}#取消进入
                    if 折叠计划模式(取字段(取字段(智能体,'session'),'events')):#日志仍是激活则还在排队离开
                        return {'kind':'success','text':'Leaving plan mode (applies from the next step).'}#仍等待提交
                    return {'kind':'success','text':'Plan mode is already inactive.'}#已经未激活
                结局=自身.设置(智能体,True)#选择激活
                if 消息!='':#非空附言
                    解开(智能体.steer(创建用户消息({#注入为用户消息
                        'content':[{'type':'text','text':消息}],#附言正文
                        'source':{'kind':'user'},#用户来源
                    })))#steer 结束
                if 结局=='committed':#已立刻写入
                    回执='Plan mode on. Use /plan off to leave.'#已打开
                else:#排队
                    回执='Entering plan mode (applies from the next step). Use /plan off to leave.'#下一步生效
                return {'kind':'success','text':回执}#成功回执
            命令上下文.commands.register({#登记 /plan
                'name':'plan',#命令名
                'description':'Enter or leave plan mode',#进入或离开计划模式
                'input':{'hint':'[off|message]'},#off 离开；其余当作用户附言
                'handler':处理,#处理函数
            })#登记结束
        上下文.inject(['commands'],命令安装)#等到命令缝
        def 执行(参数,执行上下文):#向用户审阅计划，批准则排队离开
            """向用户审阅计划，批准则排队离开。"""
            智能体=取字段(执行上下文,'agent')#调用方智能体
            if 智能体 is None:#无会话无法切换
                raise Exception(退出计划模式+' requires a calling agent (no session to switch)')#拒绝
            if not 折叠计划模式(取字段(取字段(智能体,'session'),'events')):#必须已在计划模式
                raise Exception(退出计划模式+' is only available in plan mode')#未激活则拒绝
            计划=取字段(参数,'plan')#计划正文
            if 计划 is None:#缺席
                计划=''#空
            if 首级标题起头.search(计划.strip()) is None:#必须以非空 # 标题起头
                raise Exception(退出计划模式+' requires a non-empty markdown plan starting with a # heading')#计划形状不对
            交互=上下文.get('userQuestions')#审阅通道
            if 交互 is None:#没有提问通道
                raise Exception('no user-questions channel is available to review the plan; ask the user to switch the session mode instead')#让用户改用 /plan off
            def 问():#弹出审阅
                """弹出审阅。"""
                return 交互.ask({#审阅请求
                    'questions':[{#一道审阅题
                        'id':审阅标识,#与答案回显的 id
                        'header':'Plan review',#审阅标题
                        'question':'Approve this plan and leave plan mode?',#是否批准并离开
                        'detail':计划,#计划正文
                        'options':[#两个选项
                            {'label':批准标签,'description':'Leave plan mode; the plan is carried out from the next step.'},#批准离开
                            {'label':继续规划标签,'description':'Stay in plan mode; feedback goes back to the model.'},#继续规划
                        ],#选项结束
                        'intent':{'kind':'plan-review','approve':批准标签},#审阅意图
                    }],#问题结束
                    'agent':智能体,#所属智能体
                    'signal':取字段(执行上下文,'signal'),#随工具调用取消
                })#ask 结束
            try:#把取消审阅说成用户要发言
                答案=解开(问())#等待审阅
            except Exception as 原因:#审阅失败
                if isinstance(原因,用户提问错误) and 取字段(原因,'code')=='ASK_CANCELLED':#用户关掉审阅去说话
                    raise Exception('The user dismissed the plan review to speak instead; '#换成计划模式语境
                        +'stay in plan mode, stop here, and wait for their message.')#停住等用户
                raise 原因#其余错误原样抛
            if 自身.已拆除:#服务已重载
                raise Exception('the plan-mode service was reloaded while the plan was under review; present the plan again')#请再呈一次计划
            审阅项们=[]#本审阅题的答案
            for 条目 in 取字段(答案,'answers') or []:#逐条答案
                if 取字段(条目,'id')==审阅标识:#本审阅题
                    审阅项们.append(条目)#收下
            条目=审阅项们[0] if len(审阅项们)==1 else None#恰好一条才用
            所选=取字段(条目,'selected') if 条目 is not None else None#所选标签
            if (所选 is None) or len(所选)!=1 or 所选[0]!=批准标签 or 取字段(条目,'custom') is not None:#不是干净的批准
                反馈=取字段(条目,'custom') if 条目 is not None else None#用户自定义反馈
                if 反馈 is None:#无反馈
                    反馈=''#空
                if 反馈=='':#无反馈则通用继续规划
                    raise Exception('The user chose to keep planning; revise the plan and present it again.')#请修改再呈
                raise Exception('The user chose to keep planning; their feedback: '+反馈)#带上反馈
            自身.未决意图[取字段(智能体,'session')]={'active':False,'narrate':False}#排队离开且不重复叙述
            return 已兑现({'approved':True})#结构化成功
        def 呈现调用(参数):#调用卡片：标题取计划首条标题
            """调用卡片：标题取计划首条标题。"""
            计划=取字段(参数,'plan')#计划正文
            标题=首条标题(计划) if 计划 is not None else None#首条标题
            if 标题 is None:#无标题
                标题='Plan'#默认标题
            return {#通用卡片
                'card':'generic',#通用卡片
                'title':标题,#标题
                'kind':'other',#其他类
                'content':[{'type':'text','text':计划}],#计划正文
            }#卡片结束
        def 呈现结果(_参数,结果):#结果卡片
            """结果卡片。"""
            return {#通用卡片
                'card':'generic',#通用卡片
                'title':'Plan review',#审阅
                'content':取字段(结果,'content'),#已渲染内容
            }#卡片结束
        def 渲染成功(*位置参数):#模型可见成功文案
            """模型可见成功文案。"""
            return [{'type':'text','text':'Plan approved — plan mode exited; carry out the plan starting with your next step.'}]#成功文案
        上下文.tools.登记(定义工具({#始终注册退出工具，目录不随模式变
            'name':退出计划模式,#工具名
            'description':退出说明,#面向模型的说明
            'parameters':{#唯一参数：完整计划
                'plan':{'type':'string','required':True,'description':'The complete plan, as markdown, starting with a # heading that names it.'},#markdown 计划
            },#参数结束
            'output':{#成功时的结构化输出
                'schema':{#只允许 approved: true
                    'type':'object',#对象
                    'additionalProperties':False,#禁多余键
                    'properties':{#字段
                        'approved':{'type':'boolean','const':True,'required':True},#必须批准
                    },#字段结束
                },#schema结束
                'render':渲染成功,#模型可见成功文案
            },#output结束
            'execute':执行,#审阅并排队离开
            'presentCall':呈现调用,#调用卡片
            'presentResult':呈现结果,#结果卡片
        }))#登记结束

    def 获取(自身,智能体):#读已记录 + 未决
        """读取已记录的计划状态，以及等待下一个被接受的回合内 pre-step 的所选状态。"""
        激活=折叠计划模式(取字段(取字段(智能体,'session'),'events'))#日志折叠
        未决=自身.未决意图.get(取字段(智能体,'session'))#内存未决
        if 未决 is None:#无未决则省略 pending
            return {'active':激活}#仅已记录
        return {'active':激活,'pending':取字段(未决,'active')}#带未决目标

    def 设置(自身,智能体,激活):#选择目标模式
        """选择计划模式是否应激活。回合之间立刻追加变更；打开回合期间选择保持待定，直到下一个被接受的回合内 pre-step。重复选择当前或已待定状态是空操作。返回 `committed`、`queued`、`cancelled` 或 `noop`。"""
        会话=取字段(智能体,'session')#本会话
        未决=自身.未决意图.get(会话)#现有未决
        if 未决 is not None:#有未决
            目标=取字段(未决,'active')#当前瞄准的状态
        else:#无未决
            目标=折叠计划模式(取字段(会话,'events'))#日志折叠
        if 激活==目标:#已经是该目标
            return 'noop'#空操作
        if 有打开回合(取字段(会话,'events')):#回合中：只能排队
            自身.未决意图[会话]={'active':激活,'narrate':True}#记下用户选择并要叙述
            if 折叠计划模式(取字段(会话,'events'))==激活:#回到已记录则算取消
                return 'cancelled'#取消
            return 'queued'#排队
        if 激活==折叠计划模式(取字段(会话,'events')):#目标已是日志状态（清未决）
            自身.未决意图.pop(会话,None)#丢掉未决
            return 'cancelled'#取消相反选择
        解开(会话.append('plan/mode',{'active':激活}))#立刻写入日志
        自身.未决意图.pop(会话,None)#提交成功后清未决
        叙述=自身.叙述(会话,激活)#若上次请求头是另一模式则通知
        if 叙述 is not None:#需要通知
            解开(智能体.inject(叙述))#空闲时注入用户消息
        return 'committed'#已提交

    def 在边界(自身,会话):#pre-step 边界提交
        """在下一次请求组装之前追加一条未决选择。"""
        未决=自身.未决意图.get(会话)#未决选择
        if 未决 is None:#没有则跳过
            return#跳过
        目标=取字段(未决,'active')#目标模式
        if 目标==折叠计划模式(取字段(会话,'events')):#已经是日志状态
            自身.未决意图.pop(会话,None)#只需清未决
            return#无需追加
        解开(会话.append('plan/mode',{'active':目标}))#写入日志
        自身.未决意图.pop(会话,None)#提交成功后清未决

    def 叙述(自身,会话,目标):#是否需要告诉模型模式变了
        """当最近一条已记录请求头描述的是另一模式时，构造用户切换通知。"""
        已告=上次请求头处计划模式(取字段(会话,'events'))#上次请求头处的模式
        if 已告 is None or 已告==目标:#尚无请求头，或已经告诉过目标
            return None#无需通知
        if 目标:#进入
            文本='The user switched this session to plan mode.'#进入
        else:#离开
            文本='The user switched this session back to the default mode.'#离开
        return 创建用户消息({#插件通知形用户消息
            'content':[{'type':'text','text':文本}],#一句正文
            'source':{'kind':'plugin','plugin':'plan-mode','form':'notice','summary':文本},#插件通知来源
        })#结束创建用户消息

default=计划模式控制器#默认导出控制器
默认=计划模式控制器#中文默认导出
