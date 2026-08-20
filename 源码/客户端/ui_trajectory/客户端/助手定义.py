"""轨迹助手流式块、结算与请求生命周期的 ConversationNode Definition。

对齐上游 `ui-trajectory/src/client/trajectory-assistant-definition.ts`。公开面仅中文名。
运行时助手块转换未迁完时本地实现最小 toAssistantBlock / emptyAssistantBlock。
"""
from .定义公共 import 轨迹节点#包成轨迹视图节点
from .轨迹记录 import 取字段#读字段

__all__=['登记轨迹助手定义']#仅中文公开名

def 空助手块(块类型):#空助手块
    """按 blockType 播种空块。"""
    if 块类型=='text':#文本
        return {'kind':'text','text':''}#空文本
    if 块类型=='reasoning':#推理
        return {'kind':'reasoning','text':''}#空推理
    if 块类型=='tool-call':#工具调用
        return {'kind':'tool-call','callId':'','name':'','argsRaw':''}#空调用
    return {'kind':块类型}#其余

def 转助手块(块):#完整块覆盖该槽
    """把事件上的完整块收成助手块。"""
    if isinstance(块,dict) and 'kind' in 块:#已是助手块形
        return 块#原样
    类型=取字段(块,'type')#内容块类型
    if 类型=='text':#文本
        return {'kind':'text','text':取字段(块,'text') or ''}#文本块
    if 类型=='reasoning':#推理
        return {'kind':'reasoning','text':取字段(块,'text') or ''}#推理块
    if 类型=='tool-call' or 类型=='tool_use':#工具调用
        return {'kind':'tool-call','callId':str(取字段(块,'id') or 取字段(块,'callId') or ''),'name':取字段(块,'name') or '','argsRaw':取字段(块,'arguments') or 取字段(块,'argsRaw') or ''}#调用块
    return {'kind':'other','block':块}#其它

def 转助手块们(内容):#内容数组转助手块数组
    """逐条转换。"""
    return [转助手块(块) for 块 in 内容 or []]#转换

def 展示失败文案(失败):#失败展示文案
    """优先 message。"""
    if 失败 is None:#无
        return 'error'#占位
    if isinstance(失败,str):#字符串
        return 失败#原样
    return 取字段(失败,'message') or str(失败)#message 或 str

def 是否令牌增量(块):#是否 token 增量
    """text/reasoning/tool-call delta。"""
    类型=取字段(块,'type')#块种类
    return 类型 in ('text-delta','reasoning-delta','tool-call-delta')#增量类

def 压缩块(块们):#去掉稀疏洞
    """过滤 None 槽。"""
    return [块 for 块 in 块们 if 块 is not None]#过滤

def 有可见内容(块们):#是否有对用户可见的内容（工具调用不算）
    """任一可见块即真。"""
    for 块 in 块们:#逐块
        种类=取字段(块,'kind')#种类
        if 种类=='tool-call':#工具调用对轨迹不算可见
            continue#跳过
        if 种类 in ('text','reasoning'):#文本/推理须非空白
            if (取字段(块,'text') or '').strip()!='':#非空白
                return True#可见
            continue#空白跳过
        return True#其余种类视为可见
    return False#无可见

def 有打断证据(块们):#闭合边界上是否有可展示的打断证据
    """任一非空块即真。"""
    for 块 in 块们:#逐块
        种类=取字段(块,'kind')#种类
        if 种类 in ('text','reasoning'):#文本/推理须非空白
            if (取字段(块,'text') or '').strip()!='':#非空白
                return True#证据
            continue#空白
        return True#其余种类（含工具调用）视为证据
    return False#无证据

def 累加用量(当前,下一块):#把下一块用量累加到当前
    """输入/输出必加；可选字段两边都缺才省略。"""
    结果={'inputTokens':(取字段(当前,'inputTokens') or 0)+取字段(下一块,'inputTokens'),'outputTokens':(取字段(当前,'outputTokens') or 0)+取字段(下一块,'outputTokens')}#必加
    if 取字段(当前,'cacheReadTokens') is not None or 取字段(下一块,'cacheReadTokens') is not None:#有读缓存
        结果['cacheReadTokens']=(取字段(当前,'cacheReadTokens') or 0)+(取字段(下一块,'cacheReadTokens') or 0)#累加
    if 取字段(当前,'cacheWriteTokens') is not None or 取字段(下一块,'cacheWriteTokens') is not None:#有写缓存
        结果['cacheWriteTokens']=(取字段(当前,'cacheWriteTokens') or 0)+(取字段(下一块,'cacheWriteTokens') or 0)#累加
    if 取字段(当前,'reasoningTokens') is not None or 取字段(下一块,'reasoningTokens') is not None:#有推理
        结果['reasoningTokens']=(取字段(当前,'reasoningTokens') or 0)+(取字段(下一块,'reasoningTokens') or 0)#累加
    return 结果#累加结果

