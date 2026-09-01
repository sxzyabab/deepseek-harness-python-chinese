"""Claude Code 一次性生命周期（对齐 upstream subagent-claude-code/run.ts 骨架）。"""
import uuid#子 id
from ...内核.会话 import 会话标识#品牌
默认处置宽限毫秒=3000#宽限

def 启动claude跑(请求,规格):#startClaudeRun 骨架
    """驱动官方 Claude Agent SDK。Python 侧待 anthropic SDK 绑定。"""
    try:
        import anthropic#占位
    except ImportError as 错误:
        raise Exception('subagent-claude: @anthropic-ai/claude-agent-sdk Python binding is required: '+str(错误))#阻塞
    子标识=会话标识(str(uuid.uuid4()))#子 id
    raise Exception('subagent-claude: Claude Agent SDK driver is not yet implemented in Python')#待实现

__all__=['默认处置宽限毫秒','启动claude跑']#公开面
