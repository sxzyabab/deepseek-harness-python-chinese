默认处置宽限毫秒=3000

def 启动codex运行(请求,规格):
    """驱动 @openai/codex app-server。Python 侧待官方包绑定。"""
    try:
        import openai
    except ImportError as 错误:
        raise Exception('subagent-codex: @openai/codex Python package is required: '+str(错误))
    raise Exception('subagent-codex: Codex app-server wire driver is not yet implemented in Python')

__all__=['默认处置宽限毫秒','启动codex运行']
