__all__=['协议标注']

协议标注键={#模式标识 → 文案键
    'openai-completions':'protocolOpenAiCompletions',
    'openai-responses':'protocolOpenAiResponses',
    'anthropic-messages':'protocolAnthropicMessages',
}

def 协议标注(翻译,协议):
    """选择器展示产品名；未收录的协议回退为 settings.yaml 标识。"""
    if 协议 not in 协议标注键:
        return 协议
    return 翻译(协议标注键[协议])
