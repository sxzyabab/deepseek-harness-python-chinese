# 依赖未迁：会话/对话位置索引
"""会话拥有的增量引擎：从连续事件窗口装配业务上下文，并物化已登记的视图快照。

对齐上游 `runtime/src/client/sessions/conversation-assembler.ts`。公开面仅中文名。
插件定义面方法名与协议键保持上游英文（match/start/update/target 等）。
"""
from ..约定.会话约定 import 会话上下文键#kind+id 复合键
from .对话位置索引 import 对话位置索引#回合/步骤时间线

__all__=['对话事件定义面','对话视图定义面','对话节点组装器','对话运行时']#仅中文公开名

#------------------------------ 常量与小工具 ------------------------------

发布档位秩={'none':0,'animation-frame':1,'immediate':2}#发布档位高低
位置数据作用域们=('step','turn')#先步骤后回合（回合可读步骤）

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 空位置数据():#两作用域空槽
    """步骤与回合位置数据初始空槽。"""
    return {'step':None,'turn':None}#尚无发布

def 更高发布档(左,右):#取更高发布档
    """按秩比较两侧发布档，返回较高者。

    @param 左 - 左侧档。
    @param 右 - 右侧档。
    @returns 较高发布档。
    """
    return 左 if 发布档位秩[左]>=发布档位秩[右] else 右#按秩比较

def 开始序号(上下文):#读开始序号
    """读内部上下文的 startSeq；可能尚未见到 start。"""
    return 上下文.开始序号#可能尚未见到 start

def 插入下标(上下文们,序号):#按 startSeq 二分插入点
    """在已按 startSeq 有序的列表里找第一个 startSeq>=序号 的下标。

    @param 上下文们 - 已 start、按 startSeq 有序的内部上下文。
    @param 序号 - 待插入的 startSeq。
    @returns 插入下标。
    """
    低=0#左闭
    高=len(上下文们)#右开
    while 低<高:#二分
        中=低+(高-低)//2#中点
        候选=上下文们[中]#中点上下文
        if 候选 is not None and (候选.开始序号 if 候选.开始序号 is not None else -1)<序号:#落在候选之后
            低=中+1#右移
        else:#落在候选处或之前
            高=中#收右界
    return 低#第一个 startSeq>=序号 的下标

def 上下文投影(上下文):#投影给定义用的只读上下文
    """把内部上下文投影成定义可见的节点上下文。

    @param 上下文 - 内部上下文。
    @returns 定义可见字段表。
    """
    return {#定义可见字段
        'key':上下文.键,#复合键
        'kind':上下文.种类,#kind
        'id':上下文.标识,#实例 id
        'matches':上下文.匹配们,#匹配列表
        'start':上下文.开始,#start 匹配
        'state':上下文.状态,#折叠状态
        'current':上下文.当前,#已物化节点
    }#结束投影

def 归并匹配(键,新增们,已有们):#按 seq 归并两路匹配
    """按事件 seq 归并两路匹配；同 seq 两条则抛错。

    @param 键 - 上下文键（用于重复诊断）。
    @param 新增们 - 新匹配。
    @param 已有们 - 已有匹配。
    @returns 按 seq 有序的归并结果。
    """
    合并=[]#输出
    新游标=0#新路游标
    旧游标=0#旧路游标
    while 新游标<len(新增们) or 旧游标<len(已有们):#两路耗尽才停
        左=新增们[新游标] if 新游标<len(新增们) else None#新路当前
        右=已有们[旧游标] if 旧游标<len(已有们) else None#旧路当前
        左序号=取字段(取字段(左,'event'),'seq') if 左 is not None else None#新路 seq
        右序号=取字段(取字段(右,'event'),'seq') if 右 is not None else None#旧路 seq
        if 左 is not None and 右 is not None and 左序号==右序号:#同一 seq 两条
            raise Exception(f'conversation Context {键} received duplicate Match {左序号}')#重复匹配
        if 右 is None or (左 is not None and 左序号<右序号):#新路更早或旧路耗尽
            合并.append(左)#取新路
            新游标+=1#新路前进
        else:#旧路更早或新路耗尽
            合并.append(右)#取旧路
            旧游标+=1#旧路前进
    return 合并#按 seq 有序

def 是否位置边界(类型):#是否回合/步骤边界事件
    """事件类型是否为回合/步骤边界。"""
    return 类型 in ('turn/start','turn/end','step/start','step/end')#四种边界

def 是否安全整数(值):#对齐 Number.isSafeInteger
    """值是否为非布尔的安全整数。"""
    return isinstance(值,int) and not isinstance(值,bool) and abs(值)<=9007199254740991#JS 安全整数

def 要求状态(定义,阶段,状态):#定义折叠不得返回 undefined
    """定义折叠不得返回 None（对齐上游 undefined）。

    @param 定义 - 拥有定义。
    @param 阶段 - 阶段名（写入错误串）：start|update。
    @param 状态 - 定义返回值。
    @returns 非 None 状态。
    """
    if 状态 is None:#定义返回了 None
        raise Exception(f'conversation Definition "{取字段(定义,"kind")}" returned undefined from {阶段}()')#阶段失败
    return 状态#合法状态

