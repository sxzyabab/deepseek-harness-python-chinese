"""Chat 业务 Definition 产出的最终 Chat 渲染单元与载荷。

对齐上游 `ui-chat/src/client/contract/chat-nodes.ts`。公开面仅中文名。
"""

__all__=[#仅中文公开名
    '聊天会话视图节点','聊天节点数据表','助手聊天数据','工具聊天数据',
    '手动压缩聊天数据','重试聊天数据','回合令牌用量路由','回合令牌用量',
    '回合尾聊天数据','回合过程聊天数据','是已结算工具','是运行中工具',
    '已结算工具','运行中工具',
]#公开面结束

聊天节点数据表={}#按 renderer 种类键控的载荷注册表

def 聊天会话视图节点(锚点序号,位置,可见性='visible',种类=None,数据=None):#视图节点工厂
    """最终 Chat 渲染单元。"""
    节点={'target':'chat','anchorSeq':锚点序号,'location':位置,'visibility':可见性}#骨架
    if 种类 is not None:#有种类
        节点['kind']=种类#挂
    if 数据 is not None:#有载荷
        节点['data']=数据#挂
    return 节点#节点

def 助手聊天数据(状态,回合,步骤,块们,时间,用量=None,最终节点=None):#Assistant 行数据
    """流式与已落定态共用。"""
    数据={'status':状态,'turn':回合,'step':步骤,'blocks':块们,'time':时间}#基
    if 用量 is not None:#有用量
        数据['usage']=用量#挂
    if 最终节点 is not None:#有持久
        数据['finalNode']=最终节点#挂
    return 数据#载荷

def 工具聊天数据(根):#工具行数据
    """根生命周期拥有全部递归子调用。"""
    return {'root':根}#载荷

def 手动压缩聊天数据(命令,压缩=None):#手动压缩行数据
    """一条手动命令及其相关压缩事务。"""
    return {'command':命令,'compaction':压缩}#载荷

def 重试聊天数据(尝试们,当前):#重试行数据
    """一条持久重试链。"""
    return {'attempts':尝试们,'current':当前}#载荷

def 回合令牌用量路由(提供方,模型):#用量路由
    """贡献了计费请求尝试的一条提供方/模型路由。"""
    return {'provider':提供方,'model':模型}#路由

def 回合令牌用量(未缓存输入,输出,总量,缓存读=None,缓存写=None,推理=None,路由们=None):#轮次 token 用量
    """已完成一轮中每次尝试的精确提供方 token 记账。"""
    数据={'uncachedInputTokens':未缓存输入,'outputTokens':输出,'totalTokens':总量}#基
    if 缓存读 is not None:#有
        数据['cacheReadTokens']=缓存读#挂
    if 缓存写 is not None:#有
        数据['cacheWriteTokens']=缓存写#挂
    if 推理 is not None:#有
        数据['reasoningTokens']=推理#挂
    if 路由们 is not None:#有
        数据['routes']=路由们#挂
    return 数据#用量

def 回合尾聊天数据(回合,序号,时间,收尾=None,分支不可用=False,ttftMs=None,tokensPerSecond=None,tokenUsage=None):#轮次尾部
    """轮次局部页脚行。"""
    数据={'turn':回合,'seq':序号,'time':时间,'closing':收尾,'branchUnavailable':分支不可用}#基
    if ttftMs is not None:#有
        数据['ttftMs']=ttftMs#挂
    if tokensPerSecond is not None:#有
        数据['tokensPerSecond']=tokensPerSecond#挂
    if tokenUsage is not None:#有
        数据['tokenUsage']=tokenUsage#挂
    return 数据#载荷

def 回合过程聊天数据(回合,控件锚,过程起,正文锚,正文步,内联推理,消息数,工具数,子代理数):#轮次过程
    """定稿正文之前投影的轮级过程披露。"""
    return {#载荷
        'turn':回合,'controlAnchorSeq':控件锚,'processStartSeq':过程起,
        'answerAnchorSeq':正文锚,'answerStep':正文步,'inlineReasoning':内联推理,
        'messageCount':消息数,'toolCallCount':工具数,'subagentCount':子代理数,
    }#结束

def 是已结算工具(块):#是否已落定工具
    """根是否携带最终结果。"""
    if isinstance(块,dict):#映射
        return 'kind' in 块#有 kind 即结果态
    return hasattr(块,'kind')#属性

def 是运行中工具(块):#是否运行中工具
    """根是否尚无最终结果。"""
    return not 是已结算工具(块)#非落定即运行中

已结算工具=是已结算工具#别名
运行中工具=是运行中工具#别名
