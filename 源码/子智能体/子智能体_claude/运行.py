默认处置宽限毫秒=3000

def 启动claude运行(请求,规格):
    """驱动官方 Claude Agent SDK。Python 侧待 anthropic SDK 绑定。"""
    try:
        import anthropic
    except ImportError as 错误:
        raise Exception('subagent-claude: @anthropic-ai/claude-agent-sdk Python binding is required: '+str(错误))
    raise Exception('subagent-claude: Claude Agent SDK driver is not yet implemented in Python')

__all__=['默认处置宽限毫秒','启动claude运行']
