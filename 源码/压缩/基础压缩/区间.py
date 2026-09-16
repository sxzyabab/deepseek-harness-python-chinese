"""表面保留选择，以及自动未结束回合与手动空闲会话压缩共用的已记入日志压缩事务。"""
import uuid#铸造压缩事务 id
from ..压缩 import (#导入压缩 seam
    压缩标识,#事务品牌 id
    手动压缩错误,#手动预期失败
    压缩检查点来源,#检查点出处构造
    工具配对后平衡,#seq 之后是否平衡
    工具配对前平衡,#seq 之前是否平衡
)#压缩包
from ...模型后端.llm import 创建用户消息,错误链#导入用户消息与错误链
from .摘要器 import 装帧摘要#导入检查点装帧
from .配置 import 基础压缩错误#本包异常

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号._事件.is_set()#Event 置位即中止

def 若已中止则抛出(信号):
    """已中止则抛出承载原因的异常。"""
    if 信号 is None:#无信号
        return#无信号
    if not 信号._事件.is_set():#仍活着
        return#仍活着
    if 信号._异常 is not None:#有承载异常
        raise 信号._异常#抛出
    raise 基础压缩错误('aborted')#默认中止

def 深相等(左,右):
    """比较两条载荷是否深相等。"""
    return 左==右#结构化相等

class 表面已变错误(基础压缩错误):
    """与摘要器及收缩失败区分开，以便手动调用方可分别报告两种原因。"""
    pass#标记类

def 系统头(会话,头序号):
    """持有表面节点 0 的 system/message；否则 None。"""
    事件=会话.events[头序号]#表面头事件
    if 事件 is not None and 事件['type']=='system/message':#仅系统消息
        return 事件#系统头
    return None#无

def 选择可压缩区间(会话,计量,保留令牌):
    """返回要压缩的闭区间位置 seq 范围，或 None。系统头永不进入区间。"""
    计价节点=计量['nodes'] if 'nodes' in 计量 and 计量['nodes'] is not None else []#已计价表面节点
    if len(计价节点)==0:#空表面
        return None#无可选
    表面节点=list(会话.surface.nodes)#当前表面 seq
    if len(表面节点)!=len(计价节点) or any(#长度不一致或 seq 对不上
            表面节点[下标]!=计价节点[下标]['seq'] for 下标 in range(len(表面节点))):#逐位比对
        raise 基础压缩错误('compaction: token-meter surface does not match the current session surface')#计量与表面不同步
    首下标=0 if 系统头(会话,表面节点[0]) is None else 1#跳过系统头
    累计=0#从尾累加 token
    保留起点下标=len(计价节点)#保留起点下标
    for 下标 in range(len(计价节点)-1,-1,-1):#从尾向前
        累计+=计价节点[下标]['tokens']#累加该节点
        保留起点下标=下标#暂定保留起点
        if 累计>=保留令牌:#已够尾预算
            break#停止
    if 保留起点下标<=首下标:#整可压区都要保留
        return None#无可压缩
    while 保留起点下标>首下标:#向前找到平衡切割
        if 工具配对前平衡(会话,表面节点[保留起点下标]):#该切割平衡
            break#停止
        保留起点下标-=1#否则再让出一节点
    if 保留起点下标<=首下标:#找不到平衡切割
        return None#无可压缩
    return {'start':表面节点[首下标],'end':表面节点[保留起点下标-1]}#闭区间

def 扫描压缩入口状态(事件列表):
    """从尾扫描入口状态。"""
    未结束回合=None#未结束回合
    回合状态已知=False#回合状态是否已确定
    未配对压缩开始=None#未配对 start
    压缩入口已知=False#压缩入口是否已确定
    最近结束种子序号=None#最近 end-seed
    for 下标 in range(len(事件列表)-1,-1,-1):#从尾向前
        事件=事件列表[下标]#当前事件
        if 最近结束种子序号 is None and 事件['type']=='session/end-seed':#尚未记下种子边界
            最近结束种子序号=事件['seq']#最近 end-seed
        if not 压缩入口已知:#压缩入口未定
            if 事件['type']=='compaction/start':#先遇到 start
                未配对压缩开始=事件#未配对
                压缩入口已知=True#已确定
            elif 事件['type']=='compaction/end':#先遇到 end
                压缩入口已知=True#已配对关闭
        if not 回合状态已知:#回合状态未定
            if 事件['type']=='turn/start':#先遇到回合开始
                未结束回合=事件['data']['turn']#未结束回合
                回合状态已知=True#已确定
            elif 事件['type']=='turn/end':#先遇到回合结束
                回合状态已知=True#无未结束回合
        if 回合状态已知 and 压缩入口已知 and 最近结束种子序号 is not None:#三项都已确定
            break#可提前停
    return {#入口状态
        'openTurn':未结束回合,#未结束回合
        'unmatchedCompactionStart':未配对压缩开始,#未配对 start
        'latestEndSeedSeq':最近结束种子序号,#最近种子边界
    }#返回结束

