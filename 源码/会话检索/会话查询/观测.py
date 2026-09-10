"""活优先会话观察：history/follow 与冷探测共用。

对齐上游 `session-query/src/observation.ts`：活路径即时切口 + 冷路径
按持久修订钉住的 prepared LRU 与投影水合。公开面仅中文名。
"""
from .配置 import 会话查询错误,已中止 as _配置已中止,会话查询默认准备会话缓存大小#检索错误与默认缓存
from .语料库 import 未找到#未找到工厂
from .冷读 import 读冷会话日志#句柄冷读 + 中断闭合

__all__=['会话观测','会话观测读取器','观测已中止']#仅中文公开名

def 观测已中止(信号):
    """兼容 Event 与带 `_事件` 的中止信号。"""
    if 信号 is None:#无
        return False#未中止
    if hasattr(信号,'is_set') and callable(信号.is_set):#threading.Event
        try:
            return bool(信号.is_set())#置位
        except TypeError:
            pass#非无参 is_set
    return _配置已中止(信号)#带 _事件 的信号

def 若观测已中止则抛出(信号):
    """已取消则抛 SESSION_QUERY_ABORTED。"""
    if 观测已中止(信号):#已中止
        raise 会话查询错误('session observation was aborted','SESSION_QUERY_ABORTED')#取消

class 会话观测:
    """一次精确不可变会话切口。"""

    def __init__(自身,来源,头,继承事件数,事件列表,游标,投影=None,修订=None,保留工厂=None,关闭器=None):
        """记下切口字段。"""
        自身.source=来源#live|prepared
        自身.header=头#头
        自身.inheritedEventCount=继承事件数#继承
        自身._事件列表=事件列表#事件前缀
        自身.cursor=游标#末 seq 或 -1
        自身.projections=投影#可选投影
        自身.revision=修订#可选修订
        自身._保留工厂=保留工厂#retain
        自身._关闭器=关闭器#dispose
        自身._已关闭=False#幂等

    @property
    def events(自身):
        """切口事件前缀。"""
        return 自身._事件列表#事件

    def retain(自身):
        """为另一所有者再租一份。"""
        if 自身._已关闭:#已处置
            raise RuntimeError('session observation "'+str(自身.header.get('id'))+'" is disposed')#已处置
        if 自身._保留工厂 is None:#无工厂则浅拷
            return 会话观测(
                自身.source,自身.header,自身.inheritedEventCount,自身._事件列表,自身.cursor,
                自身.projections,自身.revision,None,None,
            )#独立拷贝
        return 自身._保留工厂()#新租约

    def close(自身):
        """释放租约。"""
        if 自身._已关闭:#幂等
            return#已关
        自身._已关闭=True#标记
        if 自身._关闭器 is not None:#有关闭器
            自身._关闭器()#关

    def __enter__(自身):
        """上下文管理。"""
        return 自身#自身

    def __exit__(自身,类型,值,回溯):
        """退出时关闭。"""
        自身.close()#关
        return False#不吞异常

