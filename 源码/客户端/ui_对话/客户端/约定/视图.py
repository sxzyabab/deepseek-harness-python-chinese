__all__=['调用标识','选中目标','视图页签','聊天存储状态','初始聊天状态']#仅中文公开名

调用标识=str#线上携带的工具调用身份

def 初始聊天状态():#每会话共享 store 初值
    """无选定、空草稿、无视图、无检视。"""
    return {'selection':None,'draft':'','view':None,'inspect':None}#初值

#选中目标：turnSeq 必填；stepSeq/callId/toolName 可选
#视图页签：id + label
#聊天存储状态：selection/draft/view/inspect
选中目标=dict#详情联动选中目标形
视图页签=dict#会话视图页签形
聊天存储状态=dict#每会话共享 store 状态形
