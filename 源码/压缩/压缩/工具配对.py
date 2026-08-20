"""会话表面上的工具配对平衡。压缩会改变表面位置，因此安全切割由当前表面顺序中的工具调用/结果内容导出，而不是步骤标记。"""
import weakref#按会话弱表缓存平衡状态

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

平衡缓存表=weakref.WeakKeyDictionary()#会话 → 平衡缓存

def 事件增量(事件):#事件对未配对计数的增量
    """返回一个表面事件如何改变进行中的工具调用计数。"""
    类型=取字段(事件,'type')#事件类型
    if 类型=='assistant/message':#助手消息
        消息=取字段(取字段(事件,'data'),'message')#消息外壳
        块们=取字段(消息,'content',[]) or []#内容块列表
        计数=0#工具调用数
        for 块 in 块们:#逐块
            if 取字段(块,'type')=='tool-call':#工具调用块
                计数+=1#每个工具调用 +1
        return 计数#增量
    if 类型=='tool/result':#工具结果
        return -1#配对掉一次调用
    return 0#其他事件不影响平衡

def 按序号取事件(事件们,序号):#按 seq 取事件
    """读取并校验表面序列所命名的事件。"""
    if 序号<0 or 序号>=len(事件们):#下标越界
        raise Exception('tool-pairing balance: surface seq '+str(序号)+' has no matching session event (corrupt surface)')#损坏表面
    事件=事件们[序号]#按下标取
    if 取字段(事件,'seq')!=序号:#缺失或 seq 对不上
        raise Exception('tool-pairing balance: surface seq '+str(序号)+' has no matching session event (corrupt surface)')#损坏表面
    return 事件#返回匹配事件

def 扩展缓存(会话,缓存,序号们):#增量扩展缓存
    """把缓存中尚未包含的表面序列折进其平衡状态。"""
    已处理=len(缓存['cutBalanced'])-1#已处理序列数
    尾部=序号们[已处理:]#尚未入缓存的尾部
    # 先校验未见尾部再改活缓存，避免损坏追加留下半推进状态。
    事件们=取字段(会话,'events')#权威事件流
    待追加切割=[]#待追加的切割平衡
    进行中=缓存['inProgressToolCalls']#从已处理尾继续计数
    for 序号 in 尾部:#逐个未见 seq
        进行中+=事件增量(按序号取事件(事件们,序号))#累加增量
        if 进行中<0:#结果多过调用
            raise Exception('tool-pairing balance: tool/result at surface seq '+str(序号)+' has no matching tool-call (corrupt surface)')#损坏表面
        待追加切割.append(进行中==0)#该切割是否平衡
    for 偏移,序号 in enumerate(尾部):#记下新 seq 的表面下标
        缓存['indexBySeq'][序号]=已处理+偏移#seq → 表面下标
    缓存['cutBalanced']=缓存['cutBalanced']+待追加切割#追加切割平衡
    缓存['inProgressToolCalls']=进行中#更新尾部未配对计数
    return 缓存#返回同一缓存对象

def 平衡缓存(会话):#取或重建缓存
    """返回与当前会话表面同步的平衡状态。"""
    表面=取字段(会话,'surface')#当前表面
    序号们=list(取字段(表面,'nodes'))#表面 seq 列表
    代数=取字段(表面,'replaceGeneration')#当前改写代数
    已缓存=平衡缓存表.get(会话)#已有缓存
    if 已缓存 is None or 取字段(已缓存,'generation')!=代数 or len(取字段(已缓存,'cutBalanced'))-1>len(序号们):#无缓存、代数变了、或缓存长于当前表面
        # 重建等于从空表面状态开始的同一次折叠，其唯一前导切割天然平衡。
        重建=扩展缓存(会话,{#从空表面重建
            'generation':代数,#当前代数
            'cutBalanced':[True],#空表面前导切割平衡
            'indexBySeq':{},#空下标表
            'inProgressToolCalls':0,#无未配对调用
        },序号们)#折入当前全部 seq
        平衡缓存表[会话]=重建#写回映射
        return 重建#返回重建缓存
    if len(取字段(已缓存,'cutBalanced'))-1<len(序号们):#表面变长则增量扩展
        return 扩展缓存(会话,已缓存,序号们)#增量扩展
    return 已缓存#已同步

def 切割平衡(缓存,序号,偏移):#查切割平衡
    """某序列位置加偏移处的切割平衡，拒绝当前成员之外的 seq。偏移 0 为前导切割，1 为尾随切割。"""
    下标=取字段(缓存,'indexBySeq').get(序号)#表面下标
    if 下标 is None:#seq 不在当前表面
        raise Exception('tool-pairing balance: surface seq '+str(序号)+' not found')#seq 未找到
    平衡列表=取字段(缓存,'cutBalanced')#切割平衡表
    目标=下标+偏移#前切或后切下标
    if 目标<0 or 目标>=len(平衡列表):#偏移越界
        raise Exception('tool-pairing balance: surface seq '+str(序号)+' not found')#seq 未找到
    return 平衡列表[目标]#返回该切割是否平衡

def 工具配对前平衡(会话,序号):#seq 之前是否平衡
    """当前表面序列紧前方的切割是否工具配对平衡。没有未回答的工具调用跨过该切割时为 true。seq 不在当前表面、表面序列没有匹配日志事件、或工具结果没有先前未结束调用时抛错。"""
    return 切割平衡(平衡缓存(会话),序号,0)#偏移 0=前导切割

def 工具配对后平衡(会话,序号):#seq 之后是否平衡
    """当前表面序列紧后方的切割是否工具配对平衡。没有未回答的工具调用跨过该切割时为 true。seq 不在当前表面、表面序列没有匹配日志事件、或工具结果没有先前未结束调用时抛错。"""
    return 切割平衡(平衡缓存(会话),序号,1)#偏移 1=尾随切割
