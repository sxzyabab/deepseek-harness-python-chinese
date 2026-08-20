"""按会话键缓存的命令目录。

对齐上游 `ui-commands/src/client/directory.ts`。公开面仅中文名。
每场会话都挂着智能体，因此 command.list({sessionId}) 是唯一请求字段。
"""

__all__=['命令目录','目录状态','中止原因']#仅中文公开名

class 目录格子:#一个会话键的缓存格子
    """cold/pending/ready/failed 生命周期。"""
    def __init__(自身):#冷格子
        """初始冷态。"""
        自身.状态='cold'#缓存生命周期
        自身.命令们=()#热快照
        自身.代次=0#代次；新拉取抢过旧拉取
        自身.最近错误=None#最近一次胜出拉取的拒绝值
        自身.等待们=[]#等落定的唤醒函数

def 中止原因(信号):#把中止收成 Error
    """已是 Exception 则原样，否则固定文案。"""
    原因=getattr(信号,'reason',None)#中止原因
    if isinstance(原因,BaseException):#已是异常
        return 原因#原样
    return Exception('command directory wait aborted')#固定文案

def 通知等待(格子):#唤醒并清空等待队列
    """先清空，避免回调里再入队搅在一起。"""
    醒来=list(格子.等待们)#本次要喊醒的
    格子.等待们=[]#先清空
    for 醒 in 醒来:#逐个唤醒
        醒()#回调

def 等到落定(格子,信号):#等到下一次胜出发布或中止
    """已经中止则立刻拒绝。"""
    if getattr(信号,'aborted',False):#已经中止
        raise 中止原因(信号)#立刻拒绝
    完成=[]#单格完成旗
    失败=[]#单格失败值
    def 等待者():#胜出发布时唤醒
        """落定。"""
        完成.append(True)#标完成
    def 中止时():#signal 中止
        """从队列摘掉自己并记下失败。"""
        格子.等待们=[w for w in 格子.等待们 if w is not 等待者]#摘掉
        失败.append(中止原因(信号))#记下
    if hasattr(信号,'addEventListener'):#DOM AbortSignal
        信号.addEventListener('abort',中止时,{'once':True})#只听一次
    格子.等待们.append(等待者)#加入等待队列
    while not 完成 and not 失败:#自旋等（无事件循环时由调用方驱动 refresh）
        if getattr(信号,'aborted',False):#中途中止
            raise 中止原因(信号)#拒绝
        if 格子.状态 in ('ready','failed') and 等待者 not in 格子.等待们:#已被唤醒
            break#离开
        break#无异步泵时一次返回；调用方循环 ensureReady
    if 失败:#中止
        raise 失败[0]#抛出
    return#落定

class 命令目录:#按会话键的目录缓存
    """普通类——拥有它的服务负责接线事件与 RPC。"""
    def __init__(自身,拉取命令):#注入拉取
        """记下拉取函数与空表。"""
        自身.拉取命令=拉取命令#按会话拉命令列表
        自身.条目们={}#会话 → 缓存格子

    def 状态(自身,会话标识):#读一场会话的缓存状态
        """从未碰过则为 cold。"""
        格子=自身.条目们.get(会话标识)#有格子
        if 格子 is None:#从未碰过
            return 'cold'#冷
        return 格子.状态#状态

    def 解析(自身,会话标识,名):#按精确名字查热快照
        """缺席或条目未就绪则为 None。"""
        格子=自身.条目们.get(会话标识)#该会话的格子
        if 格子 is None or 格子.状态!='ready':#没有格子或未就绪
            return None#未命中
        for 项 in 格子.命令们:#精确匹配
            if (项.get('name') if isinstance(项,dict) else getattr(项,'name',None))==名:#命中
                return 项#描述符
        return None#未命中

    def 全部失效(自身):#软失效：已碰过的键后台重拉
        """ready 快照继续服务。"""
        for 键 in list(自身.条目们.keys()):#每个键
            自身.刷新(键)#点火即忘地重拉

    def 重连重置(自身):#重连硬重置并预热
        """每条条目丢掉快照并预热。"""
        for 键,格子 in list(自身.条目们.items()):#遍历每个格子
            格子.状态='cold'#丢掉状态
            格子.命令们=()#丢掉快照
            自身.刷新(键)#预热重拉

    def 预热(自身,会话标识):#对一场会话点火即忘预热
        """从未拉过或上次失败才拉。"""
        格子=自身._格子(会话标识)#取或建格子
        if 格子.状态 in ('cold','failed'):#需要拉
            自身.刷新(会话标识)#重拉

    def 刷新(自身,会话标识):#为一场会话启动一次拉取
        """仅当它仍是该键最新一次拉取时才发布 ready/failed。"""
        格子=自身._格子(会话标识)#取或建格子
        格子.代次+=1#本轮代次
        代次=格子.代次#记下
        if 格子.状态!='ready':#非 ready 才标 pending
            格子.状态='pending'#避免降级热快照
        try:#拉取命令列表
            命令们=自身.拉取命令(会话标识)#注入的 command.list
            if 代次!=格子.代次:#已被更新的拉取抢过
                return#丢弃
            格子.命令们=tuple(命令们) if 命令们 is not None else ()#发布快照
            格子.状态='ready'#可服务
            格子.最近错误=None#清掉上次错误
        except Exception as 错误:#拉取被拒
            if 代次!=格子.代次:#已被更新的拉取抢过
                return#丢弃
            格子.命令们=()#丢掉快照
            格子.状态='failed'#标记失败
            格子.最近错误=错误#记下拒绝值
        finally:#无论成败
            if 代次==格子.代次:#仍是最新
                通知等待(格子)#唤醒等待者

    def 确保就绪(自身,会话标识,信号=None):#强等到目录可服务
        """ready 立即返回；cold/failed 启动新拉取；pending 加入正在飞的那次。"""
        格子=自身._格子(会话标识)#取或建格子
        while True:#直到 ready 或失败抛出
            if 格子.状态=='ready':#已可服务
                return 格子.命令们#热快照
            if 格子.状态!='pending':#cold/failed
                自身.刷新(会话标识)#启动新拉取
            if 信号 is not None:#有中止信号
                等到落定(格子,信号)#等下一次胜出发布或中止
            if 格子.状态=='failed':#等待的那次拉取失败
                错=格子.最近错误#拒绝值
                文=错.args[0] if isinstance(错,BaseException) and 错.args else str(错)#文案
                raise Exception('command directory warmup failed: '+str(文))#收成 Error
            if 格子.状态=='ready':#已就绪
                return 格子.命令们#快照
            if 信号 is None:#无异步泵
                break#让出
        return 格子.命令们#当前快照（可能仍 pending）

    def _格子(自身,会话标识):#取或建该会话的格子
        """从未碰过则新建冷格子。"""
        格子=自身.条目们.get(会话标识)#已有格子
        if 格子 is None:#从未碰过
            格子=目录格子()#新建冷格子
            自身.条目们[会话标识]=格子#挂进表
        return 格子#交出格子

目录状态=('cold','pending','ready','failed')#生命周期字面量
