"""把瞬态助手帧接到一次持久 v2 结算的 Web 呈现折叠。

帧 → `assistant/live-chunk` 瞬态条目。
"""
from ....模型后端.llm.助手流 import 展开助手流#展开基线流

__all__=['客户端助手流','助手结算条目']#仅中文公开名

class 客户端助手流:
    """把瞬态助手呈现挡在结算感知接口之后。"""

    def __init__(自身):
        """空流状态。"""
        自身._活动尝试=None#活动尝试
        自身._待结算={}#seq → 结算条目
        自身._已发布序号=set()#已发布
        自身._耐久游标=-1#持久游标
        自身._间隙瞬态=0#间隙内瞬态计数

    def 替换(自身,条目列表,基线=None):
        """替换持久 Web 窗口并采纳可选重连基线。返回可见条目列表。"""
        自身._待结算.clear()#清空
        自身._间隙瞬态=0#重置
        自身._活动尝试=None#清空
        开场=基线['activeAttempt'] if isinstance(基线,dict) and 'activeAttempt' in 基线 else None#基线尝试
        if 开场 is not None:#恢复活动
            自身._活动尝试={
                'attemptId':开场['attemptId'],
                'startedAfterSeq':开场['startedAfterSeq'],
                'turn':开场['turn'],
                'step':开场['step'],
                'nextIndex':开场['nextIndex'],
            }#活动
        可见=list(条目列表)#可见起于持久
        自身._已发布序号=set(条目['event']['seq'] for 条目 in 可见)#已发布
        自身._耐久游标=-1#游标
        for 条目 in 可见:#最大序号
            序号=条目['event']['seq']#序号
            if 序号>自身._耐久游标:#更大
                自身._耐久游标=序号#更新
        if 开场 is not None:#重建瞬态
            展开=展开助手流(开场['stream'] if 'stream' in 开场 else [])#展开
            for 下标,成员 in enumerate(展开):#带索引
                自身._间隙瞬态+=1#间隙
                可见.append({
                    'type':'transient',
                    'event':{
                        'type':'assistant/live-chunk',
                        'seq':自身._耐久游标+1-1/(自身._间隙瞬态+1),
                        'time':成员['time'],
                        'data':{
                            'attemptId':开场['attemptId'],
                            'turn':开场['turn'],
                            'step':开场['step'],
                            'chunk':成员['chunk'],
                        },
                    },
                })#瞬态
                if 下标+1>=开场['nextIndex']:#到达基线
                    break#停
        return 可见#可见

    def 接受耐久(自身,条目):
        """在匹配的存活尝试仍打开时暂存一次持久 v2 结算。返回决策或 None。"""
        事件=条目['event']#事件
        自身._耐久游标=max(自身._耐久游标,事件['seq'])#推进
        自身._间隙瞬态=0#清间隙
        结算=助手结算条目(条目)#是否结算
        if 结算 is not None and 自身._匹配结算(结算['event']) is not None:#匹配活动
            if 事件['seq'] in 自身._待结算:#重复
                return {'type':'rebaseline'}#重基线
            自身._待结算[事件['seq']]=结算#暂存
            return None#暂不可见
        return 自身._发布(条目)#直接发布

    def 接受帧(自身,帧):
        """折叠一帧稠密瞬态帧并释放其具名持久结算。返回决策或 None。"""
        类型=帧['type']#类型
        if 类型=='start':#开始
            if 自身._活动尝试 is not None or len(自身._待结算)>0:#冲突
                return {'type':'rebaseline'}#重基线
            自身._待结算.clear()#清
            自身._活动尝试={
                'attemptId':帧['attemptId'],
                'startedAfterSeq':帧['startedAfterSeq'],
                'turn':帧['turn'],
                'step':帧['step'],
                'nextIndex':0,
            }#新活动
            return None#开始不可见
        if 类型=='chunk':#分块
            尝试=自身._活动尝试#活动
            if 尝试 is None or 尝试['attemptId']!=帧['attemptId']:#无匹配
                return None#忽略
            if 帧['index']!=尝试['nextIndex']:#断
                return {'type':'rebaseline'}#重基线
            尝试['nextIndex']+=1#推进
            自身._间隙瞬态+=1#间隙
            return {
                'type':'transient',
                'entry':{
                    'type':'transient',
                    'event':{
                        'type':'assistant/live-chunk',
                        'seq':自身._耐久游标+1-1/(自身._间隙瞬态+1),
                        'time':帧['time'],
                        'data':{
                            'attemptId':帧['attemptId'],
                            'turn':尝试['turn'],
                            'step':尝试['step'],
                            'chunk':帧['chunk'],
                        },
                    },
                },
            }#瞬态
        if 类型=='end':
            尝试=自身._活动尝试#活动
            if 尝试 is None or 尝试['attemptId']!=帧['attemptId']:#不匹配
                return None#忽略
            自身._活动尝试=None#清
            if 帧['index']!=尝试['nextIndex']:#断
                return {'type':'rebaseline'}#重基线
            结果=帧['outcome']#结果
            if 结果.get('kind')=='abandoned':#放弃
                return (
                    {'type':'abandonment','attemptId':尝试['attemptId']}
                    if len(自身._待结算)==0
                    else {'type':'rebaseline'}
                )#放弃或重基线
            if 结果.get('seq') in 自身._已发布序号:#已发布
                return None#忽略
            条目=自身._待结算.get(结果.get('seq'))#待结算
            if 条目 is None or 条目['event']['type']!=结果.get('eventType'):#不匹配
                return {'type':'rebaseline'}#重基线
            自身._待结算.pop(结果['seq'],None)#移除
            自身._已发布序号.add(条目['event']['seq'])#记已发布
            return {'type':'settlement','attemptId':尝试['attemptId'],'entry':条目}#结算
        return None#未知

    def _匹配结算(自身,事件):
        """匹配结算的活动尝试。"""
        尝试=自身._活动尝试#活动
        if 尝试 is None:#无
            return None#空
        if 事件['type']=='assistant/message' and 事件.get('surfaceOp')!='append':#非追加
            return None#空
        if 事件['seq']<=尝试['startedAfterSeq']:#序号不在后
            return None#空
        数据=事件['data'] if 'data' in 事件 else {}#数据
        if 尝试['turn']!=数据.get('turn') or 尝试['step']!=数据.get('step'):#回合步进
            return None#空
        return 尝试#匹配

    def _发布(自身,条目):
        """发布存活条目。"""
        自身._已发布序号.add(条目['event']['seq'])#记
        return {'type':'publish','entry':条目}#发布

def 助手结算条目(条目):
    """判断是否结算条目。"""
    类型=条目['event']['type'] if 'event' in 条目 else None#类型
    if 类型=='assistant/message' or 类型=='assistant/attempt':#结算
        return 条目#收窄
    return None#非
