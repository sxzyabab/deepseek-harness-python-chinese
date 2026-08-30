"""表面保留选择，以及自动未结束回合与手动空闲会话压缩共用的已记入日志压缩事务。"""
import uuid#铸造压缩事务 id
from ...依赖 import cordis#外部依赖胶水
from ..压缩 import (#导入压缩 seam
    压缩标识,#事务品牌 id
    手动压缩错误,#手动预期失败
    压缩检查点来源,#检查点出处构造
    工具配对后平衡,#seq 之后是否平衡
    工具配对前平衡,#seq 之前是否平衡
)#压缩包
from ...模型后端.llm import 创建用户消息,错误链#导入用户消息与错误链
from .摘要器 import 装帧摘要#导入检查点装帧

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 若已中止则抛出(信号):#对齐 AbortSignal.throwIfAborted
    """已取消则抛出精确原因。"""
    if 信号 is None:#无信号
        return#放过
    方法=getattr(信号,'throwIfAborted',None)#英文 API
    if callable(方法):#有方法
        方法()#抛出
        return#已检查
    方法中=getattr(信号,'抛若中止',None)#中文 API
    if callable(方法中):#有中文方法
        方法中()#抛出
        return#已检查
    if 取字段(信号,'aborted') is True or 取字段(信号,'已中止') is True:#旗标已中止
        原因=取字段(信号,'reason')#英文原因
        if 原因 is None:#试中文
            原因=取字段(信号,'原因')#中文原因
        if isinstance(原因,BaseException):#原因本就是异常
            raise 原因#原样抛出
        if 原因 is not None:#非异常原因
            raise Exception(str(原因))#包成异常
        错误=Exception('This operation was aborted')#缺省中止文案
        错误.name='AbortError'#固定 AbortError 名
        raise 错误#抛出

def 深相等(左,右):#对齐 isDeepStrictEqual 的结构化比较
    """比较两条载荷是否深相等。"""
    return 左==右#结构化相等

class 表面已变错误(Exception):#拒绝替换边界已不再是其构建时所选边界的摘要
    """与摘要器及收缩失败区分开，以便手动调用方可分别报告两种原因。"""
    pass#标记类

def 选择可压缩区间(会话,计量,保留令牌):#在保留已计价近期尾、且永不拆开助手工具调用/结果对的前提下，解析下一个头锚定区间
    """返回要压缩的闭区间位置 seq 范围，或 None。"""
    计价节点=取字段(计量,'nodes') or []#已计价表面节点
    if len(计价节点)==0:#空表面
        return None#无可选
    表面节点=list(取字段(取字段(会话,'surface'),'nodes') or [])#当前表面 seq
    if len(表面节点)!=len(计价节点) or any(#长度不一致或 seq 对不上
            表面节点[下标]!=取字段(计价节点[下标],'seq') for 下标 in range(len(表面节点))):#逐位比对
        raise Exception('compaction: token-meter surface does not match the current session surface')#计量与表面不同步
    累计=0#从尾累加 token
    保留起点下标=len(计价节点)#保留起点下标
    for 下标 in range(len(计价节点)-1,-1,-1):#从尾向前
        累计+=取字段(计价节点[下标],'tokens')#累加该节点
        保留起点下标=下标#暂定保留起点
        if 累计>=保留令牌:#已够尾预算
            break#停止
    if 保留起点下标==0:#整表面都要保留
        return None#无可压缩
    while 保留起点下标>0:#向前找到平衡切割
        if 工具配对前平衡(会话,表面节点[保留起点下标]):#该切割平衡
            break#停止
        保留起点下标-=1#否则再让出一节点
    if 保留起点下标==0:#找不到平衡切割
        return None#无可压缩
    return {'start':表面节点[0],'end':表面节点[保留起点下标-1]}#头锚定闭区间

