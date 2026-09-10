"""轨迹根工具生命周期的 ConversationNode Definition。

对齐上游 `ui-trajectory/src/client/trajectory-tool-definition.ts`。公开面仅中文名。
"""
import json#子调用参数序列化
from .轨迹节点 import 轨迹节点#包成轨迹视图节点
from .轨迹记录 import 轨迹错误#本包异常

__all__=['登记轨迹工具定义']#仅中文公开名

最大深度=256#调用树允许的最大深度

def 根调用(匹配):#从 tool/call 命中抽出进行中的根调用
    """起点必须是工具调用。"""
    事件=匹配['event']#事件
    if 事件['type']!='tool/call':#起点必须是工具调用
        raise 轨迹错误('trajectory-tool-call start requires tool/call')#类型收窄失败则抛
    数据=事件['data'] if 'data' in 事件 else None#载荷
    视图=匹配['view'] if 'view' in 匹配 else None#视图
    调用面=视图['view'] if 视图 is not None and 'for' in 视图 and 视图['for']=='call' and 'view' in 视图 else None#调用视图
    return {#进行中的根调用
        'callId':str(数据['callId']),'name':数据['name'] if 数据 is not None and 'name' in 数据 else None,#身份与名
        'argsRaw':数据['arguments'] if 数据 is not None and 'arguments' in 数据 else None,#参数原文
        'turn':数据['turn'] if 数据 is not None and 'turn' in 数据 else None,#回合
        'step':数据['step'] if 数据 is not None and 'step' in 数据 else None,#步
        'time':事件['time'],#时刻
        'callView':调用面,#调用视图
        'subCalls':[],#子调用
    }#结束

def 根结果(匹配,先前=None):#从 tool/result 命中抽出根结果节点
    """类型不对则 None。"""
    事件=匹配['event']#事件
    if 事件['type']!='tool/result':#非工具结果
        return None#无法投影
    数据=事件['data'] if 'data' in 事件 else None#载荷
    消息=数据['message'] if 数据 is not None and 'message' in 数据 else None#结果消息
    内容=消息['content'] if 消息 is not None and 'content' in 消息 else None#内容
    结果=内容[0] if 内容 is not None and len(内容)>0 else {}#第一条结果内容
    视图=匹配['view'] if 'view' in 匹配 else None#视图
    来源=消息['source'] if 消息 is not None and 'source' in 消息 else None#来源
    节点={#根工具结果节点
        'kind':'tool-result',#种类
        'seq':事件['seq'],#序号
        'time':事件['time'],#时刻
        'callId':str(来源['callId']) if 来源 is not None and 'callId' in 来源 else None,#调用 id
        'call':None if 先前 is None else {'name':先前['name'] if 'name' in 先前 else None,'argsRaw':先前['argsRaw'] if 'argsRaw' in 先前 else None},#调用
        'callTime':先前['time'] if 先前 is not None and 'time' in 先前 else None,#调用时刻
        'content':结果['content'] if 'content' in 结果 else None,#内容
        'isError':('isError' in 结果 and 结果['isError'] is True),#错误
        'meta':数据['meta'] if 数据 is not None and 'meta' in 数据 else None,#元数据
        'callView':先前['callView'] if 先前 is not None and 'callView' in 先前 else None,#调用视图
        'resultView':视图['view'] if 视图 is not None and 'for' in 视图 and 视图['for']=='result' and 'view' in 视图 else None,#结果视图
        'subCalls':[],#子调用
    }#节点结束
    if 数据 is not None and 'error' in 数据 and 数据['error'] is not None:#有 error 才展开
        节点['error']=数据['error']#错误
    return 节点#根结果

def 位置回合(匹配):#从匹配位置读回合号
    """未解析位置则记 0。"""
    位置=匹配['location'] if 'location' in 匹配 else None#位置
    if 位置 is not None and 'kind' in 位置 and 位置['kind'] in ('step','turn'):#位置挂在步或回合上
        回合=位置['turn'] if 'turn' in 位置 else None#回合对象
        return 回合['turn'] if 回合 is not None and 'turn' in 回合 else 0#交出回合号
    return 0#未解析

def 位置步号(匹配):#从匹配位置读步号
    """仅 step 位置有步号。"""
    位置=匹配['location'] if 'location' in 匹配 else None#位置
    if 位置 is None or ('kind' not in 位置) or 位置['kind']!='step':#非步
        return 0#无步号
    步=位置['step'] if 'step' in 位置 else None#步对象
    return 步['step'] if 步 is not None and 'step' in 步 else 0#步号

