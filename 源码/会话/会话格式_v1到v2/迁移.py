"""相邻迁移：把已发布 v1 顶层助手块嵌入 v2 attempt 事件。"""
import json#未知类型诊断
from ...模型后端.llm.助手流 import 助手流累加器#助手流累加器
from ..会话格式 import (#从会话格式导入
    会话格式不支持迁移错误,#不支持迁移错误
    定义会话格式迁移,#定义迁移
    会话格式计数,#格式计数
)#从会话格式导入
from ..会话格式_v0到v1 import (#从v0到v1导入
    已发布v0事件处置表,#v0事件处置
    断言已发布事件载荷,#断言事件载荷
    断言已发布v1头,#断言v1头
    是否已发布助手块游程,#是否助手块游程
)#从v0到v1导入
from .校验 import 断言已发布v2头#从校验导入

块事件必填=('type','seq','time','data')#块事件必填
块事件可选=('ignorable','sourceEventSeqs','surfaceOp')#块事件可选
块事件键=frozenset([*块事件必填,*块事件可选])#块事件键

def 迁移头(头):#迁移头
    """把已发布 v1 头提升为 v2。"""
    断言已发布v1头(头)#断言v1头
    return {**头,'version':2}#提升版本

def 创建阶段(输入):#创建阶段
    """按源种类创建 v1 到 v2 阶段。"""
    if 输入['sourceKind']=='decoded':#解码源
        return 解码已发布v1到v2阶段(输入)#解码源阶段
    return 转换已发布v1到v2阶段(输入)#转换源阶段

#相邻迁移：把已发布 v1 顶层助手块嵌入 v2 attempt 事件。
会话格式v1到v2=定义会话格式迁移({#v1到v2迁移
    'name':'@deepseek-ai/dsh-session-format-v1-to-v2',#迁移名
    'fromVersion':1,#源版本
    'toVersion':2,#目标版本
    'migrateHeader':迁移头,#迁移头
    'createStage':创建阶段,#创建阶段
    'validateTargetHeader':断言已发布v2头,#校验目标头
})#会话格式v1到v2结束

class 转换已发布v1到v2阶段:#转换源阶段
    """有状态体阶段：把助手块嵌入 attempt。"""
    def __init__(自身,输入):#构造
        """记下源头并初始化迁移状态。"""
        断言已发布v1头(输入['sourceHeader'])#断言源头
        自身.状态={#初始化状态
            'sourceHeader':输入['sourceHeader'],#源头
            'sourceCut':会话格式计数(输入['sourceInheritedEventCount'],'format v1 inherited event count'),#源切口
            'mapping':{},#序号映射
            'legacyTurns':遗留回合状态(),#遗留回合
            'pending':None,#待定尝试
            'targetSeq':0,#目标序号
            'targetCut':None if 输入['sourceHeader']['isSeeded'] else 0,#目标切口
            'lastTime':输入['sourceHeader']['createdAt'],#末时间
        }#state结束

    def transformEvent(自身,事件,上下文):#转换事件
        """转换一条源事件。"""
        转换已发布事件(自身.状态,事件,上下文)#委托

    def transformRun(自身,游程,上下文):#转换游程
        """转换一个紧凑源游程。"""
        转换已发布游程(自身.状态,游程,上下文)#委托

    def finish(自身,上下文):#完成
        """结束尝试并返回目标切口。"""
        return 完成迁移(自身.状态,上下文)#委托

class 解码已发布v1到v2阶段(转换已发布v1到v2阶段):#解码源阶段
    """解码源：先断言已发布 v1 载荷。"""
    def transformEvent(自身,事件,上下文):#覆盖转换事件
        """断言载荷后委托父类。"""
        if 事件['type']!='assistant/chunk' and 事件['type'] in 已发布v0事件处置表:#已知处置
            断言已发布事件载荷(事件,1)#断言v1载荷
        super().transformEvent(事件,上下文)#父类转换