def 校验压缩未活动(未配对压缩开始,最近结束种子序号,阶段):
    """忙碌则抛手动压缩错误 busy。"""
    if 未配对压缩开始 is None:#没有未配对 start
        return#空闲
    if 最近结束种子序号 is not None and 最近结束种子序号>未配对压缩开始['seq']:#有种子边界且边界更晚则 start 已过期
        return#空闲
    raise 手动压缩错误(#仍持锁
        'busy',#忙碌码
        阶段+': compaction already in progress; the session compaction lock is already active',#锁已占用
    )#抛出结束

def 校验无活动压缩(会话,阶段):
    """导出的锁复核。"""
    入口=扫描压缩入口状态(会话.events)#扫描入口状态
    校验压缩未活动(#断言空闲
        入口['unmatchedCompactionStart'],#未配对 start
        入口['latestEndSeedSeq'],#最近种子边界
        阶段,#诊断标签
    )#断言结束

def 校验表面区间(会话,起点,终点):
    """返回已校验表面选择。"""
    节点列表=list(会话.surface.nodes)#当前表面
    try:#找起始下标
        起点下标=节点列表.index(起点)#起始下标
    except ValueError:#不在表面
        raise 基础压缩错误('compactRegion: start seq '+str(起点)+' not found in surface')#起始不在表面
    try:#找结束下标
        终点下标=节点列表.index(终点)#结束下标
    except ValueError:#不在表面
        raise 基础压缩错误('compactRegion: end seq '+str(终点)+' not found in surface')#结束不在表面
    if 起点下标>终点下标:#位置反转
        raise 基础压缩错误(#反转错误
            'compactRegion: start seq '+str(起点)+' (position '+str(起点下标)
            +') is after end seq '+str(终点)+' (position '+str(终点下标)+') on the surface'#起始在结束之后
        )#抛出结束
    if not 工具配对前平衡(会话,节点列表[起点下标]):#起始切割不平衡
        raise 基础压缩错误('compactRegion: start seq '+str(起点)+' is not a balanced boundary (would split a step\'s tool-call/result pair)')#会拆开工具对
    if not 工具配对后平衡(会话,节点列表[终点下标]):#结束切割不平衡
        raise 基础压缩错误('compactRegion: end seq '+str(终点)+' is not a balanced boundary (would split a step, or the step is still open)')#会拆开步骤或步骤未结束
    return {#含两端的 seq 切片
        'start':起点,#起始 seq
        'end':终点,#结束 seq
        'startIdx':起点下标,#起始下标
        'endIdx':终点下标,#结束下标
        'shadowedSeqs':节点列表[起点下标:终点下标+1],#被遮蔽 seq
    }#返回结束

def 构建摘要输入(会话,被遮蔽序号列表):
    """返回要浓缩的重放对话前缀；系统头经表面节点 0 派生，不在请求头 system。"""
    头=会话.请求头()#最近请求头
    事件列表=会话.events#权威事件流
    表面节点=list(会话.surface.nodes)#当前表面
    系统=None#派生系统消息
    if len(表面节点)>0:#有表面头
        头事件=系统头(会话,表面节点[0])#系统头事件
        if 头事件 is not None:#有系统头
            系统=会话.派生事件消息(头事件)#派生
    区间消息=[]#区间派生消息
    for 序号 in 被遮蔽序号列表:#区间 seq；每个都是合法日志下标
        消息=会话.派生事件消息(事件列表[序号])#派生模型可见消息
        if 消息 is not None:#丢掉非消息节点
            区间消息.append(消息)#收下
    if 系统 is not None:#系统头在前
        区间消息=[系统,*区间消息]#前缀
    输入={'messages':区间消息}#重放前缀基础
    if 头 is not None and 'tools' in 头 and 头['tools'] is not None:#复用工具模式
        输入['tools']=头['tools']#工具模式
    return 输入#返回结束