def 子调用(匹配,数据):#从 dispatch-start 抽出进行中的子调用
    """组装进行中的子调用。"""
    事件=匹配['event']#事件
    参数=数据['arguments'] if 'arguments' in 数据 else None#参数
    return {#子调用
        'callId':数据['subCallId'] if 'subCallId' in 数据 else None,#子 id
        'name':数据['name'] if 'name' in 数据 else None,#名
        'argsRaw':json.dumps(参数,ensure_ascii=False,separators=(',',':'),allow_nan=False),#参数原文
        'turn':位置回合(匹配),#回合
        'step':位置步号(匹配),#步
        'time':事件['time'],#时刻
        'callView':None,#无调用视图
        'subCalls':[],#子调用
    }#结束

def 子结果(匹配,数据,先前=None):#从 ptc-dispatch 抽出子调用结果节点
    """返回子调用结果节点。"""
    事件=匹配['event']#事件
    参数=数据['arguments'] if 'arguments' in 数据 else None#参数
    进行中=先前 is not None and not ('kind' in 先前)#先前是进行中调用
    return {#子调用结果
        'kind':'tool-result',#种类
        'seq':事件['seq'],#序号
        'time':事件['time'],#时刻
        'callId':数据['subCallId'] if 'subCallId' in 数据 else None,#子 id
        'call':{'name':数据['name'] if 'name' in 数据 else None,'argsRaw':json.dumps(参数,ensure_ascii=False,separators=(',',':'),allow_nan=False)},#调用
        'callTime':先前['time'] if 进行中 and 'time' in 先前 else None,#进行中才有开始时刻
        'content':数据['content'] if 'content' in 数据 and 数据['content'] is not None else [],#内容
        'isError':('isError' in 数据 and 数据['isError'] is True),#错误
        'callView':None,#无
        'resultView':None,#无
        'subCalls':[],#子调用
    }#结束

def 接受边(状态,父,子):#父→子边是否可加入调用树
    """自环、已有父、成环或超深则拒绝。"""
    父表=状态['parents'] if 'parents' in 状态 else {}#父表
    if 父==子 or 子 in 父表:#自环或子已有父
        return False#拒绝
    游标=父#沿父指针上溯
    父深度=0#从 parent 到根的深度
    祖先=set()#已见祖先
    while 游标 is not None:#尚未走到根
        if 游标==子 or 游标 in 祖先:#会成环
            return False#拒绝
        祖先.add(游标)#记下
        父深度+=1#深度 +1
        游标=父表[游标] if 游标 in 父表 else None#继续上溯
    待测=[{'callId':子,'depth':1}]#待测子树
    后代=set()#已见后代
    子树深度=0#子树最大深度
    序号=0#显式队列下标
    子表=状态['children'] if 'children' in 状态 else {}#子表
    while 序号<len(待测):#广度遍历
        候选=待测[序号]#本候选
        序号+=1#前进
        if 候选['callId'] in 后代:#子树成环
            return False#拒绝
        后代.add(候选['callId'])#记下
        子树深度=max(子树深度,候选['depth'])#刷新
        嵌套列表=子表[候选['callId']] if 候选['callId'] in 子表 and 子表[候选['callId']] is not None else []#直接子调用
        for 嵌套 in 嵌套列表:#每个
            待测.append({'callId':嵌套,'depth':候选['depth']+1})#入队
    return 父深度+子树深度<=最大深度#合并后不超过最大深度

