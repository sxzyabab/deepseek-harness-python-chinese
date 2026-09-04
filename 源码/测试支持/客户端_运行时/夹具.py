"""客户端测试运行时的 Controller 与 UI 域 fixture 形状。

对齐上游 `client-runtime/src/fixtures.ts`。公开面仅中文名。
"""
from ...客户端.ui_聊天.客户端.约定.快照 import 空聊天快照#空聊天快照

__all__=[#仅中文公开名
    '会话快照','对话快照','聊天快照','工作区快照','稳定器',
]#公开面结束

#上游 ui-conversation EMPTY_CONVERSATION_SNAPSHOT；包面未导出空常量时内联静止形状
空对话快照={#空对话快照
    'targets':{},#目标名册
    'activeTargetId':None,#无活动目标
}#空对话结束

def 会话快照(会话标识):#静止会话快照
    """一份完整静止的 Session Controller 快照。"""
    return {#返回快照
        'sessionId':会话标识,#会话 id
        'queue':[],#队列
        'pendingSubmissions':[],#待提交
        'running':False,#未运行
        'subagent':None,#无子智能体
        'removed':False,#未移除
        'openState':'open',#已打开
        'openError':None,#无打开错误
        'hasMore':False,#无更旧页
        'loadingOlder':False,#未加载更旧
        'promptError':None,#无提示错误
        'blank':False,#非空白
        'lastAgentError':None,#无智能体错误
        'promptAttempted':False,#未尝试提示
        'awaitingFirstTurn':False,#不等待首轮
    }#静止会话快照

def 对话快照(覆盖=None):#对话快照
    """目标无关的 Conversation 快照。"""
    return {**空对话快照,**(覆盖 or {})}#对话快照

def 聊天快照(覆盖=None):#聊天快照
    """Chat 目标快照。"""
    return {**空聊天快照,**(覆盖 or {})}#聊天快照

def 工作区快照():#空工作区快照
    """无 Workspace 行的就绪 Workspace Controller 快照。"""
    return {#返回快照
        'items':[],#无行
        'archivedSessionIds':[],#无归档
        'state':'idle',#空闲
        'phase':'ready',#就绪
        'error':None,#无错误
    }#空工作区快照

def 稳定器(函数):#默认同步稳定器
    """同步执行变更函数（对齐 act 包装的最小面）。"""
    return 函数()#直接执行

sessionSnapshot=会话快照#上游名
conversationSnapshot=对话快照#上游名
chatSnapshot=聊天快照#上游名
workspaceSnapshot=工作区快照#上游名
