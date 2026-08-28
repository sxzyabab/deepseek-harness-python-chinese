"""根工具生命周期与嵌套代码分发。

对齐上游 `ui-conversation/src/client/conversation-nodes/tool.ts`。公开面仅中文名。
"""
import json#子调用参数序列化
from ..约定.聊天节点 import 已结算工具#已结算判断
from .公共 import 聊天合成序号偏移,聊天节点#公共
from .面辅助 import 取字段,是追加面事件#面辅助

__all__=['工具定义','登记工具会话节点']#仅中文公开名

最大深度=256#父子边最大嵌套深度
投影缓存={}#源块 id → 上次投影（弱引用语义用 id 键近似）

def 同引用(左,右):#两列表是否同长度且逐项同一对象
    """长度与每项 is 都成立。"""
    return len(左)==len(右) and all(甲 is 乙 for 甲,乙 in zip(左,右))#引用相等

def 参数原文(值):#未知参数 → JSON 字符串
    """序列化。"""
    return json.dumps(值,ensure_ascii=False)#原文

def 根调用(匹配项):#从 tool/call 建运行中根调用
    """起始必须是 tool/call。"""
    事件=取字段(匹配项,'event')#事件
    if 取字段(事件,'type')!='tool/call':#必须
        raise Exception('tool-call start requires tool/call')#硬失败
    数据=取字段(事件,'data') or {}#载荷
    视图=取字段(匹配项,'view')#视图
    调用面=取字段(视图,'view') if 取字段(视图,'for')=='call' else None#调用面
    return {#运行中根
        'callId':str(取字段(数据,'callId')),#身份
        'name':取字段(数据,'name'),#名
        'argsRaw':取字段(数据,'arguments'),#参数
        'turn':取字段(数据,'turn'),'step':取字段(数据,'step'),#坐标
        'time':取字段(事件,'time'),#时间
        'callView':调用面,#调用面
        'subCalls':[],#尚无子
    }#结束

def 根结果(匹配项,先前=None):#从 tool/result 建根结果节点
    """非结果事件则 None。"""
    事件=取字段(匹配项,'event')#事件
    if 取字段(事件,'type')!='tool/result':#非
        return None#无
    数据=取字段(事件,'data') or {}#载荷
    消息=取字段(数据,'message') or {}#消息
    内容=取字段(消息,'content') or []#内容
    首=内容[0] if 内容 else {}#第一块
    来源=取字段(消息,'source') or {}#来源
    视图=取字段(匹配项,'view')#视图
    结果={#已结算根
        'kind':'tool-result',#结果
        'seq':取字段(事件,'seq'),#序号
        'time':取字段(事件,'time'),#时间
        'callId':str(取字段(来源,'callId')),#调用身份
        'call':None if 先前 is None else {'name':取字段(先前,'name'),'argsRaw':取字段(先前,'argsRaw')},#名与参数
        'callTime':取字段(先前,'time') if 先前 is not None else None,#调用时间
        'content':取字段(首,'content'),#正文
        'isError':取字段(首,'isError') is True,#错误否
        'meta':取字段(数据,'meta'),#元数据
        'callView':取字段(先前,'callView') if 先前 is not None else None,#调用面
        'resultView':取字段(视图,'view') if 取字段(视图,'for')=='result' else None,#结果面
        'subCalls':[],#投影时再填
    }#结束
    if 取字段(数据,'error') is not None:#有错误对象
        结果['error']=取字段(数据,'error')#带上
    return 结果#根结果

def 位置回合(匹配项):#从匹配位置读回合号
    """步骤或回合位置才有。"""
    位=取字段(匹配项,'location') or {}#位置
    if 取字段(位,'kind') in ('step','turn'):#有
        return 取字段(取字段(位,'turn'),'turn',0)#回合
    return 0#无

def 位置步(匹配项):#从匹配位置读步骤号
    """仅步骤位置。"""
    位=取字段(匹配项,'location') or {}#位置
    if 取字段(位,'kind')=='step':#步骤
        return 取字段(取字段(位,'step'),'step',0)#步
    return 0#无

def 子调用(匹配项,数据):#从分发起始建运行中子调用
    """运行中子调用。"""
    return {#子
        'callId':取字段(数据,'subCallId'),#子身份
        'name':取字段(数据,'name'),#名
        'argsRaw':参数原文(取字段(数据,'arguments')),#参数
        'turn':位置回合(匹配项),'step':位置步(匹配项),#坐标
        'time':取字段(取字段(匹配项,'event'),'time'),#时间
        'callView':None,'subCalls':[],#无独立面
    }#结束

