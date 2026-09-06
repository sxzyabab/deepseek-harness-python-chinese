"""已完成回合的页脚数据与 Chat 节点。

对齐上游 `ui-chat/src/client/conversation-nodes/turn-tail.ts`。公开面仅中文名。
"""
from ..约定.回合指标 import 推导回合指标 as 派生回合指标#回合指标
from .节点工厂 import 聊天错误,聊天合成序号偏移,聊天节点#公共
from .事件面 import 是追加面事件,转助手块列表#面辅助

__all__=['回合尾定义','登记回合尾会话节点']#仅中文公开名

def 有文本助手(事件):#终态助手是否含非空文本
    """assistant/message + 追加面 + 非空 text 块。"""
    if 事件['type']!='assistant/message' or not 是追加面事件(事件):#非
        return False#否
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    消息=数据['message'] if 'message' in 数据 else None#消息
    内容=消息['content'] if 消息 is not None and 'content' in 消息 else None#内容
    for 块 in 转助手块列表(内容):#扫
        文=块['text'] if 'kind' in 块 and 块['kind']=='text' and 'text' in 块 and 块['text'] is not None else ''#正文
        if 'kind' in 块 and 块['kind']=='text' and 文.strip()!='':#有文本
            return True#有
    return False#无

def 块有文本(事件):#流式块是否带非空文本
    """text-delta 或 block-end 文本。"""
    if 事件['type']!='assistant/chunk':#非
        return False#否
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    块=数据['chunk'] if 'chunk' in 数据 and 数据['chunk'] is not None else {}#块
    种=块['type'] if 'type' in 块 else None#种
    if 种=='text-delta':#增量
        文=块['text'] if 'text' in 块 and 块['text'] is not None else ''#正文
        return 文.strip()!=''#非空
    if 种=='block-end':#块结束
        定=块['block'] if 'block' in 块 and 块['block'] is not None else {}#定稿
        文=定['text'] if 'text' in 定 and 定['text'] is not None else ''#正文
        return 'type' in 定 and 定['type']=='text' and 文.strip()!=''#非空文本
    return False#其它

def 回合坐标(事件):#从事件读回合/步骤坐标
    """没有则 None。"""
    种=事件['type']#种
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    if 种 in ('assistant/message','assistant/chunk','step/end','llm/retry'):#带坐标
        出={'turn':数据['turn'] if 'turn' in 数据 else None}#回合
        if 'step' in 数据 and 数据['step'] is not None:#有步
            出['step']=数据['step']#步
        return 出#坐标
    return None#无

def 收口锚(上下文):#收口节点应挂的合成序号
    """终态文本之后，或中断流式之后。"""
    匹配列表=上下文['matches'] if 'matches' in 上下文 and 上下文['matches'] is not None else []#匹配
    终点=None#turn/end
    for 候 in 匹配列表:#扫
        if 候['event']['type']=='turn/end':#命中
            终点=候#记下
            break#停
    起点=上下文['start'] if 'start' in 上下文 else None#起点
    锚=终点['event']['seq'] if 终点 is not None else None#优先
    if 锚 is None and 起点 is not None:#无终点
        锚=起点['event']['seq']#开节点
    if 锚 is None and len(匹配列表)>0:#仍无
        锚=匹配列表[0]['event']['seq']#首匹配
    if 锚 is None:#都无
        锚=0#零
    步证={}#步 → 证据
    for 匹配项 in 匹配列表:#扫
        事件=匹配项['event']#事件
        if 事件['type']=='turn/end':#回合结束
            continue#跳过
        坐标=回合坐标(事件)#坐标
        if 坐标 is None or 'step' not in 坐标 or 坐标['step'] is None:#无步
            continue#跳过
        步=坐标['step']#步号
        先前=步证[步] if 步 in 步证 else {'streamedText':False,'finalized':False}#证据
        种=事件['type']#种
        if 种=='assistant/chunk':#流式
            步证[步]={**先前,'streamedText':先前['streamedText'] or 块有文本(事件)}#更新
            continue#下
        if 种=='assistant/message':#终态
            步证[步]={'streamedText':False,'finalized':True}#覆盖
            if 有文本助手(事件):#有文本
                锚=事件['seq']+聊天合成序号偏移['finalizedFollowup']#挪锚
            continue#下
        if 种=='llm/retry':#重试
            步证[步]={'streamedText':False,'finalized':False}#清空
            continue#下
        if 种=='step/end' and 先前['streamedText'] and not 先前['finalized']:#中断收口
            锚=事件['seq']+聊天合成序号偏移['interruptedFollowup']#中断锚
    return 锚#最终

