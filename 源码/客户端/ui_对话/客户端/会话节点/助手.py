"""助手步骤会话节点：流式 / 定稿 / 打断。

对齐上游 `ui-conversation/src/client/conversation-nodes/assistant.ts`。公开面仅中文名。
"""
from .公共 import 聊天合成序号偏移,聊天节点#公共
from .面辅助 import 取字段,是追加面事件,空助手块,转助手块,转助手块们,是令牌增量#面辅助

__all__=['助手定义','登记助手会话节点']#仅中文公开名

def 初态(回合,步):#空的逐步助手状态
    """初始字段。"""
    return {#初态
        'turn':回合,'step':步,'blocks':[],#坐标与块
        'firstVisibleSeq':None,'firstVisibleTime':None,'firstTokenTime':None,#边界
        'hidden':False,'final':None,'usage':None,#隐藏/定稿/用量
    }#结束

def 压实块(块们):#压实稀疏块
    """丢掉空洞。"""
    return [块 for 块 in 块们 if 块 is not None]#非空

def 有可见内容(块们):#是否有对用户可见的内容
    """工具调用不算可见正文。"""
    for 块 in 块们:#逐块
        种=取字段(块,'kind')#种
        if 种=='tool-call':#工具
            continue#不算
        if 种 in ('text','reasoning'):#文本/推理
            if (取字段(块,'text') or '').strip()!='':#非空白
                return True#可见
            continue#空白
        return True#其它可见
    return False#无

def 有打断证据(块们):#打断投影是否有可展示证据
    """任一非空块即算。"""
    for 块 in 块们:#逐块
        种=取字段(块,'kind')#种
        if 种 in ('text','reasoning'):#文本/推理
            if (取字段(块,'text') or '').strip()!='':#非空白
                return True#有
            continue#空白
        return True#其它也算
    return False#无

def 重试重置(态):#llm/retry 后清空块并隐藏
    """首 token 跨重试保留。"""
    下=初态(态['turn'],态['step'])#空
    下['firstTokenTime']=态.get('firstTokenTime')#保留
    下['hidden']=True#隐藏
    return 下#重试态

def 折流块(态,匹配项):#把一块 assistant/chunk 折进状态
    """按流块判别标签更新稀疏块。"""
    事件=取字段(匹配项,'event')#事件
    if 取字段(事件,'type')!='assistant/chunk':#非
        return 态#原样
    块=取字段(取字段(事件,'data'),'chunk') or {}#流块
    块们=list(态.get('blocks') or [])#复制
    种=取字段(块,'type')#种
    下标=取字段(块,'index',0)#下标
    while len(块们)<=下标:#扩容
        块们.append(None)#空洞
    if 种=='block-start':#块开始
        块们[下标]=空助手块(取字段(块,'blockType'))#空底座
    elif 种=='text-delta':#文本增量
        旧=块们[下标]#已有
        旧文=取字段(旧,'text') if 取字段(旧,'kind')=='text' else ''#旧文
        块们[下标]={'kind':'text','text':旧文+取字段(块,'text','')}#追加
    elif 种=='reasoning-delta':#推理增量
        旧=块们[下标]#已有
        旧文=取字段(旧,'text') if 取字段(旧,'kind')=='reasoning' else ''#旧文
        块们[下标]={'kind':'reasoning','text':旧文+取字段(块,'text','')}#追加
    elif 种=='tool-call-delta':#工具增量
        旧=块们[下标]#已有
        if 取字段(旧,'kind')=='tool-call':#已是
            底=旧#沿用
        else:#空底座
            底={'kind':'tool-call','callId':'','name':'','argsRaw':''}#空
        块们[下标]={#换
            'kind':'tool-call',#工具
            'callId':取字段(底,'callId') or str(取字段(块,'id') or ''),#callId
            'name':取字段(块,'name') if 取字段(块,'name') is not None else 取字段(底,'name'),#名
            'argsRaw':取字段(底,'argsRaw','')+取字段(块,'argumentsDelta',''),#参数增量
        }#结束
    elif 种=='block-end':#块结束
        块们[下标]=转助手块(取字段(块,'block'))#定稿块
    elif 种=='usage':#用量
        return {**态,'usage':取字段(块,'usage')}#只改用量
    else:#未知/finish
        return 态#原样
    可见=有可见内容(压实块(块们))#可见否
    首令牌=是令牌增量(块)#首 token
    下={**态,'blocks':块们,'hidden':False if 可见 else 态.get('hidden')}#更新
    if 可见 and 态.get('firstVisibleSeq') is None:#首次可见
        下['firstVisibleSeq']=取字段(事件,'seq')#序号
        下['firstVisibleTime']=取字段(事件,'time')#时间
    if 首令牌 and 态.get('firstTokenTime') is None:#首次 token
        下['firstTokenTime']=取字段(事件,'time')#时间
    return 下#更新态

