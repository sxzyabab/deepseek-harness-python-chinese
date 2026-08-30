"""轨迹根工具生命周期的 ConversationNode Definition。

对齐上游 `ui-trajectory/src/client/trajectory-tool-definition.ts`。公开面仅中文名。
"""
import json#子调用参数序列化
from .定义公共 import 轨迹节点#包成轨迹视图节点
from .轨迹记录 import 取字段#读字段

__all__=['登记轨迹工具定义']#仅中文公开名

最大深度=256#调用树允许的最大深度

def 根调用(匹配):#从 tool/call 命中抽出进行中的根调用
    """起点必须是工具调用。"""
    事件=取字段(匹配,'event')#事件
    if 取字段(事件,'type')!='tool/call':#起点必须是工具调用
        raise Exception('trajectory-tool-call start requires tool/call')#类型收窄失败则抛
    数据=取字段(事件,'data')#载荷
    视图=取字段(匹配,'view')#视图
    return {'callId':str(取字段(数据,'callId')),'name':取字段(数据,'name'),'argsRaw':取字段(数据,'arguments'),'turn':取字段(数据,'turn'),'step':取字段(数据,'step'),'time':取字段(事件,'time'),'callView':取字段(视图,'view') if 取字段(视图,'for')=='call' else None,'subCalls':[]}#进行中的根调用

def 根结果(匹配,先前=None):#从 tool/result 命中抽出根结果节点
    """类型不对则 None。"""
    事件=取字段(匹配,'event')#事件
    if 取字段(事件,'type')!='tool/result':#非工具结果
        return None#无法投影
    数据=取字段(事件,'data')#载荷
    消息=取字段(数据,'message')#结果消息
    结果=取字段(消息,'content')[0] if 取字段(消息,'content') else {}#第一条结果内容
    视图=取字段(匹配,'view')#视图
    节点={'kind':'tool-result','seq':取字段(事件,'seq'),'time':取字段(事件,'time'),'callId':str(取字段(取字段(消息,'source'),'callId')),'call':None if 先前 is None else {'name':取字段(先前,'name'),'argsRaw':取字段(先前,'argsRaw')},'callTime':取字段(先前,'time') if 先前 is not None else None,'content':取字段(结果,'content'),'isError':取字段(结果,'isError') is True,'meta':取字段(数据,'meta'),'callView':取字段(先前,'callView') if 先前 is not None else None,'resultView':取字段(视图,'view') if 取字段(视图,'for')=='result' else None,'subCalls':[]}#根工具结果节点
    if 取字段(数据,'error') is not None:#有 error 才展开
        节点['error']=取字段(数据,'error')#错误
    return 节点#根结果

def 位置回合(匹配):#从匹配位置读回合号
    """未解析位置则记 0。"""
    位置=取字段(匹配,'location')#位置
    if 取字段(位置,'kind') in ('step','turn'):#位置挂在步或回合上
        return 取字段(取字段(位置,'turn'),'turn')#交出回合号
    return 0#未解析

def 位置步号(匹配):#从匹配位置读步号
    """仅 step 位置有步号。"""
    位置=取字段(匹配,'location')#位置
    return 取字段(取字段(位置,'step'),'step') if 取字段(位置,'kind')=='step' else 0#步号

def 子调用(匹配,数据):#从 dispatch-start 抽出进行中的子调用
    """组装进行中的子调用。"""
    return {'callId':取字段(数据,'subCallId'),'name':取字段(数据,'name'),'argsRaw':json.dumps(取字段(数据,'arguments'),ensure_ascii=False),'turn':位置回合(匹配),'step':位置步号(匹配),'time':取字段(取字段(匹配,'event'),'time'),'callView':None,'subCalls':[]}#子调用

def 子结果(匹配,数据,先前=None):#从 code-dispatch 抽出子调用结果节点
    """返回子调用结果节点。"""
    return {'kind':'tool-result','seq':取字段(取字段(匹配,'event'),'seq'),'time':取字段(取字段(匹配,'event'),'time'),'callId':取字段(数据,'subCallId'),'call':{'name':取字段(数据,'name'),'argsRaw':json.dumps(取字段(数据,'arguments'),ensure_ascii=False)},'callTime':None if 先前 is None or (isinstance(先前,dict) and 'kind' in 先前) else 取字段(先前,'time'),'content':取字段(数据,'content') or [],'isError':取字段(数据,'isError') is True,'callView':None,'resultView':None,'subCalls':[]}#子调用结果