def 扫描压缩入口状态(事件们):#独立检查未结束回合、未配对压缩与最近种子边界状态
    """从尾扫描入口状态。"""
    未结束回合=None#未结束回合
    回合状态已知=False#回合状态是否已确定
    未配对压缩开始=None#未配对 start
    压缩入口已知=False#压缩入口是否已确定
    最近结束种子序号=None#最近 end-seed
    for 下标 in range(len(事件们)-1,-1,-1):#从尾向前
        事件=事件们[下标]#当前事件
        if 最近结束种子序号 is None and 取字段(事件,'type')=='session/end-seed':#尚未记下种子边界
            最近结束种子序号=取字段(事件,'seq')#最近 end-seed
        if not 压缩入口已知:#压缩入口未定
            if 取字段(事件,'type')=='compaction/start':#先遇到 start
                未配对压缩开始=事件#未配对
                压缩入口已知=True#已确定
            elif 取字段(事件,'type')=='compaction/end':#先遇到 end
                压缩入口已知=True#已配对关闭
        if not 回合状态已知:#回合状态未定
            if 取字段(事件,'type')=='turn/start':#先遇到回合开始
                未结束回合=取字段(取字段(事件,'data'),'turn')#未结束回合
                回合状态已知=True#已确定
            elif 取字段(事件,'type')=='turn/end':#先遇到回合结束
                回合状态已知=True#无未结束回合
        if 回合状态已知 and 压缩入口已知 and 最近结束种子序号 is not None:#三项都已确定
            break#可提前停
    return {#入口状态
        'openTurn':未结束回合,#未结束回合
        'unmatchedCompactionStart':未配对压缩开始,#未配对 start
        'latestEndSeedSeq':最近结束种子序号,#最近种子边界
    }#返回结束

def 断言压缩未活动(未配对压缩开始,最近结束种子序号,阶段):#拒绝耐久未配对压缩标记，除非后续构造期种子边界证明其所有者属于更早的会话生命周期
    """忙碌则抛手动压缩错误 busy。"""
    if 未配对压缩开始 is None:#没有未配对 start
        return#空闲
    if 最近结束种子序号 is not None and 最近结束种子序号>取字段(未配对压缩开始,'seq'):#有种子边界且边界更晚则 start 已过期
        return#空闲
    raise 手动压缩错误(#仍持锁
        'busy',#忙碌码
        阶段+': compaction already in progress; the session compaction lock is already active',#锁已占用
    )#抛出结束

def 断言无活动压缩(会话,阶段):#在异步政策决策之后复核耐久压缩锁
    """导出的锁复核。"""
    入口=扫描压缩入口状态(取字段(会话,'events') or [])#扫描入口状态
    断言压缩未活动(#断言空闲
        取字段(入口,'unmatchedCompactionStart'),#未配对 start
        取字段(入口,'latestEndSeedSeq'),#最近种子边界
        阶段,#诊断标签
    )#断言结束

def 校验表面区间(会话,起点,终点):#在异步工作开始前校验一个请求的表面位置跨度
    """返回已校验表面选择。"""
    节点们=list(取字段(取字段(会话,'surface'),'nodes') or [])#当前表面
    try:#找起始下标
        起点下标=节点们.index(起点)#起始下标
    except ValueError:#不在表面
        raise Exception('compactRegion: start seq '+str(起点)+' not found in surface')#起始不在表面
    try:#找结束下标
        终点下标=节点们.index(终点)#结束下标
    except ValueError:#不在表面
        raise Exception('compactRegion: end seq '+str(终点)+' not found in surface')#结束不在表面
    if 起点下标>终点下标:#位置反转
        raise Exception(#反转错误
            'compactRegion: start seq '+str(起点)+' (position '+str(起点下标)
            +') is after end seq '+str(终点)+' (position '+str(终点下标)+') on the surface'#起始在结束之后
        )#抛出结束
    if not 工具配对前平衡(会话,节点们[起点下标]):#起始切割不平衡
        raise Exception('compactRegion: start seq '+str(起点)+' is not a balanced boundary (would split a step\'s tool-call/result pair)')#会拆开工具对
    if not 工具配对后平衡(会话,节点们[终点下标]):#结束切割不平衡
        raise Exception('compactRegion: end seq '+str(终点)+' is not a balanced boundary (would split a step, or the step is still open)')#会拆开步骤或步骤未结束
    return {#含两端的 seq 切片
        'start':起点,#起始 seq
        'end':终点,#结束 seq
        'startIdx':起点下标,#起始下标
        'endIdx':终点下标,#结束下标
        'shadowedSeqs':节点们[起点下标:终点下标+1],#被遮蔽 seq
    }#返回结束

def 构建摘要输入(会话,被遮蔽序号们):#为被遮蔽区间重建最近一次已路由请求的可缓存前缀
    """返回要浓缩的重放对话前缀。"""
    头=会话.requestHeader() if hasattr(会话,'requestHeader') else 会话.请求头()#最近请求头
    事件们=取字段(会话,'events')#权威事件流
    区间消息=[]#区间派生消息
    for 序号 in 被遮蔽序号们:#区间 seq；每个都是合法日志下标
        消息=会话.deriveEventMessage(事件们[序号]) if hasattr(会话,'deriveEventMessage') else 会话.派生事件消息(事件们[序号])#派生模型可见消息
        if 消息 is not None:#丢掉非消息节点
            区间消息.append(消息)#收下
    输入={'messages':区间消息}#重放前缀基础
    if 头 is not None and 取字段(头,'system') is not None:#复用系统提示
        输入['system']=取字段(头,'system')#系统提示
    if 头 is not None and 取字段(头,'tools') is not None:#复用工具模式
        输入['tools']=取字段(头,'tools')#工具模式
    return 输入#返回结束

