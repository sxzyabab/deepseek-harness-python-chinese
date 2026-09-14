from .轨迹节点 import 轨迹节点#包成轨迹视图节点
from .轨迹记录 import 轨迹错误#本包异常

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
    if not isinstance(块,dict):#非对象
        return {'kind':'other','block':块}#其它
    类型=块['type'] if 'type' in 块 else None#内容块类型
    if 类型=='text':#文本
        return {'kind':'text','text':块['text'] if 'text' in 块 and 块['text'] is not None else ''}#文本块
    if 类型=='reasoning':#推理
        return {'kind':'reasoning','text':块['text'] if 'text' in 块 and 块['text'] is not None else ''}#推理块
    if 类型=='tool-call' or 类型=='tool_use':#工具调用
        调用标识=块['id'] if 'id' in 块 and 块['id'] is not None else (块['callId'] if 'callId' in 块 else None)#调用 id
        名称=块['name'] if 'name' in 块 and 块['name'] is not None else ''#名
        参数原文=块['arguments'] if 'arguments' in 块 and 块['arguments'] is not None else (块['argsRaw'] if 'argsRaw' in 块 and 块['argsRaw'] is not None else '')#参数
        return {'kind':'tool-call','callId':str(调用标识 or ''),'name':名称,'argsRaw':参数原文}#调用块
    return {'kind':'other','block':块}#其它

def 转助手块列表(内容):#内容数组转助手块数组
    """逐条转换。"""
    return [转助手块(块) for 块 in (内容 if 内容 is not None else [])]#转换

def 展示失败文案(失败):#失败展示文案
    """优先 message。"""
    if 失败 is None:#无
        return 'error'#占位
    if isinstance(失败,str):#字符串
        return 失败#原样
    if isinstance(失败,dict) and 'message' in 失败 and 失败['message'] is not None:#有 message
        return 失败['message']#message
    return str(失败)#str

def 是否令牌增量(块):#是否 token 增量
    """text/reasoning/tool-call delta。"""
    类型=块['type'] if 块 is not None and 'type' in 块 else None#块种类
    return 类型 in ('text-delta','reasoning-delta','tool-call-delta')#增量类

def 压缩块(块列表):#去掉稀疏洞
    """过滤 None 槽。"""
    return [块 for 块 in 块列表 if 块 is not None]#过滤

def 有可见内容(块列表):#是否有对用户可见的内容（工具调用不算）
    """任一可见块即真。"""
    for 块 in 块列表:#逐块
        种类=块['kind'] if 'kind' in 块 else None#种类
        if 种类=='tool-call':#工具调用对轨迹不算可见
            continue#跳过
        if 种类 in ('text','reasoning'):#文本/推理须非空白
            文=块['text'] if 'text' in 块 and 块['text'] is not None else ''#文本
            if 文.strip()!='':#非空白
                return True#可见
            continue#空白跳过
        return True#其余种类视为可见
    return False#无可见

def 有打断证据(块列表):#闭合边界上是否有可展示的打断证据
    """任一非空块即真。"""
    for 块 in 块列表:#逐块
        种类=块['kind'] if 'kind' in 块 else None#种类
        if 种类 in ('text','reasoning'):#文本/推理须非空白
            文=块['text'] if 'text' in 块 and 块['text'] is not None else ''#文本
            if 文.strip()!='':#非空白
                return True#证据
            continue#空白
        return True#其余种类（含工具调用）视为证据
    return False#无证据