def 更新分派(状态,匹配):#把一条 dispatch 事件并入调用树
    """非 dispatch 事件状态不变。"""
    事件=匹配['event']#本条事件
    种类=事件['type']#类型
    if 种类 not in ('tool/ptc-dispatch-start','tool/ptc-dispatch'):#非 dispatch
        return 状态#不变
    数据=事件['data'] if 'data' in 事件 else None#dispatch 载荷
    父标识=str(数据['parentCallId'])#父调用 id
    子标识=str(数据['subCallId'])#子调用 id
    子表原=状态['children'] if 'children' in 状态 else {}#子表
    兄弟=list(子表原[父标识] if 父标识 in 子表原 and 子表原[父标识] is not None else [])#父节点已有的子 id 列表
    下标=兄弟.index(子标识) if 子标识 in 兄弟 else -1#该子是否已挂在父下
    if 下标<0 and not 接受边(状态,父标识,子标识):#新边不合法
        return 状态#不变
    if 种类=='tool/ptc-dispatch-start' and 下标>=0:#已有子调用再 start
        return 状态#忽略
    调用表=dict(状态['calls'])#复制调用表
    if 种类=='tool/ptc-dispatch-start':#start 则记进行中调用
        调用表[子标识]=子调用(匹配,数据)#写入
    else:#dispatch 则记结果
        先前=调用表[子标识] if 子标识 in 调用表 else None#先前块
        调用表[子标识]=子结果(匹配,数据,先前)#带上先前块
    if 下标>=0:#边已存在，只更新块
        return {**状态,'calls':调用表}#只更新
    子表=dict(子表原)#复制子表
    子表[父标识]=兄弟+[子标识]#把子 id 追加到父下
    父表=dict(状态['parents'] if 'parents' in 状态 else {})#复制父表
    父表[子标识]=父标识#记下子→父
    return {**状态,'calls':调用表,'children':子表,'parents':父表}#更新后的调用树

def 打断点(上下文):#读出本节点所属步/回合已闭合时的打断点
    """有闭合边界才返回序号与时间。"""
    起点=上下文['start'] if 'start' in 上下文 else None#起点
    位置=起点['location'] if 起点 is not None and 'location' in 起点 else None#起点位置
    if 位置 is None:#无位置
        return None#尚未闭合
    if 位置['kind']=='step':#步位置
        步=位置['step'] if 'step' in 位置 else None#步
        if 步 is not None and 'status' in 步 and 步['status']=='closed':#步已闭合
            return 步['end'] if 'end' in 步 else None#步结束点
    if 位置['kind'] in ('step','turn'):#步或回合
        回合=位置['turn'] if 'turn' in 位置 else None#回合
        if 回合 is not None and 'status' in 回合 and 回合['status']=='closed':#回合已闭合
            return 回合['end'] if 'end' in 回合 else None#回合结束点
    return None#尚未闭合

def 投影调用(状态,调用标识,打断于,已见=None,深度=1):#把调用树投影成带嵌套 subCalls 的块
    """无此调用则 None。"""
    if 已见 is None:#默认空集
        已见=set()#空
    调用表=状态['calls'] if 'calls' in 状态 else {}#调用表
    块=调用表[调用标识] if 调用标识 in 调用表 else None#取出本调用块
    if 块 is None:#调用表无此 id
        return None#无
    if 调用标识 in 已见 or 深度>最大深度:#成环或超深
        return {**块,'subCalls':[]}#截断子调用
    下一已见=set(已见)#复制已见集
    下一已见.add(调用标识)#把本调用记入已见
    子调用列表=[]#已投影的子调用
    子表=状态['children'] if 'children' in 状态 else {}#子表
    子标识列表=子表[调用标识] if 调用标识 in 子表 and 子表[调用标识] is not None else []#子 id
    for 子标识 in 子标识列表:#逐子投影
        子=投影调用(状态,子标识,打断于,下一已见,深度+1)#递归
        if 子 is not None:#成功
            子调用列表.append(子)#收下
    if ('kind' in 块) or 打断于 is None:#已是结果或未打断
        return {**块,'subCalls':子调用列表}#原样带上子调用
    return {#进行中调用被打断
        'kind':'tool-result',#种类
        'seq':打断于['seq']-0.8,#合成序号
        'time':打断于['time'],#时刻
        'callId':块['callId'] if 'callId' in 块 else None,#调用 id
        'call':{'name':块['name'] if 'name' in 块 else None,'argsRaw':块['argsRaw'] if 'argsRaw' in 块 else None},#调用
        'callTime':块['time'] if 'time' in 块 else None,#开始
        'content':[],#空内容
        'isError':True,#打断视为错误
        'error':{'name':'Interrupted','code':'interrupted'},#打断错误
        'callView':块['callView'] if 'callView' in 块 else None,#调用视图
        'resultView':None,#无结果视图
        'subCalls':子调用列表,#子调用
    }#结束