def 子结果(匹配项,数据,先前=None):#从分发结算建子结果
    """已结算子结果。"""
    return {#子结果
        'kind':'tool-result',#结果
        'seq':取字段(取字段(匹配项,'event'),'seq'),#序号
        'time':取字段(取字段(匹配项,'event'),'time'),#时间
        'callId':取字段(数据,'subCallId'),#子身份
        'call':{'name':取字段(数据,'name'),'argsRaw':参数原文(取字段(数据,'arguments'))},#名参
        'callTime':取字段(先前,'time') if 先前 is not None else None,#先前时间
        'content':取字段(数据,'content') if 取字段(数据,'content') is not None else [],#正文
        'isError':取字段(数据,'isError') is True,#错误
        'callView':None,'resultView':None,'subCalls':[],#无独立面
    }#结束

def 接受边(态,父,子):#是否允许 parent→child 边
    """自环/已有父/成环/超深则拒绝。"""
    if 父==子 or 子 in (态.get('parents') or {}):#自环或已有父
        return False#拒
    游标=父#沿父链
    父深=0#深度
    祖先=set()#已走
    父表=态.get('parents') or {}#父表
    while 游标 is not None:#尚未到根
        if 游标==子 or 游标 in 祖先:#成环
            return False#拒
        祖先.add(游标)#记
        父深+=1#加深
        游标=父表.get(游标)#上一层
    待=[{'callId':子,'depth':1}]#子树队列
    后代=set()#已见
    子深=0#最大深度
    子表=态.get('children') or {}#子表
    甲=0#游标
    while 甲<len(待):#广度
        候=待[甲]#候选
        甲+=1#前进
        if 候['callId'] in 后代:#成环
            return False#拒
        后代.add(候['callId'])#记
        子深=max(子深,候['depth'])#刷新
        for 嵌 in 子表.get(候['callId']) or []:#直接子
            待.append({'callId':取字段(嵌,'callId'),'depth':候['depth']+1})#入队
    return 父深+子深<=最大深度#不超深

def 折分发(态,匹配项):#把代码分发事件折进子树
    """start 挂运行中；dispatch 结算。"""
    事件=取字段(匹配项,'event')#事件
    种=取字段(事件,'type')#种
    if 种 not in ('tool/code-dispatch-start','tool/code-dispatch'):#非
        return 态#原样
    数据=取字段(事件,'data') or {}#载荷
    父标识=str(取字段(数据,'parentCallId'))#父
    子标识=str(取字段(数据,'subCallId'))#子
    子表=dict(态.get('children') or {})#拷贝子表
    父表=dict(态.get('parents') or {})#拷贝父表
    兄弟=list(子表.get(父标识) or [])#同父子
    下标=next((甲 for 甲,候 in enumerate(兄弟) if 取字段(候,'callId')==子标识),-1)#是否已有
    if 种=='tool/code-dispatch-start':#分发起始
        if 下标>=0 or not 接受边({'children':子表,'parents':父表},父标识,子标识):#已存在或非法
            return 态#不改
        子表[父标识]=兄弟+[子调用(匹配项,数据)]#追加
        父表[子标识]=父标识#记父
        return {**态,'children':子表,'parents':父表}#新态
    if 下标<0 and not 接受边({'children':子表,'parents':父表},父标识,子标识):#尚无且非法
        return 态#不改
    先前=兄弟[下标] if 下标>=0 else None#先前
    结算=子结果(匹配项,数据,先前)#结算
    if 下标<0:#追加
        子表[父标识]=兄弟+[结算]#追加
        父表[子标识]=父标识#记父
    else:#替换
        子表[父标识]=[结算 if 甲==下标 else 候 for 甲,候 in enumerate(兄弟)]#替换
    return {**态,'children':子表,'parents':父表}#新态

def 投影块(块,态,打断于,已访=None,深度=1):#把一块及其子投影成展示树
    """成环或超深则截断。"""
    已访=已访 or set()#路径
    标识=取字段(块,'callId')#callId
    if 标识 in 已访 or 深度>最大深度:#截断
        return {**块,'subCalls':[]} if isinstance(块,dict) else 块#空子
    下访=set(已访)#拷
    下访.add(标识)#计入
    原子=态.get('children',{}).get(标识)#状态子
    if 原子 is None:#无
        原子=取字段(块,'subCalls') or []#块自带
    孩子们=[投影块(子,态,打断于,下访,深度+1) for 子 in 原子]#递归
    已结算='kind' in 块 if isinstance(块,dict) else hasattr(块,'kind')#已结算
    打断序号=None if 已结算 else (取字段(打断于,'seq') if 打断于 else None)#打断序号
    打断时间=None if 已结算 else (取字段(打断于,'time') if 打断于 else None)#打断时间
    键=id(块)#缓存键
    缓存=投影缓存.get(键)#上次
    if 缓存 is not None and 缓存['interruptionSeq']==打断序号 and 缓存['interruptionTime']==打断时间 and 同引用(缓存['children'],孩子们):#命中
        return 缓存['value']#复用
    if 已结算 or 打断于 is None:#只换子
        投影=块 if 同引用(取字段(块,'subCalls') or [],孩子们) else {**块,'subCalls':孩子们}#复用或换
    else:#运行中且打断：合成错误结果
        投影={#打断结果
            'kind':'tool-result',#结果
            'seq':取字段(打断于,'seq')+聊天合成序号偏移['interruptedFollowup'],#合成
            'time':取字段(打断于,'time'),#时间
            'callId':标识,#身份
            'call':{'name':取字段(块,'name'),'argsRaw':取字段(块,'argsRaw')},#原名参
            'callTime':取字段(块,'time'),#原时间
            'content':[],#无正文
            'isError':True,#错误
            'error':{'name':'Interrupted','code':'interrupted'},#打断
            'callView':取字段(块,'callView'),#沿用
            'resultView':None,#无结果面
            'subCalls':孩子们,#子
        }#结束
    投影缓存[键]={'children':孩子们,'interruptionSeq':打断序号,'interruptionTime':打断时间,'value':投影}#写缓存
    return 投影#本次