def 累加用量(当前,下一块):#把下一块用量累加到当前
    """输入/输出必加；可选字段两边都缺才省略。"""
    当前入=当前['inputTokens'] if 当前 is not None and 'inputTokens' in 当前 else None#当前入
    下入=下一块['inputTokens'] if 下一块 is not None and 'inputTokens' in 下一块 else None#下入
    当前出=当前['outputTokens'] if 当前 is not None and 'outputTokens' in 当前 else None#当前出
    下出=下一块['outputTokens'] if 下一块 is not None and 'outputTokens' in 下一块 else None#下出
    结果={'inputTokens':(当前入 or 0)+下入,'outputTokens':(当前出 or 0)+下出}#必加
    当前读=当前['cacheReadTokens'] if 当前 is not None and 'cacheReadTokens' in 当前 else None#当前读
    下读=下一块['cacheReadTokens'] if 下一块 is not None and 'cacheReadTokens' in 下一块 else None#下读
    if 当前读 is not None or 下读 is not None:#有读缓存
        结果['cacheReadTokens']=(当前读 or 0)+(下读 or 0)#累加
    当前写=当前['cacheWriteTokens'] if 当前 is not None and 'cacheWriteTokens' in 当前 else None#当前写
    下写=下一块['cacheWriteTokens'] if 下一块 is not None and 'cacheWriteTokens' in 下一块 else None#下写
    if 当前写 is not None or 下写 is not None:#有写缓存
        结果['cacheWriteTokens']=(当前写 or 0)+(下写 or 0)#累加
    当前思=当前['reasoningTokens'] if 当前 is not None and 'reasoningTokens' in 当前 else None#当前思
    下思=下一块['reasoningTokens'] if 下一块 is not None and 'reasoningTokens' in 下一块 else None#下思
    if 当前思 is not None or 下思 is not None:#有推理
        结果['reasoningTokens']=(当前思 or 0)+(下思 or 0)#累加
    return 结果#累加结果

def 初始状态(回合,步号,起点序号,起点时间,已开始):#播种一条尚未见块的助手状态
    """空块、无用量、无重试。"""
    return {'turn':回合,'step':步号,'startSeq':起点序号,'startTime':起点时间,'started':已开始,'sawChunk':False,'blocks':[],'firstVisibleSeq':None,'firstVisibleTime':None,'firstTokenTime':None,'final':None,'usage':None,'retry':None,'stepEnd':None}#初始状态

def 更新块(状态,匹配):#按一条 assistant/live-chunk 推进块与用量
    """非块事件原样返回。"""
    事件=匹配['event'] if 'event' in 匹配 else None#事件
    if 事件 is None or ('type' not in 事件) or 事件['type']!='assistant/live-chunk':#非块事件
        return 状态#原样
    数据=事件['data'] if 'data' in 事件 else None#载荷
    块=数据['chunk'] if 数据 is not None and 'chunk' in 数据 else None#取出块载荷
    if 块 is not None and 'type' in 块 and 块['type']=='usage':#用量块
        return {**状态,'sawChunk':True,'usage':累加用量(状态['usage'] if 'usage' in 状态 else None,块['usage'] if 'usage' in 块 else None)}#标记见块并累加用量
    块列表=list(状态['blocks'] if 'blocks' in 状态 and 状态['blocks'] is not None else [])#复制稀疏块数组
    类型=块['type'] if 块 is not None and 'type' in 块 else None#块种类
    槽=块['index'] if 块 is not None and 'index' in 块 else None#槽下标
    while len(块列表)<=槽:#扩容稀疏数组
        块列表.append(None)#扩洞
    if 类型=='block-start':#块开始
        块列表[槽]=空助手块(块['blockType'] if 'blockType' in 块 else None)#在该槽放入空块
    elif 类型=='text-delta':#文本增量
        先前=块列表[槽]#该槽已有块
        旧文=(先前['text'] if 先前 is not None and 'text' in 先前 else '') if 先前 is not None and 'kind' in 先前 and 先前['kind']=='text' else ''#旧文本
        增=块['text'] if 块 is not None and 'text' in 块 and 块['text'] is not None else ''#增量
        块列表[槽]={'kind':'text','text':旧文+增}#接上增量
    elif 类型=='reasoning-delta':#推理增量
        先前=块列表[槽]#该槽已有块
        旧文=(先前['text'] if 先前 is not None and 'text' in 先前 else '') if 先前 is not None and 'kind' in 先前 and 先前['kind']=='reasoning' else ''#旧推理
        增=块['text'] if 块 is not None and 'text' in 块 and 块['text'] is not None else ''#增量
        块列表[槽]={'kind':'reasoning','text':旧文+增}#接上增量
    elif 类型=='tool-call-delta':#工具调用增量
        先前=块列表[槽]#该槽已有块
        if 先前 is not None and 'kind' in 先前 and 先前['kind']=='tool-call':#已是工具调用
            底=先前#沿用
        else:#否则空底
            底={'kind':'tool-call','callId':'','name':'','argsRaw':''}#空底
        调用标识=底['callId'] if 'callId' in 底 and 底['callId'] is not None else str(块['id'] if 块 is not None and 'id' in 块 and 块['id'] is not None else '')#调用 id
        名称=块['name'] if 块 is not None and 'name' in 块 and 块['name'] is not None else 底['name']#名
        旧参=底['argsRaw'] if 'argsRaw' in 底 and 底['argsRaw'] is not None else ''#旧参
        参增=块['argumentsDelta'] if 块 is not None and 'argumentsDelta' in 块 and 块['argumentsDelta'] is not None else ''#参增
        块列表[槽]={'kind':'tool-call','callId':调用标识,'name':名称,'argsRaw':旧参+参增}#累积工具调用
    elif 类型=='block-end':#块结束
        块列表[槽]=转助手块(块['block'] if 块 is not None and 'block' in 块 else None)#用完整块覆盖该槽
    else:#未知块种类
        return {**状态,'sawChunk':True}#只标记见块
    可见=有可见内容(压缩块(块列表))#压缩后是否已有可见内容
    新状态={**状态,'sawChunk':True,'blocks':块列表}#写出新状态
    if 可见 and ('firstVisibleSeq' not in 状态 or 状态['firstVisibleSeq'] is None):#首次出现可见内容
        新状态['firstVisibleSeq']=事件['seq']#记下序号
        新状态['firstVisibleTime']=事件['time']#记下时间
    if 是否令牌增量(块) and ('firstTokenTime' not in 状态 or 状态['firstTokenTime'] is None):#首次 token 增量
        新状态['firstTokenTime']=事件['time']#记下时间
    return 新状态#新状态

