"""与协议无关的模型能力与推理档位。"""
from ...llm import 推理力度标识#力度品牌

__all__=('目录模型信息','模型信息')#仅中文公开名

关闭力度=推理力度标识('off')#关闭力度
低力度=推理力度标识('low')#低力度
高度力度=推理力度标识('high')#高力度
最大力度=推理力度标识('max')#最大力度
完整力度列表=[
    {'id':关闭力度,'name':'Off','description':'Use for simple tasks that do not need reasoning.'},#关闭
    {'id':低力度,'name':'Low','description':'Prefer for routine or latency-sensitive tasks.'},#低
    {'id':高度力度,'name':'High','description':'The default balance for most tasks.'},#高
    {'id':最大力度,'name':'Max','description':'Reserve for the hardest quality-first tasks.'},#最大
]#完整力度
仅关闭力度列表=[
    {'id':关闭力度,'name':'Off','description':'Use for simple tasks that do not need reasoning.'},#关闭
]#仅关闭

def 目录模型信息(提供方,模型):#目录条目转展示信息
    """通告一条目录条目。模型为目录 dict。"""
    if 'name' in 模型 and 模型['name'] is not None:#??：显式空串仍用空串，缺席才落到 id
        名称=模型['name']#展示名
    else:#缺席
        名称=模型['id']#展示名或id
    信息={
        'provider':提供方,#提供方
        'id':模型['id'],#模型id
        'name':名称,#展示名或id
        'inputModalities':模型['inputModalities'] if 'inputModalities' in 模型 and 模型['inputModalities'] is not None else ['text'],#缺席当纯文本
    }#拆离信息
    if 'description' in 模型 and 模型['description'] is not None:#有描述
        信息['description']=模型['description']#有描述才带上
    return 信息#模型信息

def 模型信息(连接,提供方,模型):#相对一代配置解析能力
    """相对一代已校验连接事实解析模型能力。"""
    条目=None#目录条目
    for 项 in 连接['models']:#逐条
        if 项['id']==模型:#命中
            条目=项#命中目录
            break#找到即停
    if 条目 is not None and 'contextWindow' in 条目 and 条目['contextWindow'] is not None:#条目有窗口
        窗口=条目['contextWindow']#条目窗口
    else:#回落默认
        窗口=连接['defaultContextWindow']#默认窗口
    if 条目 is None:#未编目
        信息={'provider':提供方,'id':模型,'name':模型,'inputModalities':['text']}#未编目仍声明纯文本
    else:#有目录
        信息=目录模型信息(提供方,条目)#目录条目
    信息['context']={'contextWindow':窗口}#窗口
    if 条目 is not None and 'maxTokens' in 条目 and 条目['maxTokens'] is not None:#条目上限
        信息['defaultMaxTokens']=条目['maxTokens']#条目上限
    else:#配置上限
        信息['defaultMaxTokens']=连接['maxTokens']#配置上限
    if 条目 is not None and 'systemPromptUpdate' in 条目 and 条目['systemPromptUpdate'] is not None:#有更新模式
        信息['systemPromptUpdate']=条目['systemPromptUpdate']#有更新模式才带上
    默认表=连接['defaults']#部署默认 dict
    if 'thinking' in 默认表 and 默认表['thinking']=='disabled':#部署关掉思考
        信息['reasoning']={
            'efforts':仅关闭力度列表,#只有off
            'defaultEffort':关闭力度,#默认关闭
        }#仅关闭力度
    else:#完整力度
        默认力度配置=默认表['reasoningEffort'] if 'reasoningEffort' in 默认表 else None#配置力度
        if 默认力度配置=='off':#关闭
            默认力度=关闭力度#关闭
        elif 默认力度配置=='low':#低
            默认力度=低力度#低
        elif 默认力度配置=='max':#最大
            默认力度=最大力度#最大
        else:#其余默认high
            默认力度=高度力度#其余默认high
        信息['reasoning']={
            'efforts':完整力度列表,#off/low/high/max
            'defaultEffort':默认力度,#默认力度
        }#完整力度
    return 信息#已解析信息