def 准备压缩(依赖,会话,选择):#为已校验表面区间快照计价与重放输入
    """返回带快照的准备结果。"""
    计量=依赖['meter'].measure(会话)#当前计量
    所选节点=list(取字段(计量,'nodes') or [])[取字段(选择,'startIdx'):取字段(选择,'endIdx')+1]#所选节点
    被遮蔽=取字段(选择,'shadowedSeqs')#被遮蔽 seq
    if len(所选节点)!=len(被遮蔽) or any(#长度不一致或 seq 对不上
            取字段(所选节点[下标],'seq')!=被遮蔽[下标] for 下标 in range(len(所选节点))):#逐位比对
        raise 表面已变错误('compaction: selected surface changed before summarization began')#摘要前表面已变
    合计=0#合计 token
    for 节点 in 所选节点:#累加
        合计+=取字段(节点,'tokens')#节点价格
    准备=dict(选择)#选择字段副本
    准备['measurement']=计量#当时计量
    准备['selectedNodes']=所选节点#所选节点
    准备['shadowedTokenCount']=合计#合计 token
    准备['input']=构建摘要输入(会话,被遮蔽)#重放输入
    return 准备#返回结束

def 摘要压缩(依赖,准备,智能体,压缩事务标识,来源命令标识,信号=None):#跑摘要器并装帧其替换检查点
    """返回摘要后待提交快照。"""
    摘要结果=解开(依赖['summarize'](取字段(准备,'input'),智能体,信号))#跑摘要钩子
    检查点消息=创建用户消息({#合成替换用户消息
        'content':装帧摘要(取字段(摘要结果,'summary')),#装帧摘要
        'source':压缩检查点来源(压缩事务标识,来源命令标识),#检查点出处
    })#用户消息结束
    装帧令牌=依赖['meter'].estimateMessage(检查点消息)#装帧后启发式价格
    if 装帧令牌>=取字段(准备,'shadowedTokenCount'):#没有更小
        raise Exception(#收缩失败
            'summary is not smaller than the shadowed content ('
            +str(装帧令牌)+' estimated framed tokens >= '+str(取字段(准备,'shadowedTokenCount'))+')'#装帧 token 不小于被遮蔽
        )#抛出结束
    合并=dict(准备)#快照副本
    合并.update(摘要结果)#摘要结果
    合并['checkpointMessage']=检查点消息#替换消息
    return 合并#返回结束

def 断言整表面未变(依赖,会话,准备):#拒绝针对任何更早表面代数准备的摘要
    """整表面节点列表须与构建时快照深相等。"""
    当前=依赖['meter'].measure(会话)#当前计量
    if not 深相等(取字段(当前,'nodes'),取字段(取字段(准备,'measurement'),'nodes')):#节点列表已变
        raise 表面已变错误('compaction: session surface changed during summarization')#摘要期间表面已变

def 断言所选跨度稳定(依赖,会话,准备):#只要求所选跨度仍是同一份现存、连续、等价计价、平衡的替换目标
    """在它之外新增的节点仍可见，且不使摘要失效。"""
    try:#按原 seq 再校验
        当前=校验表面区间(会话,取字段(准备,'start'),取字段(准备,'end'))#仍须是合法区间
    except Exception as 错误:#不再合法
        已变=表面已变错误('compaction: the selected span is no longer a valid replacement target')#映射为表面已变
        已变.__cause__=错误#保留原因
        raise 已变#抛出
    if not 深相等(list(取字段(当前,'shadowedSeqs')),list(取字段(准备,'shadowedSeqs'))):#seq 列表已变
        raise 表面已变错误('compaction: the selected span changed during summarization')#摘要期间跨度已变
    计量切片=list(取字段(依赖['meter'].measure(会话),'nodes') or [])[取字段(当前,'startIdx'):取字段(当前,'endIdx')+1]#当前计价切片
    if not 深相等(计量切片,取字段(准备,'selectedNodes')):#计价已变
        raise 表面已变错误('compaction: the selected span was rewritten during summarization')#摘要期间跨度被改写

