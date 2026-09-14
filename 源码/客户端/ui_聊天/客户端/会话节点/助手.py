from .节点工厂 import 聊天错误,聊天合成序号偏移,聊天节点#公共
from .事件面 import 是追加面事件,空助手块,转助手块,转助手块列表,是令牌增量#面辅助

__all__=['助手定义','登记助手会话节点']#仅中文公开名

def 初态(回合,步):#空的逐步助手状态
    """初始字段。"""
    return {#初态
        'turn':回合,'step':步,'blocks':[],#坐标与块
        'firstVisibleSeq':None,'firstVisibleTime':None,'firstTokenTime':None,#边界
        'hidden':False,'final':None,'usage':None,#隐藏/定稿/用量
    }#结束

def 压实块(块列表):#压实稀疏块
    """丢掉空洞。"""
    return [块 for 块 in 块列表 if 块 is not None]#非空

def 有可见内容(块列表):#是否有对用户可见的内容
    """工具调用不算可见正文。"""
    for 块 in 块列表:#逐块
        种=块['kind'] if 'kind' in 块 else None#种
        if 种=='tool-call':#工具
            continue#不算
        if 种 in ('text','reasoning'):#文本/推理
            文=块['text'] if 'text' in 块 and 块['text'] is not None else ''#正文
            if 文.strip()!='':#非空白
                return True#可见
            continue#空白
        return True#其它可见
    return False#无

def 有打断证据(块列表):#打断投影是否有可展示证据
    """任一非空块即算。"""
    for 块 in 块列表:#逐块
        种=块['kind'] if 'kind' in 块 else None#种
        if 种 in ('text','reasoning'):#文本/推理
            文=块['text'] if 'text' in 块 and 块['text'] is not None else ''#正文
            if 文.strip()!='':#非空白
                return True#有
            continue#空白
        return True#其它也算
    return False#无

def 重试重置(态):#llm/retry 后清空块并隐藏
    """首 token 跨重试保留。"""
    下=初态(态['turn'],态['step'])#空
    下['firstTokenTime']=态['firstTokenTime'] if 'firstTokenTime' in 态 else None#保留
    下['hidden']=True#隐藏
    return 下#重试态

