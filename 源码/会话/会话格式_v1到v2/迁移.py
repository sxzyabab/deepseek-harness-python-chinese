"""相邻迁移：把已发布 v1 顶层助手块嵌入 v2 attempt 事件。"""
import json#未知类型诊断
from ...模型后端.llm import 助手流累加器#助手流累加器
from ..会话格式 import (#从会话格式导入
    会话格式不支持迁移错误,#不支持迁移错误
    定义会话格式迁移,#定义迁移
    快照会话格式产物,#快照产物
)#从会话格式导入
from ..会话格式_v0到v1 import (#从v0到v1导入
    已发布v0事件处置,#v0事件处置
    断言已发布v1产物,#断言v1产物
    断言已发布v1头,#断言v1头
)#从v0到v1导入
from .校验 import 断言已发布v2产物,断言已发布v2头#从校验导入

def 收集尝试组(事件们):#收集尝试组
    """把 v1 助手块与消息归并为 attempt 组。"""
    组们=[]#组列表
    当前={}#当前组
    for 事件 in 事件们:#遍历
        if 事件['type']=='assistant/chunk':#块
            数据=记录(事件['data'])#data
            回合=坐标(数据['turn'])#回合
            步骤=坐标(数据['step'])#步骤
            键=f'{回合}:{步骤}'#键
            组=当前.get(键)#取组
            if 组 is None or 组['已终止']:#新组
                组={'回合':回合,'步骤':步骤,'块们':[],'已终止':False}#创建
                组们.append(组)#推入
                当前[键]=组#登记
            组['块们'].append(事件)#推块
            块=记录(数据['chunk'])#chunk
            if 块['type']=='finish':#finish终止
                组['已终止']=True#终止
            continue#继续
        if 事件['type']!='assistant/message':#非消息
            边界关闭尝试(事件,当前)#边界关闭
            continue#继续
        数据=记录(事件['data'])#data
        回合=坐标(数据['turn'])#回合
        步骤=坐标(数据['step'])#步骤
        出处=事件.get('sourceEventSeqs')#出处
        if not isinstance(出处,list):#无列表
            未认领=False#未认领
            for 候选 in 组们:#查未认领
                if '消息序号' not in 候选 and 候选['回合']==回合 and 候选['步骤']==步骤:#未认领
                    未认领=True#命中
                    break#找到
            if 未认领:#有未认领
                raise 拒绝(f"assistant/message {事件['seq']} does not cite its complete v1 chunk attempt")#拒绝
            组们.append({'回合':回合,'步骤':步骤,'块们':[],'已终止':True,'消息序号':事件['seq']})#空块消息
            continue#继续
        if len(出处)==0:#显式空列表
            #已发布v1用显式空列表声明本消息不拥有前置块；缺列表不能做该声明。
            组们.append({'回合':回合,'步骤':步骤,'块们':[],'已终止':True,'消息序号':事件['seq']})#空块消息
            continue#继续
        组=None#匹配组
        for 候选 in 组们:#找匹配组
            if ('消息序号' not in 候选#未绑消息
                and 候选['回合']==回合#同回合
                and 候选['步骤']==步骤#同步骤
                and 相同数字([块['seq'] for 块 in 候选['块们']],出处)):#出处一致
                组=候选#命中
                break#找到
        if 组 is None:#无匹配
            raise 拒绝(f"assistant/message {事件['seq']} chunk provenance is not one complete ordered attempt")#拒绝
        组['消息序号']=事件['seq']#绑定消息
        组['已终止']=True#终止
    return 组们#返回