def 接受边(状态,父,子):#父→子边是否可加入调用树
    """自环、已有父、成环或超深则拒绝。"""
    if 父==子 or 子 in 取字段(状态,'parents'):#自环或子已有父
        return False#拒绝
    游标=父#沿父指针上溯
    父深度=0#从 parent 到根的深度
    祖先=set()#已见祖先
    while 游标 is not None:#尚未走到根
        if 游标==子 or 游标 in 祖先:#会成环
            return False#拒绝
        祖先.add(游标)#记下
        父深度+=1#深度 +1
        游标=取字段(状态,'parents').get(游标)#继续上溯
    待测=[{'callId':子,'depth':1}]#待测子树
    后代=set()#已见后代
    子树深度=0#子树最大深度
    序号=0#显式队列下标
    while 序号<len(待测):#广度遍历
        候选=待测[序号]#本候选
        序号+=1#前进
        if 候选['callId'] in 后代:#子树成环
            return False#拒绝
        后代.add(候选['callId'])#记下
        子树深度=max(子树深度,候选['depth'])#刷新
        for 嵌套 in 取字段(状态,'children').get(候选['callId']) or []:#直接子调用
            待测.append({'callId':嵌套,'depth':候选['depth']+1})#入队
    return 父深度+子树深度<=最大深度#合并后不超过最大深度

def 更新分派(状态,匹配):#把一条 dispatch 事件并入调用树
    """非 dispatch 事件状态不变。"""
    事件=取字段(匹配,'event')#本条事件
    种类=取字段(事件,'type')#类型
    if 种类 not in ('tool/code-dispatch-start','tool/code-dispatch'):#非 dispatch
        return 状态#不变
    数据=取字段(事件,'data')#dispatch 载荷
    父标识=str(取字段(数据,'parentCallId'))#父调用 id
    子标识=str(取字段(数据,'subCallId'))#子调用 id
    兄弟=list(取字段(状态,'children').get(父标识) or [])#父节点已有的子 id 列表
    下标=兄弟.index(子标识) if 子标识 in 兄弟 else -1#该子是否已挂在父下
    if 下标<0 and not 接受边(状态,父标识,子标识):#新边不合法
        return 状态#不变
    if 种类=='tool/code-dispatch-start' and 下标>=0:#已有子调用再 start
        return 状态#忽略
    调用表=dict(取字段(状态,'calls'))#复制调用表
    if 种类=='tool/code-dispatch-start':#start 则记进行中调用
        调用表[子标识]=子调用(匹配,数据)#写入
    else:#dispatch 则记结果
        调用表[子标识]=子结果(匹配,数据,调用表.get(子标识))#带上先前块
    if 下标>=0:#边已存在，只更新块
        return {**状态,'calls':调用表}#只更新
    子表=dict(取字段(状态,'children'))#复制子表
    子表[父标识]=兄弟+[子标识]#把子 id 追加到父下
    父表=dict(取字段(状态,'parents'))#复制父表
    父表[子标识]=父标识#记下子→父
    return {**状态,'calls':调用表,'children':子表,'parents':父表}#更新后的调用树

def 打断点(上下文):#读出本节点所属步/回合已闭合时的打断点
    """有闭合边界才返回序号与时间。"""
    起点=取字段(上下文,'start')#起点
    位置=取字段(起点,'location') if 起点 is not None else None#起点位置
    if 取字段(位置,'kind')=='step' and 取字段(取字段(位置,'step'),'status')=='closed':#步已闭合
        return 取字段(取字段(位置,'step'),'end')#步结束点
    if 取字段(位置,'kind') in ('step','turn') and 取字段(取字段(位置,'turn'),'status')=='closed':#回合已闭合
        return 取字段(取字段(位置,'turn'),'end')#回合结束点
    return None#尚未闭合

def 投影调用(状态,调用标识,打断于,已见=None,深度=1):#把调用树投影成带嵌套 subCalls 的块
    """无此调用则 None。"""
    if 已见 is None:#默认空集
        已见=set()#空
    块=取字段(状态,'calls').get(调用标识)#取出本调用块
    if 块 is None:#调用表无此 id
        return None#无
    if 调用标识 in 已见 or 深度>最大深度:#成环或超深
        return {**块,'subCalls':[]}#截断子调用
    下一已见=set(已见)#复制已见集
    下一已见.add(调用标识)#把本调用记入已见
    子调用们=[]#已投影的子调用
    for 子标识 in 取字段(状态,'children').get(调用标识) or []:#逐子投影
        子=投影调用(状态,子标识,打断于,下一已见,深度+1)#递归
        if 子 is not None:#成功
            子调用们.append(子)#收下
    if (isinstance(块,dict) and 'kind' in 块) or 打断于 is None:#已是结果或未打断
        return {**块,'subCalls':子调用们}#原样带上子调用
    return {'kind':'tool-result','seq':取字段(打断于,'seq')-0.8,'time':取字段(打断于,'time'),'callId':取字段(块,'callId'),'call':{'name':取字段(块,'name'),'argsRaw':取字段(块,'argsRaw')},'callTime':取字段(块,'time'),'content':[],'isError':True,'error':{'name':'Interrupted','code':'interrupted'},'callView':取字段(块,'callView'),'resultView':None,'subCalls':子调用们}#进行中调用被打断