def 折流块(态,匹配项):#把一块 assistant/live-chunk 折进状态
    """按流块判别标签更新稀疏块。"""
    事件=匹配项['event']#事件
    if 事件['type']!='assistant/live-chunk':#非
        return 态#原样
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    块=数据['chunk'] if 'chunk' in 数据 and 数据['chunk'] is not None else {}#流块
    块列表=list(态['blocks'] if 'blocks' in 态 and 态['blocks'] is not None else [])#复制
    种=块['type'] if 'type' in 块 else None#种
    下标=块['index'] if 'index' in 块 else 0#下标
    while len(块列表)<=下标:#扩容
        块列表.append(None)#空洞
    if 种=='block-start':#块开始
        块列表[下标]=空助手块(块['blockType'] if 'blockType' in 块 else None)#空底座
    elif 种=='text-delta':#文本增量
        旧=块列表[下标]#已有
        旧文=''#默认
        if 旧 is not None and 'kind' in 旧 and 旧['kind']=='text':#已是文本
            旧文=旧['text'] if 'text' in 旧 and 旧['text'] is not None else ''#旧文
        增量=块['text'] if 'text' in 块 and 块['text'] is not None else ''#增量
        块列表[下标]={'kind':'text','text':旧文+增量}#追加
    elif 种=='reasoning-delta':#推理增量
        旧=块列表[下标]#已有
        旧文=''#默认
        if 旧 is not None and 'kind' in 旧 and 旧['kind']=='reasoning':#已是推理
            旧文=旧['text'] if 'text' in 旧 and 旧['text'] is not None else ''#旧文
        增量=块['text'] if 'text' in 块 and 块['text'] is not None else ''#增量
        块列表[下标]={'kind':'reasoning','text':旧文+增量}#追加
    elif 种=='tool-call-delta':#工具增量
        旧=块列表[下标]#已有
        if 旧 is not None and 'kind' in 旧 and 旧['kind']=='tool-call':#已是
            底=旧#沿用
        else:#空底座
            底={'kind':'tool-call','callId':'','name':'','argsRaw':''}#空
        标识=块['id'] if 'id' in 块 else None#id
        名=块['name'] if 'name' in 块 else None#名
        底标识=底['callId'] if 'callId' in 底 else None#旧 id
        底名=底['name'] if 'name' in 底 else None#旧名
        底参=底['argsRaw'] if 'argsRaw' in 底 and 底['argsRaw'] is not None else ''#旧参
        参增量=块['argumentsDelta'] if 'argumentsDelta' in 块 and 块['argumentsDelta'] is not None else ''#增量
        块列表[下标]={#换
            'kind':'tool-call',#工具
            'callId':底标识 if 底标识 not in (None,'') else str(标识 if 标识 is not None else ''),#callId
            'name':名 if 名 is not None else 底名,#名
            'argsRaw':底参+参增量,#参数增量
        }#结束
    elif 种=='block-end':#块结束
        块列表[下标]=转助手块(块['block'] if 'block' in 块 else None)#定稿块
    elif 种=='usage':#用量
        return {**态,'usage':块['usage'] if 'usage' in 块 else None}#只改用量
    else:#未知/finish
        return 态#原样
    可见=有可见内容(压实块(块列表))#可见否
    首令牌=是令牌增量(块)#首 token
    下={**态,'blocks':块列表,'hidden':False if 可见 else (态['hidden'] if 'hidden' in 态 else None)}#更新
    if 可见 and ('firstVisibleSeq' not in 态 or 态['firstVisibleSeq'] is None):#首次可见
        下['firstVisibleSeq']=事件['seq']#序号
        下['firstVisibleTime']=事件['time'] if 'time' in 事件 else None#时间
    if 首令牌 and ('firstTokenTime' not in 态 or 态['firstTokenTime'] is None):#首次 token
        下['firstTokenTime']=事件['time'] if 'time' in 事件 else None#时间
    return 下#更新态

def 关闭边界(位置):#已关闭位置的结束边界
    """步骤或回合关闭边界。"""
    种=位置['kind'] if 'kind' in 位置 else None#种
    if 种=='step':#步骤
        步=位置['step'] if 'step' in 位置 and 位置['step'] is not None else {}#步
        if 'status' in 步 and 步['status']=='closed' and 'end' in 步 and 步['end'] is not None:#已关
            return 步['end']#步骤结束
    if 种 in ('step','turn'):#步骤或回合
        回合=位置['turn'] if 'turn' in 位置 and 位置['turn'] is not None else {}#回合
        if 'status' in 回合 and 回合['status']=='closed' and 'end' in 回合 and 回合['end'] is not None:#已关
            return 回合['end']#回合结束
    return None#仍开放

def 定稿节点(态,上下文):#从状态与上下文合成定稿或打断助手节点
    """有定稿消息优先；否则关闭边界+证据合成打断。"""
    终=态['final'] if 'final' in 态 else None#定稿匹配
    终事件=终['event'] if 终 is not None and 'event' in 终 else None#事件
    if 终事件 is not None and 终事件['type']=='assistant/message':#定稿
        数据=终事件['data'] if 'data' in 终事件 else {}#载荷
        消息=数据['message'] if 'message' in 数据 else {}#消息
        起点=上下文['start'] if 'start' in 上下文 else None#起点
        起点事件=起点['event'] if 起点 is not None and 'event' in 起点 else None#起点事件
        return {#完整助手
            'kind':'assistant',#助手
            'seq':终事件['seq'],#序号
            'messageId':消息['id'] if 'id' in 消息 else None,#消息 id
            'time':终事件['time'] if 'time' in 终事件 else None,#时间
            'turn':态['turn'],'step':态['step'],#坐标
            'blocks':转助手块列表(消息['content'] if 'content' in 消息 else None),#块
            'usage':数据['usage'] if 'usage' in 数据 else None,#用量
            'timing':{#计时
                'stepStartTime':起点事件['time'] if 起点事件 is not None and 'time' in 起点事件 else None,#步进
                'firstTokenTime':态['firstTokenTime'] if 'firstTokenTime' in 态 else None,#首 token
                'completedTime':终事件['time'] if 'time' in 终事件 else None,#完成
            },#计时结束
        }#结束
    起点=上下文['start'] if 'start' in 上下文 else None#起点
    匹配列表=上下文['matches'] if 'matches' in 上下文 and 上下文['matches'] is not None else []#匹配
    if 起点 is not None and 'location' in 起点:#有起点位置
        位置=起点['location']#位置
    elif len(匹配列表)>0 and 'location' in 匹配列表[-1]:#末匹配
        位置=匹配列表[-1]['location']#位置
    else:#无
        位置=None#无
    边界=关闭边界(位置) if 位置 is not None else None#边界
    块列表=压实块(态['blocks'] if 'blocks' in 态 and 态['blocks'] is not None else [])#压实
    if 边界 is None or not 有打断证据(块列表):#无
        return None#不合成
    return {#打断助手
        'kind':'assistant',#助手
        'seq':边界['seq']+聊天合成序号偏移['interruptedAssistant'],#合成序号
        'time':边界['time'] if 'time' in 边界 else None,#时间
        'turn':态['turn'],'step':态['step'],#坐标
        'blocks':块列表,#流式块
        'interrupted':True,#打断
    }#结束