def 闭合边界(上下文):#从状态或位置推出已闭合的步/回合边界
    """有闭合边界则返回其 seq/time。"""
    状态=上下文['state'] if 'state' in 上下文 else None#本节点状态
    步结束=状态['stepEnd'] if 状态 is not None and 'stepEnd' in 状态 else None#step/end 命中
    步事件=步结束['event'] if 步结束 is not None and 'event' in 步结束 else None#步事件
    if 步事件 is not None and 'type' in 步事件 and 步事件['type']=='step/end':#已匹配 step/end
        return 步事件#取其事件
    起点=上下文['start'] if 'start' in 上下文 else None#起点
    位置=起点['location'] if 起点 is not None and 'location' in 起点 else None#起点位置
    if 位置 is None:#否则最后一次命中的位置
        命中列表=上下文['matches'] if 'matches' in 上下文 and 上下文['matches'] is not None else []#命中列表
        位置=命中列表[-1]['location'] if 命中列表 and 'location' in 命中列表[-1] else None#末次位置
    位置种=位置['kind'] if 位置 is not None and 'kind' in 位置 else None#位置种类
    步=位置['step'] if 位置 is not None and 'step' in 位置 else None#步
    if 位置种=='step' and 步 is not None and 'status' in 步 and 步['status']=='closed':#步已闭合
        return 步['end'] if 'end' in 步 else None#取步结束
    回合=位置['turn'] if 位置 is not None and 'turn' in 位置 else None#回合
    if 位置种 in ('step','turn') and 回合 is not None and 'status' in 回合 and 回合['status']=='closed':#回合已闭合
        return 回合['end'] if 'end' in 回合 else None#取回合结束
    return None#尚无闭合边界

def 结算节点(状态,上下文):#投影已结算或被打断的助手消息节点
    """有结算或打断证据才返回。"""
    结算=状态['final'] if 'final' in 状态 else None#assistant/message 命中
    结算事件=结算['event'] if 结算 is not None and 'event' in 结算 else None#结算事件
    if 结算事件 is not None and 'type' in 结算事件 and 结算事件['type']=='assistant/message':#已有完整结算
        事件=结算事件#取出结算事件
        数据=事件['data'] if 'data' in 事件 else None#载荷
        消息=数据['message'] if 数据 is not None and 'message' in 数据 else None#消息
        来源=消息['source'] if 消息 is not None and 'source' in 消息 else None#出处
        已开始=状态['started'] if 'started' in 状态 else None#已开始
        return {'kind':'assistant','seq':事件['seq'],'messageId':消息['id'] if 消息 is not None and 'id' in 消息 else None,'time':事件['time'],'turn':状态['turn'] if 'turn' in 状态 else None,'step':状态['step'] if 'step' in 状态 else None,'blocks':转助手块列表(消息['content'] if 消息 is not None and 'content' in 消息 else None),'usage':数据['usage'] if 数据 is not None and 'usage' in 数据 else None,'provenance':{'provider':来源['provider'] if 来源 is not None and 'provider' in 来源 else None,'model':来源['model'] if 来源 is not None and 'model' in 来源 else None},'timing':{'stepStartTime':状态['startTime'] if 已开始 else None,'firstTokenTime':状态['firstTokenTime'] if 'firstTokenTime' in 状态 else None,'completedTime':事件['time']}}#完整节点
    边界=闭合边界(上下文)#找闭合边界
    块列表=压缩块(状态['blocks'] if 'blocks' in 状态 and 状态['blocks'] is not None else [])#去掉稀疏洞
    if 边界 is None or not 有打断证据(块列表):#无边界或无打断证据
        return None#不投影
    return {'kind':'assistant','seq':边界['seq'],'time':边界['time'],'turn':状态['turn'] if 'turn' in 状态 else None,'step':状态['step'] if 'step' in 状态 else None,'blocks':块列表,'interrupted':True}#打断节点用边界序号，seq 保持 int