def 初始状态(回合,步号,起点序号,起点时间,已开始):#播种一条尚未见块的助手状态
    """空块、无用量、无重试。"""
    return {'turn':回合,'step':步号,'startSeq':起点序号,'startTime':起点时间,'started':已开始,'sawChunk':False,'blocks':[],'firstVisibleSeq':None,'firstVisibleTime':None,'firstTokenTime':None,'final':None,'usage':None,'retry':None,'stepEnd':None}#初始状态

def 更新块(状态,匹配):#按一条 assistant/chunk 推进块与用量
    """非块事件原样返回。"""
    事件=取字段(匹配,'event')#事件
    if 取字段(事件,'type')!='assistant/chunk':#非块事件
        return 状态#原样
    块=取字段(取字段(事件,'data'),'chunk')#取出块载荷
    if 取字段(块,'type')=='usage':#用量块
        return {**状态,'sawChunk':True,'usage':累加用量(取字段(状态,'usage'),取字段(块,'usage'))}#标记见块并累加用量
    块们=list(取字段(状态,'blocks') or [])#复制稀疏块数组
    类型=取字段(块,'type')#块种类
    槽=取字段(块,'index')#槽下标
    while len(块们)<=槽:#扩容稀疏数组
        块们.append(None)#扩洞
    if 类型=='block-start':#块开始
        块们[槽]=空助手块(取字段(块,'blockType'))#在该槽放入空块
    elif 类型=='text-delta':#文本增量
        先前=块们[槽]#该槽已有块
        旧文=取字段(先前,'text') if 取字段(先前,'kind')=='text' else ''#旧文本
        块们[槽]={'kind':'text','text':旧文+(取字段(块,'text') or '')}#接上增量
    elif 类型=='reasoning-delta':#推理增量
        先前=块们[槽]#该槽已有块
        旧文=取字段(先前,'text') if 取字段(先前,'kind')=='reasoning' else ''#旧推理
        块们[槽]={'kind':'reasoning','text':旧文+(取字段(块,'text') or '')}#接上增量
    elif 类型=='tool-call-delta':#工具调用增量
        先前=块们[槽]#该槽已有块
        if 取字段(先前,'kind')=='tool-call':#已是工具调用
            底=先前#沿用
        else:#否则空底
            底={'kind':'tool-call','callId':'','name':'','argsRaw':''}#空底
        块们[槽]={'kind':'tool-call','callId':取字段(底,'callId') or str(取字段(块,'id') or ''),'name':取字段(块,'name') if 取字段(块,'name') is not None else 取字段(底,'name'),'argsRaw':(取字段(底,'argsRaw') or '')+(取字段(块,'argumentsDelta') or '')}#累积工具调用
    elif 类型=='block-end':#块结束
        块们[槽]=转助手块(取字段(块,'block'))#用完整块覆盖该槽
    else:#未知块种类
        return {**状态,'sawChunk':True}#只标记见块
    可见=有可见内容(压缩块(块们))#压缩后是否已有可见内容
    新状态={**状态,'sawChunk':True,'blocks':块们}#写出新状态
    if 可见 and 取字段(状态,'firstVisibleSeq') is None:#首次出现可见内容
        新状态['firstVisibleSeq']=取字段(事件,'seq')#记下序号
        新状态['firstVisibleTime']=取字段(事件,'time')#记下时间
    if 是否令牌增量(块) and 取字段(状态,'firstTokenTime') is None:#首次 token 增量
        新状态['firstTokenTime']=取字段(事件,'time')#记下时间
    return 新状态#新状态