def 边界关闭尝试(事件,当前):#边界关闭尝试
    """在回合/步骤边界把当前 attempt 标为终止。"""
    if 事件['type']=='turn/end':#回合结束
        数据=记录(事件['data'])#data
        回合=坐标(数据['turn'])#回合
        for 组 in 当前.values():#遍历组
            if 组['回合']==回合:#同回合
                组['已终止']=True#终止
        return#返回
    if (事件['type']!='step/end'#非边界
        and 事件['type']!='llm/retry'
        and 事件['type']!='llm/retry-started'):
        return#非边界则返回
    数据=记录(事件['data'])#data
    回合=坐标(数据['turn'])#回合
    步骤=坐标(数据['step'])#步骤
    组=当前.get(f'{回合}:{步骤}')#取组
    if 组 is not None:#有组
        组['已终止']=True#终止

def 流自组(组):#组转流
    """把一组 v1 块累加为嵌入流快照。"""
    累加器=助手流累加器()#累加器
    for 事件 in 组['块们']:#遍历块
        数据=记录(事件['data'])#data
        累加器.推入({'time':事件['time'],'chunk':数据['chunk']})#推入
    return 累加器.快照()#快照

def 消息事件(源,组):#消息事件
    """把 v1 助手消息改写为带嵌入流的 v2 消息。"""
    数据=记录(源['data'])#data
    事件=dict(源)#去掉出处
    事件.pop('sourceEventSeqs',None)#去掉出处
    新数据=dict(数据)#载荷
    新数据['stream']=流自组(组)#嵌入流
    事件['data']=新数据#写回
    return 事件#返回

def 尝试事件(组):#attempt事件
    """无收口消息时由末块合成 assistant/attempt。"""
    末块=组['块们'][-1]#末块
    return {#返回
        'type':'assistant/attempt',#类型
        'seq':末块['seq'],#序号
        'time':末块['time'],#时间
        'data':{'turn':组['回合'],'step':组['步骤'],'stream':流自组(组)},#数据
    }#return结束

def 暂存(暂存们,旧到新,源序号,事件):#暂存
    """登记旧序号映射并推入暂存事件。"""
    旧到新[源序号]=len(暂存们)#登记映射
    暂存们.append({'源序号':源序号,'事件':事件})#推入

def 重映射继承切割(源,组们,暂存们):#重映射继承切割
    """把继承切割映射到压缩后的暂存序列。"""
    切割=源['inheritedEventCount']#旧切割
    for 组 in 组们:#遍历组
        if '消息序号' not in 组:#无消息
            成员=[块['seq'] for 块 in 组['块们']]#仅块
        else:#有消息
            成员=[块['seq'] for 块 in 组['块们']]+[组['消息序号']]#块加消息
        前=any(序号<切割 for 序号 in 成员)#切割前
        后=any(序号>=切割 for 序号 in 成员)#切割后
        if 前 and 后:#拆分
            raise 拒绝(f'inherited Session cut {切割} splits one Assistant attempt')#拒绝拆分
    return len([候选 for 候选 in 暂存们 if 候选['源序号']<切割])#新切割长度

def 重映射引用(源,目标序号,映射):#重映射引用
    """按旧到新映射改写出处、表面操作与载荷引用。"""
    事件=dict(源)#拆字段
    出处序号=事件.pop('sourceEventSeqs',None)#出处
    表面操作=事件.pop('surfaceOp',None)#表面操作
    if 出处序号 is None:#无出处
        出处们={}#空
    else:#有出处
        出处们={'sourceEventSeqs':映射列表(#出处映射
            数字数组(出处序号),#数字数组
            映射,#映射
            f"{源['type']} {源['seq']} sources",#标签
        )}#出处结束
    操作=表面操作#表面操作
    if 表面操作 is not None and 表面操作!='append':#替换操作
        替换=记录(表面操作)#记录
        操作={#新操作
            'op':'replace',#操作
            'start':映射一个(#起点
                坐标(替换['start']),#坐标
                映射,#映射
                f"{源['type']} {源['seq']} surface start",#标签
            ),#start结束
            'end':映射一个(#终点
                坐标(替换['end']),#坐标
                映射,#映射
                f"{源['type']} {源['seq']} surface end",#标签
            ),#end结束
        }#新操作结束
    结果={**事件,'seq':目标序号,'data':重映射载荷引用(源,映射),**出处们}#基结果
    if 操作 is not None:#有表面操作
        结果['surfaceOp']=操作#写回
    return 结果#返回