def 打断边界(上下文):#关闭位置上的打断边界
    """步骤/回合关闭。"""
    起点=取字段(上下文,'start')#起点
    位置=取字段(起点,'location') if 起点 is not None else None#位置
    if 位置 is None:#无
        return None#无
    种=取字段(位置,'kind')#种
    if 种=='step' and 取字段(取字段(位置,'step'),'status')=='closed':#步骤关
        return 取字段(取字段(位置,'step'),'end')#步骤结束
    if 种 in ('step','turn') and 取字段(取字段(位置,'turn'),'status')=='closed':#回合关
        return 取字段(取字段(位置,'turn'),'end')#回合结束
    return None#开放

def 回放工具(上下文):#无增量时从匹配重放
    """找根结果再折分发。"""
    匹配们=取字段(上下文,'matches') or []#匹配
    根匹配=next((候 for 候 in 匹配们 if 取字段(取字段(候,'event'),'type')=='tool/result'),None)#根结果
    根=根结果(根匹配) if 根匹配 is not None else None#建成
    if 根 is None:#无
        return None#无法回放
    态={'root':根,'children':{},'parents':{}}#空子树
    for 候 in 匹配们:#按序
        态=折分发(态,候)#折
    return 态#重放

def 工具匹配(事件):#按事件认领本根调用
    """call 开；result/分发 更新。"""
    种=取字段(事件,'type')#种
    数据=取字段(事件,'data') or {}#载荷
    if 种=='tool/call':#调用开始
        return {'id':str(取字段(数据,'callId')),'role':'start'}#开
    if 种=='tool/result' and 是追加面事件(事件):#追加面结果
        来源=取字段(取字段(取字段(数据,'message'),'source'),'callId')#来源
        return {'id':str(来源),'role':'update'}#更新
    if 种 in ('tool/code-dispatch-start','tool/code-dispatch'):#分发
        根标识=取字段(数据,'rootCallId')#根
        if isinstance(根标识,str) and 根标识!='':#合法
            return {'id':根标识,'role':'update'}#挂根
        return None#不认领
    return None#其它

def 工具开始(_上下文,匹配项):#从 tool/call 开空子树
    """根调用。"""
    return {'root':根调用(匹配项),'children':{},'parents':{}}#空子树

def 工具更新(上下文,匹配项):#折一条更新事件
    """result 换根；其余当分发。"""
    事件=取字段(匹配项,'event')#事件
    态=取字段(上下文,'state')#态
    if 取字段(事件,'type')=='tool/result':#根结果
        运行=None if 已结算工具(态['root']) else 态['root']#仍运行才取
        结果=根结果(匹配项,运行)#建成
        return 态 if 结果 is None else {**态,'root':结果}#换根
    return 折分发(态,匹配项)#分发

def 工具建视图(上下文):#造聊天视图节点
    """投影含子调用与打断。"""
    态=取字段(上下文,'state') or 回放工具(上下文)#态
    if 态 is None:#无
        return None#无
    投影=投影块(态['root'],态,打断边界(上下文))#投影
    起点=取字段(上下文,'start')#起点
    锚=取字段(取字段(起点,'event'),'seq') if 起点 is not None else None#起始序号
    if 锚 is None:#无
        根=态['root']#根
        匹配们=取字段(上下文,'matches') or []#匹配
        锚=取字段(根,'seq') if 已结算工具(根) else (取字段(取字段(匹配们[0],'event'),'seq') if 匹配们 else 0)#回退
    return 聊天节点(上下文,'tool-call',锚,{'root':投影})#节点

工具定义={#根工具调用节点定义
    'kind':'tool-call','target':'chat',#kind/目标
    'match':工具匹配,'start':工具开始,'update':工具更新,'buildViewNode':工具建视图,#生命周期
}#结束

def 登记工具会话节点(上下文):#登记根工具生命周期
    """挂到 conversationEvents。"""
    上下文.conversationEvents.register(工具定义)#登记
