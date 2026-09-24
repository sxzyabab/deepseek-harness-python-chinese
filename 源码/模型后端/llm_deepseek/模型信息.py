"""与协议无关的模型能力与推理力度。"""
from ..llm.标识构造 import 推理力度标识

__all__=['目录模型信息','模型信息']

关闭力度=推理力度标识('off')
低力度=推理力度标识('low')
高力度=推理力度标识('high')
最大力度=推理力度标识('max')
推理力度表=(
    {'id':关闭力度,'name':'Off','description':'用于不需要推理的简单任务。'},
    {'id':低力度,'name':'Low','description':'适合常规或对延迟敏感的任务。'},
    {'id':高力度,'name':'High','description':'大多数任务的默认平衡。'},
    {'id':最大力度,'name':'Max','description':'留给最难的质量优先任务。'},
)
仅关闭力度表=(
    {'id':关闭力度,'name':'Off','description':'用于不需要推理的简单任务。'},
)

def 目录模型信息(提供方,模型):
    """通告一条目录条目。"""
    条目={
        'provider':提供方,
        'id':模型['id'],
        'name':模型['name'] if 'name' in 模型 and 模型['name'] is not None else 模型['id'],
        'inputModalities':模型['inputModalities'] if 'inputModalities' in 模型 and 模型['inputModalities'] is not None else ['text'],
    }
    if 'description' in 模型 and 模型['description'] is not None:
        条目['description']=模型['description']
    return 条目

def 模型信息(连接,提供方,模型):
    """按一代配置解析模型能力。"""
    已配=None
    for 条目 in 连接['models']:
        if 条目['id']==模型:
            已配=条目
            break
    窗口=已配['contextWindow'] if 已配 is not None and 'contextWindow' in 已配 and 已配['contextWindow'] is not None else 连接['defaultContextWindow']
    if 已配 is None:
        基础={'provider':提供方,'id':模型,'name':模型,'inputModalities':['text']}
    else:
        基础=目录模型信息(提供方,已配)
    结果=dict(基础)
    结果['context']={'contextWindow':窗口}
    结果['defaultMaxTokens']=已配['maxTokens'] if 已配 is not None and 'maxTokens' in 已配 and 已配['maxTokens'] is not None else 连接['maxTokens']
    if 已配 is not None and 'systemPromptUpdate' in 已配 and 已配['systemPromptUpdate'] is not None:
        结果['systemPromptUpdate']=已配['systemPromptUpdate']
    默认=连接['defaults']
    if 默认.get('thinking')=='disabled':
        结果['reasoning']={'efforts':list(仅关闭力度表),'defaultEffort':关闭力度}
        return 结果
    力度=默认.get('reasoningEffort')
    if 力度=='off':
        默认力度=关闭力度
    elif 力度=='low':
        默认力度=低力度
    elif 力度=='max':
        默认力度=最大力度
    else:
        默认力度=高力度
    结果['reasoning']={'efforts':list(推理力度表),'defaultEffort':默认力度}
    return 结果
