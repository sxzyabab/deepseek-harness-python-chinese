"""从一轮推导出的当前过程范围与定稿正文边界。

对齐上游 `ui-chat/src/client/contract/turn-process.ts`。公开面仅中文名。
"""

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

def 回合过程规格(回合,控件锚,过程起,正文锚,正文步,内联推理,消息数,工具数,子代理数):#过程规格工厂
    """从一轮推导出的当前过程范围与定稿正文边界。"""
    return {#规格
        'turn':回合,'controlAnchorSeq':控件锚,'processStartSeq':过程起,
        'answerAnchorSeq':正文锚,'answerStep':正文步,'inlineReasoning':内联推理,
        'messageCount':消息数,'toolCallCount':工具数,'subagentCount':子代理数,
    }#结束

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 同回合过程规格(左,右):#规格相等判定
    """按已发布字段比较不可变的轮次过程规格。"""
    return (#字段全等
        取字段(左,'turn')==取字段(右,'turn')#轮次
        and 取字段(左,'controlAnchorSeq')==取字段(右,'controlAnchorSeq')#控件锚点
        and 取字段(左,'processStartSeq')==取字段(右,'processStartSeq')#过程起点
        and 取字段(左,'answerAnchorSeq')==取字段(右,'answerAnchorSeq')#正文锚点
        and 取字段(左,'answerStep')==取字段(右,'answerStep')#正文步骤
        and 取字段(左,'inlineReasoning')==取字段(右,'inlineReasoning')#内联推理
        and 取字段(左,'messageCount')==取字段(右,'messageCount')#消息计数
        and 取字段(左,'toolCallCount')==取字段(右,'toolCallCount')#工具计数
        and 取字段(左,'subagentCount')==取字段(右,'subagentCount')#subagent 计数
    )#结束

def 是子代理委派工具(名称):#是否 subagent 委派工具
    """识别出厂 subagent 委派名及其配置变体。"""
    return 名称=='subagent' or 名称.startswith('subagent_')#精确或前缀