def 闭合边界(上下文):#从状态或位置推出已闭合的步/回合边界
    """有闭合边界则返回其 seq/time。"""
    状态=取字段(上下文,'state')#本节点状态
    步结束=取字段(状态,'stepEnd') if 状态 is not None else None#step/end 命中
    if 步结束 is not None and 取字段(取字段(步结束,'event'),'type')=='step/end':#已匹配 step/end
        return 取字段(步结束,'event')#取其事件
    起点=取字段(上下文,'start')#起点
    位置=取字段(起点,'location') if 起点 is not None else None#起点位置
    if 位置 is None:#否则最后一次命中的位置
        命中们=取字段(上下文,'matches') or []#命中列表
        位置=取字段(命中们[-1],'location') if 命中们 else None#末次位置
    if 取字段(位置,'kind')=='step' and 取字段(取字段(位置,'step'),'status')=='closed':#步已闭合
        return 取字段(取字段(位置,'step'),'end')#取步结束
    if 取字段(位置,'kind') in ('step','turn') and 取字段(取字段(位置,'turn'),'status')=='closed':#回合已闭合
        return 取字段(取字段(位置,'turn'),'end')#取回合结束
    return None#尚无闭合边界

def 结算节点(状态,上下文):#投影已结算或被打断的助手消息节点
    """有结算或打断证据才返回。"""
    结算=取字段(状态,'final')#assistant/message 命中
    if 结算 is not None and 取字段(取字段(结算,'event'),'type')=='assistant/message':#已有完整结算
        事件=取字段(结算,'event')#取出结算事件
        消息=取字段(取字段(事件,'data'),'message')#消息
        return {'kind':'assistant','seq':取字段(事件,'seq'),'messageId':取字段(消息,'id'),'time':取字段(事件,'time'),'turn':取字段(状态,'turn'),'step':取字段(状态,'step'),'blocks':转助手块们(取字段(消息,'content')),'usage':取字段(取字段(事件,'data'),'usage'),'provenance':{'provider':取字段(取字段(消息,'source'),'provider'),'model':取字段(取字段(消息,'source'),'model')},'timing':{'stepStartTime':取字段(状态,'startTime') if 取字段(状态,'started') else None,'firstTokenTime':取字段(状态,'firstTokenTime'),'completedTime':取字段(事件,'time')}}#完整节点
    边界=闭合边界(上下文)#找闭合边界
    块们=压缩块(取字段(状态,'blocks') or [])#去掉稀疏洞
    if 边界 is None or not 有打断证据(块们):#无边界或无打断证据
        return None#不投影
    return {'kind':'assistant','seq':取字段(边界,'seq')-0.9,'time':取字段(边界,'time'),'turn':取字段(状态,'turn'),'step':取字段(状态,'step'),'blocks':块们,'interrupted':True}#合成被打断的助手节点

def 助手请求(状态,节点,边界):#把累积状态投影成 assistant RequestView
    """见过 start 才返回。"""
    if not 取字段(状态,'started'):#回放缺 start
        return None#不投影请求
    if 节点 is not None and 取字段(节点,'interrupted') is not True:#已有未打断的结算节点
        状态字='complete'#视为完成
    elif 取字段(状态,'retry') is not None or 边界 is not None:#有重试或边界
        状态字='error'#出错
    else:#否则进行中
        状态字='running'#进行中
    请求={'purpose':'assistant','startSeq':取字段(状态,'startSeq'),'turn':取字段(状态,'turn'),'step':取字段(状态,'step'),'startedAt':取字段(状态,'startTime'),'completedAt':取字段(节点,'time') if 节点 is not None else (取字段(边界,'time') if 边界 is not None else None),'status':状态字}#组装
    重试=取字段(状态,'retry')#重试
    if 重试 is not None:#有重试则展开
        请求['error']=取字段(重试,'message')#失败展示文案
        请求['retry']=取字段(重试,'retry')#当前重试次数
        if 取字段(重试,'maxRetries') is not None:#normal 模式才有上限
            请求['maxRetries']=取字段(重试,'maxRetries')#上限
        请求['retryDelayMs']=取字段(重试,'delayMs')#下次重试延迟
    if 节点 is not None and 取字段(节点,'interrupted') is not True:#已结算
        请求['resultSeq']=取字段(节点,'seq')#结算序号
        if 取字段(节点,'provenance') is not None:#有出处
            请求['provenance']=取字段(节点,'provenance')#展开
    if 取字段(状态,'usage') is not None:#有用量
        请求['usage']=取字段(状态,'usage')#展开
    return 请求#RequestView