def 铸匹配(输入,角色,位置):#带位置的匹配
    """从事件输入铸一条匹配（浅拷输入字段后覆盖 role/location）。

    @param 输入 - 事件与可选线视图。
    @param 角色 - start 或 update。
    @param 位置 - 当前位置。
    @returns 匹配表。
    """
    if isinstance(输入,dict):#映射输入
        结果=dict(输入)#浅拷全部字段
    else:#属性对象：对齐上游展开可枚举字段
        结果={}#新表
        for 名 in getattr(输入,'__dict__',{}):#实例字段
            结果[名]=getattr(输入,名)#写入
        if 'event' not in 结果:#至少带事件
            结果['event']=取字段(输入,'event')#事件
    结果['role']=角色#覆盖角色
    结果['location']=位置#覆盖位置
    return 结果#匹配

#------------------------------ 内部结构 ------------------------------

class _依赖:#一条 previous() 读出的依赖
    """start 读者记下的前置依赖。"""

    def __init__(自身,种类,键,修订,窗口缺口):#铸造依赖
        """@param 种类 - 依赖的定义 kind。
        @param 键 - 前置上下文键；窗口内没有则为 None。
        @param 修订 - 前置修订号。
        @param 窗口缺口 - 前置缺失且窗外还有更早历史。
        """
        自身.种类=种类#依赖的定义 kind
        自身.键=键#前置上下文键
        自身.修订=修订#前置修订号
        自身.窗口缺口=窗口缺口#窗外是否还有历史

class _内部上下文:#装配器内部上下文
    """一条业务上下文的可变内部态。"""

    def __init__(自身,键,种类,标识,定义):#新建内部上下文
        """@param 键 - kind+id 复合键。
        @param 种类 - 定义 kind。
        @param 标识 - 实例 id。
        @param 定义 - 拥有本上下文的定义。
        """
        自身.键=键#复合键
        自身.种类=种类#定义 kind
        自身.标识=标识#实例 id
        自身.定义=定义#拥有定义
        自身.开始序号=None#start 匹配的事件 seq
        自身.开始=None#start 匹配
        自身.匹配们=[]#按 seq 排列的匹配
        自身.状态=None#定义折叠出的状态
        自身.修订=0#每次重放或更新后递增
        自身.当前={}#目标 → 最近物化节点
        自身.位置数据=空位置数据()#步骤/回合位置数据
        自身.依赖们={}#kind → 上次 previous() 依赖

class _待应用匹配:#prepend 收集的待应用匹配
    """前置扩展时暂存、尚未写入上下文的匹配。"""

    def __init__(自身,定义,标识,匹配):#铸造待应用
        """@param 定义 - 匹配到的定义。
        @param 标识 - 实例 id。
        @param 匹配 - 待并入的匹配。
        """
        自身.定义=定义#匹配到的定义
        自身.标识=标识#实例 id
        自身.匹配=匹配#待并入的匹配

class _视图状态:#一个已登记视图的构建器与快照
    """已登记视图目标的构建器与最近快照。"""

    def __init__(自身,目标,构建器,快照):#铸造视图状态
        """@param 目标 - 视图目标名。
        @param 构建器 - 增量构建器。
        @param 快照 - 最近快照。
        """
        自身.目标=目标#视图目标名
        自身.构建器=构建器#增量构建器
        自身.快照=快照#最近快照

#------------------------------ 定义面协议说明 ------------------------------

class 对话事件定义面:#事件定义面（协议说明）
    """会话拥有的装配器所消费的事件注册表子集。

    实现须提供：
    - entries() → 登记顺序的普通定义
    - fallbackEntry() → 已登记时的未匹配事件回退（可缺席）
    """

class 对话视图定义面:#视图定义面（协议说明）
    """会话拥有的装配器所消费的视图注册表子集。

    实现须提供：
    - entries() → 登记顺序的视图构建器工厂
    """

class 对话运行时:#运行时注册表对（协议说明）
    """Session 与 SessionManager 接受的结构注册表对。

    字段：
    - events：对话事件定义面，另带 subscribe(listener)→取消
    - views：对话视图定义面，另带 subscribe(listener)→取消
    """

#------------------------------ 组装器 ------------------------------

