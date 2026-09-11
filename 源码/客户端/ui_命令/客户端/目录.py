"""按会话键缓存的命令目录。

对齐上游 `ui-commands/src/client/directory.ts`。公开面仅中文名。
AbortSignal 译为 threading.Event；拉取同步落定。描述符为跨包 dict。
"""
import threading#中止与等待
from .约定 import 命令错误#本包异常
from .解析 import 解析命令#精确名优先于本地化别名

__all__=['命令目录','已中止','若已中止则抛出']#仅中文公开名

def 已中止(信号):
    """Event 已置位。"""
    return 信号 is not None and 信号.is_set()#已中止

def 若已中止则抛出(信号):
    """已置位则抛本包异常。"""
    if 已中止(信号):#已中止
        raise 命令错误('command directory wait aborted')#中止

class 目录格子:#一个会话键的缓存格子
    """cold / pending / ready / failed。"""
    def __init__(自身):
        """从未拉过。"""
        自身.状态='cold'#缓存生命周期
        自身.命令表=()#热快照
        自身.代次=0#拉取代次
        自身.最近错误=None#最近一次胜出拉取的拒绝值
        自身.等待者=[]#等落定的 Event

class 命令目录:#按会话键的目录缓存
    """拥有它的服务负责接线事件与 RPC。"""
    def __init__(自身,拉命令):
        """记下按会话拉宿主目录的回调。"""
        自身.拉命令=拉命令#拉取
        自身.格子表={}#会话 → 格子

    def status(自身,会话标识):
        """一场会话当前的缓存状态。"""
        if 会话标识 not in 自身.格子表:#从未碰过
            return 'cold'#cold
        return 自身.格子表[会话标识].状态#格子状态

    def resolve(自身,会话标识,名):
        """就绪目录上同步查找；精确名优先于本地化别名。"""
        if 会话标识 not in 自身.格子表:#无格子
            return None#缺席
        格子=自身.格子表[会话标识]#格子
        if 格子.状态!='ready':#未就绪
            return None#缺席
        return 解析命令(名,格子.命令表)#精确名优先，再别名

    def invalidateAll(自身):
        """软失效：已碰过的键后台重拉。"""
        for 键 in list(自身.格子表.keys()):#每个键
            自身.刷新(键)#重拉

    def resetSession(自身,会话标识):
        """丢掉该会话旧组合并预热。"""
        格子=自身.格子(会话标识)#取或建
        格子.状态='cold'#丢掉状态
        格子.命令表=()#丢掉快照
        格子.最近错误=None#清错误
        自身.刷新(会话标识)#预热重拉

    def resetConnected(自身):
        """重连硬重置并预热。"""
        for 键,格子 in list(自身.格子表.items()):#每个格子
            格子.状态='cold'#丢掉状态
            格子.命令表=()#丢掉快照
            自身.刷新(键)#预热重拉

    def warm(自身,会话标识):
        """对一场会话点火即忘预热。"""
        格子=自身.格子(会话标识)#取或建
        if 格子.状态 in ('cold','failed'):#从未拉过或上次失败
            自身.刷新(会话标识)#拉

    def 刷新(自身,会话标识):
        """启动一次拉取。仅在仍是该键最新拉取时才发布 ready/failed。"""
        格子=自身.格子(会话标识)#取或建
        格子.代次+=1#本拉取代次
        本代=格子.代次#记下
        if 格子.状态!='ready':#非 ready 才标 pending
            格子.状态='pending'#pending
        try:#跑注入的拉取
            命令表=自身.拉命令(会话标识)#拉命令列表
            if 本代!=格子.代次:#已被更新的拉取抢过
                return#丢弃
            格子.命令表=tuple(命令表)#写入快照
            格子.状态='ready'#标为就绪
            格子.最近错误=None#清错误
        except 命令错误 as 错误:#拉取失败
            if 本代!=格子.代次:#已被更新的拉取抢过
                return#丢弃
            格子.命令表=()#丢掉快照
            格子.状态='failed'#标为失败
            格子.最近错误=错误#记下拒绝值
        if 本代==格子.代次:#仍是胜者
            自身.唤醒等待(格子)#唤醒等待者

    def ensureReady(自身,会话标识,信号=None):
        """强等到可服务。ready 立刻返回；cold/failed 起新拉取；pending 加入在飞的那次。"""
        格子=自身.格子(会话标识)#取或建
        while True:#直到 ready 或抛错
            若已中止则抛出(信号)#中止
            if 格子.状态=='ready':#已就绪
                return 格子.命令表#交出快照
            if 格子.状态!='pending':#cold/failed 起新拉取
                自身.刷新(会话标识)#拉
            if 格子.状态=='ready':#同步拉取已落定
                return 格子.命令表#交出
            自身.等落定(格子,信号)#等下一次胜出发布
            if 格子.状态=='failed':#等待的拉取失败
                错=格子.最近错误#拒绝值
                文=错.args[0] if isinstance(错,命令错误) and len(错.args)>0 else str(错)#消息
                raise 命令错误('command directory warmup failed: '+文)#把失败抬成 Error

    def 格子(自身,会话标识):
        """取或建格子。"""
        if 会话标识 not in 自身.格子表:#从未碰过
            自身.格子表[会话标识]=目录格子()#新建
        return 自身.格子表[会话标识]#交出

    def 等落定(自身,格子,信号):
        """等一次胜出发布或中止。"""
        若已中止则抛出(信号)#已中止
        唤醒=threading.Event()#本次等待
        格子.等待者.append(唤醒)#挂上
        if 信号 is None:#无中止
            唤醒.wait()#等
            return#落定
        while 唤醒.is_set() is False:#未唤醒
            若已中止则抛出(信号)#中止则摘掉
            if 唤醒 in 格子.等待者 and 已中止(信号):#中止
                格子.等待者=[项 for 项 in 格子.等待者 if 项 is not 唤醒]#摘掉
                raise 命令错误('command directory wait aborted')#拒绝
            唤醒.wait(0.05)#短等

    def 唤醒等待(自身,格子):
        """唤醒该条目全部等待者。"""
        醒来=格子.等待者#拷出
        格子.等待者=[]#清空
        for 项 in 醒来:#逐个
            项.set()#唤醒
