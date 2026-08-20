"""审批能力缝的服务定义，覆盖请求、取消、审计与按会话策略。缺少回答者则失败闭合；授予只作用于所请求的动作。"""
import uuid,threading#配对 id 与中止竞赛线程
from schemastery import 模式#配置校验
from cordis import 服务#Cordis 服务基类
from cordis.工具 import 承诺,是否thenable,已兑现#操作链承诺、可等待判定与立刻兑现
from llm import 创建用户消息#把策略切换通知注入下一步
from scope import 作用域目标#按智能体过滤的瀑布载体
from .类型 import 审批请求标识,审批结果#再导出线路安全标识与结果

名称='user-approval'#Cordis 插件名（包目录用下划线，插件名保留上游连字符）
name=名称#Cordis 插件名
结果表=审批结果#封闭结果表，用于运行时归一化回答者返回值
审批策略=('ask','never')#会话审批策略封闭表
审批策略表=审批策略#每一个审批策略，用于选项公布以及对未信任策略字符串的运行时校验
永不句=('Approval prompts are disabled in this session: actions that require approval are rejected automatically '#never 策略模型可见句前段
    +'— do not request sandbox escalation (do not set `sandbox_permissions`).')#never 策略模型可见句后段
询问句=('Approval policy: ask. Operations that require approval may ask through the configured answerers; '#ask 策略模型可见句前段
    +'without an available answerer, the request fails closed.')#ask 策略模型可见句后段
配置模式=模式.对象({#插件配置：全部可选——static Config 给出默认值
    'policy':模式.联合(['ask','never']).默认('ask'),#没有覆盖时的部署默认策略
})#配置模式结束
Config=配置模式#Cordis 配置模式

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
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

def 信号已中止(信号):#对齐 AbortSignal.aborted
    """英文 aborted 或中文 已中止 任一为真则视为已中止。"""
    if 信号 is None:#无信号
        return False#未中止
    if getattr(信号,'aborted',False) is True:#英文旗标
        return True#已中止
    if getattr(信号,'已中止',False) is True:#中文旗标
        return True#已中止
    return False#未中止

def 生效审批策略(事件们):#从日志折叠当前策略
    """会话的审批策略覆盖：日志里最后一条 approval/policy 事件；会话从未切换时为 None（调用方套用插件配置的默认）。纯折叠——恢复不需要追赶机械，因为回放日志就是状态。"""
    if 事件们 is None:#无日志
        return None#从未切换
    for 下标 in range(len(事件们)-1,-1,-1):#从后往前找
        事件=事件们[下标]#取该条事件
        if 取字段(事件,'type')=='approval/policy':#命中最后一次切换
            return 取字段(取字段(事件,'data'),'policy')#返回策略
    return None#从未切换

def 有打开回合(事件们):#是否有打开回合
    """日志当前是否坐在打开回合里（一条尚未被 turn/end 关闭的 turn/start）——审批服务.请求 的前置条件。审计配对必须被回合包住：回合是持久日志的提交/回放边界，回合之间追加的裸事件与崩溃尾巴无法区分，重载时会被静默丢掉。"""
    if 事件们 is None:#无日志
        return False#从未有回合
    for 下标 in range(len(事件们)-1,-1,-1):#从后往前找
        类型=取字段(事件们[下标],'type')#取事件类型
        if 类型=='turn/start':#最近是开始则打开
            return True#打开
        if 类型=='turn/end':#最近是结束则关闭
            return False#关闭
    return False#从未有回合

def 设审批策略(会话,策略):#写入策略覆盖事件
    """追加会话策略覆盖的唯一持久表示。非法值在日志改动之前抛出；消费方每次读取都折叠新值。"""
    if 策略 not in 审批策略表:#必须在封闭表内
        raise TypeError('approval policy must be one of "ask" or "never"')#拒绝未知策略
    会话.追加('approval/policy',{'policy':策略})#追加覆盖事件