def 助手请求(状态,节点,边界):#把累积状态投影成 assistant RequestView
    """见过 start 才返回。"""
    if not (状态['started'] if 'started' in 状态 else None):#回放缺 start
        return None#不投影请求
    打断=节点 is not None and 'interrupted' in 节点 and 节点['interrupted'] is True#打断
    if 节点 is not None and not 打断:#已有未打断的结算节点
        状态字='complete'#视为完成
    elif ('retry' in 状态 and 状态['retry'] is not None) or 边界 is not None:#有重试或边界
        状态字='error'#出错
    else:#否则进行中
        状态字='running'#进行中
    完成于=节点['time'] if 节点 is not None and 'time' in 节点 else (边界['time'] if 边界 is not None and 'time' in 边界 else None)#完成时间
    请求={'purpose':'assistant','startSeq':状态['startSeq'] if 'startSeq' in 状态 else None,'turn':状态['turn'] if 'turn' in 状态 else None,'step':状态['step'] if 'step' in 状态 else None,'startedAt':状态['startTime'] if 'startTime' in 状态 else None,'completedAt':完成于,'status':状态字}#组装
    重试=状态['retry'] if 'retry' in 状态 else None#重试
    if 重试 is not None:#有重试则展开
        请求['error']=重试['message'] if 'message' in 重试 else None#失败展示文案
        请求['retry']=重试['retry'] if 'retry' in 重试 else None#当前重试次数
        if 'maxRetries' in 重试 and 重试['maxRetries'] is not None:#normal 模式才有上限
            请求['maxRetries']=重试['maxRetries']#上限
        请求['retryDelayMs']=重试['delayMs'] if 'delayMs' in 重试 else None#下次重试延迟
    if 节点 is not None and not 打断:#已结算
        请求['resultSeq']=节点['seq'] if 'seq' in 节点 else None#结算序号
        if 'provenance' in 节点 and 节点['provenance'] is not None:#有出处
            请求['provenance']=节点['provenance']#展开
    if 'usage' in 状态 and 状态['usage'] is not None:#有用量
        请求['usage']=状态['usage']#展开
    return 请求#RequestView

def 回放状态(上下文):#无 start 时从命中回放累积状态
    """可能仍 None（无助手事件）。"""
    状态=None#尚未见助手事件
    for 匹配 in (上下文['matches'] if 'matches' in 上下文 and 上下文['matches'] is not None else []):#按到达顺序回放
        事件=匹配['event'] if 'event' in 匹配 else None#取出事件
        种类=事件['type'] if 事件 is not None and 'type' in 事件 else None#事件类型
        数据=事件['data'] if 事件 is not None and 'data' in 事件 else None#载荷
        if 种类=='assistant/live-chunk':#流式块
            if 状态 is None:#首次见块则播种
                状态=初始状态(数据['turn'] if 数据 is not None and 'turn' in 数据 else None,数据['step'] if 数据 is not None and 'step' in 数据 else None,事件['seq'],事件['time'],False)#started=false
            状态=更新块(状态,匹配)#推进块与用量
        elif 种类=='assistant/message':#结算消息
            if 状态 is None:#首次见消息则播种
                状态=初始状态(数据['turn'] if 数据 is not None and 'turn' in 数据 else None,数据['step'] if 数据 is not None and 'step' in 数据 else None,事件['seq'],事件['time'],False)#播种
            消息=数据['message'] if 数据 is not None and 'message' in 数据 else None#消息
            用量=状态['usage'] if 状态 is not None and 'usage' in 状态 and 状态['usage'] is not None else (数据['usage'] if 数据 is not None and 'usage' in 数据 else None)#用量
            状态={**状态,'blocks':转助手块列表(消息['content'] if 消息 is not None and 'content' in 消息 else None),'final':匹配,'usage':用量}#覆盖块并记下结算
        elif 种类=='step/end' and 状态 is not None:#步结束且已有状态
            状态={**状态,'stepEnd':匹配}#记下 step/end 命中
    return 状态#可能仍 None