def 回合位置(上下文):#取回合位置
    """turn/step 才有。"""
    起点=上下文['start'] if 'start' in 上下文 else None#起点
    匹配列表=上下文['matches'] if 'matches' in 上下文 and 上下文['matches'] is not None else []#匹配
    if 起点 is not None and 'location' in 起点:#有起点
        位置=起点['location']#位置
    elif len(匹配列表)>0 and 'location' in 匹配列表[0]:#首匹配
        位置=匹配列表[0]['location']#位置
    else:#无
        位置=None#无
    if 位置 is not None and 'kind' in 位置 and 位置['kind'] in ('turn','step'):#有
        return 位置['turn'] if 'turn' in 位置 else None#回合
    return None#无

def 有文本(数据):#助手行是否已终态且含非空文本
    """须有 finalNode 与非空 text。"""
    if 'finalNode' not in 数据 or 数据['finalNode'] is None:#无终态
        return False#否
    块列表=数据['blocks'] if 'blocks' in 数据 and 数据['blocks'] is not None else []#块
    for 块 in 块列表:#扫
        文=块['text'] if 'kind' in 块 and 块['kind']=='text' and 'text' in 块 and 块['text'] is not None else ''#正文
        if 'kind' in 块 and 块['kind']=='text' and 文.strip()!='':#有
            return True#有
    return False#无

def 终态序号(候):#排序键：终态 seq
    """无则 0。"""
    终=候['finalNode'] if 'finalNode' in 候 else None#终态
    return 终['seq'] if 终 is not None and 'seq' in 终 else 0#序号

def 尾载荷(上下文):#折叠已结束回合的尾载荷
    """尚未结束则 None。"""
    态=上下文['state'] if 'state' in 上下文 and 上下文['state'] is not None else {}#态
    结束=态['end'] if 'end' in 态 else None#已记下
    if 结束 is None:#无
        匹配列表=上下文['matches'] if 'matches' in 上下文 and 上下文['matches'] is not None else []#匹配
        for 候 in 匹配列表:#扫
            if 候['event']['type']=='turn/end':#命中
                结束=候#记下
                break#停
    if 结束 is None or 结束['event']['type']!='turn/end':#尚未结束
        return None#无法出尾
    回合=回合位置(上下文)#回合位置
    if 回合 is None:#无
        return None#无法
    步列表=回合['steps'] if 'steps' in 回合 and 回合['steps'] is not None else []#各步
    助手列表=[]#助手行
    for 步 in 步列表:#每步
        数据面=步['data'] if 'data' in 步 else None#data
        候=数据面['assistant-step'] if 数据面 is not None and 'assistant-step' in 数据面 else None#助手
        if 候 is not None:#有
            助手列表.append(候)#收下
    已结=[候 for 候 in 助手列表 if 'finalNode' in 候 and 候['finalNode'] is not None]#有终态
    已结=sorted(已结,key=终态序号)#按 seq
    收束=None#收口
    for 候 in reversed(已结):#从后找
        if 有文本(候):#有文本
            收束=候#收口
            break#停
    最新转录=已结[-1]['finalNode']['seq'] if len(已结)>0 else None#默认
    匹配列表=上下文['matches'] if 'matches' in 上下文 and 上下文['matches'] is not None else []#匹配
    for 匹配项 in 匹配列表:#扫转录
        事件=匹配项['event']#事件
        种=事件['type']#种
        数据=事件['data'] if 'data' in 事件 else {}#载荷
        候选=None#候选 seq
        if 种=='tool/call' or (种=='tool/result' and 是追加面事件(事件)) or 种=='llm/retry':#算转录
            候选=事件['seq']#序号
        else:#可能出错结束
            原因=数据['reason'] if 'reason' in 数据 else None#原因
            if 种=='turn/end' and 原因 is not None and 'kind' in 原因 and 原因['kind']=='error':#出错结束
                候选=事件['seq']#序号
        if 候选 is not None and (最新转录 is None or 候选>最新转录):#更晚
            最新转录=候选#抬高
    指标表=派生回合指标([候['finalNode'] for 候 in 已结])#按终态算
    结束数据=结束['event']['data'] if 'data' in 结束['event'] else {}#载荷
    回合号=结束数据['turn'] if 'turn' in 结束数据 else None#回合号
    指标=指标表[回合号] if isinstance(指标表,dict) and 回合号 in 指标表 else None#本回合
    收束终=收束['finalNode'] if 收束 is not None and 'finalNode' in 收束 else None#收束终态
    出={#回合尾载荷
        'turn':回合号,#回合
        'seq':结束['event']['seq'],#序号
        'time':结束['event']['time'] if 'time' in 结束['event'] else None,#时刻
        'closing':收束,#收口
        'branchUnavailable':收束 is None or 最新转录!=(收束终['seq'] if 收束终 is not None and 'seq' in 收束终 else None),#能否分叉
    }#结束
    if 指标 is not None:#有指标
        if 'ttftMs' in 指标 and 指标['ttftMs'] is not None:#TTFT
            出['ttftMs']=指标['ttftMs']#带上
        if 'tokensPerSecond' in 指标 and 指标['tokensPerSecond'] is not None:#吞吐
            出['tokensPerSecond']=指标['tokensPerSecond']#带上
    return 出#载荷