class 审批请求:#只读的同进程权限问题（运行时结构，非线路 TypedDict）
    """只读的同进程权限问题。callId 链到已经展示过的工具调用，因此这里不重复参数。"""
    def __init__(自身,agent,toolName,callId=None,reason=None,signal=None):#智能体、工具身份与可选调用/原因/信号
        """记下所属智能体、工具名，以及可选的精确调用、原因与中止信号。"""
        自身.agent=agent#为其提问的智能体；路由该问题（UI 回答者只为自己拥有的智能体作答），并在其会话日志上接收审计事件
        自身.toolName=toolName#问题所关的工具（展示与审计）
        自身.callId=callId#正在决定的精确工具调用，提问者已有时提供——让 UI 把提示贴到它已经流过的工具调用上
        自身.reason=reason#提问者面向人的解释：为什么要问
        自身.signal=signal#中止即撤回问题：请求立刻结算 cancelled，仍在等待的回答者迟到答案会被丢掉

class 审批服务(服务):#审批服务：在回答者之前套用会话策略，并把每次提问/结果配对记到请求会话
    """审批服务：在回答者之前套用会话策略，并把每次提问/结果配对记到请求会话。它通过运行时上下文快照和切换通知，把确定性策略变化暴露给模型。"""
    Config=配置模式#插件配置模式
    def __init__(自身,ctx,配置):#构造审批服务
        """以 approval 名安装服务，并在系统提示词就绪后贡献策略上下文。"""
        super().__init__(ctx,'approval')#以 approval 名安装服务
        自身.config=配置#插件配置
        自身.配置=配置#中文别名
        def 挂提示(提示上下文,*其余):#系统提示词就绪后再贡献
            """登记运行时上下文片段：完整当前值走在保留历史之后，因此切换策略不会改写稳定系统提示词缓存前缀。"""
            def 文本(组装上下文):#按当前智能体渲染
                """按当前智能体渲染策略句。"""
                智能体=取字段(组装上下文,'agent')#组装时的智能体
                if 智能体 is None:#裸 assemble()（测试、诊断）没有可陈述的会话
                    return ''#无智能体则空
                策略=自身.生效策略(取字段(智能体,'session'))#取生效策略
                if 策略=='never':#确定性拒绝
                    return 永不句#never 句
                return 询问句#ask 句
            提示上下文.systemPrompt.context({#登记运行时上下文片段
                'name':'approval:policy',#片段名
                'order':115,#排在保留历史之后
                'text':文本,#按当前智能体渲染
            })#context 登记结束
        自身.ctx.inject(['systemPrompt'],挂提示)#系统提示词就绪后再贡献

    def 设策略(自身,智能体,策略):#运行时切换策略
        """切换一个存活智能体的策略，并把过渡排进它的下一步模型步骤。会话初始化直接用 设审批策略，因为没有先前可见策略可改。"""
        先前=自身.生效策略(取字段(智能体,'session'))#切换前策略
        if 先前==策略:#未变则空操作
            return#空操作
        设审批策略(取字段(智能体,'session'),策略)#写入覆盖事件
        解开(智能体.inject(创建用户消息({#把切换通知注入下一步
            'content':[{#文本块
                'type':'text',#文本
                'text':'The approval policy changed from "'+str(先前)+'" to "'+str(策略)+'" (changed by the user).',#模型可见切换句
            }],#content 结束
            'source':{'kind':'plugin','plugin':'user-approval'},#插件来源
        })))#inject 结束

    def 请求(自身,请求):#发出一次审批请求
        """请组合回答者决定一次只读同进程请求。服务直接借用请求、智能体、会话和存活信号。请求要求有打开回合，因为审计配对必须被持久日志的提交/回放边界包住；空闲提问在追加任何东西之前拒绝。回答者阶段总会产出结果：已中止信号得到 cancelled，缺失或抛出的回答者得到 unavailable（失败闭合），非词表返回值被归一成 unavailable。阻止任一条审计追加提交的失败仍会拒绝，因为返回未记录的决定会破坏配对。会话内含提交后观察者失败，因此一次权威追加不能拒绝请求或压掉其配对审计事件。"""
        会话=取字段(取字段(请求,'agent'),'session')#审计写入该会话
        if not 有打开回合(取字段(会话,'events')):#没有打开回合
            raise Exception(#拒绝回合外提问
                'approval.request() outside an open turn: the approval/asked + approval/decided audit pair '
                +'must be turn-enclosed (a bare event between turns is crash-tail garbage on reload). '
                +'Ask from inside the turn that needs the decision.'
            )#抛出回合前置错误
        配对=审批请求标识(str(uuid.uuid4()))#铸造本次配对 id
        提问载荷={'id':配对,'toolName':取字段(请求,'toolName')}#先写提问审计
        调用标识=取字段(请求,'callId')#可选精确工具调用
        if 调用标识 is not None:#有调用 id
            提问载荷['callId']=调用标识#带上调用 id
        原因=取字段(请求,'reason')#可选原因
        if 原因 is not None:#有原因
            提问载荷['reason']=原因#带上原因
        会话.追加('approval/asked',提问载荷)#asked 结束
        结果=自身.决定(请求,会话)#问回答者链
        会话.追加('approval/decided',{'id':配对,'outcome':结果})#再写裁决审计
        return 结果#返回封闭结果

    def 生效策略(自身,会话):#取生效策略
        """会话的生效策略：它自己的 approval/policy 折叠，否则是配置默认（模式已把省略的策略默认成 ask；?? 只收窄可选输入类型）。"""
        覆盖=自身.覆盖于(会话)#日志覆盖
        if 覆盖 is not None:#有覆盖
            return 覆盖#覆盖优先
        配置策略=取字段(自身.config,'policy')#配置默认
        if 配置策略 is not None:#有配置
            return 配置策略#用配置
        return 'ask'#再否则 ask

    def 覆盖于(自身,会话):#只读日志覆盖
        """读会话覆盖，不套用配置默认。返回最后一条已记录策略；没有则为 None。"""
        return 生效审批策略(取字段(会话,'events'))#纯折叠

    def 决定(自身,请求,会话):#决定一次请求
        """派发瀑布，内含，并与请求信号竞赛。'never' 策略在这里、任何派发之前决定：本服务挂载之后用 prepend:true 登记的监听器会坐在任何门监听器前面，因此监听器形态的门无法守住文档承诺——无论登记顺序，never 都确定拒绝——只有服务自己的请求路径能。"""
        信号=取字段(请求,'signal')#可选取消信号
        if 信号已中止(信号):#已中止则撤回
            return 'cancelled'#撤回
        if 自身.生效策略(会话)=='never':#never 则不问
            return 'rejected'#确定拒绝
        def 默认不可用():#无人认领则失败闭合
            """瀑布末端：无人认领则 unavailable。"""
            return 已兑现('unavailable')#失败闭合
        def 问回答者():#先入微任务再派发：同步抛出必须落到与异步相同的拒绝路径
            """派发作用域过滤的 approval/request 瀑布并归一结果。"""
            try:#内含抛出
                原始=自身.ctx.waterfall(#作用域过滤的瀑布
                    作用域目标(自身,取字段(请求,'agent')),#按智能体路由
                    'approval/request',#瀑布事件名
                    请求,#待决决定
                    默认不可用,#无人认领则失败闭合
                )#waterfall 结束
                结果=解开(原始)#等待可等待返回
            except BaseException:#抛出的回答者必须让问题失败闭合
                return 'unavailable'#抛出当 unavailable
            if 结果 in 结果表:#词表内
                return 结果#原样
            return 'unavailable'#流氓返回值当 unavailable
        if 信号 is None:#无信号则只等回答
            return 问回答者()#只等回答
        结果承诺=承诺()#与中止竞赛
        已结算=[False]#只结算一次
        def 结算(回调):#幂等结算
            """只结算一次。"""
            if 已结算[0]:#已结算
                return#无事
            已结算[0]=True#标记
            回调()#执行结算
        def 在中止(*位置参数):#中止胜出
            """中止则撤回。"""
            结算(lambda:结果承诺.兑现('cancelled'))#撤回
        def 等回答():#跟随回答者
            """跟随回答者兑现。"""
            结果=问回答者()#问回答者
            结算(lambda:结果承诺.兑现(结果))#兑现回答；中止已赢后是空操作
        工作=threading.Thread(target=等回答)#后台等回答
        工作.daemon=True#不挡住退出
        工作.start()#启动
        if 信号已中止(信号):#挂监听前已中止
            在中止()#立刻处理
        else:#挂监听
            加监听=getattr(信号,'addEventListener',None)#DOM 风格
            if callable(加监听):#有监听 API
                加监听('abort',在中止,{'once':True})#只听一次中止
            else:#无 DOM 监听则靠处理函数自行检查
                pass#调用方用 aborted 旗标
        return 解开(结果承诺)#竞赛结果

default=审批服务#Cordis 默认导出
默认=审批服务#中文默认导出