def 回放状态(上下文):#无增量状态时从匹配重放
    """按匹配顺序折。"""
    态=None#累加
    for 匹配项 in (上下文['matches'] if 'matches' in 上下文 and 上下文['matches'] is not None else []):#遍历
        事件=匹配项['event']#事件
        种=事件['type']#种
        if 种=='assistant/live-chunk':#流块
            数据=事件['data'] if 'data' in 事件 else {}#载荷
            if 态 is None:#首次
                态=初态(数据['turn'] if 'turn' in 数据 else None,数据['step'] if 'step' in 数据 else None)#开
            态=折流块(态,匹配项)#折
            continue#下
        if 种=='assistant/message':#定稿
            数据=事件['data'] if 'data' in 事件 else {}#载荷
            消息=数据['message'] if 'message' in 数据 else {}#消息
            if 态 is None:#首次
                态=初态(数据['turn'] if 'turn' in 数据 else None,数据['step'] if 'step' in 数据 else None)#开
            态={**态,'blocks':转助手块列表(消息['content'] if 'content' in 消息 else None),'hidden':False,'final':匹配项,'usage':数据['usage'] if 'usage' in 数据 else None}#覆盖
            continue#下
        if 种=='llm/retry' and 态 is not None:#重试
            态=重试重置(态)#重置
    return 态#结果

def 投影助手(上下文):#从上下文投影助手行
    """增量状态或重放。"""
    态=上下文['state'] if 'state' in 上下文 else None#增量
    if 态 is None:#无
        态=回放状态(上下文)#重放
    if 态 is None:#仍无
        return None#无材料
    已结=定稿节点(态,上下文)#定稿或打断
    块列表=已结['blocks'] if 已结 is not None and 'blocks' in 已结 else 压实块(态['blocks'] if 'blocks' in 态 and 态['blocks'] is not None else [])#块
    可见=有可见内容(块列表)#可见
    if 已结 is not None and 'interrupted' in 已结 and 已结['interrupted'] is True:#打断
        状态='interrupted'#打断
    elif 已结 is None:#无定稿
        状态='running'#运行中
    else:#已结算
        状态='settled'#结算
    匹配列表=上下文['matches'] if 'matches' in 上下文 and 上下文['matches'] is not None else []#匹配
    锚=已结['seq'] if 已结 is not None and 'seq' in 已结 else (态['firstVisibleSeq'] if 'firstVisibleSeq' in 态 else None)#锚
    if 锚 is None:#仍无
        锚=匹配列表[0]['event']['seq'] if len(匹配列表)>0 else 0#首匹配
    时=已结['time'] if 已结 is not None and 'time' in 已结 else (态['firstVisibleTime'] if 'firstVisibleTime' in 态 else None)#时间
    if 时 is None:#仍无
        时=匹配列表[0]['event']['time'] if len(匹配列表)>0 and 'time' in 匹配列表[0]['event'] else 0#首匹配
    数据={'status':状态,'turn':态['turn'],'step':态['step'],'blocks':块列表,'time':时}#载荷
    if 'usage' in 态 and 态['usage'] is not None:#有用量
        数据['usage']=态['usage']#带上
    if 已结 is not None:#有定稿
        数据['finalNode']=已结#带上
    return {'data':数据,'anchorSeq':锚,'visible':可见,'settled':已结}#投影