def 转换已发布事件(状态,事件,上下文):#转换已发布事件
    """转换一条已发布 v1 事件。"""
    if 事件['type']=='assistant/chunk':#块
        断言块信封(事件)#断言块信封
    if 事件['type'] not in 已发布v0事件处置表:#未知类型
        raise 拒绝(f"format v1 contains unknown event type {json.dumps(事件['type'],ensure_ascii=False)} at seq {事件['seq']}")#拒绝
    中断=遗留中断回合(状态['legacyTurns'],事件)#遗留中断回合
    if 事件['type']=='turn/start' and 状态['legacyTurns']['openTurn'] is not None and 中断 is None:#未关闭先验
        raise 拒绝(f"turn/start {json.dumps(记录(事件['data'])['turn'],ensure_ascii=False)} does not close the prior turn")#拒绝
    断言源投递标记(状态,事件)#断言投递标记
    观察遗留回合(状态['legacyTurns'],事件)#观察遗留回合
    状态['lastTime']=事件['time']#更新末时间
    if 中断 is not None:#有中断回合
        结束尝试(状态,上下文)#结束尝试
        发出生成(状态,事件['seq'],中断,上下文)#发出生成
    遗留目标=拆遗留目标变更(事件)#拆遗留目标变更
    if 遗留目标 is not None:#有目标变更
        发出生成(状态,事件['seq'],遗留目标['change'],上下文)#发出变更
        发出源(状态,遗留目标['message'],上下文)#发出消息
        return#返回
    if 事件['type']=='assistant/chunk':#助手块
        转换块(状态,事件,上下文)#转换块
        return#返回
    if 事件['type']=='assistant/message':#助手消息
        转换消息(状态,事件,上下文)#转换消息
        return#返回
    if 关闭尝试(事件):#关闭尝试
        结束尝试(状态,上下文)#结束尝试
        发出源(状态,事件,上下文)#发出源
        return#返回
    if 状态['pending'] is not None:#有待定
        状态['pending']['afterLastChunk'].append(事件)#缓冲
        return#返回
    发出源(状态,事件,上下文)#发出源

def 断言块信封(事件):#断言块信封
    """断言 assistant/chunk 信封键。"""
    for 键 in 事件.keys():#意外键
        if 键 not in 块事件键:#意外
            raise 拒绝(f"assistant/chunk {事件['seq']} has unexpected member {键}")#意外成员
    for 键 in 块事件必填:#缺必填
        if 键 not in 事件:#缺
            raise 拒绝(f"assistant/chunk {事件['seq']} lacks required member {键}")#缺成员
    if 'ignorable' in 事件 and 事件['ignorable'] is not True:#ignorable非法
        raise 拒绝(f"assistant/chunk {事件['seq']} ignorable must be true when present")#拒绝

def 断言源投递标记(状态,事件):#断言源投递标记
    """拒绝错会话的当代投递标记。"""
    if 事件['type']!='session-log-deepseek/delivery-accepted':#非该类型
        return#返回
    数据=记录(事件['data'])#data
    继承=状态['sourceHeader'].get('parentSession') is not None and 事件['seq']<状态['sourceCut']#继承
    if 数据.get('sessionFormatVersion')==1 and not 继承 and 数据.get('sessionId')!=状态['sourceHeader']['id']:#错会话
        raise 拒绝('current-generation delivery marker names the wrong Session')#拒绝

def 转换已发布游程(状态,游程,上下文):#转换已发布游程
    """转换紧凑助手块游程或展开其它游程。"""
    if not 是否已发布助手块游程(游程):#非助手块游程
        for 事件 in 游程.expand():#展开
            转换已发布事件(状态,事件,上下文)#转换
        return#返回
    状态['legacyTurns']['previous']=None#清空前事件
    状态['lastTime']=游程.lastTime#更新末时间
    待定=状态['pending']#待定
    if 待定 is not None and (待定['group']['terminal'] or 待定['group']['turn']!=游程.turn or 待定['group']['step']!=游程.step):#变尝试
        结束尝试(状态,上下文)#结束尝试
    elif 待定 is not None:#同尝试续接
        冲刷缓冲(状态,待定,上下文)#冲刷缓冲
    if 状态['pending'] is None:#确保待定
        状态['pending']={'group':尝试组(游程.turn,游程.step),'afterLastChunk':[]}#新建
    断言尝试范围(状态,游程.firstSeq,游程.lastSeq)#断言跨度切口
    冲刷累加器(状态['pending']['group'])#冲刷累加器
    追加流记录(状态['pending']['group'],游程.stream,游程.lastTime)#追加流记录
    记块跨度(状态['pending']['group'],游程.firstSeq,游程.eventCount,游程.lastTime)#记跨度

