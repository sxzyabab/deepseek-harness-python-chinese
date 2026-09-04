"""已完成回合的页脚数据与 Chat 节点。

对齐上游 `ui-chat/src/client/conversation-nodes/turn-tail.ts`。公开面仅中文名。
"""
from ..约定.回合指标 import 推导回合指标 as 派生回合指标#回合指标
from .公共 import 聊天合成序号偏移,聊天节点#公共
from .面辅助 import 取字段,是追加面事件,转助手块们#面辅助

__all__=['回合尾定义','登记回合尾会话节点']#仅中文公开名

def 有文本助手(事件):#终态助手是否含非空文本
    """assistant/message + 追加面 + 非空 text 块。"""
    if 取字段(事件,'type')!='assistant/message' or not 是追加面事件(事件):#非
        return False#否
    内容=取字段(取字段(取字段(事件,'data'),'message'),'content')#内容
    return any(取字段(块,'kind')=='text' and (取字段(块,'text') or '').strip()!='' for 块 in 转助手块们(内容))#有文本

def 块有文本(事件):#流式块是否带非空文本
    """text-delta 或 block-end 文本。"""
    if 取字段(事件,'type')!='assistant/chunk':#非
        return False#否
    块=取字段(取字段(事件,'data'),'chunk') or {}#块
    种=取字段(块,'type')#种
    if 种=='text-delta':#增量
        return (取字段(块,'text') or '').strip()!=''#非空
    if 种=='block-end':#块结束
        定=取字段(块,'block') or {}#定稿
        return 取字段(定,'type')=='text' and (取字段(定,'text') or '').strip()!=''#非空文本
    return False#其它

def 回合坐标(事件):#从事件读回合/步骤坐标
    """没有则 None。"""
    种=取字段(事件,'type')#种
    数据=取字段(事件,'data') or {}#载荷
    if 种 in ('assistant/message','assistant/chunk','step/end','llm/retry'):#带坐标
        出={'turn':取字段(数据,'turn')}#回合
        if 取字段(数据,'step') is not None:#有步
            出['step']=取字段(数据,'step')#步
        return 出#坐标
    return None#无

def 收口锚(上下文):#收口节点应挂的合成序号
    """终态文本之后，或中断流式之后。"""
    匹配们=取字段(上下文,'matches') or []#匹配
    终点=next((候 for 候 in 匹配们 if 取字段(取字段(候,'event'),'type')=='turn/end'),None)#turn/end
    起点=取字段(上下文,'start')#起点
    锚=取字段(取字段(终点,'event'),'seq') if 终点 is not None else None#优先
    if 锚 is None and 起点 is not None:#无终点
        锚=取字段(取字段(起点,'event'),'seq')#开节点
    if 锚 is None and 匹配们:#仍无
        锚=取字段(取字段(匹配们[0],'event'),'seq')#首匹配
    if 锚 is None:#都无
        锚=0#零
    步证={}#步 → 证据
    for 匹配项 in 匹配们:#扫
        事件=取字段(匹配项,'event')#事件
        if 取字段(事件,'type')=='turn/end':#回合结束
            continue#跳过
        坐标=回合坐标(事件)#坐标
        if 坐标 is None or 坐标.get('step') is None:#无步
            continue#跳过
        步=坐标['step']#步号
        先前=步证.get(步) or {'streamedText':False,'finalized':False}#证据
        种=取字段(事件,'type')#种
        if 种=='assistant/chunk':#流式
            步证[步]={**先前,'streamedText':先前['streamedText'] or 块有文本(事件)}#更新
            continue#下
        if 种=='assistant/message':#终态
            步证[步]={'streamedText':False,'finalized':True}#覆盖
            if 有文本助手(事件):#有文本
                锚=取字段(事件,'seq')+聊天合成序号偏移['finalizedFollowup']#挪锚
            continue#下
        if 种=='llm/retry':#重试
            步证[步]={'streamedText':False,'finalized':False}#清空
            continue#下
        if 种=='step/end' and 先前['streamedText'] and not 先前['finalized']:#中断收口
            锚=取字段(事件,'seq')+聊天合成序号偏移['interruptedFollowup']#中断锚
    return 锚#最终

def 回合位置(上下文):#取回合位置
    """turn/step 才有。"""
    起点=取字段(上下文,'start')#起点
    匹配们=取字段(上下文,'matches') or []#匹配
    位置=取字段(起点,'location') if 起点 is not None else (取字段(匹配们[0],'location') if 匹配们 else None)#位置
    if 取字段(位置,'kind') in ('turn','step'):#有
        return 取字段(位置,'turn')#回合
    return None#无

def 有文本(数据):#助手行是否已终态且含非空文本
    """须有 finalNode 与非空 text。"""
    if 取字段(数据,'finalNode') is None:#无终态
        return False#否
    return any(取字段(块,'kind')=='text' and (取字段(块,'text') or '').strip()!='' for 块 in (取字段(数据,'blocks') or []))#有