def 提交压缩正文(会话,开始事件,已摘要):#不让出地追加一条已完成摘要记录与替换正文
    """返回待补 endSeq 的结果。"""
    起点=取字段(已摘要,'start')#起始 seq
    终点=取字段(已摘要,'end')#结束 seq
    被遮蔽序号=取字段(已摘要,'shadowedSeqs')#被遮蔽 seq
    被遮蔽令牌=取字段(已摘要,'shadowedTokenCount')#被遮蔽 token
    摘要=取字段(已摘要,'summary')#安全摘要
    提供方=取字段(已摘要,'provider')#提供方
    模型=取字段(已摘要,'model')#模型
    最大令牌=取字段(已摘要,'maxTokens')#生成上限
    用量=取字段(已摘要,'usage')#用量
    检查点消息=取字段(已摘要,'checkpointMessage')#替换消息
    if 取字段(已摘要,'llmStreamCall') is True:#是否已标记 LLM 调用
        调用出处={'rawOutput':取字段(已摘要,'rawOutput'),'llmStreamCall':True}#已标记须带完整输出
    elif 取字段(已摘要,'rawOutput') is None:#未标记且无输出
        调用出处={}#省略
    else:#未标记则可选输出
        调用出处={'rawOutput':取字段(已摘要,'rawOutput')}#可选输出
    摘要载荷={#摘要计量事件
        'compactionId':取字段(取字段(开始事件,'data'),'compactionId'),#事务 id
        'summary':摘要,#安全摘要
        'shadowedRange':{'start':起点,'end':终点},#被遮蔽区间
        'shadowedSeqs':list(被遮蔽序号),#seq 列表副本
        'shadowedTokenCount':被遮蔽令牌,#启发式价格
        'provider':提供方,#提供方
        'model':模型,#模型
    }#摘要载荷基础
    摘要载荷.update(调用出处)#调用出处
    if 取字段(取字段(开始事件,'data'),'sourceCommandId') is not None:#start 是否带命令
        摘要载荷['sourceCommandId']=取字段(取字段(开始事件,'data'),'sourceCommandId')#沿用命令 id
    if 最大令牌 is not None:#有上限才写入
        摘要载荷['maxTokens']=最大令牌#生成上限
    if 用量 is not None:#有用量才写入
        摘要载荷['usage']=用量#用量
    摘要事件=会话.append('compaction/summary',摘要载荷)#summary 结束
    会话.append('user/message',检查点消息,{#替换用户消息
        'surfaceOp':{'op':'replace','start':起点,'end':终点},#替换该区间
        'sourceEventSeqs':[取字段(开始事件,'seq'),取字段(摘要事件,'seq'),*被遮蔽序号],#引用 start、summary 与被遮蔽节点
    })#替换结束
    结果={#待补 end 的结果
        'compactionId':取字段(取字段(开始事件,'data'),'compactionId'),#事务 id
        'startSeq':取字段(开始事件,'seq'),#start 序号
        'summarySeq':取字段(摘要事件,'seq'),#summary 序号
        'summary':摘要,#摘要内容
        'shadowedRange':{'start':起点,'end':终点},#被遮蔽区间
        'shadowedSeqs':list(被遮蔽序号),#seq 列表副本
        'shadowedTokenCount':被遮蔽令牌,#启发式价格
    }#结果基础
    if 取字段(取字段(开始事件,'data'),'sourceCommandId') is not None:#是否带命令
        结果['sourceCommandId']=取字段(取字段(开始事件,'data'),'sourceCommandId')#沿用
    return 结果#返回结束

def 完成压缩(待完成,结束事件):#把成功追加的关闭事件接到待完成结果上
    """补上 endSeq。"""
    完成=dict(待完成)#副本
    完成['endSeq']=取字段(结束事件,'seq')#补上 end 序号
    return 完成#完整结果

def 抛手动失败(失败):#分类一次已关闭的手动尝试，不削弱取消优先级
    """按阶段映射为手动压缩错误。"""
    if 取字段(失败,'stage')=='commit':#提交阶段
        raise 手动压缩错误(#映射为 commit
            'commit',#提交码
            'manual compaction did not commit cleanly',#未干净提交
            {'cause':取字段(失败,'error')},#保留原因
        )#抛出结束
    if isinstance(取字段(失败,'error'),表面已变错误):#所选历史已变
        raise 手动压缩错误(#映射为 changed
            'changed',#已变码
            'the compacted history changed during manual compaction',#压缩期间历史已变
            {'cause':取字段(失败,'error')},#保留原因
        )#抛出结束
    raise 手动压缩错误(#其余视为摘要失败
        'summary',#摘要码
        'manual compaction could not produce a smaller summary',#未能产出更小摘要
        {'cause':取字段(失败,'error')},#保留原因
    )#抛出结束