def 回放状态(上下文):#回放缺 start 时从结果重建状态
    """无根结果则 None。"""
    结果匹配=None#第一条工具结果命中
    for 匹配 in 取字段(上下文,'matches') or []:#找
        if 取字段(取字段(匹配,'event'),'type')=='tool/result':#命中
            结果匹配=匹配#记下
            break#找到
    根=根结果(结果匹配) if 结果匹配 is not None else None#有命中才抽出根结果
    if 根 is None:#无根结果
        return None#无法回放
    状态={'rootId':取字段(根,'callId'),'calls':{取字段(根,'callId'):根},'children':{},'parents':{}}#以根结果播种
    for 匹配 in 取字段(上下文,'matches') or []:#把所有 dispatch 事件并入
        状态=更新分派(状态,匹配)#并入
    return 状态#回放得到的调用树

def 工具匹配(事件):#按事件类型归入本根调用
    """start / update / null。"""
    种类=取字段(事件,'type')#事件类型
    数据=取字段(事件,'data')#载荷
    if 种类=='tool/call':#工具调用
        return {'id':str(取字段(数据,'callId')),'role':'start'}#作本节点 start
    if 种类=='tool/result':#工具结果
        return {'id':str(取字段(取字段(取字段(数据,'message'),'source'),'callId')),'role':'update'}#按来源调用 id
    if 种类 in ('tool/code-dispatch-start','tool/code-dispatch'):#嵌套 dispatch
        根标识=取字段(数据,'rootCallId')#根调用 id
        return {'id':根标识,'role':'update'} if isinstance(根标识,str) and 根标识!='' else None#合法才匹配
    return None#无关事件

def 工具开始(_上下文,匹配):#从 tool/call 播种调用树
    """以根调用播种状态。"""
    根=根调用(匹配)#抽出进行中的根调用
    return {'rootId':取字段(根,'callId'),'calls':{取字段(根,'callId'):根},'children':{},'parents':{}}#初始状态

def 工具更新(上下文,匹配):#按后续事件推进调用树
    """根结果或 dispatch。"""
    if 取字段(取字段(匹配,'event'),'type')!='tool/result':#非根结果则当 dispatch 并入
        return 更新分派(取字段(上下文,'state'),匹配)#dispatch
    状态=取字段(上下文,'state')#当前状态
    先前=取字段(状态,'calls').get(取字段(状态,'rootId'))#取出当前根块
    进行中=先前 if 先前 is not None and not (isinstance(先前,dict) and 'kind' in 先前) else None#仅进行中的根调用
    结果=根结果(匹配,进行中)#抽出根结果
    if 结果 is None:#投影失败
        return 状态#不变
    调用表=dict(取字段(状态,'calls'))#复制调用表
    调用表[取字段(状态,'rootId')]=结果#用根结果覆盖根块
    return {**状态,'calls':调用表}#更新后的状态

def 工具构建视图(上下文):#把调用树投影成轨迹视图节点
    """根块缺失则不产出。"""
    状态=取字段(上下文,'state')#有 start 用状态
    if 状态 is None:#否则回放
        状态=回放状态(上下文)#回放
    if 状态 is None:#无工具事件
        return None#不产出
    根=投影调用(状态,取字段(状态,'rootId'),打断点(上下文))#投影根块
    if 根 is None:#根块缺失
        return None#不产出
    起点=取字段(上下文,'start')#start 匹配
    if 起点 is not None:#优先用 start 事件序号
        锚点=取字段(取字段(起点,'event'),'seq')#start 序号
    elif isinstance(根,dict) and 'kind' in 根:#否则结果序号
        锚点=取字段(根,'seq')#结果序号
    else:#再否则首条命中或 0
        命中们=取字段(上下文,'matches') or []#命中
        锚点=取字段(取字段(命中们[0],'event'),'seq') if 命中们 else 0#首条或 0
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