def 关闭边界(位置):#已关闭位置的结束边界
    """步骤或回合关闭边界。"""
    种=取字段(位置,'kind')#种
    if 种=='step':#步骤
        步=取字段(位置,'step') or {}#步
        if 取字段(步,'status')=='closed' and 取字段(步,'end') is not None:#已关
            return 取字段(步,'end')#步骤结束
    if 种 in ('step','turn'):#步骤或回合
        回合=取字段(位置,'turn') or {}#回合
        if 取字段(回合,'status')=='closed' and 取字段(回合,'end') is not None:#已关
            return 取字段(回合,'end')#回合结束
    return None#仍开放

def 定稿节点(态,上下文):#从状态与上下文合成定稿或打断助手节点
    """有定稿消息优先；否则关闭边界+证据合成打断。"""
    终=态.get('final')#定稿匹配
    终事件=取字段(终,'event') if 终 is not None else None#事件
    if 终事件 is not None and 取字段(终事件,'type')=='assistant/message':#定稿
        数据=取字段(终事件,'data') or {}#载荷
        消息=取字段(数据,'message') or {}#消息
        起点=取字段(上下文,'start')#起点
        return {#完整助手
            'kind':'assistant',#助手
            'seq':取字段(终事件,'seq'),#序号
            'messageId':取字段(消息,'id'),#消息 id
            'time':取字段(终事件,'time'),#时间
            'turn':态['turn'],'step':态['step'],#坐标
            'blocks':转助手块们(取字段(消息,'content')),#块
            'usage':取字段(数据,'usage'),#用量
            'timing':{#计时
                'stepStartTime':取字段(取字段(起点,'event'),'time') if 起点 is not None else None,#步进
                'firstTokenTime':态.get('firstTokenTime'),#首 token
                'completedTime':取字段(终事件,'time'),#完成
            },#计时结束
        }#结束
    起点=取字段(上下文,'start')#起点
    匹配们=取字段(上下文,'matches') or []#匹配
    位置=取字段(起点,'location') if 起点 is not None else (取字段(匹配们[-1],'location') if 匹配们 else None)#位置
    边界=关闭边界(位置) if 位置 is not None else None#边界
    块们=压实块(态.get('blocks') or [])#压实
    if 边界 is None or not 有打断证据(块们):#无
        return None#不合成
    return {#打断助手
        'kind':'assistant',#助手
        'seq':取字段(边界,'seq')+聊天合成序号偏移['interruptedAssistant'],#合成序号
        'time':取字段(边界,'time'),#时间
        'turn':态['turn'],'step':态['step'],#坐标
        'blocks':块们,#流式块
        'interrupted':True,#打断
    }#结束

def 回放状态(上下文):#无增量状态时从匹配重放
    """按匹配顺序折。"""
    态=None#累加
    for 匹配项 in (取字段(上下文,'matches') or []):#遍历
        事件=取字段(匹配项,'event')#事件
        种=取字段(事件,'type')#种
        if 种=='assistant/chunk':#流块
            数据=取字段(事件,'data') or {}#载荷
            if 态 is None:#首次
                态=初态(取字段(数据,'turn'),取字段(数据,'step'))#开
            态=折流块(态,匹配项)#折
            continue#下
        if 种=='assistant/message':#定稿
            数据=取字段(事件,'data') or {}#载荷
            消息=取字段(数据,'message') or {}#消息
            if 态 is None:#首次
                态=初态(取字段(数据,'turn'),取字段(数据,'step'))#开
            态={**态,'blocks':转助手块们(取字段(消息,'content')),'hidden':False,'final':匹配项,'usage':取字段(数据,'usage')}#覆盖
            continue#下
        if 种=='llm/retry' and 态 is not None:#重试
            态=重试重置(态)#重置
    return 态#结果

def 投影助手(上下文):#从上下文投影助手行
    """增量状态或重放。"""
    态=取字段(上下文,'state')#增量
    if 态 is None:#无
        态=回放状态(上下文)#重放
    if 态 is None:#仍无
        return None#无材料
    已结=定稿节点(态,上下文)#定稿或打断
    块们=取字段(已结,'blocks') if 已结 is not None else 压实块(态.get('blocks') or [])#块
    可见=有可见内容(块们)#可见
    if 已结 is not None and 取字段(已结,'interrupted') is True:#打断
        状态='interrupted'#打断
    elif 已结 is None:#无定稿
        状态='running'#运行中
    else:#已结算
        状态='settled'#结算
    匹配们=取字段(上下文,'matches') or []#匹配
    锚=取字段(已结,'seq') if 已结 is not None else 态.get('firstVisibleSeq')#锚
    if 锚 is None:#仍无
        锚=取字段(取字段(匹配们[0],'event'),'seq') if 匹配们 else 0#首匹配
    时=取字段(已结,'time') if 已结 is not None else 态.get('firstVisibleTime')#时间
    if 时 is None:#仍无
        时=取字段(取字段(匹配们[0],'event'),'time') if 匹配们 else 0#首匹配
    数据={'status':状态,'turn':态['turn'],'step':态['step'],'blocks':块们,'time':时}#载荷
    if 态.get('usage') is not None:#有用量
        数据['usage']=态['usage']#带上
    if 已结 is not None:#有定稿
        数据['finalNode']=已结#带上
    return {'data':数据,'anchorSeq':锚,'visible':可见,'settled':已结}#投影