def 准备压缩(依赖,会话,选择):
    """返回带快照的准备结果。"""
    计量=依赖['meter'].测量(会话)#当前计量
    所选节点=list(计量['nodes'] if 'nodes' in 计量 and 计量['nodes'] is not None else [])[选择['startIdx']:选择['endIdx']+1]#所选节点
    被遮蔽=选择['shadowedSeqs']#被遮蔽 seq
    if len(所选节点)!=len(被遮蔽) or any(#长度不一致或 seq 对不上
            所选节点[下标]['seq']!=被遮蔽[下标] for 下标 in range(len(所选节点))):#逐位比对
        raise 表面已变错误('compaction: selected surface changed before summarization began')#摘要前表面已变
    启发式合计=0#启发式 token
    路由合计=0#路由 token
    for 节点 in 所选节点:#累加
        启发式合计+=节点['heuristicTokens'] if 'heuristicTokens' in 节点 else 节点['tokens']#启发式价格
        路由合计+=节点['tokens']#路由价格
    准备=dict(选择)#选择字段副本
    准备['measurement']=计量#当时计量
    准备['selectedNodes']=所选节点#所选节点
    准备['shadowedTokenCount']=启发式合计#影子价格合计
    准备['shadowedRouteTokenCount']=路由合计#路由合计
    准备['input']=构建摘要输入(会话,被遮蔽)#重放输入
    return 准备#返回结束

def 摘要压缩(依赖,准备,智能体,压缩事务标识,来源命令标识,校验稳定,信号=None):
    """返回摘要后待提交快照。"""
    while True:#失败可恢复则重试
        若已中止则抛出(信号)#进入前检查取消
        try:#跑摘要钩子
            摘要结果=依赖['summarize'](准备['input'],智能体,信号)#跑摘要钩子
            break#成功则离开
        except Exception as 错误:#摘要失败
            if 已中止(信号):#取消优先
                raise 错误#原样抛
            校验稳定(依赖,智能体.session,准备)#跨度须仍合法
            if not 依赖['recover'](错误,智能体,准备['shadowedSeqs'],信号):#无法恢复
                raise 错误#原样抛
            准备=准备压缩(依赖,智能体.session,校验表面区间(智能体.session,准备['start'],准备['end']))#按耐久改写重计价
    检查点消息=创建用户消息({#合成替换用户消息
        'content':装帧摘要(摘要结果['summary']),#装帧摘要
        'source':压缩检查点来源(压缩事务标识,来源命令标识),#检查点出处
    })#用户消息结束
    装帧令牌=依赖['meter'].计价消息(检查点消息)#装帧后启发式价格
    路由合计=准备['shadowedRouteTokenCount']#跨度路由价
    if 装帧令牌>=路由合计:#没有更小
        raise 基础压缩错误(#收缩失败
            'summary is not smaller than the shadowed content ('
            +str(装帧令牌)+' estimated framed tokens >= '+str(路由合计)+')'#装帧 token 不小于被遮蔽路由价
        )#抛出结束
    合并=dict(准备)#快照副本
    合并.update(摘要结果)#摘要结果
    合并['checkpointMessage']=检查点消息#替换消息
    return 合并#返回结束

def 校验整表面未变(依赖,会话,准备):
    """整表面节点列表须与构建时快照深相等。"""
    当前=依赖['meter'].测量(会话)#当前计量
    if not 深相等(当前['nodes'],准备['measurement']['nodes']):#节点列表已变
        raise 表面已变错误('compaction: session surface changed during summarization')#摘要期间表面已变

def 校验所选跨度稳定(依赖,会话,准备):
    """在它之外新增的节点仍可见，且不使摘要失效。"""
    try:#按原 seq 再校验
        当前=校验表面区间(会话,准备['start'],准备['end'])#仍须是合法区间
    except 基础压缩错误 as 错误:#不再合法
        已变=表面已变错误('compaction: the selected span is no longer a valid replacement target')#映射为表面已变
        已变.__cause__=错误#保留原因
        raise 已变#抛出
    if not 深相等(list(当前['shadowedSeqs']),list(准备['shadowedSeqs'])):#seq 列表已变
        raise 表面已变错误('compaction: the selected span changed during summarization')#摘要期间跨度已变
    计量=依赖['meter'].测量(会话)#当前计量
    计量切片=list(计量['nodes'] if 'nodes' in 计量 and 计量['nodes'] is not None else [])[当前['startIdx']:当前['endIdx']+1]#当前计价切片
    if not 深相等(计量切片,准备['selectedNodes']):#计价已变
        raise 表面已变错误('compaction: the selected span was rewritten during summarization')#摘要期间跨度被改写