def 助手匹配(事件):#按事件认领本步骤
    """step/start 开；chunk/message/retry 更新。"""
    种=事件['type']#种
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    if 种=='step/start':#步骤开始
        return {'id':str(数据['turn'])+':'+str(数据['step']),'role':'start'}#开
    if 种=='assistant/live-chunk' or (种=='assistant/message' and 是追加面事件(事件)):#流/定稿
        return {'id':str(数据['turn'])+':'+str(数据['step']),'role':'update'}#更新
    if 种=='llm/retry':#重试
        return {'id':str(数据['turn'])+':'+str(数据['step']),'role':'update'}#更新
    return None#不认领

def 助手开始(_上下文,匹配项):#从 step/start 开状态
    """必须是步骤开始。"""
    事件=匹配项['event']#事件
    if 事件['type']!='step/start':#必须
        raise 聊天错误('assistant-step start requires step/start')#硬失败
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    return 初态(数据['turn'] if 'turn' in 数据 else None,数据['step'] if 'step' in 数据 else None)#空状态

def 助手更新(上下文,匹配项):#折一条更新事件
    """chunk / message / retry。"""
    事件=匹配项['event']#事件
    种=事件['type']#种
    态=上下文['state']#态
    if 种=='assistant/live-chunk':#流块
        return 折流块(态,匹配项)#折
    if 种=='assistant/message':#定稿
        数据=事件['data'] if 'data' in 事件 else {}#载荷
        消息=数据['message'] if 'message' in 数据 else {}#消息
        return {**态,'blocks':转助手块列表(消息['content'] if 'content' in 消息 else None),'hidden':False,'final':匹配项,'usage':数据['usage'] if 'usage' in 数据 else None}#覆盖
    if 种=='llm/retry':#重试
        return 重试重置(态)#重置
    return 态#不改

def 助手发布(匹配项):#何时发布投影
    """start 不发；chunk 跟动画帧；用量/结束不发。"""
    事件=匹配项['event']#事件
    种=事件['type']#种
    if 种=='step/start':#开始
        return 'none'#不发
    if 种!='assistant/live-chunk':#定稿/重试
        return 'immediate'#立即
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    块=数据['chunk'] if 'chunk' in 数据 else None#流块
    块种=块['type'] if 块 is not None and 'type' in 块 else None#流块种
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
        态=上下文['state'] if 'state' in 上下文 else None#态
        if 态 is None:#无
            态=回放状态(上下文)#重放
        if 态 is None:#无
            return None#无
        当前=None#已发布
        取=上下文['current'] if 'current' in 上下文 else None#current 面
        if 取 is not None and 'chat' in 取:#有聊天节点
            当前=取['chat']#聊天节点
        if ('hidden' not in 态 or not 态['hidden']) or 当前 is None:#非重试隐藏或尚无
            return None#不发空行
    打断=投影['settled'] is not None and 'interrupted' in 投影['settled'] and 投影['settled']['interrupted'] is True#打断可见
    可见='visible' if 打断 or 投影['visible'] else 'hidden'#可见性
    return 聊天节点(上下文,'assistant-step',投影['anchorSeq'],投影['data'],{'visibility':可见})#节点

助手定义={#助手步骤节点定义
    'kind':'assistant-step','target':'chat',#kind/目标
    'match':助手匹配,'start':助手开始,'update':助手更新,#生命周期
    'publication':助手发布,'buildLocationData':助手位置数据,'buildViewNode':助手建视图,#发布/视图
}#结束

def 登记助手会话节点(上下文):#登记助手生命周期
    """挂到 uiConversation.events。"""
    上下文.uiConversation.events.register(助手定义)#登记
