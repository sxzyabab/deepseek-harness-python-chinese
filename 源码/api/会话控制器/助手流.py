"""为重连 Web 跟随者保留的进程内助手状态。"""
from ...模型后端.llm import 助手流累加器#流累加器

__all__=['会话助手流累加器','空助手流基线']#仅中文公开名

空助手流基线={'revision':0}#空基线

class 会话助手流累加器:
    """折叠稠密智能体帧，并为每个已接受修订物化一份共享不可变重连基线。"""

    def __init__(自身):
        """空累加器。"""
        自身._活动尝试=None#活动尝试 dict
        自身._修订=0#当前修订
        自身._快照值=dict(空助手流基线)#缓存快照
        自身._脏=False#是否需物化

    def 接受(自身,帧,耐久游标):
        """折叠来自当前已附着智能体生命周期的一帧受信任帧。帧为 dict。"""
        if 帧['type']=='start' and 帧['revision']==1 and 自身._修订!=0:#新生命周期起点
            自身._活动尝试=None#清空
            自身._修订=0#重置
        if 帧['revision']!=自身._修订+1:#修订不连续
            自身._活动尝试=None#丢弃
            自身._修订=帧['revision']#跳到该修订
            自身._脏=True#脏
            return#跳过折叠
        自身._修订=帧['revision']#接受修订
        类型=帧['type']#帧类型
        if 类型=='start':#开始尝试
            自身._活动尝试={
                'attemptId':帧['attemptId'],#尝试 id
                'startedAfterSeq':耐久游标,#起始后序号
                'turn':帧['turn'],#回合
                'step':帧['step'],#步进
                'stream':助手流累加器(),#新累加器
                'nextIndex':0,#从 0
            }#尝试
        elif 类型=='chunk':#分块
            尝试=自身._活动尝试#当前
            if (
                尝试 is None
                or 尝试['attemptId']!=帧['attemptId']
                or 帧['index']!=尝试['nextIndex']
            ):#坏分块
                自身._活动尝试=None#丢弃
            else:#推入
                尝试['stream'].推入({'time':帧['time'],'chunk':帧['chunk']})#推入
                尝试['nextIndex']+=1#推进
        elif 类型=='end':
            自身._活动尝试=None#清空
        自身._脏=True#脏

    def 快照(自身):
        """读取缓存的重连基线；状态变更后才物化。"""
        if not 自身._脏:#未脏
            return 自身._快照值#复用
        基线={'revision':自身._修订}#新快照
        if 自身._活动尝试 is not None:#有活动
            活动=自身._活动尝试#活动
            基线['activeAttempt']={
                'attemptId':活动['attemptId'],#尝试 id
                'startedAfterSeq':活动['startedAfterSeq'],#起始后序号
                'turn':活动['turn'],#回合
                'step':活动['step'],#步进
                'nextIndex':活动['nextIndex'],#下一索引
                'stream':活动['stream'].快照(),#流快照
            }#活动尝试
        自身._快照值=基线#缓存
        自身._脏=False#清脏
        return 基线#返回