class 会话观测读取器:
    """构建点观察；冷路径按修订钉住 prepared LRU。"""

    def __init__(自身,上下文,语料库,缓存容量=None):
        """保存上下文、语料与缓存容量。"""
        自身._上下文=上下文#Cordis
        自身._语料库=语料库#语料（回退冷读）
        自身._缓存容量=会话查询默认准备会话缓存大小 if 缓存容量 is None else 缓存容量#容量
        自身._缓存={}#sessionId → PreparedEntry（插入序≈LRU：删后重插）

    def 读(自身,会话标识,选项=None):
        """观察一个活优先会话。选项为 dict。"""
        if 选项 is None:#缺省
            选项={}#空
        信号=选项['signal'] if 'signal' in 选项 else None#取消
        投影模式=选项['projectionMode'] if 'projectionMode' in 选项 else 'all'#投影
        while True:#直至成功（准备竞态）
            若观测已中止则抛出(信号)#入口
            活=自身._上下文.sessions.get(会话标识)#活会话
            if 活 is not None:#活路径
                return 自身._活(活,投影模式)#活
            持久化=自身._上下文.获取服务('sessionPersistence')#持久化
            if 持久化 is None:#无后端
                raise 未找到(会话标识)#未找到
            快照=自身._统计源(持久化,会话标识,信号)#修订观察
            挂上=自身._上下文.sessions.get(会话标识)#stat 期间附着
            if 挂上 is not None:#改走活
                return 自身._活(挂上,投影模式)#活
            条目=自身._缓存条目(持久化,会话标识,快照['revision'])#查缓存
            if 条目 is None:#无有效缓存
                已加载=自身._加载源(持久化,会话标识,信号)#冷读
                若观测已中止则抛出(信号)#加载后
                挂上=自身._上下文.sessions.get(会话标识)#加载后附着
                if 挂上 is not None:#改走活
                    return 自身._活(挂上,投影模式)#活
                种子=list(已加载['events']) if 已加载['events'] is not None else []#种子
                try:
                    会话=自身._上下文.sessions.准备(会话标识,{
                        'seed':种子,
                        'meta':dict(已加载['header']),
                        'inheritedEventCount':已加载['inheritedEventCount'] if 'inheritedEventCount' in 已加载 else 0,
                        **({'eventState':已加载['eventState']} if 'eventState' in 已加载 and 已加载['eventState'] is not None else {}),
                    })#准备未发布会话
                except BaseException as 错误:
                    if 自身._上下文.sessions.get(会话标识) is not None:#竞态活
                        continue#重试
                    raise 会话查询错误(
                        'stored session "'+str(会话标识)+'" is corrupt: '+str(错误),
                        'SESSION_QUERY_CORRUPT_SESSION',
                        {'cause':错误},
                    )#损坏
                条目={
                    'persistence':持久化,
                    'revision':快照['revision'],
                    'session':会话,
                    'events':tuple(种子),
                    'refs':0,
                }#条目
                自身._入库(会话标识,条目)#入库
            try:
                投影=None if 投影模式=='none' else 自身._准备投影(条目)#投影
            except BaseException as 错误:
                raise 会话查询错误(
                    'failed to project session "'+str(会话标识)+'": '+str(错误),
                    'SESSION_QUERY_CORRUPT_SESSION',
                    {'cause':错误},
                )#损坏
            return 自身._准备租约(会话标识,条目,投影)#租约

    def _统计源(自身,持久化,会话标识,信号):
        """轻量修订观察；映射缺席与后端失败。"""
        try:
            if hasattr(持久化,'观察'):#jsonl 面
                快照=持久化.观察(会话标识,{'signal':信号} if 信号 is not None else None)#观察
            elif hasattr(持久化,'stat'):#上游名
                快照=持久化.stat(会话标识,{'signal':信号} if 信号 is not None else None)#stat
            else:#无轻量面：经语料加载后合成
                已加载=自身._语料库.加载(会话标识,信号)#加载
                return {'header':已加载['header'],'revision':None}#无修订钉住
        except BaseException as 错误:
            若观测已中止则抛出(信号)#优先取消
            raise _映射持久失败(会话标识,错误)#映射
        若观测已中止则抛出(信号)#取消
        if 快照 is None:#缺席
            raise 未找到(会话标识)#未找到
        if 快照['header']['id']!=会话标识:#身份不符
            raise 会话查询错误(
                'session persistence returned "'+str(快照['header']['id'])+'" for "'+str(会话标识)+'"',
                'SESSION_QUERY_SOURCE_CONFLICT',
            )#冲突
        return 快照#快照

    def _加载源(自身,持久化,会话标识,信号):
        """完整平衡冷日志（已存 + 中断末回合内存闭合）。"""
        try:
            冷=读冷会话日志(持久化,会话标识,信号)#句柄冷读
            return {
                'header':冷['header'],#头
                'inheritedEventCount':冷['inheritedEventCount'] if 'inheritedEventCount' in 冷 else 0,#继承
                'events':list(冷['events']) if 冷.get('events') is not None else [],#平衡事件
                'eventState':冷['eventState'] if 'eventState' in 冷 else None,#别名状态
            }#冷日志
        except 会话查询错误:
            raise#原样
        except BaseException as 错误:
            若观测已中止则抛出(信号)#优先取消
            raise _映射持久失败(会话标识,错误)#映射

    def _缓存条目(自身,持久化,会话标识,修订):
        """仍有效的缓存条目并标为最近使用。"""
        已缓存=自身._缓存.get(会话标识)#取
        if 已缓存 is None:#无
            return None#无
        if 已缓存['persistence'] is not 持久化:#实例换了
            return None#无效
        if 修订 is not None and 已缓存['revision']!=修订:#修订变
            return None#无效
        # 删后重插刷新 LRU
        del 自身._缓存[会话标识]#删
        自身._缓存[会话标识]=已缓存#重插
        return 已缓存#返回

    def _入库(自身,会话标识,条目):
        """插入或替换，再驱逐超容量。"""
        自身._缓存.pop(会话标识,None)#删旧
        自身._缓存[会话标识]=条目#插新
        自身._驱逐超容量(条目)#驱逐

    def _驱逐超容量(自身,保留=None):
        """驱逐最旧未钉条目直至合容量。"""
        if len(自身._缓存)<=自身._缓存容量:#未超
            return#空
        for 标识 in list(自身._缓存.keys()):#插入序
            候选=自身._缓存[标识]#候选
            if 候选 is 保留 or 候选['refs']>0:#保留或已钉
                continue#跳
            del 自身._缓存[标识]#驱逐
            if len(自身._缓存)<=自身._缓存容量:#合
                return#停

    def _准备租约(自身,会话标识,条目,投影):
        """在缓存条目上构建可处置租约。"""
        条目['refs']+=1#钉住

        def 租约():
            """新租约。"""
            已处置=[False]#旗

            def 保留():
                """再钉。"""
                if 已处置[0]:#已处置
                    raise RuntimeError('session observation "'+str(会话标识)+'" is disposed')#已处置
                条目['refs']+=1#再钉
                return 租约()#新

            def 关闭():
                """解钉。"""
                if 已处置[0]:#幂等
                    return#空
                已处置[0]=True#标记
                条目['refs']-=1#解钉
                if 条目['refs']==0:#可驱逐
                    自身._驱逐超容量()#驱逐

            事件列表=条目['events']#事件
            游标=事件列表[-1]['seq'] if len(事件列表)>0 else -1#游标
            return 会话观测(
                'prepared',条目['session'].header,
                getattr(条目['session'],'inheritedEventCount',0),
                事件列表,游标,投影,条目['revision'],保留,关闭,
            )#观察

        return 租约()#首租约

    def _活(自身,会话,投影模式):
        """活会话切口。"""
        序号=会话.seq#记下长度
        事件列表=list(会话.snapshotEvents(0,序号))#前缀
        游标=-1 if 序号==0 else 序号-1#游标
        投影=None#投影
        if 投影模式!='none':#需要
            注册表=自身._上下文.获取服务('sessionProjections')#投影服务
            if 注册表 is not None and hasattr(注册表,'snapshot'):#有
                快照=注册表.snapshot(会话)#快照
                if 快照 is not None:#有块
                    投影={'asOfSeq':快照['asOfSeq'],'values':快照['values']}#块
            elif 注册表 is not None and hasattr(注册表,'快照'):#中文
                快照=注册表.快照(会话)#快照
                if 快照 is not None:#有块
                    投影={'asOfSeq':快照['asOfSeq'],'values':快照['values']}#块
        return 会话观测(
            'live',会话.header,getattr(会话,'inheritedEventCount',0),
            事件列表,游标,投影,None,None,None,
        )#活观察

    def _准备投影(自身,条目):
        """准备投影：优先投影缓存注水。"""
        注册表=自身._上下文.获取服务('sessionProjections')#注册表
        if 注册表 is None:#无
            return None#省略
        缓存=自身._上下文.获取服务('sessionProjectionCache')#缓存
        会话=条目['session']#会话
        事件列表=条目['events']#事件
        if 缓存 is not None:#有缓存
            if hasattr(缓存,'注水预备'):#中文
                块=缓存.注水预备(会话,会话.header,事件列表)#注水
            elif hasattr(缓存,'hydratePrepared'):#上游
                块=缓存.hydratePrepared(会话,事件列表)#注水
            else:#无注水
                块=None#空
            if 块 is not None:#有
                return 块 if isinstance(块,dict) and 'values' in 块 else 块#块
        if hasattr(注册表,'注水'):#直接注水
            return 注册表.注水(会话,{},事件列表,0)#注水
        if hasattr(注册表,'hydrate'):#上游
            return 注册表.hydrate(会话,{},事件列表,0)#注水
        return None#省略


def _映射持久失败(会话标识,错误):
    """映射持久化失败到查询分类。"""
    名=getattr(错误,'name',None) or type(错误).__name__#名
    if 名 in ('SessionPersistenceNotFoundError','会话持久化未找到错误') or getattr(错误,'code',None)=='SESSION_PERSISTENCE_NOT_FOUND':#未找到
        return 未找到(会话标识)#映射
    if 'Corrupt' in str(名) or '损坏' in str(名):#损坏
        return 会话查询错误(
            'stored session "'+str(会话标识)+'" is corrupt: '+str(错误),
            'SESSION_QUERY_CORRUPT_SESSION',
            {'cause':错误},
        )#损坏
    return 会话查询错误(
        'failed to observe session "'+str(会话标识)+'": '+str(错误),
        'SESSION_QUERY_PERSISTENCE_FAILED',
        {'cause':错误},
    )#持久失败
