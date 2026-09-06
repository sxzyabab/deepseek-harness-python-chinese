"""与持久状态投影无关的一次性 Team 变更等待者。

对齐上游 `agent-team/src/activity.ts`。公开面仅中文名。
"""
import threading#定时与事件
from .生命周期 import 已中止#信号已中止
from .错误 import 团队错误#领域错误

__all__=['团队活动']#仅中文公开名

class 团队活动:#团队活动等待器
    """拥有当前 Team 变更等待者，每个最多释放一次。"""
    def __init__(自身):#构造
        """空等待表。"""
        自身._等待者={}#按团队索引
        自身._已关闭=False#是否已关闭准入

    def 等待(自身,标识,超时毫秒,信号):#等待变化
        """等待一次之后的 Team 域或成员状态变化。"""
        if (not isinstance(超时毫秒,int) or isinstance(超时毫秒,bool)
                or 超时毫秒<10_000 or 超时毫秒>3_600_000):#非法超时
            raise 团队错误('timeoutMs must be an integer from 10000 through 3600000','TEAM_INVALID_TIMEOUT')#非法
        if 已中止(信号):#已取消
            raise 团队错误('wait_agent aborted','TEAM_WAIT_ABORTED')#包装
        if 自身._已关闭:#已关闭视为已变化
            return {'timedOut':False}#已变化
        门=threading.Event()#结算门
        结果盒={'changed':None,'error':None}#结果与错误
        结算锁=threading.Lock()#竞态锁
        已结算=[False]#是否已结算
        等待集=自身._等待者[标识] if 标识 in 自身._等待者 else None#该团队等待集
        if 等待集 is None:#无集合
            等待集=set()#新建
            自身._等待者[标识]=等待集#挂上
        停止听=threading.Event()#摘中止监听
        def 收尾(结算):#统一收尾
            """只结算一次。"""
            with 结算锁:#竞态
                if 已结算[0]:#已结算
                    return#忽略
                已结算[0]=True#标记
            定时器.cancel()#清定时器
            停止听.set()#停中止盯梢
            等待集.discard(等待者)#移出
            if len(等待集)==0:#空则删键
                自身._等待者.pop(标识,None)#删键
            结算()#执行结算
            门.set()#放行
        def 取消结算():#拒绝
            """包装取消。"""
            结果盒['error']=团队错误('wait_agent aborted','TEAM_WAIT_ABORTED')#包装
        def 取消处理():#取消处理
            """收尾并拒绝。"""
            收尾(取消结算)#收尾
        def 已变化结算():#变化结算
            """记下已变化。"""
            结果盒['changed']=True#已变化
        def 唤醒():#通知为已变化
            """变化结算。"""
            收尾(已变化结算)#已变化
        def 未变化结算():#超时结算体
            """记下未变化。"""
            结果盒['changed']=False#未变化
        def 超时结算():#超时未变化
            """超时结算。"""
            收尾(未变化结算)#未变化
        等待者={'resolve':唤醒}#等待者
        等待集.add(等待者)#登记
        定时器=threading.Timer(超时毫秒/1000,超时结算)#超时
        定时器.daemon=True#守护
        定时器.start()#启动
        def 盯中止():#盯调用方事件
            """信号置位则取消。"""
            if 信号 is None:#无信号
                return#返回
            while not 停止听.is_set():#尚未收尾
                if 信号.is_set():#已中止
                    取消处理()#取消
                    return#结束
                停止听.wait(0.05)#短等摘除
        if 信号 is not None:#有信号
            threading.Thread(target=盯中止,daemon=True).start()#盯梢
            if 信号.is_set():#同步间隙补检
                取消处理()#补检
        门.wait()#等结算
        if 结果盒['error'] is not None:#取消
            raise 结果盒['error']#抛出
        return {'timedOut':not 结果盒['changed']}#反转为是否超时

    def 通知(自身,标识):#通知变化
        """唤醒并移除一个团队的当前全部等待者。"""
        等待集=自身._等待者[标识] if 标识 in 自身._等待者 else None#取集合
        if 等待集 is None:#无人等待
            return#返回
        自身._等待者.pop(标识,None)#先摘下
        for 等待者 in list(等待集):#逐个唤醒
            等待者['resolve']()#唤醒

    def 关闭(自身):#关闭活动
        """关闭准入，并在运行时拆除期间唤醒全部当前等待者。"""
        自身._已关闭=True#标记关闭
        for 等待集 in list(自身._等待者.values()):#遍历团队
            for 等待者 in list(等待集):#唤醒全部
                等待者['resolve']()#唤醒
        自身._等待者.clear()#清空