def 助手匹配(事件):#按事件类型归入本步
    """start / update / null。"""
    种类=事件['type'] if 'type' in 事件 else None#事件类型
    数据=事件['data'] if 'data' in 事件 else None#载荷
    回合=数据['turn'] if 数据 is not None and 'turn' in 数据 else None#回合
    步号=数据['step'] if 数据 is not None and 'step' in 数据 else None#步
    if 种类=='step/start':#步开始
        return {'id':f'{回合}:{步号}','role':'start'}#作本节点 start
    if 种类 in ('assistant/live-chunk','assistant/message','llm/retry','step/end'):#update 类
        return {'id':f'{回合}:{步号}','role':'update'}#作本节点 update
    return None#无关事件

def 助手开始(_上下文,匹配):#从 step/start 播种状态
    """见过 start，started=True。"""
    事件=匹配['event'] if 'event' in 匹配 else None#事件
    if 事件 is None or ('type' not in 事件) or 事件['type']!='step/start':#类型守卫
        raise 轨迹错误('trajectory-assistant-step start requires step/start')#类型收窄失败则抛
    数据=事件['data'] if 'data' in 事件 else None#载荷
    return 初始状态(数据['turn'] if 数据 is not None and 'turn' in 数据 else None,数据['step'] if 数据 is not None and 'step' in 数据 else None,事件['seq'],事件['time'],True)#初始状态

def 助手更新(上下文,匹配):#按后续事件推进状态
    """chunk / message / step/end / llm/retry。"""
    事件=匹配['event'] if 'event' in 匹配 else None#事件
    种类=事件['type'] if 事件 is not None and 'type' in 事件 else None#类型
    状态=上下文['state'] if 'state' in 上下文 else None#当前状态
    if 种类=='assistant/live-chunk':#流式块
        return 更新块(状态,匹配)#推进
    数据=事件['data'] if 事件 is not None and 'data' in 事件 else None#载荷
    if 种类=='assistant/message':#结算消息
        消息=数据['message'] if 数据 is not None and 'message' in 数据 else None#消息
        用量=状态['usage'] if 状态 is not None and 'usage' in 状态 and 状态['usage'] is not None else (数据['usage'] if 数据 is not None and 'usage' in 数据 else None)#用量
        return {**状态,'blocks':转助手块列表(消息['content'] if 消息 is not None and 'content' in 消息 else None),'final':匹配,'usage':用量}#覆盖块并记下结算
    if 种类=='step/end':#步结束
        return {**状态,'stepEnd':匹配}#记下
    if 种类!='llm/retry':#其余不改
        return 状态#原样
    重试={'message':展示失败文案(数据['failure'] if 数据 is not None and 'failure' in 数据 else None),'retry':数据['retry'] if 数据 is not None and 'retry' in 数据 else None,'delayMs':数据['delayMs'] if 数据 is not None and 'delayMs' in 数据 else None}#记下本次失败与延迟
    if 数据 is not None and 'mode' in 数据 and 数据['mode']=='normal':#normal 才带上限
        重试['maxRetries']=数据['maxRetries'] if 'maxRetries' in 数据 else None#上限
    新状态=初始状态(状态['turn'] if 'turn' in 状态 else None,状态['step'] if 'step' in 状态 else None,状态['startSeq'] if 'startSeq' in 状态 else None,状态['startTime'] if 'startTime' in 状态 else None,True)#按原起点重新播种
    新状态['firstTokenTime']=状态['firstTokenTime'] if 'firstTokenTime' in 状态 else None#保留首 token 时间
    新状态['usage']=状态['usage'] if 'usage' in 状态 else None#保留已累计用量
    新状态['retry']=重试#挂重试
    return 新状态#重试状态

