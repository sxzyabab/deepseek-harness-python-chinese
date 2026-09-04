"""轮次作用域的过程范围与正文边界 Definition。

对齐上游 `ui-chat/src/client/conversation-nodes/turn-process.ts`。公开面仅中文名。
"""
from ..约定.助手内容 import 有助手回复内容#可见回复
from ..约定.回合过程 import 是子代理委派工具,同回合过程规格,回合过程规格#过程契约
from .公共 import 聊天合成序号偏移,聊天节点#公共
from .事件投影 import 转助手块们#块转换
from .面辅助 import 取字段,是追加面事件#面辅助

__all__=['回合过程定义','登记回合过程']#仅中文公开名

def 事件回合(事件):#从事件取轮次
    """数字轮次或缺席。"""
    数据=取字段(事件,'data') or {}#载荷
    回合=取字段(数据,'turn')#轮次
    return 回合 if isinstance(回合,(int,float)) and not isinstance(回合,bool) else None#数字

def 是块行事件(事件):#是否 chunk 行事件
    """三种 chunkrow。"""
    return 取字段(事件,'type') in ('chunkrow/text-chunks','chunkrow/reasoning-chunks','chunkrow/tool-call-chunks')#三种

def 可见助手事件(事件):#是否可见 Assistant 事件
    """流式或定稿可见正文。"""
    种=取字段(事件,'type')#种
    if 种=='assistant/chunk':#流式
        块=取字段(取字段(事件,'data'),'chunk') or {}#块
        块种=取字段(块,'type')#块种
        if 块种 in ('text-delta','reasoning-delta'):#增量
            return (取字段(块,'text') or '').strip()!=''#非空
        if 块种=='block-start':#开始
            return 取字段(块,'blockType') not in ('text','reasoning','tool-call')#其它可见
        if 块种!='block-end':#非结束
            return False#否
        定=取字段(块,'block') or {}#定稿
        if 取字段(定,'type')=='tool-call':#工具
            return False#否
        if 取字段(定,'type') in ('text','reasoning'):#文本
            return (取字段(定,'text') or '').strip()!=''#非空
        return True#其它
    if 种=='assistant/message' and 是追加面事件(事件):#定稿
        内容=取字段(取字段(取字段(事件,'data'),'message'),'content')#内容
        return 有助手回复内容(转助手块们(内容))#可见
    return False#否

def 过程证据(事件):#从事件取过程证据
    """assistant 或 other。"""
    if 是块行事件(事件):#chunk 行
        if 取字段(事件,'type')=='chunkrow/tool-call-chunks':#工具行
            return None#不算
        文们=取字段(取字段(事件,'data'),'texts') or []#文本
        首=next((甲 for 甲,文 in enumerate(文们) if str(文).strip()!=''),-1)#首非空
        if 首<0:#全空
            return None#无
        return {'kind':'assistant','seq':取字段(事件,'seq')+首,'step':取字段(取字段(事件,'data'),'step')}#证据
    if 可见助手事件(事件):#可见助手
        数据=取字段(事件,'data') or {}#载荷
        return {'kind':'assistant','seq':取字段(事件,'seq'),'step':取字段(数据,'step')}#证据
    种=取字段(事件,'type')#种
    if 种=='tool/call' or (种=='tool/result' and 是追加面事件(事件)) or 种=='llm/retry':#其它
        return {'kind':'other','seq':取字段(事件,'seq')}#其它
    return None#无

