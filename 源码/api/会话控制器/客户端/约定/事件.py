"""域组装器消费的可观察连续会话事件窗口。

对齐上游 `session-controller/src/client/contract/events.ts`。公开面仅中文名。
"""
from .....客户端.存储 import 通知订阅者#安全通知

__all__=['可变会话事件源']#仅中文公开名

def _叶(条目列表):
    """构造叶节点。"""
    return {'kind':'leaf','entries':tuple(条目列表),'length':len(条目列表)}#叶

def _拼接(左,右):
    """构造拼接节点。"""
    return {'kind':'concat','left':左,'right':右,'length':左['length']+右['length']}#拼接

def _物化(节点):
    """物化为条目数组。"""
    if 节点['kind']=='leaf':#叶
        return list(节点['entries'])#直接
    条目=[None]*节点['length']#预分配
    待=[节点]#栈
    下标=0#写入
    while len(待)>0:#展开
        当前=待.pop()#弹出
        if 当前['kind']=='concat':#拼接
            待.append(当前['right'])#先右
            待.append(当前['left'])#后左 → 弹出左先
            continue#继续
        for 项 in 当前['entries']:#叶条目
            条目[下标]=项#写入
            下标+=1#前进
    return 条目#数组

def _窗口快照(节点,还有更多,修订,变更):
    """构造窗口快照（惰性物化 entries）。"""
    缓存={'entries':None}#惰性
    class 快照:
        """事件窗口快照。"""
        @property
        def entries(自身):
            """惰性物化。"""
            if 缓存['entries'] is None:#首次
                缓存['entries']=_物化(节点)#物化
            return 缓存['entries']#条目
        @property
        def hasMore(自身):
            """是否还有更早。"""
            return 还有更多#位
        @property
        def revision(自身):
            """修订号。"""
            return 修订#号
        @property
        def change(自身):
            """最近变更。"""
            return 变更#变更
        def __getitem__(自身,键):
            """dict 兼容。"""
            if 键=='entries':#条目
                return 自身.entries#条目
            if 键=='hasMore':#更多
                return 还有更多#位
            if 键=='revision':#修订
                return 修订#号
            if 键=='change':#变更
                return 变更#变更
            raise KeyError(键)#未知
    return 快照()#快照

class 可变会话事件源:
    """会话拥有的事件馈送；每一次被接受的窗口变更都同步发布。"""

    def __init__(自身):
        """空窗口。"""
        自身._监听者=set()#订阅者
        自身._窗口=_叶([])#窗口树
        自身._快照=_窗口快照(自身._窗口,False,0,{'kind':'replace','entries':[]})#初始

    def getSnapshot(自身):
        """取缓存的事件窗口快照。"""
        return 自身._快照#快照

    def 订阅(自身,监听者):
        """订阅同步窗口发布。"""
        自身._监听者.add(监听者)#登记
        def 取消():
            """取消。"""
            自身._监听者.discard(监听者)#移除
        return 取消#取消

    def 替换(自身,条目列表,还有更多):
        """替换完整连续窗口。"""
        自身._窗口=_叶(条目列表)#重置为叶
        自身._发布(还有更多,{'kind':'replace','entries':list(条目列表)})#发布

    def 前置(自身,条目列表,还有更多):
        """前置一页更早的连续内容。"""
        自身._窗口=_拼接(_叶(条目列表),自身._窗口)#拼到左侧
        自身._发布(还有更多,{'kind':'prepend','entries':list(条目列表)})#发布

    def 追加(自身,条目):
        """追加一个连续存活条目。"""
        条目列表=[条目]#单页
        自身._窗口=_拼接(自身._窗口,_叶(条目列表))#拼到右侧
        自身._发布(自身._快照.hasMore,{'kind':'append','entries':条目列表})#发布

    def 结算助手(自身,尝试标识,条目=None):
        """用已提交的持久落定替换一次尝试的瞬态行。"""
        条目列表=[候选 for 候选 in _物化(自身._窗口) if not (候选.get('type')=='transient' and 候选.get('event',{}).get('data',{}).get('attemptId')==尝试标识)]#去瞬态
        if 条目 is not None:#有落定
            插入=-1#下标
            for 下标,候选 in enumerate(条目列表):#找更大 seq
                if 候选.get('event',{}).get('seq',-1)>条目['event']['seq']:#更大
                    插入=下标#记下
                    break#停
            if 插入<0:#末尾
                条目列表.append(条目)#追加
            else:#插入
                条目列表.insert(插入,条目)#插前
        自身._窗口=_叶(条目列表)#重置
        变更={'kind':'settle-assistant','attemptId':尝试标识}#变更
        if 条目 is not None:#带条目
            变更['entry']=条目#写入
        自身._发布(自身._快照.hasMore,变更)#发布

    def _发布(自身,还有更多,变更):
        """升修订并通知。"""
        自身._快照=_窗口快照(自身._窗口,还有更多,自身._快照.revision+1,变更)#新快照
        通知订阅者(自身._监听者,'[session-controller] event feed')#通知