def 完成迁移(状态,上下文):#完成迁移
    """结束尝试、补种子切口并返回目标切口。"""
    结束尝试(状态,上下文)#结束尝试
    if 状态['sourceHeader']['isSeeded'] and 状态['targetCut'] is None:#种子缺切口
        状态['targetCut']=状态['targetSeq']#记切口
        上下文.emitEvent({#发出结束种子
            'type':'session/end-seed',#类型
            'seq':状态['targetSeq'],#序号
            'time':状态['lastTime'],#时间
            'data':{'inherited':True},#继承
        })#emit结束
        状态['targetSeq']+=1#推进
    return 状态['targetCut']#返回切口

def 转换块(状态,事件,上下文):#转换块
    """把一条 assistant/chunk 并入待定尝试。"""
    数据=记录(事件['data'])#data
    回合=坐标(数据['turn'])#回合
    步骤=坐标(数据['step'])#步骤
    块=记录(数据['chunk'])#块
    待定=状态['pending']#待定
    if 待定 is not None and (待定['group']['terminal'] or 待定['group']['turn']!=回合 or 待定['group']['step']!=步骤):#变尝试
        结束尝试(状态,上下文)#结束尝试
    elif 待定 is not None:#同尝试
        冲刷缓冲(状态,待定,上下文)#冲刷缓冲
    if 状态['pending'] is None:#确保待定
        状态['pending']={'group':尝试组(回合,步骤),'afterLastChunk':[]}#新建
    待定=状态['pending']#取待定
    断言尝试切口(状态,待定['group'],事件['seq'])#断言切口
    if 待定['group'].get('accumulator') is None:#确保累加器
        待定['group']['accumulator']=助手流累加器()#新建
    待定['group']['accumulator'].推入({'time':事件['time'],'chunk':数据['chunk']})#推入块
    记块跨度(待定['group'],事件['seq'],1,事件['time'])#记跨度
    if 块.get('type')=='finish':#终止
        待定['group']['terminal']=True#终止

def 转换消息(状态,事件,上下文):#转换消息
    """把助手消息绑定到完整块尝试。"""
    数据=记录(事件['data'])#data
    回合=坐标(数据['turn'])#回合
    步骤=坐标(数据['step'])#步骤
    出处=事件.get('sourceEventSeqs')#出处
    待定=状态['pending']#待定
    if 待定 is not None and (待定['group']['turn']!=回合 or 待定['group']['step']!=步骤):#坐标不符
        结束尝试(状态,上下文)#结束尝试
        发出源(状态,消息事件(事件,尝试组(回合,步骤)),上下文)#发出空流消息
        return#返回
    if not isinstance(出处,list):#无出处
        if 待定 is not None:#却有待定
            raise 拒绝(f"assistant/message {事件['seq']} does not cite its complete v1 chunk attempt")#拒绝
        发出源(状态,消息事件(事件,尝试组(回合,步骤)),上下文)#发出空流消息
        return#返回
    if len(出处)==0:#空出处
        结束尝试(状态,上下文)#结束尝试
        发出源(状态,消息事件(事件,尝试组(回合,步骤)),上下文)#发出空流消息
        return#返回
    if 待定 is None or not 出处匹配(待定['group'],出处):#出处不匹配
        raise 拒绝(f"assistant/message {事件['seq']} chunk provenance is not one complete ordered attempt")#拒绝
    断言尝试切口(状态,待定['group'],事件['seq'])#断言切口
    待定['group']['terminal']=True#终止
    冲刷缓冲(状态,待定,上下文)#冲刷缓冲
    发出源(状态,消息事件(事件,待定['group']),上下文)#发出消息
    状态['pending']=None#清空待定

def 结束尝试(状态,上下文):#结束尝试
    """发出 pending attempt 并冲刷缓冲。"""
    待定=状态['pending']#待定
    if 待定 is None:#无待定
        return#返回
    发出生成(状态,待定['group']['lastChunkSeq'],尝试事件(待定['group']),上下文)#发出attempt
    冲刷缓冲(状态,待定,上下文)#冲刷缓冲
    状态['pending']=None#清空

def 冲刷缓冲(状态,待定,上下文):#冲刷缓冲
    """发出末块后缓冲事件。"""
    for 事件 in 待定['afterLastChunk']:#缓冲
        发出源(状态,事件,上下文)#发出
    待定['afterLastChunk'].clear()#清空

def 发出源(状态,事件,上下文):#发出源事件
    """重映射并发出一条源事件。"""
    源=事件#源
    if (状态['sourceHeader']['isSeeded']
        and 事件['seq']==状态['sourceCut']
        and 事件['type']=='session/end-seed'):#恰在切口
        源={**事件,'data':{'inherited':True}}#标记继承
    确保目标切口(状态,事件['seq'],事件['time'],源['type'],上下文)#确保目标切口
    状态['mapping'][事件['seq']]=状态['targetSeq']#记映射
    上下文.emitEvent(重映射引用(源,状态['targetSeq'],状态['mapping']))#重映射发出
    状态['targetSeq']+=1#推进