class 对话节点组装器:#节点装配器
    """会话拥有的增量引擎：装配业务上下文并物化已登记视图快照。"""

    def __init__(自身,事件定义们,视图定义们):#会话拥有的装配器
        """@param 事件定义们 - 活着的事件定义注册表。
        @param 视图定义们 - 活着的视图构建器注册表。
        """
        自身._事件定义们=事件定义们#事件定义
        自身._视图定义们=视图定义们#视图定义
        自身._上下文们={}#键 → 内部上下文
        自身._上下文按种类={}#kind → 已 start、按 startSeq 有序
        自身._上下文按序号={}#事件 seq → 拥有该匹配的上下文集合
        自身._输入们={}#窗口内 seq → 输入
        自身._位置索引=对话位置索引()#回合/步骤时间线
        自身._脏集=set()#待 flush 物化
        自身._已修订=set()#本趟修订过、可能牵动依赖方
        自身._依赖方们={}#被依赖键 → 依赖方集合
        自身._视图们={}#目标 → 视图状态
        自身._还有更多=False#窗外是否还有更早历史
        自身._待整表替换=True#下次 flush 走整表 replace
        自身._时间线脏=True#时间线变过，视图需带上
        自身._重置视图构建器()#按当前注册表建空视图

    def 替换窗口(自身,条目们,还有更多):#整窗替换
        """在打开、再同步或缺口修复之后替换完整已加载窗口。

        @param 条目们 - 完整连续窗口。
        @param 还有更多 - 窗外是否还有更早历史。
        @returns 立即发布请求。
        """
        自身._上下文们.clear()#丢掉旧上下文
        自身._上下文按种类.clear()#丢掉 kind 索引
        自身._上下文按序号.clear()#丢掉 seq 索引
        自身._输入们.clear()#丢掉旧窗口
        自身._脏集.clear()#丢掉脏集
        自身._已修订.clear()#丢掉修订集
        自身._依赖方们.clear()#丢掉依赖方
        自身._还有更多=还有更多#窗外是否还有历史
        排序=sorted(条目们,key=lambda 项:取字段(取字段(项,'event'),'seq'))#按 seq 升序
        for 条目 in 排序:#写入窗口
            自身._输入们[取字段(取字段(条目,'event'),'seq')]=条目#seq → 输入
        自身._位置索引.重建(排序)#重建时间线
        自身._时间线脏=True#时间线已换
        for 条目 in 排序:#逐条匹配
            自身._匹配输入(条目)#写入上下文
        自身._重放依赖()#依赖可能因窗口缺口变化
        自身._已修订.clear()#replace 不走依赖方增量
        for 上下文 in 自身._上下文们.values():#全部待物化
            自身._脏集.add(上下文)#加入脏集
        自身._待整表替换=True#下次 flush 整表替换
        return 'immediate'#立即发布

    def 追加(自身,输入):#追加活尾
        """追加一条连续的活尾事件，不扫已有上下文。

        @param 输入 - 追加的事件与可选线视图。
        @returns 所请求的最高发布档。
        """
        序号=取字段(取字段(输入,'event'),'seq')#本条 seq
        if 序号 in 自身._输入们:#重复 seq 忽略
            return 'none'#无发布
        自身._已修订.clear()#本趟修订从空开始
        自身._输入们[序号]=输入#写入窗口
        发布='none'#累计发布档
        事件=取字段(输入,'event')#本条事件
        if 是否位置边界(取字段(事件,'type')):#回合/步骤边界
            先前时间线=自身._位置索引.快照()#追加前时间线引用
            变更=自身._位置索引.追加边界(事件)#只重访所属回合
            if 自身._位置索引.快照() is not 先前时间线:#时间线引用变了
                自身._时间线脏=True#视图需带时间线
                发布='immediate'#立即发布
            自身._重放上下文们(自身._刷新匹配位置(变更))#刷新变过 seq 的匹配位置并重放
            if len(变更)>0:#有位置变化则立即
                发布='immediate'#立即
        else:#非边界
            自身._位置索引.追加非边界(事件)#只索引本条
        发布=更高发布档(发布,自身._匹配输入(输入))#匹配本条
        if 自身._重放已修订依赖方():#依赖方重放则立即
            发布='immediate'#立即
        自身._已修订.clear()#清本趟修订
        return 发布#最高档

    def 前置(自身,条目们,还有更多):#向前扩展窗口
        """加入更早一页，同时保留已有上下文与视图身份。

        @param 条目们 - 新加载的更早事件。
        @param 还有更多 - 扩展后的窗口之前是否还有历史。
        @returns 所请求的最高发布档。
        """
        自身._已修订.clear()#本趟修订从空开始
        发布='none'#累计发布档
        先前还有更多=自身._还有更多#扩展前的缺口位
        新鲜=[条目 for 条目 in 条目们 if 取字段(取字段(条目,'event'),'seq') not in 自身._输入们]#跳过已在窗口内的
        新鲜=sorted(新鲜,key=lambda 项:取字段(取字段(项,'event'),'seq'))#按 seq 升序
        for 条目 in 新鲜:#写入窗口
            自身._输入们[取字段(取字段(条目,'event'),'seq')]=条目#seq → 输入
        自身._还有更多=还有更多#更新缺口位
        先前时间线=自身._位置索引.快照()#重建前时间线引用
        变更位置=自身._位置索引.重建(自身._排序输入())#整窗重建时间线
        if 自身._位置索引.快照() is not 先前时间线:#时间线引用变了
            自身._时间线脏=True#视图需带时间线
        受影响=自身._刷新匹配位置(变更位置)#刷新变过 seq 的匹配位置
        待应用={}#键 → 待应用匹配
        for 条目 in 新鲜:#先收集再并入，避免边走边乱序
            发布=更高发布档(发布,自身._收集输入(条目,待应用))#按定义收集
        自身._应用待匹配(待应用,受影响)#并入匹配并索引新 start
        自身._重放上下文们(受影响)#受影响上下文从头重放
        if (len(自身._已修订)>0 or 先前还有更多!=还有更多) and 自身._重放依赖():#有修订或缺口位变了
            发布='immediate'#依赖方可能要重放
        if len(变更位置)>0:#有位置变化则立即
            发布='immediate'#立即
        自身._已修订.clear()#清本趟修订
        return 发布#最高档

    def 重建注册表(自身):#注册表变更后重建
        """低频插件变更后按当前注册表集重建。

        @returns 立即发布请求。
        """
        自身._重置视图构建器()#按新视图定义换构建器
        return 自身.替换窗口(自身._排序输入(),自身._还有更多)#整窗重匹配

    def 冲刷(自身):#物化并发布视图
        """物化脏上下文，并推进每个已登记视图构建器。

        @returns 是否有视图快照被重建或增量应用。
        """
        if not 自身._待整表替换 and len(自身._脏集)==0 and not 自身._时间线脏:#无事可做
            return False#无发布
        if 自身._待整表替换:#整表替换路径
            自身._替换位置数据()#按作用域装位置数据
            按目标全部={}#目标 → 全部节点
            for 目标 in 自身._视图们.keys():#每个目标先空列表
                按目标全部[目标]=[]#空
            for 上下文 in 自身._上下文们.values():#每个上下文
                目标=取字段(上下文.定义,'target')#定义声明的目标
                if 目标 is None or 目标 not in 自身._视图们:#无目标或未登记视图
                    continue#跳过
                节点=自身._构建节点(上下文,目标)#物化节点
                上下文.当前[目标]=节点#记下当前节点
                if 节点 is not None:#可见则列入
                    按目标全部[目标].append(节点)#追加
            for 视图 in 自身._视图们.values():#每个视图
                视图.快照=视图.构建器.replace({#整表交给构建器
                    'nodes':按目标全部.get(视图.目标) or [],#该目标节点
                    'timeline':自身._位置索引.快照(),#当前时间线
                })#结束 replace
            自身._待整表替换=False#下次走增量
            自身._脏集.clear()#脏已消化
            自身._时间线脏=False#时间线已带上
            return True#确有发布
        按目标增量={}#目标 → 增量节点
        for 目标 in 自身._视图们.keys():#每个目标先空列表
            按目标增量[目标]=[]#空
        if 自身._应用脏位置数据():#位置数据变了则时间线脏
            自身._时间线脏=True#标脏
        for 上下文 in list(自身._脏集):#每个脏上下文
            目标=取字段(上下文.定义,'target')#定义声明的目标
            if 目标 is None or 目标 not in 自身._视图们:#无目标或未登记视图
                continue#跳过
            先前=上下文.当前.get(目标)#上次节点
            if 先前 is None and 目标 not in 上下文.当前:#显式缺席
                先前=None#无
            节点=自身._构建节点(上下文,目标)#本次节点
            if 节点 is None and 先前 is not None:#已物化目标不得撤回
                raise Exception(#应改用同一键加 hidden 可见性
                    f'conversation Definition "{上下文.种类}" withdrew materialized target "{目标}"; return the same key with hidden visibility instead',
                )#结束错误
            上下文.当前[目标]=节点#记下当前节点
            if 节点 is not None:#可见则列入增量
                按目标增量[目标].append(节点)#追加
        自身._脏集.clear()#脏已消化
        时间线脏=自身._时间线脏#本趟是否要带时间线
        自身._时间线脏=False#清脏
        for 视图 in 自身._视图们.values():#每个视图
            增量=按目标增量.get(视图.目标) or []#该目标增量
            if len(增量)==0 and not 时间线脏:#无节点也无时间线则跳过
                continue#跳过
            视图.快照=视图.构建器.apply({#增量交给构建器
                'upserts':增量,#upsert 节点
                'timeline':自身._位置索引.快照(),#当前时间线
            })#结束 apply
        return True#确有发布

    def 快照(自身,目标):#按目标名读快照
        """读一个已登记目标的最新快照。

        @param 目标 - 已登记视图目标。
        @returns 目标快照；未登记构建器时为 None。
        """
        视图=自身._视图们.get(目标)#已有视图
        return None if 视图 is None else 视图.快照#没有构建器则 None

    def 取(自身,目标):#按类型目标读快照
        """按目标名读快照（对齐上游 get）。

        @param 目标 - 已登记目标。
        @returns 快照或 None。
        """
        return 自身.快照(目标)#转交

    def _排序输入(自身):#窗口输入按 seq 排序
        """窗口内输入按事件 seq 升序。"""
        return sorted(自身._输入们.values(),key=lambda 项:取字段(取字段(项,'event'),'seq'))#升序

    def _匹配输入(自身,输入):#立即接受一条输入的匹配
        """立即接受一条输入的匹配并写入上下文。"""
        def 接受(定义,标识,角色):#命中后写入
            return 自身._接受匹配(定义,标识,角色,输入)#写入上下文
        return 自身._派发输入(输入,接受)#按定义派发

    def _收集输入(自身,输入,待应用):#收集一条输入的匹配，暂不写入上下文
        """收集一条输入的匹配，暂不写入上下文。

        @param 输入 - 本条输入。
        @param 待应用 - 键 → 待应用列表。
        @returns 本条请求的发布档。
        """
        def 接受(定义,标识,角色):#命中后收集
            键=会话上下文键(取字段(定义,'kind'),标识)#复合键
            匹配=铸匹配(输入,角色,自身._位置索引.位置于(取字段(输入,'event')))#带位置的匹配
            列表=待应用.get(键) or []#该键已收集
            列表.append(_待应用匹配(定义,标识,匹配))#追加本条
            待应用[键]=列表#写回
            发布函数=取字段(定义,'publication')#定义请求的档
            return 发布函数(匹配) if 发布函数 is not None else 'immediate'#缺省立即
        return 自身._派发输入(输入,接受)#按定义派发

    def _派发输入(自身,输入,接受):#对普通定义与回退跑 match
        """对普通定义与回退跑 match，累计最高发布档。

        @param 输入 - 本条输入。
        @param 接受 - 命中后的接受回调 (定义,标识,角色)→发布档。
        @returns 累计最高档。
        """
        已命中目标=set()#普通定义已命中的目标
        发布='none'#累计档
        事件=取字段(输入,'event')#本条事件
        for 定义 in 自身._事件定义们.entries():#登记顺序的普通定义
            结果=定义.match(事件)#尝试匹配
            if 结果 is None:#未命中
                continue#下一条
            目标=取字段(定义,'target')#定义目标
            if 目标 is not None:#有目标
                已命中目标.add(目标)#记下目标，挡住回退
            标识=取字段(结果,'id')#实例 id
            角色=取字段(结果,'role')#start 或 update
            发布=更高发布档(发布,接受(定义,标识,角色))#接受并累计
        回退=自身._事件定义们.fallbackEntry()#未匹配回退
        回退目标=取字段(回退,'target') if 回退 is not None else None#回退目标
        if 回退 is not None and 回退目标 is not None and 回退目标 not in 已命中目标:#有回退且该目标尚无普通命中
            结果=回退.match(事件)#回退尝试匹配
            if 结果 is not None:#回退命中
                发布=更高发布档(发布,接受(回退,取字段(结果,'id'),取字段(结果,'role')))#接受并累计
        return 发布#最高档

    def _接受匹配(自身,定义,标识,角色,输入):#把一条匹配写入（或创建）上下文
        """把一条匹配写入（或创建）上下文。

        @param 定义 - 命中的定义。
        @param 标识 - 实例 id。
        @param 角色 - start 或 update。
        @param 输入 - 本条输入。
        @returns 该匹配的发布档。
        """
        键=会话上下文键(取字段(定义,'kind'),标识)#复合键
        上下文=自身._上下文们.get(键)#已有上下文
        if 角色=='start' and 上下文 is not None and 上下文.开始 is not None:#已经有过 start
            raise Exception(f'conversation Context {键} received more than one start Match')#只能一条 start
        if 上下文 is None:#尚未见过该实例
            上下文=_内部上下文(键,取字段(定义,'kind'),标识,定义)#新建
            自身._上下文们[键]=上下文#挂上
        匹配=铸匹配(输入,角色,自身._位置索引.位置于(取字段(输入,'event')))#带位置的匹配
        先前=上下文.匹配们[-1] if 上下文.匹配们 else None#已有最后一条
        输入序号=取字段(取字段(输入,'event'),'seq')#本条 seq
        if 先前 is not None and 取字段(取字段(先前,'event'),'seq')>=输入序号:#不是严格追加
            raise Exception(f'conversation Context {键} received non-appended Match {输入序号}')#append 路径必须递增
        if 角色=='start' and len(上下文.匹配们)>0:#start 来在 update 之后
            raise Exception(f'conversation Context {键} received an update before its start Match')#start 必须最先
        上下文.匹配们.append(匹配)#追加匹配
        if 角色=='start':#本条是 start
            上下文.开始序号=输入序号#记下开始序号
            上下文.开始=匹配#记下 start 匹配
            自身._索引已开始上下文(上下文)#插入 kind 有序索引
        拥有者=自身._上下文按序号.get(输入序号)#该 seq 的拥有者
        if 拥有者 is None:#尚无集合
            拥有者=set()#新建
            自身._上下文按序号[输入序号]=拥有者#挂上
        拥有者.add(上下文)#本上下文也拥有
        if 角色=='start':#start 必须从头折叠
            自身._重放上下文(上下文)#跑 start 再跑后续 update
        elif 上下文.状态 is not None:#已有状态才能增量 update
            投影=上下文投影(上下文)#带状态的投影
            上下文.状态=要求状态(定义,'update',定义.update(投影,匹配))#定义不得返回 None
            上下文.修订+=1#修订号递增
            自身._已修订.add(上下文)#可能牵动依赖方
        自身._脏集.add(上下文)#待 flush 物化
        发布函数=取字段(定义,'publication')#定义请求的档
        return 发布函数(匹配) if 发布函数 is not None else 'immediate'#缺省立即

    def _应用待匹配(自身,待应用,受影响):#把 prepend 收集的匹配并入上下文
        """把前置扩展收集的匹配并入上下文。

        @param 待应用 - 键 → 待应用列表。
        @param 受影响 - 并入后需重放的上下文集合。
        """
        按种类开始={}#本趟新发现的 start，按 kind 分组
        for 键,条目们 in 待应用.items():#每个上下文键
            if not 条目们:#空列表跳过
                continue#下一条
            首条=条目们[0]#至少应有一条
            上下文=自身._上下文们.get(键)#已有上下文
            if 上下文 is None:#本页才见到该实例
                上下文=_内部上下文(键,取字段(首条.定义,'kind'),首条.标识,首条.定义)#新建
                自身._上下文们[键]=上下文#挂上
            发现开始=None#本批里的 start
            新增=[]#待并入匹配
            for 条目 in 条目们:#校验并取出匹配
                if 条目.定义 is not 上下文.定义 or 条目.标识!=上下文.标识:#同一键必须同一身份
                    raise Exception(f'conversation Context {键} received inconsistent Definition identity')#定义身份不一致
                if 取字段(条目.匹配,'role')=='start':#本条是 start
                    if 发现开始 is not None or 上下文.开始 is not None:#已经有过 start
                        raise Exception(f'conversation Context {键} received more than one start Match')#只能一条 start
                    发现开始=条目.匹配#记下本批 start
                序号=取字段(取字段(条目.匹配,'event'),'seq')#本条 seq
                拥有者=自身._上下文按序号.get(序号)#该 seq 的拥有者
                if 拥有者 is None:#尚无集合
                    拥有者=set()#新建
                    自身._上下文按序号[序号]=拥有者#挂上
                拥有者.add(上下文)#本上下文也拥有
                新增.append(条目.匹配)#取出匹配
            新增=sorted(新增,key=lambda 项:取字段(取字段(项,'event'),'seq'))#按 seq 升序再并
            上下文.匹配们=归并匹配(上下文.键,新增,上下文.匹配们)#与已有归并
            if 发现开始 is not None:#本批发现 start
                上下文.开始=发现开始#记下 start 匹配
                上下文.开始序号=取字段(取字段(发现开始,'event'),'seq')#记下开始序号
                列表=按种类开始.get(上下文.种类) or []#该 kind 本趟 start
                列表.append(上下文)#加入
                按种类开始[上下文.种类]=列表#写回
            if 上下文.开始 is not None and (not 上下文.匹配们 or 上下文.匹配们[0] is not 上下文.开始):#start 不是第一条
                raise Exception(f'conversation Context {上下文.键} received an update before its start Match')#start 必须最先
            受影响.add(上下文)#需重放
            自身._脏集.add(上下文)#待 flush 物化
        for 种类,上下文们 in 按种类开始.items():#按 kind 归并进有序索引
            自身._索引已开始上下文们(种类,上下文们)#归并

    def _重放上下文们(自身,上下文们):#按 startSeq 重放一组上下文
        """按 startSeq 重放一组上下文；尚无 start 的排到最后。"""
        有序=sorted(上下文们,key=lambda 项:(项.开始序号 if 项.开始序号 is not None else float('inf')))#升序
        for 上下文 in 有序:#每个上下文
            if 上下文.开始 is None:#还没有 start（只有更早页的 update）
                上下文.状态=None#不能折叠
                自身._脏集.add(上下文)#仍要物化（可能隐藏）
                continue#跳过重放
            自身._重放上下文(上下文)#从头折叠

    def _重放上下文(自身,上下文):#从 start 重放一个上下文
        """从 start 重放一个上下文的折叠。"""
        开始=上下文.开始#start 匹配
        if 开始 is None:#没有 start
            上下文.状态=None#不能折叠
            return#停
        if not 上下文.匹配们 or 上下文.匹配们[0] is not 开始:#start 不是第一条
            raise Exception(f'conversation Context {上下文.键} received an update before its start Match')#start 必须最先
        依赖表={}#本趟 previous() 记下的依赖
        读者=自身._读者于(取字段(取字段(开始,'event'),'seq'),依赖表)#start 之前的读者
        上下文.状态=None#先清再跑 start
        上下文.状态=要求状态(#定义不得返回 None
            上下文.定义,#拥有定义
            'start',#start 阶段
            上下文.定义.start(上下文投影(上下文),开始,读者),#跑 start
        )#结束 start 状态
        自身._替换依赖(上下文,依赖表)#换依赖边
        下标=1#start 之后
        while 下标<len(上下文.匹配们):#后续匹配
            匹配=上下文.匹配们[下标]#本条匹配
            if 匹配 is None or 取字段(匹配,'role')!='update':#跳过非 update
                下标+=1#前进
                continue#下一条
            投影=上下文投影(上下文)#带状态的投影
            上下文.状态=要求状态(#定义不得返回 None
                上下文.定义,#拥有定义
                'update',#update 阶段
                上下文.定义.update(投影,匹配),#跑 update
            )#结束 update 状态
            下标+=1#前进
        上下文.修订+=1#修订号递增
        自身._已修订.add(上下文)#可能牵动依赖方
        自身._脏集.add(上下文)#待 flush 物化

    def _替换依赖(自身,上下文,依赖表):#替换依赖边
        """拆旧依赖边并挂上新表。"""
        for 依赖 in 上下文.依赖们.values():#拆旧边
            if 依赖.键 is None:#没有前置上下文
                continue#下一条
            当前=自身._依赖方们.get(依赖.键)#该键的依赖方
            if 当前 is not None:#有集合
                当前.discard(上下文)#去掉本上下文
                if len(当前)==0:#空集则删键
                    del 自身._依赖方们[依赖.键]#删除
        上下文.依赖们=依赖表#换新表
        for 依赖 in 依赖表.values():#挂新边
            if 依赖.键 is None:#没有前置上下文
                continue#下一条
            当前=自身._依赖方们.get(依赖.键)#已有或空集
            if 当前 is None:#尚无
                当前=set()#新建
                自身._依赖方们[依赖.键]=当前#挂上
            当前.add(上下文)#加入依赖方

    def _重放已修订依赖方(自身):#重放本趟修订牵动的依赖方
        """BFS 扩依赖方闭包并按 startSeq 重放。

        @returns 是否有依赖方。
        """
        待处理=list(自身._已修订)#从已修订出发
        受影响=set()#闭包内的依赖方
        游标=0#BFS 游标
        while 游标<len(待处理):#BFS 扩依赖方
            被依赖=待处理[游标]#当前被依赖者
            游标+=1#前进
            if 被依赖 is None:#空洞跳过
                continue#下一条
            for 依赖方 in 自身._依赖方们.get(被依赖.键) or []:#直接依赖方
                if 依赖方 in 受影响:#已进闭包
                    continue#跳过
                受影响.add(依赖方)#记下
                待处理.append(依赖方)#继续扩
        自身._重放上下文们(受影响)#按 startSeq 重放闭包
        return len(受影响)>0#是否有依赖方

    def _读者于(自身,之前序号,依赖表):#构造 start 之前的上下文读者
        """构造 start 之前的上下文读者。

        @param 之前序号 - 只看该 seq 之前的前置。
        @param 依赖表 - 本趟记下的依赖。
        @returns 定义 start 用的读者（含 previous）。
        """
        组装器=自身#闭包
        def 前置(种类):#读某 kind 的前置
            """读某 kind 在 beforeSeq 之前最近的有状态上下文投影。"""
            前任=组装器._前置上下文(种类,之前序号)#startSeq 小于 beforeSeq 的最近有状态者
            依赖表[种类]=_依赖(#记下本趟依赖
                种类,#依赖 kind
                None if 前任 is None else 前任.键,#前置键
                None if 前任 is None else 前任.修订,#前置修订
                前任 is None and 组装器._还有更多,#缺失且窗外还有历史
            )#结束依赖
            if 前任 is None or 前任.状态 is None:#没有可投影状态
                return None#缺席
            序号=开始序号(前任)#前置开始序号
            if 序号 is None:#没有 start 则不能当前置
                return None#缺席
            return {#前置投影
                'key':前任.键,#复合键
                'kind':前任.种类,#kind
                'id':前任.标识,#实例 id
                'startSeq':序号,#开始序号
                'state':前任.状态,#只读状态
                'matches':前任.匹配们,#匹配列表
            }#结束前置
        return {'previous':前置}#读者

    def _前置上下文(自身,种类,之前序号):#某 kind 在 beforeSeq 之前最近的有状态上下文
        """某 kind 在 beforeSeq 之前最近的有状态上下文。"""
        候选们=自身._上下文按种类.get(种类) or []#该 kind 已 start、按 startSeq 有序
        下标前=插入下标(候选们,之前序号)#第一个 startSeq>=beforeSeq
        下标=下标前-1#从右往左
        while 下标>=0:#找有状态者
            候选=候选们[下标]#候选
            if 候选 is not None and 候选.状态 is not None:#最近有状态
                return 候选#返回
            下标-=1#继续往左
        return None#窗口内没有

    def _索引已开始上下文(自身,上下文):#插入单条 start
        """把一条新发现的 start 插入其定义的有序前置索引。"""
        序号=上下文.开始序号#开始序号
        if 序号 is None:#尚未 start
            return#停
        候选们=自身._上下文按种类.get(上下文.种类)#该 kind 已有
        if 候选们 is None:#尚无列表
            候选们=[]#新建
            自身._上下文按种类[上下文.种类]=候选们#挂上
        先前=候选们[-1] if 候选们 else None#当前最右（最晚 start）
        if 先前 is None or (先前.开始序号 if 先前.开始序号 is not None else -1)<序号:#追加即可
            候选们.append(上下文)#追加
        else:#否则二分插入
            候选们.insert(插入下标(候选们,序号),上下文)#插入

    def _索引已开始上下文们(自身,种类,新增们):#归并一批新 start
        """把一批新 start 归并进 kind 有序索引。"""
        if not 新增们:#无新 start
            return#停
        排序=sorted(新增们,key=lambda 项:项.开始序号 if 项.开始序号 is not None else 0)#本批按 startSeq
        已有=自身._上下文按种类.get(种类) or []#已有有序表
        合并=[]#归并输出
        旧游标=0#旧路游标
        新游标=0#新路游标
        while 旧游标<len(已有) or 新游标<len(排序):#两路耗尽才停
            左=已有[旧游标] if 旧游标<len(已有) else None#旧路当前
            右=排序[新游标] if 新游标<len(排序) else None#新路当前
            左序号=左.开始序号 if 左 is not None else None#旧路 seq
            右序号=右.开始序号 if 右 is not None else None#新路 seq
            if 右 is None or (左 is not None and 左序号 is not None and 右序号 is not None and 左序号<右序号):#旧路更早或新路耗尽
                合并.append(左)#取旧路
                旧游标+=1#旧路前进
            else:#新路更早或旧路耗尽
                合并.append(右)#取新路
                新游标+=1#新路前进
        自身._上下文按种类[种类]=合并#写回有序表

    def _重放依赖(自身):#前置键/修订/窗口缺口变了则重放
        """前置键/修订/窗口缺口变了则重放。

        @returns 是否重放过。
        """
        已重放=False#是否重放过
        有序=[上下文 for 上下文 in 自身._上下文们.values() if 开始序号(上下文) is not None]#只要已 start
        有序=sorted(有序,key=lambda 项:开始序号(项))#按 startSeq
        for 上下文 in 有序:#每个已 start 上下文
            if 上下文.状态 is None or len(上下文.依赖们)==0:#无状态或无依赖
                continue#下一条
            之前=开始序号(上下文)#本上下文 start 之前
            if 之前 is None:#防御：filter 已保证
                continue#下一条
            已变=False#依赖是否过期
            for 依赖 in 上下文.依赖们.values():#每条依赖
                当前=自身._前置上下文(依赖.种类,之前)#现在的前置
                窗口缺口=当前 is None and 自身._还有更多#现在的缺口
                当前键=None if 当前 is None else 当前.键#现在的键
                当前修订=None if 当前 is None else 当前.修订#现在的修订
                if 当前键!=依赖.键 or 当前修订!=依赖.修订 or 窗口缺口!=依赖.窗口缺口:#过期
                    已变=True#需要重放
                    break#一条过期即可
            if 已变:#依赖过期
                自身._重放上下文(上下文)#从头折叠
                已重放=True#记下
        return 已重放#是否重放过

    def _刷新匹配位置(自身,变更序号们):#刷新变过 seq 的匹配位置
        """刷新变过 seq 的匹配位置，返回拥有这些 seq 的上下文。

        @param 变更序号们 - 位置引用变过的 seq 集合。
        @returns 需重放的上下文集合。
        """
        受影响=set()#拥有这些 seq 的上下文
        if len(变更序号们)==0:#无变化
            return 受影响#空
        for 序号 in 变更序号们:#每个变过的 seq
            for 上下文 in 自身._上下文按序号.get(序号) or []:#加入拥有者
                受影响.add(上下文)#记下
        for 上下文 in 受影响:#每个拥有者
            开始=上下文.开始#可能要换 start 引用
            匹配们=[]#新匹配列表
            for 匹配 in 上下文.匹配们:#逐条刷新位置
                if 取字段(取字段(匹配,'event'),'seq') not in 变更序号们:#本条位置没变
                    匹配们.append(匹配)#原样
                    continue#下一条
                刷新=dict(匹配) if isinstance(匹配,dict) else 铸匹配(匹配,取字段(匹配,'role'),None)#浅拷
                刷新['location']=自身._位置索引.位置于(取字段(匹配,'event'))#换位置引用
                if 匹配 is 开始:#同步 start
                    开始=刷新#新引用
                匹配们.append(刷新)#新匹配
            上下文.匹配们=匹配们#换匹配列表
            上下文.开始=开始#换 start（可能仍是原引用）
        return 受影响#需重放的上下文

    def _构建节点(自身,上下文,目标):#物化一个视图节点
        """物化一个视图节点；目标不对或未声明构建则返回 None。"""
        if 取字段(上下文.定义,'target')!=目标 or 取字段(上下文.定义,'buildViewNode') is None:#目标不对或未声明构建
            return None#不物化
        节点=上下文.定义.buildViewNode(上下文投影(上下文))#定义构建
        if 节点 is None:#定义选择不物化
            return None#空
        if 取字段(节点,'key')!=上下文.键:#键必须稳定等于上下文键
            raise Exception(f'conversation Definition "{上下文.种类}" returned unstable key "{取字段(节点,"key")}"; expected "{上下文.键}"')#键不稳定
        if 取字段(节点,'target')!=目标:#节点目标必须是正在构建的目标
            raise Exception(f'conversation Definition "{上下文.种类}" returned target "{取字段(节点,"target")}" while building "{目标}"')#目标不一致
        return 节点#可见节点

    def _构建位置数据(自身,上下文,作用域):#构建一作用域的位置数据
        """构建一作用域的位置数据；未声明或选择不发布则返回 None。"""
        if 取字段(上下文.定义,'buildLocationData') is None:#未声明构建
            return None#空
        数据=上下文.定义.buildLocationData(上下文投影(上下文),作用域)#定义构建
        if 数据 is None:#定义选择不发布
            return None#空
        if 取字段(数据,'kind')!=作用域:#发布种类必须等于所请求作用域
            raise Exception(#作用域错配
                f'conversation Definition "{上下文.种类}" published {取字段(数据,"kind")} data through its {作用域} scope',
            )#结束错误
        if 取字段(数据,'key')!=上下文.种类:#位置数据键必须是所拥有 kind
            raise Exception(#键不是自己的 kind
                f'conversation Definition "{上下文.种类}" published Location data key "{取字段(数据,"key")}"; expected its owned kind',
            )#结束错误
        回合=取字段(数据,'turn')#回合号
        if not 是否安全整数(回合) or 回合<0:#回合号必须是非负安全整数
            raise Exception(f'conversation Definition "{上下文.种类}" published invalid turn {回合}')#非法回合
        if 取字段(数据,'kind')=='step':#步骤发布必须带合法步骤号
            步骤=取字段(数据,'step')#步骤号
            if not 是否安全整数(步骤) or 步骤<0:#非法
                raise Exception(f'conversation Definition "{上下文.种类}" published invalid step {步骤}')#非法步骤
        return 数据#合法发布

    def _替换位置数据(自身):#整表替换路径：按作用域装位置数据
        """整表替换路径：按作用域装位置数据。"""
        条目们=[]#累计发布
        for 作用域 in 位置数据作用域们:#先步骤后回合
            for 上下文 in 自身._上下文们.values():#每个上下文
                数据=自身._构建位置数据(上下文,作用域)#本作用域发布
                上下文.位置数据[作用域]=数据#记下
                if 数据 is not None:#非空则列入累计
                    条目们.append({'owner':上下文.键,'data':数据})#累计
            # 回合发布方可在同一次 flush 读步骤数据，因此每阶段先装上累计替换再让下一阶段构建。
            自身._位置索引.替换数据(条目们)#装上本阶段为止的累计

    def _应用脏位置数据(自身):#增量路径：只对脏上下文发布位置数据
        """增量路径：只对脏上下文发布位置数据。

        @returns 是否有仓库变过。
        """
        已变=False#是否有仓库变过
        for 作用域 in 位置数据作用域们:#先步骤后回合
            变更们=[]#本作用域变更
            for 上下文 in 自身._脏集:#每个脏上下文
                先前=上下文.位置数据[作用域]#变更前
                其后=自身._构建位置数据(上下文,作用域)#变更后
                上下文.位置数据[作用域]=其后#记下
                if 先前 is not 其后:#引用变了才列入
                    变更们.append({'owner':上下文.键,'previous':先前,'next':其后})#变更
            已变=自身._位置索引.应用数据(变更们) or 已变#应用到索引
        return 已变#是否有数据变化

    def _重置视图构建器(自身):#按当前视图定义换构建器
        """按当前视图定义换构建器，并标待整表替换。"""
        自身._视图们.clear()#丢掉旧构建器
        for 定义 in 自身._视图定义们.entries():#每个视图定义
            构建器=定义.create()#新建构建器
            目标=取字段(定义,'target')#目标名
            自身._视图们[目标]=_视图状态(#挂上
                目标,#目标名
                构建器,#构建器
                取字段(构建器,'empty'),#空快照
            )#结束视图状态
        自身._待整表替换=True#下次 flush 整表替换