def 助手发布(匹配):#控制该命中何时发布视图
    """start 不单独发布；用量/结束不发布。"""
    事件=匹配['event'] if 'event' in 匹配 else None#事件
    种类=事件['type'] if 事件 is not None and 'type' in 事件 else None#事件类型
    if 种类=='step/start':#start
        return 'none'#不单独发布
    if 种类!='assistant/live-chunk':#结算/重试/步结束
        return 'immediate'#立即发布
    数据=事件['data'] if 事件 is not None and 'data' in 事件 else None#载荷
    块=数据['chunk'] if 数据 is not None and 'chunk' in 数据 else None#块
    块类型=块['type'] if 块 is not None and 'type' in 块 else None#块种类
    return 'none' if 块类型 in ('usage','finish') else 'animation-frame'#用量/结束不发布

def 助手构建视图(上下文):#投影轨迹视图节点
    """三者皆空则不产出。"""
    状态=上下文['state'] if 'state' in 上下文 else None#有 start 用状态
    if 状态 is None:#否则回放
        状态=回放状态(上下文)#回放
    if 状态 is None:#无助手事件
        return None#不产出
    节点=结算节点(状态,上下文)#结算或打断节点
    边界=闭合边界(上下文)#闭合边界
    if 节点 is None and 边界 is None and ('sawChunk' in 状态 and 状态['sawChunk']):#尚在流式且已见块
        流式={'turn':状态['turn'] if 'turn' in 状态 else None,'step':状态['step'] if 'step' in 状态 else None,'blocks':压缩块(状态['blocks'] if 'blocks' in 状态 and 状态['blocks'] is not None else [])}#部分助手视图
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
    return 轨迹节点(上下文,状态['startSeq'] if 'startSeq' in 状态 else None,数据)#包进轨迹信封

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
    事件=匹配['event'] if 'event' in 匹配 else None#事件
    if 事件 is None or ('type' not in 事件) or 事件['type']!='turn/end':#类型守卫
        raise 轨迹错误('trajectory-turn-end start requires turn/end')#类型收窄失败则抛
    数据=事件['data'] if 'data' in 事件 else None#载荷
    原因=数据['reason'] if 数据 is not None and 'reason' in 数据 else None#结束原因
    状态={'turn':数据['turn'] if 数据 is not None and 'turn' in 数据 else None,'seq':事件['seq'],'time':事件['time']}#基本字段
    if 原因 is not None and 'kind' in 原因 and 原因['kind']=='error':#出错才展开 error
        状态['error']=展示失败文案(原因['error'] if 'error' in 原因 else None)#展示文案
    return 状态#状态

def 回合结束匹配(事件):#只匹配回合结束
    """以序号为 id 起步。"""
    if 'type' in 事件 and 事件['type']=='turn/end':#回合结束
        return {'id':str(事件['seq']),'role':'start'}#起步
    return None#其它

def 回合结束更新(上下文,_匹配):#无后续事件
    """状态原样。"""
    return 上下文['state'] if 'state' in 上下文 else None#原样

def 回合结束构建视图(上下文):#包进轨迹信封
    """无状态则不产出。"""
    状态=上下文['state'] if 'state' in 上下文 else None#状态
    if 状态 is None:#无
        return None#不产出
    数据={'kind':'turn-end','turn':状态['turn'] if 'turn' in 状态 else None,'time':状态['time'] if 'time' in 状态 else None}#贡献
    if 'error' in 状态 and 状态['error'] is not None:#有错误才展开
        数据['error']=状态['error']#错误
    return 轨迹节点(上下文,状态['seq'] if 'seq' in 状态 else None,数据)#包进轨迹信封

回合结束定义={#回合结束 Definition
    'kind':'trajectory-turn-end',#节点种类
    'target':'trajectory',#投递到轨迹槽
    'match':回合结束匹配,#只匹配回合结束
    'start':回合结束开始,#播种
    'update':回合结束更新,#无后续事件
    'buildViewNode':回合结束构建视图,#包进轨迹信封
}#定义结束

def 登记轨迹助手定义(上下文):#登记助手步与回合结束
    """登记轨迹助手生命周期 Definition。"""
    上下文.conversationEvents.register(轨迹助手定义)#登记助手流式/结算
    上下文.conversationEvents.register(回合结束定义)#登记回合结束