def 发出生成(状态,源序号,事件,上下文):#发出生成事件
    """发出一条生成事件。"""
    确保目标切口(状态,源序号,事件['time'],事件['type'],上下文)#确保目标切口
    上下文.emitEvent(重映射引用(事件,状态['targetSeq'],状态['mapping']))#重映射发出
    状态['targetSeq']+=1#推进

def 确保目标切口(状态,源序号,时间,类型,上下文):#确保目标切口
    """在源切口处插入目标 end-seed。"""
    if not 状态['sourceHeader']['isSeeded'] or 状态['targetCut'] is not None or 源序号<状态['sourceCut']:#无需
        return#返回
    状态['targetCut']=状态['targetSeq']#记切口
    if 源序号==状态['sourceCut'] and 类型=='session/end-seed':#本事件即标记
        return#返回
    上下文.emitEvent({#插入结束种子
        'type':'session/end-seed',#类型
        'seq':状态['targetSeq'],#序号
        'time':时间,#时间
        'data':{'inherited':True},#继承
    })#emit结束
    状态['targetSeq']+=1#推进

def 断言尝试切口(状态,组,成员):#断言尝试切口
    """拒绝跨继承切口的 attempt。"""
    首=组['spans'][0]['firstSeq'] if 组['spans'] else 成员#首序号
    if (首<状态['sourceCut'])!=(成员<状态['sourceCut']):#跨切口
        raise 拒绝(f"inherited Session cut {状态['sourceCut']} splits one Assistant attempt")#拒绝

def 断言尝试范围(状态,首,末):#断言尝试范围
    """拒绝跨继承切口的游程范围。"""
    if (首<状态['sourceCut'])!=(末<状态['sourceCut']):#跨切口
        raise 拒绝(f"inherited Session cut {状态['sourceCut']} splits one Assistant attempt")#拒绝

def 遗留回合状态():#创建遗留回合状态
    """开放回合观察初值。"""
    return {'openTurn':None,'openStep':None,'previous':None}#初值

def 遗留中断回合(状态,事件):#遗留中断回合
    """在拼接模式下合成 turn/end。"""
    if (事件['type']!='turn/start' or 状态['openTurn'] is None or 状态['openStep'] is not None
        or 坐标(记录(事件['data'])['turn'])!=状态['openTurn']+1
        or (状态['previous'] is None or 状态['previous']['type']!='agent/inbox/spliced')):#条件不符
        return None#无
    拼接=记录(状态['previous']['data'])#拼接data
    if 拼接.get('target')!='next-turn' or not isinstance(拼接.get('inserted'),list) or len(拼接['inserted'])==0:#非有效拼接
        return None#无
    return {#合成turn/end
        'type':'turn/end',#类型
        'seq':事件['seq'],#序号
        'time':事件['time'],#时间
        'data':{'turn':状态['openTurn'],'reason':{'kind':'interrupted'}},#中断原因
    }#return结束

def 观察遗留回合(状态,事件):#观察遗留回合
    """更新开放回合/步骤。"""
    数据=记录(事件['data'])#data
    if 事件['type']=='turn/start':#回合开始
        状态['openTurn']=坐标(数据['turn'])#开放
        状态['openStep']=None#清空步骤
    elif 事件['type']=='turn/end':#回合结束
        状态['openTurn']=None#关闭
        状态['openStep']=None#清空
    elif 事件['type']=='step/start':#步骤开始
        状态['openStep']=坐标(数据['step'])#开放
    elif 事件['type']=='step/end':#步骤结束
        状态['openStep']=None#关闭
    状态['previous']=事件#记前事件

def 拆遗留目标变更(事件):#拆遗留目标变更
    """把 goal 出处用户消息拆成 change + message。"""
    if 事件['type']!='user/message':#非用户消息
        return None#无
    数据=记录(事件['data'])#data
    出处=记录(数据['source'])#出处
    if 出处.get('kind')!='goal' or 'change' not in 出处:#非遗留目标
        return None#无
    return {#拆分
        'change':{#变更
            'type':'goal/change',#类型
            'seq':事件['seq'],#序号
            'time':事件['time'],#时间
            'data':出处['change'],#变更data
        },#change结束
        'message':{#消息
            **事件,#展开
            'data':{**数据,'source':{'kind':'plugin','plugin':'goal'}},#插件出处
        },#message结束
    }#return结束