def 助手匹配(事件):#按事件认领本步骤
    """step/start 开；chunk/message/retry 更新。"""
    种=取字段(事件,'type')#种
    数据=取字段(事件,'data') or {}#载荷
    if 种=='step/start':#步骤开始
        return {'id':str(取字段(数据,'turn'))+':'+str(取字段(数据,'step')),'role':'start'}#开
    if 种=='assistant/chunk' or (种=='assistant/message' and 是追加面事件(事件)):#流/定稿
        return {'id':str(取字段(数据,'turn'))+':'+str(取字段(数据,'step')),'role':'update'}#更新
    if 种=='llm/retry':#重试
        return {'id':str(取字段(数据,'turn'))+':'+str(取字段(数据,'step')),'role':'update'}#更新
    return None#不认领

def 助手开始(_上下文,匹配项):#从 step/start 开状态
    """必须是步骤开始。"""
    事件=取字段(匹配项,'event')#事件
    if 取字段(事件,'type')!='step/start':#必须
        raise Exception('assistant-step start requires step/start')#硬失败
    数据=取字段(事件,'data') or {}#载荷
    return 初态(取字段(数据,'turn'),取字段(数据,'step'))#空状态

def 助手更新(上下文,匹配项):#折一条更新事件
    """chunk / message / retry。"""
    事件=取字段(匹配项,'event')#事件
    种=取字段(事件,'type')#种
    态=取字段(上下文,'state')#态
    if 种=='assistant/chunk':#流块
        return 折流块(态,匹配项)#折
    if 种=='assistant/message':#定稿
        数据=取字段(事件,'data') or {}#载荷
        消息=取字段(数据,'message') or {}#消息
        return {**态,'blocks':转助手块们(取字段(消息,'content')),'hidden':False,'final':匹配项,'usage':取字段(数据,'usage')}#覆盖
    if 种=='llm/retry':#重试
        return 重试重置(态)#重置
    return 态#不改

def 助手发布(匹配项):#何时发布投影
    """start 不发；chunk 跟动画帧；用量/结束不发。"""
    事件=取字段(匹配项,'event')#事件
    种=取字段(事件,'type')#种
    if 种=='step/start':#开始
        return 'none'#不发
    if 种!='assistant/chunk':#定稿/重试
        return 'immediate'#立即
    块种=取字段(取字段(取字段(事件,'data'),'chunk'),'type')#流块种
    return 'none' if 块种 in ('usage','finish') else 'animation-frame'#动画帧

def 助手位置数据(上下文,作用域):#步骤作用域的位置载荷
    """只给步骤作用域。"""
    if 作用域!='step':#非
        return None#无
    投影=投影助手(上下文)#投影
    if 投影 is None:#无
        return None#无
    数据=投影['data']#载荷
    return {'kind':'step','turn':数据['turn'],'step':数据['step'],'key':'assistant-step','value':数据}#条目

def 助手建视图(上下文):#造聊天视图节点
    """运行中无可见正文时的空行纪律。"""
    投影=投影助手(上下文)#投影
    if 投影 is None:#无
        return None#无
    if 投影['settled'] is None and not 投影['visible']:#运行中无正文
        态=取字段(上下文,'state') or 回放状态(上下文)#态
        if 态 is None:#无
            return None#无
        当前=None#已发布
        取=取字段(上下文,'current')#current 面
        if 取 is not None and hasattr(取,'get'):#有
            当前=取.get('chat')#聊天节点
        if not 态.get('hidden') or 当前 is None:#非重试隐藏或尚无
            return None#不发空行
    可见='visible' if (投影['settled'] is not None and 取字段(投影['settled'],'interrupted') is True) or 投影['visible'] else 'hidden'#可见性
    return 聊天节点(上下文,'assistant-step',投影['anchorSeq'],投影['data'],{'visibility':可见})#节点

助手定义={#助手步骤节点定义
    'kind':'assistant-step','target':'chat',#kind/目标
    'match':助手匹配,'start':助手开始,'update':助手更新,#生命周期
    'publication':助手发布,'buildLocationData':助手位置数据,'buildViewNode':助手建视图,#发布/视图
}#结束

def 登记助手会话节点(上下文):#登记助手生命周期
    """挂到 conversationEvents。"""
    上下文.conversationEvents.register(助手定义)#登记