def 重映射载荷引用(事件,映射):#重映射载荷引用
    """按事件类型重映射载荷内序号引用。"""
    数据=记录(事件['data'])#data
    类型=事件['type']#类型
    if 类型=='command/done':#命令完成
        if 'sourceEventSeq' not in 数据:#无引用
            return 数据#原样
        新数据=dict(数据)#副本
        新数据['sourceEventSeq']=映射一个(#映射
            坐标(数据['sourceEventSeq']),#坐标
            映射,#映射
            f"command/done {事件['seq']} sourceEventSeq",#标签
        )#映射结束
        return 新数据#有引用
    if 类型=='compaction/prune' or 类型=='compaction/summary':#压缩
        范围=记录(数据['shadowedRange'])#范围
        新数据=dict(数据)#副本
        新数据['shadowedRange']={#新范围
            'start':映射一个(#起点
                坐标(范围['start']),#坐标
                映射,#映射
                f"{类型} {事件['seq']} shadowedRange start",#标签
            ),#start结束
            'end':映射一个(#终点
                坐标(范围['end']),#坐标
                映射,#映射
                f"{类型} {事件['seq']} shadowedRange end",#标签
            ),#end结束
        }#范围结束
        新数据['shadowedSeqs']=映射列表(#序号列表
            数字数组(数据['shadowedSeqs']),#数字数组
            映射,#映射
            f"{类型} {事件['seq']} shadowedSeqs",#标签
        )#映射结束
        return 新数据#返回
    if 类型=='session/title' or 类型=='session/title-llm-request':#标题
        新数据=dict(数据)#副本
        新数据['messageSeqs']=映射列表(#消息序号
            数字数组(数据['messageSeqs']),#数字数组
            映射,#映射
            f"{类型} {事件['seq']} messageSeqs",#标签
        )#映射结束
        return 新数据#返回
    return 数据#原样

def 映射列表(值们,映射,标签):#映射列表
    """逐个映射序号列表。"""
    return [映射一个(值,映射,标签) for 值 in 值们]#逐个映射

def 映射一个(值,映射,标签):#映射单个
    """映射单个旧序号；缺失则拒绝。"""
    if 值 not in 映射:#无映射
        raise 拒绝(f'{标签} targets consumed assistant/chunk {值}')#拒绝
    return 映射[值]#返回

def 记录(值):#转记录
    """载荷坐标已由 assertReleasedV1Artifact 校验。"""
    return 值#断言

def 数字数组(值):#转数字数组
    """断言为数字数组。"""
    return 值#断言

def 坐标(值):#转坐标
    """断言为数字坐标。"""
    return 值#断言

def 相同数字(左,右):#数字序列相同
    """比较两个数字序列是否全等。"""
    return len(左)==len(右) and all(左[下标]==右[下标] for 下标 in range(len(左)))#比较

def 拒绝(消息):#拒绝错误
    """构造不支持迁移错误。"""
    return 会话格式不支持迁移错误(消息)#构造

def 迁移头(头):#迁移头
    """把已发布 v1 头提升为 v2。"""
    断言已发布v1头(头)#断言v1头
    结果=dict(头)#副本
    结果['version']=2#提升版本
    return 结果#返回

