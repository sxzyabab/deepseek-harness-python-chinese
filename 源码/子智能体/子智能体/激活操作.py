import weakref#弱引用集合
from .助手输出 import 最终助手输出#最终助手输出选取
from .生命周期 import 纪元停止原因#纪元停止原因
from .异常 import 子智能体错误#缝内失败

__all__=[#仅中文公开名
    '激活池','子体锁','激活智能体','要求本地激活','观察本地失败','捕获本地结果',
]#公开面结束

class 激活池:
    '经不间断可续跑父链共享的进程内槽位'
    def __init__(自身):
        '建立空槽位集'
        自身._槽位=set()#已占用槽

    def 预留(自身,容量):
        '重建前预留；释放对未发布回滚也幂等。返回幂等释放器'
        if len(自身._槽位)>=容量:#已满
            raise 子智能体错误(
                'subagent limit reached (active child limit: '+str(容量)+'); wait for an existing child to finish '
                +'or complete this work with the current agents',
                'ACTIVATION_LIMIT_REACHED',
            )#拒绝
        槽=object()#本纪元槽
        自身._槽位.add(槽)#占用
        def 释放():
            '归还槽位'
            自身._槽位.discard(槽)#幂等
        return 释放#释放器

class 子体锁:
    '把同一耐久子体的投递、释放与拆除串行化'
    def __init__(自身):
        '建立每子尾期约'
        自身._尾={}#子 id → 尾期约

    def 运行(自身,子标识,操作):
        '在该子先前排队的操作之后跑操作，返回操作自己的期约'
        from ...基础设施.js特性 import PromiseEX as 期约#期约
        先前=自身._尾.get(子标识)#先前尾
        if 先前 is None:#没有先前
            先前=期约()#已兑现起点
            先前.解决()#空链
        结果=期约()#本次结果
        def 接着(_值=None):
            '前一节落定后跑本次'
            try:
                产出=操作()#临界区
            except BaseException as 错误:#同步失败
                结果.拒绝(错误)#拒绝
                return
            if hasattr(产出,'然后'):#期约
                产出.然后(结果.解决,结果.拒绝)#接上
            else:#同步值
                结果.解决(产出)#兑现
        先前.然后(接着,接着)#成败都继续
        尾=期约()#吞掉本次拒绝的链尾
        def 吞成功(_值=None):
            '成功也只推进链'
            尾.解决()#推进
        def 吞失败(_错误=None):
            '失败不传染后续调用方'
            尾.解决()#推进
        结果.然后(吞成功,吞失败)#链尾不拒绝
        自身._尾[子标识]=尾#记下尾
        def 收尾(_值=None):
            '仍是当前尾才摘掉'
            if 自身._尾.get(子标识) is 尾:#仍是本尾
                自身._尾.pop(子标识,None)#摘掉
        尾.然后(收尾,收尾)#收尾
        return 结果#操作自己的结算

def 激活智能体(激活):
    '读本地执行保留的活智能体；外部跑没有'
    if 激活['kind']=='local':#本地
        return 激活['handle'].智能体#活智能体
    return None#外部

def 要求本地激活(激活):
    '接受后续输入前要求本地驻留'
    if 激活['kind']=='local':#本地
        return 激活#本地激活
    raise 子智能体错误('subagent "'+str(激活['childId'])+'" does not accept follow-up input','NOT_CONTINUABLE')#外部不能再收消息

def 观察本地失败(激活,唤醒):
    '保留没有更晚已提交回合结束盖过的本地失败'
    孩子=激活['handle'].智能体#本地智能体
    def 智能体错误到达(载荷):
        'agent/error：记下当前序号并唤醒'
        智能体=载荷['agent'] if isinstance(载荷,dict) and 'agent' in 载荷 else None#事件里的智能体
        if 智能体 is not 孩子:#不是本子
            return#忽略
        激活['failureAt']=孩子.session.seq() if callable(孩子.session.seq) else 孩子.session.seq#失败序号
        唤醒()#再检查结算
    def 会话事件到达(会话,事件=None):
        '更晚的 turn/end 清掉失败标记'
        if 事件 is None and isinstance(会话,tuple):#单参数拆包
            会话,事件=会话#拆开
        if 会话 is not 孩子.session:#不是本会话
            return#忽略
        if not isinstance(事件,dict) or 事件.get('type')!='turn/end':#不是回合结束
            return#忽略
        失败于=激活['failureAt']#失败序号
        if 失败于 is not None and 事件.get('seq',-1)>=失败于:#已提交的更晚结束
            激活['failureAt']=None#清掉
    孩子.ctx.监听('agent/error',智能体错误到达)#失败
    孩子.ctx.监听('session/event',会话事件到达)#回合结束

def 捕获本地结果(激活):
    '捕获本地输出，并保留没有更晚已提交回合结束的失败'
    事件列表=激活['handle'].智能体.session.snapshotEvents(激活['outputStart'])#本纪元后缀
    输出=最终助手输出(事件列表)#最终助手输出
    if 输出 is None:#没有
        输出=[]#空
    停止原因='error' if 激活['failureAt'] is not None else 纪元停止原因(事件列表)#失败优先
    结构化=激活['structured']#结构化附件
    if 结构化 is not None:#有附件
        已捕获=结构化['captured']()#已提交值
        if 已捕获 is not None:#已提交
            return {'output':输出,'stopReason':停止原因,'structured':已捕获['value']}#带结构化
        if 停止原因=='completed':#完成但没捕获
            return {'output':输出,'stopReason':'error'}#不算成功
    return {'output':输出,'stopReason':停止原因}#普通终态

def 弱集合(成员):
    '尽量用弱集合记住活智能体身份'
    集合=weakref.WeakSet()#弱集合
    for 项 in 成员:#逐个
        集合.add(项)#加入
    return 集合#集合