def 回合尾匹配(事件):#判定事件是否属于本节点
    """turn/start 开；end/工具/坐标更新。"""
    种=事件['type']#种
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    if 种=='turn/start':#开始
        return {'id':str(数据['turn']),'role':'start'}#开
    if 种=='turn/end':#结束
        return {'id':str(数据['turn']),'role':'update'}#更新
    if 种 in ('tool/call','tool/result'):#工具
        return {'id':str(数据['turn']),'role':'update'}#更新
    坐标=回合坐标(事件)#坐标
    if 坐标 is not None:#有
        return {'id':str(坐标['turn']),'role':'update'}#更新
    return None#忽略

def 回合尾开始(_上下文,匹配项):#用 turn/start 建折叠状态
    """必须是 turn/start。"""
    事件=匹配项['event']#事件
    if 事件['type']!='turn/start':#非
        raise 聊天错误('turn-tail start requires turn/start')#硬失败
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    return {'turn':数据['turn'] if 'turn' in 数据 else None}#记下

def 回合尾更新(上下文,匹配项):#turn/end 写入 end 匹配
    """其余不改。"""
    if 匹配项['event']['type']=='turn/end':#结束
        return {**上下文['state'],'end':匹配项}#记下
    return 上下文['state']#不改

def 回合尾发布(匹配项):#只有结束才立刻发表
    """immediate / none。"""
    return 'immediate' if 匹配项['event']['type']=='turn/end' else 'none'#发表

def 回合尾位置数据(上下文,作用域):#往回合位置写折叠数据
    """只贡献回合范围。"""
    if 作用域!='turn':#非
        return None#无
    值=尾载荷(上下文)#折叠
    if 值 is None:#未结束
        return None#不写
    return {'kind':'turn','turn':值['turn'],'key':'turn-tail','value':值}#位置数据

def 回合尾建视图(上下文):#组装 Chat 目标上的回合尾节点
    """读已写入的尾载荷。"""
    回合=回合位置(上下文)#回合
    if 回合 is None:#无
        return None#无
    数据面=回合['data'] if 'data' in 回合 else None#data
    数据=数据面['turn-tail'] if 数据面 is not None and 'turn-tail' in 数据面 else None#尾载荷
    if 数据 is None:#无
        return None#无
    return 聊天节点(上下文,'turn-tail',收口锚(上下文),数据)#节点

回合尾定义={#回合尾会话节点定义
    'kind':'turn-tail','target':'chat',#kind/目标
    'match':回合尾匹配,'start':回合尾开始,'update':回合尾更新,#生命周期
    'publication':回合尾发布,'buildLocationData':回合尾位置数据,'buildViewNode':回合尾建视图,#发布/视图
}#结束

def 登记回合尾会话节点(上下文):#注册已完成回合页脚
    """挂到 uiConversation.events。"""
    上下文.uiConversation.events.register(回合尾定义)#登记