def 迁移产物(源):#迁移产物
    """把已发布 v1 产物嵌入助手流并升到 v2。"""
    断言已发布v1产物(源)#断言源
    未知=None#未知事件
    for 事件 in 源['events']:#找未知
        if 事件['type'] not in 已发布v0事件处置:#未知
            未知=事件#记下
            break#找到
    if 未知 is not None:#有未知
        raise 拒绝(f'format v1 contains unknown event type {json.dumps(未知["type"],ensure_ascii=False)} at seq {未知["seq"]}')#拒绝
    组们=收集尝试组(源['events'])#收集尝试组
    块到组={}#块到组
    消息到组={}#消息到组
    for 组 in 组们:#遍历组
        for 块 in 组['块们']:#登记块
            块到组[块['seq']]=组#登记
        if '消息序号' in 组:#有消息
            消息到组[组['消息序号']]=组#登记消息
    暂存们=[]#暂存
    旧到新={}#旧到新映射
    for 源事件 in 源['events']:#遍历源事件
        组=块到组.get(源事件['seq'])#块所属组
        if 组 is not None:#是块
            if '消息序号' not in 组 and 源事件['seq']==组['块们'][-1]['seq']:#无消息且末块
                暂存(暂存们,旧到新,源事件['seq'],尝试事件(组))#暂存attempt
            continue#跳过块
        消息组=消息到组.get(源事件['seq'])#消息所属组
        if 消息组 is not None:#是消息
            暂存(暂存们,旧到新,源事件['seq'],消息事件(源事件,消息组))#暂存消息
            continue#跳过
        if (源['header']['isSeeded']#是否种子切割
            and 源事件['seq']==源['inheritedEventCount']#恰为切割点
            and 源事件['type']=='session/end-seed'):#end-seed
            事件=dict(源事件)#副本
            事件['data']={'inherited':True}#补inherited
        else:#原样
            事件=源事件#原样
        暂存(暂存们,旧到新,源事件['seq'],事件)#暂存
    继承事件数=重映射继承切割(源,组们,暂存们)#重映射切割
    if 源['header']['isSeeded'] and (源['inheritedEventCount']>=len(源['events']) or 源['events'][源['inheritedEventCount']]['type']!='session/end-seed'):#缺标记
        下一=源['events'][源['inheritedEventCount']] if 源['inheritedEventCount']<len(源['events']) else None#下一事件
        上一=源['events'][源['inheritedEventCount']-1] if 源['inheritedEventCount']>0 else None#上一事件
        if 下一 is not None:#有下一
            时间=下一['time']#时间
        elif 上一 is not None:#有上一
            时间=上一['time']#时间
        else:#用头
            时间=源['header']['createdAt']#时间
        暂存们.insert(继承事件数,{#插入end-seed
            '源序号':-1,#合成源
            '事件':{#事件
                'type':'session/end-seed',#类型
                'seq':继承事件数,#序号
                'time':时间,#时间
                'data':{'inherited':True},#数据
            },#event结束
        })#insert结束
        旧到新.clear()#清空映射
        for 序号,候选 in enumerate(暂存们):#重建映射
            if 候选['源序号']>=0:#真实源
                旧到新[候选['源序号']]=序号#登记
    for 组 in 组们:#删除块映射
        for 块 in 组['块们']:#删块
            旧到新.pop(块['seq'],None)#删块
    目标头=dict(源['header'])#v2头
    目标头['version']=2#版本
    目标=快照会话格式产物({#快照目标
        'header':目标头,#v2头
        'inheritedEventCount':继承事件数,#继承数
        'events':[重映射引用(项['事件'],序号,旧到新) for 序号,项 in enumerate(暂存们)],#重映射事件
    },'released v1-to-v2 target')#标签
    断言已发布v2产物(目标)#断言目标
    return 目标#返回

会话格式v1到v2=定义会话格式迁移({#v1到v2迁移
    'name':'@deepseek-ai/dsh-session-format-v1-to-v2',#迁移名
    'fromVersion':1,#源版本
    'toVersion':2,#目标版本
    'migrateHeader':迁移头,#迁移头
    'migrate':迁移产物,#迁移产物
    'validateTarget':断言已发布v2产物,#校验目标
    'validateTargetHeader':断言已发布v2头,#校验目标头
})#会话格式v1到v2结束