def 更新过程状态(态,事件):#更新过程状态
    """消息/工具计数与证据锚点。"""
    当前=态#累计
    种=取字段(事件,'type')#种
    数据=取字段(事件,'data') or {}#载荷
    if 种=='assistant/message' and 是追加面事件(事件) and 有助手回复内容(转助手块们(取字段(取字段(数据,'message'),'content'))):#消息
        步进=dict(当前.get('messageCountByStep') or {})#拷贝
        步=取字段(数据,'step')#步
        步进[步]=步进.get(步,0)+1#+1
        当前={**当前,'messageCountByStep':步进,'messageCount':当前.get('messageCount',0)+1}#更新
    if 种=='tool/call':#工具
        委派=是子代理委派工具(取字段(数据,'name') or '')#委派
        当前={#计数
            **当前,
            'toolCallCount':当前.get('toolCallCount',0)+(0 if 委派 else 1),#工具
            'subagentCount':当前.get('subagentCount',0)+(1 if 委派 else 0),#subagent
        }#结束
    证据=过程证据(事件)#证据
    if 证据 is None:#无
        return 当前#原样
    if 证据['kind']=='other':#其它
        if 当前.get('otherStartSeq') is not None:#已有
            return 当前#不变
        锚=当前.get('controlAnchorSeq')#控件
        return {#首个其它
            **当前,
            'otherStartSeq':证据['seq'],#起点
            'controlAnchorSeq':证据['seq'] if 锚 is None else min(锚,证据['seq']),#控件
        }#结束
    步进起=dict(当前.get('assistantStartByStep') or {})#拷贝
    if 证据['step'] in 步进起:#已记
        return 当前#不变
    步进起[证据['step']]=证据['seq']#记
    锚=当前.get('controlAnchorSeq')#控件
    return {#助手证据
        **当前,
        'assistantStartByStep':步进起,#步进
        'controlAnchorSeq':证据['seq'] if 锚 is None else min(锚,证据['seq']),#控件
    }#结束

def 回合过程匹配(事件):#匹配事件
    """turn/start 开；过程相关更新。"""
    种=取字段(事件,'type')#种
    数据=取字段(事件,'data') or {}#载荷
    if 种=='turn/start':#开始
        return {'id':str(取字段(数据,'turn')),'role':'start'}#开
    回合=事件回合(事件)#轮次
    if 回合 is None:#无
        return None#不
    if 种 in ('assistant/chunk','assistant/message','tool/call','tool/result','llm/retry','step/start','step/end','turn/end') or 是块行事件(事件):#相关
        return {'id':str(回合),'role':'update'}#更新
    return None#否

def 回合过程开始(_上下文,匹配项):#起始状态
    """turn/start。"""
    事件=取字段(匹配项,'event')#事件
    if 取字段(事件,'type')!='turn/start':#必须
        raise Exception('turn-process start requires turn/start')#硬失败
    return {#初态
        'turn':取字段(取字段(事件,'data'),'turn'),#轮次
        'assistantStartByStep':{},#步进起
        'messageCountByStep':{},#步进消息
        'messageCount':0,'toolCallCount':0,'subagentCount':0,#计数
    }#结束

def 回合过程更新(上下文,匹配项):#折事件
    """更新过程状态。"""
    return 更新过程状态(取字段(上下文,'state') or {},取字段(匹配项,'event'))#折

def 回合过程建视图(上下文):#造过程控件节点
    """无控件锚则不渲染。"""
    态=取字段(上下文,'state')#态
    if 态 is None or 态.get('controlAnchorSeq') is None:#无锚
        return None#无
    规格=回合过程规格(#规格
        态['turn'],态['controlAnchorSeq'],态['controlAnchorSeq'],
        None,None,False,态.get('messageCount',0),态.get('toolCallCount',0),态.get('subagentCount',0),
    )#简化开放规格
    锚=态['controlAnchorSeq']+聊天合成序号偏移['processControl']#过程控件偏移
    return 聊天节点(上下文,'turn-process',锚,规格)#节点

回合过程定义={#过程定义
    'kind':'turn-process','target':'chat',#kind/目标
    'match':回合过程匹配,'start':回合过程开始,'update':回合过程更新,'buildViewNode':回合过程建视图,#生命周期
}#结束

def 登记回合过程(上下文):#登记轮次过程
    """挂到 conversationEvents。"""
    上下文.conversationEvents.register(回合过程定义)#登记