def 尾载荷(上下文):#折叠已结束回合的尾载荷
    """尚未结束则 None。"""
    态=取字段(上下文,'state') or {}#态
    结束=态.get('end')#已记下
    if 结束 is None:#无
        结束=next((候 for 候 in (取字段(上下文,'matches') or []) if 取字段(取字段(候,'event'),'type')=='turn/end'),None)#找
    if 结束 is None or 取字段(取字段(结束,'event'),'type')!='turn/end':#尚未结束
        return None#无法出尾
    回合=回合位置(上下文)#回合位置
    if 回合 is None:#无
        return None#无法
    步们=取字段(回合,'steps') or []#各步
    助手们=[]#助手行
    for 步 in 步们:#每步
        数据面=取字段(步,'data')#data
        候=数据面.get('assistant-step') if hasattr(数据面,'get') else None#助手
        if 候 is not None:#有
            助手们.append(候)#收下
    已结=[候 for 候 in 助手们 if 取字段(候,'finalNode') is not None]#有终态
    已结=sorted(已结,key=lambda 候:取字段(取字段(候,'finalNode'),'seq',0))#按 seq
    收束=None#收口
    for 候 in reversed(已结):#从后找
        if 有文本(候):#有文本
            收束=候#收口
            break#停
    最新转录=取字段(取字段(已结[-1],'finalNode'),'seq') if 已结 else None#默认
    for 匹配项 in (取字段(上下文,'matches') or []):#扫转录
        事件=取字段(匹配项,'event')#事件
        种=取字段(事件,'type')#种
        数据=取字段(事件,'data') or {}#载荷
        候选=None#候选 seq
        if 种=='tool/call' or (种=='tool/result' and 是追加面事件(事件)) or 种=='llm/retry':#算转录
            候选=取字段(事件,'seq')#序号
        elif 种=='turn/end' and 取字段(取字段(数据,'reason'),'kind')=='error':#出错结束
            候选=取字段(事件,'seq')#序号
        if 候选 is not None and (最新转录 is None or 候选>最新转录):#更晚
            最新转录=候选#抬高
    指标表=派生回合指标([取字段(候,'finalNode') for 候 in 已结])#按终态算
    回合号=取字段(取字段(结束,'event'),'data',{}).get('turn') if isinstance(取字段(取字段(结束,'event'),'data'),dict) else 取字段(取字段(取字段(结束,'event'),'data'),'turn')#回合号
    指标=指标表.get(回合号) if isinstance(指标表,dict) else None#本回合
    出={#回合尾载荷
        'turn':回合号,#回合
        'seq':取字段(取字段(结束,'event'),'seq'),#序号
        'time':取字段(取字段(结束,'event'),'time'),#时刻
        'closing':收束,#收口
        'branchUnavailable':收束 is None or 最新转录!=取字段(取字段(收束,'finalNode'),'seq'),#能否分叉
    }#结束
    if 指标 is not None:#有指标
        if 指标.get('ttftMs') is not None:#TTFT
            出['ttftMs']=指标['ttftMs']#带上
        if 指标.get('tokensPerSecond') is not None:#吞吐
            出['tokensPerSecond']=指标['tokensPerSecond']#带上
    return 出#载荷

def 回合尾匹配(事件):#判定事件是否属于本节点
    """turn/start 开；end/工具/坐标更新。"""
    种=取字段(事件,'type')#种
    数据=取字段(事件,'data') or {}#载荷
    if 种=='turn/start':#开始
        return {'id':str(取字段(数据,'turn')),'role':'start'}#开
    if 种=='turn/end':#结束
        return {'id':str(取字段(数据,'turn')),'role':'update'}#更新
    if 种 in ('tool/call','tool/result'):#工具
        return {'id':str(取字段(数据,'turn')),'role':'update'}#更新
    坐标=回合坐标(事件)#坐标
    if 坐标 is not None:#有
        return {'id':str(坐标['turn']),'role':'update'}#更新
    return None#忽略

def 回合尾开始(_上下文,匹配项):#用 turn/start 建折叠状态
    """必须是 turn/start。"""
    事件=取字段(匹配项,'event')#事件
    if 取字段(事件,'type')!='turn/start':#非
        raise Exception('turn-tail start requires turn/start')#硬失败
    return {'turn':取字段(取字段(事件,'data'),'turn')}#记下

def 回合尾更新(上下文,匹配项):#turn/end 写入 end 匹配
    """其余不改。"""
    if 取字段(取字段(匹配项,'event'),'type')=='turn/end':#结束
        return {**取字段(上下文,'state'),'end':匹配项}#记下
    return 取字段(上下文,'state')#不改

def 回合尾发布(匹配项):#只有结束才立刻发表
    """immediate / none。"""
    return 'immediate' if 取字段(取字段(匹配项,'event'),'type')=='turn/end' else 'none'#发表

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
    数据面=取字段(回合,'data')#data
    数据=数据面.get('turn-tail') if hasattr(数据面,'get') else None#尾载荷
    if 数据 is None:#无
        return None#无
    return 聊天节点(上下文,'turn-tail',收口锚(上下文),数据)#节点

回合尾定义={#回合尾会话节点定义
    'kind':'turn-tail','target':'chat',#kind/目标
    'match':回合尾匹配,'start':回合尾开始,'update':回合尾更新,#生命周期
    'publication':回合尾发布,'buildLocationData':回合尾位置数据,'buildViewNode':回合尾建视图,#发布/视图
}#结束

def 登记回合尾会话节点(上下文):#注册已完成回合页脚
    """挂到 conversationEvents。"""
    上下文.conversationEvents.register(回合尾定义)#登记
