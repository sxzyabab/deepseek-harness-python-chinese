"""Chat 拥有的选中状态，transcript 与详情面板共用。

对齐上游 `ui-chat/src/client/contract/store.ts`。公开面仅中文名。
"""

__all__=['工具调用标识','选中目标','回合过程视图条目','聊天仓库状态']#仅中文公开名

工具调用标识=str#工具调用 id 别名

def 选中目标(turnSeq,stepSeq=None,callId=None,toolName=None):#选中目标工厂
    """Chat 详情联动通道的选中目标。"""
    return {'turnSeq':turnSeq,'stepSeq':stepSeq,'callId':callId,'toolName':toolName}#目标

def 回合过程视图条目(turn,answerStep):#过程展开条目
    """一轮手动展开的 Turn 正文 generation。"""
    return {'turn':turn,'answerStep':answerStep}#条目

初始聊天状态={'selection':None,'turnProcesses':[]}#初始无选中、无展开

聊天仓库状态=dict#Chat store 状态别名