def 回放状态(上下文):#无 start 时从命中回放累积状态
    """可能仍 None（无助手事件）。"""
    状态=None#尚未见助手事件
    for 匹配 in 取字段(上下文,'matches') or []:#按到达顺序回放
        事件=取字段(匹配,'event')#取出事件
        种类=取字段(事件,'type')#事件类型
        if 种类=='assistant/chunk':#流式块
            if 状态 is None:#首次见块则播种
                状态=初始状态(取字段(取字段(事件,'data'),'turn'),取字段(取字段(事件,'data'),'step'),取字段(事件,'seq'),取字段(事件,'time'),False)#started=false
            状态=更新块(状态,匹配)#推进块与用量
        elif 种类=='assistant/message':#结算消息
            if 状态 is None:#首次见消息则播种
                状态=初始状态(取字段(取字段(事件,'data'),'turn'),取字段(取字段(事件,'data'),'step'),取字段(事件,'seq'),取字段(事件,'time'),False)#播种
            状态={**状态,'blocks':转助手块们(取字段(取字段(取字段(事件,'data'),'message'),'content')),'final':匹配,'usage':取字段(状态,'usage') if 取字段(状态,'usage') is not None else 取字段(取字段(事件,'data'),'usage')}#覆盖块并记下结算
        elif 种类=='step/end' and 状态 is not None:#步结束且已有状态
            状态={**状态,'stepEnd':匹配}#记下 step/end 命中
    return 状态#可能仍 None

def 助手匹配(事件):#按事件类型归入本步
    """start / update / null。"""
    种类=取字段(事件,'type')#事件类型
    数据=取字段(事件,'data')#载荷
    if 种类=='step/start':#步开始
        return {'id':f"{取字段(数据,'turn')}:{取字段(数据,'step')}",'role':'start'}#作本节点 start
    if 种类 in ('assistant/chunk','assistant/message','llm/retry','step/end'):#update 类
        return {'id':f"{取字段(数据,'turn')}:{取字段(数据,'step')}",'role':'update'}#作本节点 update
    return None#无关事件

def 助手开始(_上下文,匹配):#从 step/start 播种状态
    """见过 start，started=True。"""
    事件=取字段(匹配,'event')#事件
    if 取字段(事件,'type')!='step/start':#类型守卫
        raise Exception('trajectory-assistant-step start requires step/start')#类型收窄失败则抛
    数据=取字段(事件,'data')#载荷
    return 初始状态(取字段(数据,'turn'),取字段(数据,'step'),取字段(事件,'seq'),取字段(事件,'time'),True)#初始状态

def 助手更新(上下文,匹配):#按后续事件推进状态
    """chunk / message / step/end / llm/retry。"""
    事件=取字段(匹配,'event')#事件
    种类=取字段(事件,'type')#类型
    状态=取字段(上下文,'state')#当前状态
    if 种类=='assistant/chunk':#流式块
        return 更新块(状态,匹配)#推进
    if 种类=='assistant/message':#结算消息
        return {**状态,'blocks':转助手块们(取字段(取字段(取字段(事件,'data'),'message'),'content')),'final':匹配,'usage':取字段(状态,'usage') if 取字段(状态,'usage') is not None else 取字段(取字段(事件,'data'),'usage')}#覆盖块并记下结算
    if 种类=='step/end':#步结束
        return {**状态,'stepEnd':匹配}#记下
    if 种类!='llm/retry':#其余不改
        return 状态#原样
    数据=取字段(事件,'data')#重试载荷
    重试={'message':展示失败文案(取字段(数据,'failure')),'retry':取字段(数据,'retry'),'delayMs':取字段(数据,'delayMs')}#记下本次失败与延迟
    if 取字段(数据,'mode')=='normal':#normal 才带上限
        重试['maxRetries']=取字段(数据,'maxRetries')#上限
    新状态=初始状态(取字段(状态,'turn'),取字段(状态,'step'),取字段(状态,'startSeq'),取字段(状态,'startTime'),True)#按原起点重新播种
    新状态['firstTokenTime']=取字段(状态,'firstTokenTime')#保留首 token 时间
    新状态['usage']=取字段(状态,'usage')#保留已累计用量
    新状态['retry']=重试#挂重试
    return 新状态#重试状态

