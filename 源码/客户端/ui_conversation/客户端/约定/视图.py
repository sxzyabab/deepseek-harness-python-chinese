"""共享的会话视图、选中目标与 store 状态约定。

对齐上游 `ui-conversation/src/client/contract/views.ts`。公开面仅中文名。
"""

__all__=['调用标识','选中目标','视图页签','聊天仓库状态','初始聊天状态']#仅中文公开名

调用标识=str#线上携带的工具调用身份

def 初始聊天状态():#每会话共享 store 初值
    """无选定、空草稿、无视图、无检视。"""
    return {'selection':None,'draft':'','view':None,'inspect':None}#初值

#选中目标：turnSeq 必填；stepSeq/callId/toolName 可选
#视图页签：id + label
#聊天仓库状态：selection/draft/view/inspect
选中目标=dict#详情联动选中目标形
视图页签=dict#会话视图页签形
聊天仓库状态=dict#每会话共享 store 状态形