def 压缩表面区间(依赖,会话,起点,终点,智能体,选项,信号=None):#在一个所选位置跨度上跑单次压缩事务
    """选择与校验只读；返回成功的耐久压缩结果。"""
    if 取字段(选项,'owner') is None:#独立事务入口检查取消
        若已中止则抛出(信号)#入口取消
    选择=校验表面区间(会话,起点,终点)#只读校验区间
    入口=扫描压缩入口状态(取字段(会话,'events') or [])#扫描入口状态
    断言压缩未活动(#耐久锁须空闲
        取字段(入口,'unmatchedCompactionStart'),#未配对 start
        取字段(入口,'latestEndSeedSeq'),#最近种子边界
        'compaction',#诊断标签
    )#锁检查结束
    if 取字段(选项,'owner') is None:#独立括号
        if 取字段(入口,'openTurn') is not None:#已有未结束回合
            raise 手动压缩错误('busy','manual compaction: the session already has an open turn')#手动须在回合之间
        所有者=None#独立
    else:#回合内自动
        if 取字段(入口,'openTurn') is None:#没有未结束回合
            raise Exception('compactRegion: no open turn — automatic compaction events must be enclosed in a turn')#自动须包在回合内
        所有者=取字段(入口,'openTurn')#沿用当前回合
    压缩事务标识=压缩标识(str(uuid.uuid4()))#铸造事务 id
    生命周期={#start/end 共用载荷
        'compactionId':压缩事务标识,#事务 id
        'turn':所有者,#所有者
    }#lifecycle 基础
    if 取字段(选项,'sourceCommandId') is not None:#可选命令 id
        生命周期['sourceCommandId']=取字段(选项,'sourceCommandId')#写入
    开始事件=会话.append('compaction/start',生命周期)#耐久锁
    if 取字段(选项,'stability')=='whole-surface':#整表面或所选跨度
        断言稳定=断言整表面未变#整表面未变
    else:#只要求所选跨度稳定
        断言稳定=断言所选跨度稳定#所选跨度
    失败=None#捕获的失败
    刷盘失败=None#刷盘失败
    结果=None#成功结果
    已关闭=False#是否已追加 end
    正在关闭=False#是否已进入关闭
    阶段='summary'#当前阶段
    try:#摘要并提交
        准备=准备压缩(依赖,会话,选择)#快照计价与重放输入
        已摘要=摘要压缩(#跑摘要并装帧
            依赖,#计量
            准备,#快照
            智能体,#智能体
            压缩事务标识,#事务 id
            取字段(选项,'sourceCommandId'),#来源命令
            信号,#取消
        )#摘要结束
        if 取字段(选项,'owner') is None:#提交前再检查取消
            若已中止则抛出(信号)#取消
        断言稳定(依赖,会话,已摘要)#摘要后稳定检查
        阶段='commit'#进入提交阶段
        待完成=提交压缩正文(会话,开始事件,已摘要)#同步追加 summary 与替换
        正在关闭=True#开始关闭
        结束事件=会话.append('compaction/end',生命周期)#成功 end
        已关闭=True#已关闭
        结果=完成压缩(待完成,结束事件)#补上 endSeq
    except Exception as 错误:#摘要或提交失败
        失败={'error':错误,'stage':'commit' if 正在关闭 else 阶段}#记下阶段
        if not 正在关闭:#尚未关闭
            正在关闭=True#尝试关闭
            try:#追加失败 end
                失败生命周期=dict(生命周期)#副本
                失败生命周期['error']=错误链(错误)#带错误链的 end
                会话.append('compaction/end',失败生命周期)#失败 end
                已关闭=True#已关闭
            except Exception as 关闭错误:#关闭本身失败
                失败={'error':关闭错误,'stage':'commit'}#改记为提交失败
    if 已关闭 and 取字段(选项,'flush') is not None:#已关闭且要刷盘
        try:#耐久检查点
            解开(选项['flush']())#刷盘
        except Exception as 错误:#刷盘失败
            刷盘失败=错误#记下，不掩盖事务结果
    if 取字段(选项,'owner') is None:#取消仍优先于失败分类
        若已中止则抛出(信号)#取消优先
    if 失败 is not None:#事务失败
        if 取字段(选项,'owner') is None:#手动路径分类抛出
            抛手动失败(失败)#分类
        raise 取字段(失败,'error')#自动路径原样抛
    if 刷盘失败 is not None:#刷盘失败
        raise 手动压缩错误(#映射为 persistence
            'persistence',#持久化码
            'manual compaction durability checkpoint failed',#刷盘失败
            {'cause':刷盘失败},#保留原因
        )#抛出结束
    if 结果 is None:#无结果却走到成功
        raise Exception('compaction committed without a result')#无结果
    return 结果#成功结果