def 提交压缩正文(会话,开始事件,已摘要):
    """返回待补 endSeq 的结果。"""
    起点=已摘要['start']#起始 seq
    终点=已摘要['end']#结束 seq
    被遮蔽序号=已摘要['shadowedSeqs']#被遮蔽 seq
    被遮蔽令牌=已摘要['shadowedTokenCount']#被遮蔽 token
    摘要=已摘要['summary']#安全摘要
    提供方=已摘要['provider']#提供方
    模型=已摘要['model']#模型
    最大令牌=已摘要['maxTokens'] if 'maxTokens' in 已摘要 else None#生成上限
    用量=已摘要['usage'] if 'usage' in 已摘要 else None#用量
    检查点消息=已摘要['checkpointMessage']#替换消息
    if 'llmStreamCall' in 已摘要 and 已摘要['llmStreamCall'] is True:#是否已标记 LLM 调用
        调用记录={'rawOutput':已摘要['rawOutput'],'llmStreamCall':True}#已标记须带完整输出
    elif 'rawOutput' not in 已摘要 or 已摘要['rawOutput'] is None:#未标记且无输出
        调用记录={}#省略
    else:#未标记则可选输出
        调用记录={'rawOutput':已摘要['rawOutput']}#可选输出
    开始数据=开始事件['data']#start 载荷
    摘要载荷={#摘要计量事件
        'compactionId':开始数据['compactionId'],#事务 id
        'summary':摘要,#安全摘要
        'shadowedRange':{'start':起点,'end':终点},#被遮蔽区间
        'shadowedSeqs':list(被遮蔽序号),#seq 列表副本
        'shadowedTokenCount':被遮蔽令牌,#启发式价格
        'provider':提供方,#提供方
        'model':模型,#模型
    }#摘要载荷基础
    摘要载荷.update(调用记录)#调用记录
    if 'sourceCommandId' in 开始数据 and 开始数据['sourceCommandId'] is not None:#start 是否带命令
        摘要载荷['sourceCommandId']=开始数据['sourceCommandId']#沿用命令 id
    if 最大令牌 is not None:#有上限才写入
        摘要载荷['maxTokens']=最大令牌#生成上限
    if 用量 is not None:#有用量才写入
        摘要载荷['usage']=用量#用量
    摘要事件=会话.追加('compaction/summary',摘要载荷)#summary 结束
    会话.追加('user/message',检查点消息,{#替换用户消息
        'surfaceOp':{'op':'replace','startSeq':起点,'endSeq':终点},#替换该区间
        'sourceEventSeqs':[开始事件['seq'],摘要事件['seq'],*被遮蔽序号],#引用 start、summary 与被遮蔽节点
    })#替换结束
    结果={#待补 end 的结果
        'compactionId':开始数据['compactionId'],#事务 id
        'startSeq':开始事件['seq'],#start 序号
        'summarySeq':摘要事件['seq'],#summary 序号
        'summary':摘要,#摘要内容
        'shadowedRange':{'start':起点,'end':终点},#被遮蔽区间
        'shadowedSeqs':list(被遮蔽序号),#seq 列表副本
        'shadowedTokenCount':被遮蔽令牌,#启发式价格
    }#结果基础
    if 'sourceCommandId' in 开始数据 and 开始数据['sourceCommandId'] is not None:#是否带命令
        结果['sourceCommandId']=开始数据['sourceCommandId']#沿用
    return 结果#返回结束

def 完成压缩(待完成,结束事件):
    """补上 endSeq。"""
    完成=dict(待完成)#副本
    完成['endSeq']=结束事件['seq']#补上 end 序号
    return 完成#完整结果

def 抛手动失败(失败):
    """按阶段映射为手动压缩错误。"""
    if 失败['stage']=='commit':#提交阶段
        raise 手动压缩错误(#映射为 commit
            'commit',#提交码
            'manual compaction did not commit cleanly',#未干净提交
            {'cause':失败['error']},#保留原因
        )#抛出结束
    if isinstance(失败['error'],表面已变错误):#所选历史已变
        raise 手动压缩错误(#映射为 changed
            'changed',#已变码
            'the compacted history changed during manual compaction',#压缩期间历史已变
            {'cause':失败['error']},#保留原因
        )#抛出结束
    raise 手动压缩错误(#其余视为摘要失败
        'summary',#摘要码
        'manual compaction could not produce a smaller summary',#未能产出更小摘要
        {'cause':失败['error']},#保留原因
    )#抛出结束