def 关闭尝试(事件):#是否关闭尝试
    """回合/步骤/重试边界关闭 attempt。"""
    return 事件['type'] in ('turn/end','step/end','llm/retry','llm/retry-started')#边界

def 尝试组(回合,步骤):#创建尝试组
    """空 attempt 组。"""
    return {'turn':回合,'step':步骤,'spans':[],'stream':[],'chunkCount':0,'terminal':False}#初值

def 记块跨度(组,首序号,事件数,末时间):#记块跨度
    """合并或追加块跨度。"""
    前=组['spans'][-1] if 组['spans'] else None#上一跨度
    if 前 is not None and 前['firstSeq']+前['eventCount']==首序号:#可合并
        前['eventCount']+=事件数#合并
    else:#新跨度
        组['spans'].append({'firstSeq':首序号,'eventCount':事件数})#推入
    组['chunkCount']+=事件数#累加块数
    组['lastChunkSeq']=首序号+事件数-1#末序号
    组['lastChunkTime']=末时间#末时间

def 出处匹配(组,出处):#出处是否匹配
    """出处列表是否恰为一完整有序 attempt。"""
    if len(出处)!=组['chunkCount']:#长度不符
        return False#不符
    索引=0#索引
    for 跨度 in 组['spans']:#遍历跨度
        for 偏移 in range(跨度['eventCount']):#遍历成员
            if 出处[索引]!=跨度['firstSeq']+偏移:#序号不符
                return False#不符
            索引+=1#推进
    return True#匹配

def 流记录末时间(记录值):#流记录末时间
    """计算紧凑流记录末时间。"""
    if 记录值['type']=='chunk':#单块
        return 记录值['time']#时间
    时间=记录值['time0']#起点
    for 间隙 in 记录值['dt']:#累加
        时间+=间隙#推进
    return 时间#返回

def 可变流记录(记录值):#可变流记录
    """拷贝可合并流记录。"""
    if 记录值['type']=='chunk':#单块原样
        return 记录值#原样
    if 记录值['type']=='tool-call-chunks':#工具块
        return {**记录值,'dt':list(记录值['dt']),'args':list(记录值['args'])}#拷贝
    return {**记录值,'dt':list(记录值['dt']),'texts':list(记录值['texts'])}#文本/推理拷贝

def 追加流记录(组,源,末时间,已拥有=True):#追加流记录
    """合并或追加一条紧凑流记录。"""
    流=组['stream']#流
    前=流[-1] if 流 else None#前一记录
    if 前 is None or 源['type']=='chunk' or 前['record']['type']!=源['type']:#不可合并
        流.append({'record':源 if 已拥有 else 可变流记录(源),'lastTime':末时间})#推入
        return#返回
    间隙=源['time0']-前['lastTime']#间隙
    if 前['record']['index']!=源['index'] or not isinstance(间隙,int) or isinstance(间隙,bool):#索引或间隙非法
        流.append({'record':源 if 已拥有 else 可变流记录(源),'lastTime':末时间})#推入
        return#返回
    if 源['type']=='tool-call-chunks':#工具合并
        目标=前['record']#目标
        if 目标['id']!=源['id'] or 目标.get('name')!=源.get('name'):#身份不符
            流.append({'record':源 if 已拥有 else 可变流记录(源),'lastTime':末时间})#推入
            return#返回
        目标['dt'].append(间隙)#推间隙
        目标['dt'].extend(源['dt'])#推时间差
        目标['args'].extend(源['args'])#推参数
    else:#文本/推理合并
        目标=前['record']#目标
        目标['dt'].append(间隙)#推间隙
        目标['dt'].extend(源['dt'])#推时间差
        目标['texts'].extend(源['texts'])#推文本
    前['lastTime']=末时间#更新末时间

def 冲刷累加器(组):#冲刷累加器
    """把累加器快照并入流。"""
    累加器=组.get('accumulator')#累加器
    if 累加器 is None:#无则返回
        return#返回
    for 记录值 in 累加器.快照():#快照记录
        追加流记录(组,记录值,流记录末时间(记录值),False)#追加
    组.pop('accumulator',None)#删除累加器