def 回放状态(上下文):#回放缺 start 时从结果重建状态
    """无根结果则 None。"""
    结果匹配=None#第一条工具结果命中
    命中列表=上下文['matches'] if 'matches' in 上下文 and 上下文['matches'] is not None else []#命中
    for 匹配 in 命中列表:#找
        事件=匹配['event'] if 'event' in 匹配 else None#事件
        if 事件 is not None and 事件['type']=='tool/result':#命中
            结果匹配=匹配#记下
            break#找到
    根=根结果(结果匹配) if 结果匹配 is not None else None#有命中才抽出根结果
    if 根 is None:#无根结果
        return None#无法回放
    状态={'rootId':根['callId'],'calls':{根['callId']:根},'children':{},'parents':{}}#以根结果播种
    for 匹配 in 命中列表:#把所有 dispatch 事件并入
        状态=更新分派(状态,匹配)#并入
    return 状态#回放得到的调用树

def 工具匹配(事件):#按事件类型归入本根调用
    """start / update / null。"""
    种类=事件['type']#事件类型
    数据=事件['data'] if 'data' in 事件 else None#载荷
    if 种类=='tool/call':#工具调用
        return {'id':str(数据['callId']),'role':'start'}#作本节点 start
    if 种类=='tool/result':#工具结果
        消息=数据['message'] if 数据 is not None and 'message' in 数据 else None#消息
        来源=消息['source'] if 消息 is not None and 'source' in 消息 else None#来源
        return {'id':str(来源['callId']),'role':'update'}#按来源调用 id
    if 种类 in ('tool/ptc-dispatch-start','tool/ptc-dispatch'):#嵌套 dispatch
        根标识=数据['rootCallId'] if 数据 is not None and 'rootCallId' in 数据 else None#根调用 id
        return {'id':根标识,'role':'update'} if isinstance(根标识,str) and 根标识!='' else None#合法才匹配
    return None#无关事件

def 工具开始(_上下文,匹配):#从 tool/call 播种调用树
    """以根调用播种状态。"""
    根=根调用(匹配)#抽出进行中的根调用
    return {'rootId':根['callId'],'calls':{根['callId']:根},'children':{},'parents':{}}#初始状态

def 工具更新(上下文,匹配):#按后续事件推进调用树
    """根结果或 dispatch。"""
    事件=匹配['event']#事件
    if 事件['type']!='tool/result':#非根结果则当 dispatch 并入
        return 更新分派(上下文['state'],匹配)#dispatch
    状态=上下文['state']#当前状态
    调用表原=状态['calls'] if 'calls' in 状态 else {}#调用表
    根标识=状态['rootId']#根 id
    先前=调用表原[根标识] if 根标识 in 调用表原 else None#取出当前根块
    进行中块=先前 if 先前 is not None and ('kind' not in 先前) else None#仅进行中的根调用
    结果=根结果(匹配,进行中块)#抽出根结果
    if 结果 is None:#投影失败
        return 状态#不变
    调用表=dict(调用表原)#复制调用表
    调用表[根标识]=结果#用根结果覆盖根块
    return {**状态,'calls':调用表}#更新后的状态

def 工具构建视图(上下文):#把调用树投影成轨迹视图节点
    """根块缺失则不产出。"""
    状态=上下文['state'] if 'state' in 上下文 else None#有 start 用状态
    if 状态 is None:#否则回放
        状态=回放状态(上下文)#回放
    if 状态 is None:#无工具事件
        return None#不产出
    根=投影调用(状态,状态['rootId'],打断点(上下文))#投影根块
    if 根 is None:#根块缺失
        return None#不产出
    起点=上下文['start'] if 'start' in 上下文 else None#start 匹配
    if 起点 is not None:#优先用 start 事件序号
        锚点=起点['event']['seq']#start 序号
    elif 'kind' in 根:#否则结果序号
        锚点=根['seq']#结果序号
    else:#再否则首条命中或 0
        命中列表=上下文['matches'] if 'matches' in 上下文 and 上下文['matches'] is not None else []#命中
        锚点=命中列表[0]['event']['seq'] if len(命中列表)>0 else 0#首条或 0
    return 轨迹节点(上下文,锚点,{'kind':'tool','root':根})#包进轨迹信封

轨迹工具定义={#根工具节点 Definition
    'kind':'trajectory-tool-call',#节点种类
    'target':'trajectory',#投递到轨迹槽
    'match':工具匹配,#匹配
    'start':工具开始,#播种
    'update':工具更新,#更新
    'buildViewNode':工具构建视图,#投影
}#定义结束

def 登记轨迹工具定义(上下文):#向会话事件登记根工具 Definition
    """登记轨迹根工具生命周期 Definition。"""
    上下文.conversationEvents.register(轨迹工具定义)#登记根工具生命周期
