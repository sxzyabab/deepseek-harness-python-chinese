__all__=['回合过程规格','回合过程独立种类表','回合过程独立种类','同回合过程规格','是子代理委派工具']#仅中文公开名

回合过程独立种类表=(#过程披露外的独立节点种类
    'system-prompt',#系统提示词
    'user',#用户消息
    'steering',#转向消息
    'turn-process',#过程控件
    'turn-error',#轮次错误
    'turn-max-tokens',#达 token 上限
    'turn-tail',#轮次尾部
)#种类列表

回合过程独立种类=frozenset(回合过程独立种类表)#独立种类集合

def 回合过程规格(回合,控件锚,过程起,正文锚,正文步,内联推理,消息数,工具数,子代理数):
    """从一轮推导出的当前过程范围与定稿正文边界。"""
    return {#规格
        'turn':回合,'controlAnchorSeq':控件锚,'processStartSeq':过程起,
        'answerAnchorSeq':正文锚,'answerStep':正文步,'inlineReasoning':内联推理,
        'messageCount':消息数,'toolCallCount':工具数,'subagentCount':子代理数,
    }#结束

def 同回合过程规格(左,右):
    """按已发布字段比较不可变的轮次过程规格。规格为 dict。"""
    if 左 is None or 右 is None:#任一侧缺
        return 左 is 右#同缺或同在
    return (#字段全等
        (左['turn'] if 'turn' in 左 else None)==(右['turn'] if 'turn' in 右 else None)#轮次
        and (左['controlAnchorSeq'] if 'controlAnchorSeq' in 左 else None)==(右['controlAnchorSeq'] if 'controlAnchorSeq' in 右 else None)#控件锚点
        and (左['processStartSeq'] if 'processStartSeq' in 左 else None)==(右['processStartSeq'] if 'processStartSeq' in 右 else None)#过程起点
        and (左['answerAnchorSeq'] if 'answerAnchorSeq' in 左 else None)==(右['answerAnchorSeq'] if 'answerAnchorSeq' in 右 else None)#正文锚点
        and (左['answerStep'] if 'answerStep' in 左 else None)==(右['answerStep'] if 'answerStep' in 右 else None)#正文步骤
        and (左['inlineReasoning'] if 'inlineReasoning' in 左 else None)==(右['inlineReasoning'] if 'inlineReasoning' in 右 else None)#内联推理
        and (左['messageCount'] if 'messageCount' in 左 else None)==(右['messageCount'] if 'messageCount' in 右 else None)#消息计数
        and (左['toolCallCount'] if 'toolCallCount' in 左 else None)==(右['toolCallCount'] if 'toolCallCount' in 右 else None)#工具计数
        and (左['subagentCount'] if 'subagentCount' in 左 else None)==(右['subagentCount'] if 'subagentCount' in 右 else None)#subagent 计数
    )#结束

def 是子代理委派工具(名称):
    """识别出厂 subagent 委派名及其配置变体。"""
    return 名称=='subagent' or 名称.startswith('subagent_')#精确或前缀