def 组流(组):#组流
    """冲刷并返回流记录列表。"""
    冲刷累加器(组)#冲刷
    return [项['record'] for 项 in 组['stream']]#映射记录

def 消息事件(源,组):#消息事件
    """把 v1 助手消息改写为带嵌入流的 v2 消息。"""
    数据=记录(源['data'])#data
    事件={键:值 for 键,值 in 源.items() if 键!='sourceEventSeqs'}#去掉出处
    return {**事件,'data':{**数据,'stream':组流(组)}}#返回嵌入流

def 尝试事件(组):#attempt事件
    """构造 assistant/attempt。"""
    return {#返回
        'type':'assistant/attempt',#类型
        'seq':组['lastChunkSeq'],#序号
        'time':组['lastChunkTime'],#时间
        'data':{'turn':组['turn'],'step':组['step'],'stream':组流(组)},#数据
    }#return结束

def 重映射引用(源,目标序号,映射):#重映射引用
    """重映射表面出处与载荷引用。"""
    事件={键:值 for 键,值 in 源.items() if 键 not in ('sourceEventSeqs','surfaceOp')}#拆字段
    出处=源.get('sourceEventSeqs')#出处
    出处字段={} if 出处 is None else {#映射出处
        'sourceEventSeqs':映射列表(数字数组(出处),映射,f"{源['type']} {源['seq']} sources"),#映射列表
    }#sources结束
    操作=源.get('surfaceOp')#表面操作
    if 操作 is not None and 操作!='append':#替换
        替换=记录(操作)#替换记录
        操作={#映射替换
            'op':'replace',#操作
            'start':映射一项(坐标(替换['start']),映射,f"{源['type']} {源['seq']} surface start"),#起点
            'end':映射一项(坐标(替换['end']),映射,f"{源['type']} {源['seq']} surface end"),#终点
        }#operation结束
    结果={#返回
        **事件,#展开
        'seq':目标序号,#目标序号
        'data':重映射载荷引用(源,映射),#载荷引用
        **出处字段,#出处
    }#return结束
    if 操作 is not None:#有表面操作
        结果['surfaceOp']=操作#带上
    return 结果#返回

def 重映射载荷引用(事件,映射):#重映射载荷引用
    """按事件类型重映射载荷内序号。"""
    数据=记录(事件['data'])#data
    if 事件['type']=='command/done':#命令完成
        if 'sourceEventSeq' not in 数据:#无源序号
            return 数据#原样
        return {#映射源序号
            **数据,#展开
            'sourceEventSeq':映射一项(坐标(数据['sourceEventSeq']),映射,f"command/done {事件['seq']} sourceEventSeq"),#映射
        }#return结束
    if 事件['type'] in ('compaction/prune','compaction/summary'):#压缩剪枝/摘要
        范围=记录(数据['shadowedRange'])#范围
        return {#映射遮蔽
            **数据,#展开
            'shadowedRange':{#范围
                'start':映射一项(坐标(范围['start']),映射,f"{事件['type']} {事件['seq']} shadowedRange start"),#起点
                'end':映射一项(坐标(范围['end']),映射,f"{事件['type']} {事件['seq']} shadowedRange end"),#终点
            },#shadowedRange结束
            'shadowedSeqs':映射列表(数字数组(数据['shadowedSeqs']),映射,f"{事件['type']} {事件['seq']} shadowedSeqs"),#序号列表
        }#return结束
    if 事件['type'] in ('session/title','session/title-llm-request'):#会话标题
        return {#映射消息序号
            **数据,#展开
            'messageSeqs':映射列表(数字数组(数据['messageSeqs']),映射,f"{事件['type']} {事件['seq']} messageSeqs"),#列表
        }#return结束
    return 数据#原样

def 映射列表(值列表,映射,标签):#映射列表
    """逐项映射序号列表。"""
    return [映射一项(值,映射,标签) for 值 in 值列表]#逐项映射

def 映射一项(值,映射,标签):#映射一项
    """查序号映射。"""
    if 值 not in 映射:#无映射
        raise 拒绝(f'{标签} targets consumed assistant/chunk {值}')#消费块
    return 映射[值]#返回

def 记录(值):#记录
    """断言为对象。"""
    return 值#断言

def 数字数组(值):#数字数组
    """断言为数字数组。"""
    return 值#断言

def 坐标(值):#坐标
    """断言为数字坐标。"""
    return 值#断言

def 拒绝(消息):#拒绝错误
    """构造不支持迁移错误。"""
    return 会话格式不支持迁移错误(消息)#构造