def 助手发布(匹配):#控制该命中何时发布视图
    """start 不单独发布；用量/结束不发布。"""
    种类=取字段(取字段(匹配,'event'),'type')#事件类型
    if 种类=='step/start':#start
        return 'none'#不单独发布
    if 种类!='assistant/chunk':#结算/重试/步结束
        return 'immediate'#立即发布
    类型=取字段(取字段(取字段(匹配,'event'),'data'),'chunk')#块
    块类型=取字段(类型,'type')#块种类
    return 'none' if 块类型 in ('usage','finish') else 'animation-frame'#用量/结束不发布

def 助手构建视图(上下文):#投影轨迹视图节点
    """三者皆空则不产出。"""
    状态=取字段(上下文,'state')#有 start 用状态
    if 状态 is None:#否则回放
        状态=回放状态(上下文)#回放
    if 状态 is None:#无助手事件
        return None#不产出
    节点=结算节点(状态,上下文)#结算或打断节点
    边界=闭合边界(上下文)#闭合边界
    if 节点 is None and 边界 is None and 取字段(状态,'sawChunk'):#尚在流式且已见块
        流式={'turn':取字段(状态,'turn'),'step':取字段(状态,'step'),'blocks':压缩块(取字段(状态,'blocks') or [])}#部分助手视图
    else:#已结算/已闭合/未见块
        流式=None#无 partial
    请求=助手请求(状态,节点,边界)#请求生命周期视图
    if 节点 is None and 流式 is None and 请求 is None:#三者皆空
        return None#不产出
    数据={'kind':'assistant','partial':流式}#贡献载荷
    if 节点 is not None:#有结算/打断节点才展开
        数据['node']=节点#节点
    if 请求 is not None:#有请求视图才展开
        数据['request']=请求#请求
    return 轨迹节点(上下文,取字段(状态,'startSeq'),数据)#包进轨迹信封

轨迹助手定义={#助手步 Definition
    'kind':'trajectory-assistant-step',#节点种类
    'target':'trajectory',#投递到轨迹槽
    'match':助手匹配,#匹配
    'start':助手开始,#播种
    'update':助手更新,#更新
    'publication':助手发布,#发布策略
    'buildViewNode':助手构建视图,#投影
}#定义结束

def 回合结束开始(_上下文,匹配):#从 turn/end 播种状态
    """记下回合、序号、时间，出错则带文案。"""
    事件=取字段(匹配,'event')#事件
    if 取字段(事件,'type')!='turn/end':#类型守卫
        raise Exception('trajectory-turn-end start requires turn/end')#类型收窄失败则抛
    原因=取字段(取字段(事件,'data'),'reason')#结束原因
    状态={'turn':取字段(取字段(事件,'data'),'turn'),'seq':取字段(事件,'seq'),'time':取字段(事件,'time')}#基本字段
    if 取字段(原因,'kind')=='error':#出错才展开 error
        状态['error']=展示失败文案(取字段(原因,'error'))#展示文案
    return 状态#状态

回合结束定义={#回合结束 Definition
    'kind':'trajectory-turn-end',#节点种类
    'target':'trajectory',#投递到轨迹槽
    'match':lambda 事件:({'id':str(取字段(事件,'seq')),'role':'start'} if 取字段(事件,'type')=='turn/end' else None),#只匹配回合结束
    'start':回合结束开始,#播种
    'update':lambda 上下文,_匹配:取字段(上下文,'state'),#无后续事件
    'buildViewNode':lambda 上下文:(None if 取字段(上下文,'state') is None else 轨迹节点(上下文,取字段(取字段(上下文,'state'),'seq'),{**{'kind':'turn-end','turn':取字段(取字段(上下文,'state'),'turn'),'time':取字段(取字段(上下文,'state'),'time')},**({'error':取字段(取字段(上下文,'state'),'error')} if 取字段(取字段(上下文,'state'),'error') is not None else {})})),#包进轨迹信封
}#定义结束

def 登记轨迹助手定义(上下文):#登记助手步与回合结束
    """登记轨迹助手生命周期 Definition。"""
    上下文.conversationEvents.register(轨迹助手定义)#登记助手流式/结算
    上下文.conversationEvents.register(回合结束定义)#登记回合结束