def 压缩表面区间(依赖,会话,起点,终点,智能体,选项,信号=None):
    """选择与校验只读；返回成功的耐久压缩结果。"""
    if ('owner' not in 选项) or 选项['owner'] is None:#独立事务入口检查取消
        若已中止则抛出(信号)#入口取消
    选择=校验表面区间(会话,起点,终点)#只读校验区间
    入口=扫描压缩入口状态(会话.events)#扫描入口状态
    校验压缩未活动(#耐久锁须空闲
        入口['unmatchedCompactionStart'],#未配对 start
        入口['latestEndSeedSeq'],#最近种子边界
        'compaction',#诊断标签
    )#锁检查结束
    if ('owner' not in 选项) or 选项['owner'] is None:#独立括号
        if 入口['openTurn'] is not None:#已有未结束回合
            raise 手动压缩错误('busy','manual compaction: the session already has an open turn')#手动须在回合之间
        所有者=None#独立
    else:#回合内自动
        if 入口['openTurn'] is None:#没有未结束回合
            raise 基础压缩错误('compactRegion: no open turn — automatic compaction events must be enclosed in a turn')#自动须包在回合内
        所有者=入口['openTurn']#沿用当前回合
    压缩事务标识=压缩标识(str(uuid.uuid4()))#铸造事务 id
    生命周期={#start/end 共用载荷
        'compactionId':压缩事务标识,#事务 id
        'turn':所有者,#所有者
    }#lifecycle 基础
    if 'sourceCommandId' in 选项 and 选项['sourceCommandId'] is not None:#可选命令 id
        生命周期['sourceCommandId']=选项['sourceCommandId']#写入
    开始事件=会话.追加('compaction/start',生命周期)#耐久锁
    if 'stability' in 选项 and 选项['stability']=='whole-surface':#整表面或所选跨度
        校验稳定=校验整表面未变#整表面未变
    else:#只要求所选跨度稳定
        校验稳定=校验所选跨度稳定#所选跨度
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
            选项['sourceCommandId'] if 'sourceCommandId' in 选项 else None,#来源命令
            校验稳定,#稳定检查
            信号,#取消
        )#摘要结束
        if ('owner' not in 选项) or 选项['owner'] is None:#提交前再检查取消
            若已中止则抛出(信号)#取消
        校验稳定(依赖,会话,已摘要)#摘要后稳定检查
        阶段='commit'#进入提交阶段
        待完成=提交压缩正文(会话,开始事件,已摘要)#同步追加 summary 与替换
        正在关闭=True#开始关闭
        结束事件=会话.追加('compaction/end',生命周期)#成功 end
        已关闭=True#已关闭
        结果=完成压缩(待完成,结束事件)#补上 endSeq
    except Exception as 错误:#摘要或提交任意失败仍须尝试关闭锁
        失败={'error':错误,'stage':'commit' if 正在关闭 else 阶段}#记下阶段
        if not 正在关闭:#尚未关闭
            正在关闭=True#尝试关闭
            try:#追加失败 end
                失败生命周期=dict(生命周期)#副本
                失败生命周期['error']=错误链(错误)#带错误链的 end
                会话.追加('compaction/end',失败生命周期)#失败 end
                已关闭=True#已关闭
            except Exception as 关闭错误:#关闭本身失败不得掩盖
                失败={'error':关闭错误,'stage':'commit'}#改记为提交失败
    if 已关闭 and 'flush' in 选项 and 选项['flush'] is not None:#已关闭且要刷盘
        try:#耐久检查点
            选项['flush']().等待()#刷盘
        except Exception as 错误:#刷盘失败不得掩盖事务结果
            刷盘失败=错误#记下，不掩盖事务结果
    if ('owner' not in 选项) or 选项['owner'] is None:#取消仍优先于失败分类
        若已中止则抛出(信号)#取消优先
    if 失败 is not None:#事务失败
        if ('owner' not in 选项) or 选项['owner'] is None:#手动路径分类抛出
            抛手动失败(失败)#分类
        raise 失败['error']#自动路径原样抛
    if 刷盘失败 is not None:#刷盘失败
        raise 手动压缩错误(#映射为 persistence
            'persistence',#持久化码
            'manual compaction durability checkpoint failed',#刷盘失败
            {'cause':刷盘失败},#保留原因
        )#抛出结束
    if 结果 is None:#无结果却走到成功
        raise 基础压缩错误('compaction committed without a result')#无结果
    return 结果#成功结果
