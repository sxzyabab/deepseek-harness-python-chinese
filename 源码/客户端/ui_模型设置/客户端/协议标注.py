from .文案 import 中文

__all__=['协议标注']

协议标注键={
    'openai-completions':'protocolOpenAiCompletions',
    'openai-responses':'protocolOpenAiResponses',
    'anthropic-messages':'protocolAnthropicMessages',
}

def 协议标注(协议):
    '选择器上的协议产品名。页面没命名的协议仍显示 settings.yaml 里的标识'
    键=协议标注键.get(协议)
    if 键 is None:
        return 协议
    return 中文[键]
