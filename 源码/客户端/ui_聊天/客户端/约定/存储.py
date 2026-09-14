__all__=['工具调用标识','选中目标','回合过程视图条目','聊天存储状态']#仅中文公开名

工具调用标识=str#工具调用 id 别名

def 选中目标(回合序号,步骤序号=None,调用标识值=None,工具名=None):#选中目标工厂
    """Chat 详情联动通道的选中目标。"""
    return {'turnSeq':回合序号,'stepSeq':步骤序号,'callId':调用标识值,'toolName':工具名}#目标

def 回合过程视图条目(回合,正文步):#过程展开条目
    """一轮手动展开的 Turn 正文 generation。"""
    return {'turn':回合,'answerStep':正文步}#条目

初始聊天状态={'selection':None,'turnProcesses':[]}#初始无选中、无展开

聊天存储状态=dict#Chat 存储状态别名
