"""把 harness 消息序列化成 DeepSeek 对话补全。

对齐上游 `llm-deepseek/src/serialize.ts`。公开面仅中文名；无英文别名。
"""
from ..llm import 内容含图片,大模型错误#图片检测与LLM错误

__all__=('校验推理力度','解析思考','序列化助手','序列化消息','序列化请求')#仅中文公开名

def 校验推理力度(力度):#校验适配器拥有的力度
    """在解析其深求线路字段之前校验适配器拥有的力度。"""
    if 力度=='off' or 力度=='high' or 力度=='max':#合法力度
        return 力度#合法力度
    文案='DeepSeek does not support reasoning effort "'+str(力度)+'"'#不支持文案（诊断字面量）
    raise 大模型错误(文案,'UNSUPPORTED_REASONING_EFFORT')#不支持的力度

def 解析思考(选项,默认):#解析思考/力度
    """解析一对合法的思考/力度，不把 off 暴露成线路力度。"""
    if 选项.get('purpose')=='session-title':#标题任务
        return {'thinking':'disabled'}#标题任务关掉思考
    if 选项.get('reasoningEffort') is None:#未给力度
        力度=默认.get('reasoningEffort')#用适配器默认
    else:#调用方力度
        力度=校验推理力度(选项['reasoningEffort'])#校验调用方力度
    if 默认.get('thinking')=='disabled' and 力度 is not None and 力度!='off':#部署关掉思考却请求了力度
        文案='DeepSeek deployment does not support reasoning effort "'+str(力度)+'"'#部署不支持文案（诊断字面量）
        raise 大模型错误(文案,'UNSUPPORTED_REASONING_EFFORT')#部署关掉思考却请求了力度
    if 力度=='off':#off
        return {'thinking':'disabled'}#off映射为关掉思考
    if 力度=='high' or 力度=='max':#打开思考
        return {'thinking':'enabled','reasoningEffort':力度}#打开思考并带线路力度
    if 默认.get('thinking') is None:#无默认开关
        return {}#不放到线路上
    return {'thinking':默认['thinking']}#只带适配器思考开关

def 拼文本(块列表):
    """拼接一条消息的文本块。"""
    文本=''#累积
    for 块 in 块列表:#逐块
        if 块.get('type')=='text':#文本块
            文本+=块.get('text') or ''#只要文本
    return 文本#拼接结果

def 断言纯文本(块列表):
    """在任何文本压平路径能静默抹掉图片之前拒绝核心图片内容。"""
    if 内容含图片(块列表):#含图片
        raise 大模型错误('The DeepSeek chat-completions adapter does not support image content.','UNSUPPORTED_CONTENT')#不支持图片

def 序列化助手(消息):
    """序列化一条助手消息（文本、推理、工具调用）。"""
    文本=拼文本(消息['content'])#可见文本
    推理=''#推理累积
    for 块 in 消息['content']:#逐块
        if 块.get('type')=='reasoning':#推理
            推理+=块.get('text') or ''#取出推理文本
    工具调用=[]#线路调用
    for 块 in 消息['content']:#逐块
        if 块.get('type')=='tool-call':#工具调用
            工具调用.append({
                'id':块['id'],#调用id
                'type':'function',#函数类型
                'function':{'name':块['name'],'arguments':块['arguments']},#名字与参数
            })#一条线路调用
    线路={'role':'assistant','content':文本}#可见文本可为空串，绝不用null
    if len(工具调用)>0 and len(推理)>0:#工具调用回合带回传
        线路['reasoning_content']=推理#仅工具调用回合带回传
    if len(工具调用)>0:#有调用
        线路['tool_calls']=工具调用#有调用才带上
    return 线路#线路助手消息

def 序列化消息(消息列表):
    """序列化对话。tool-result块变成独立的role:tool消息。"""
    线路=[]#线路消息
    for 消息 in 消息列表:#逐条
        断言纯文本(消息['content'])#拒绝图片
        if 消息['role']=='system':#系统
            线路.append({'role':'system','content':拼文本(消息['content'])})#系统文本
            continue#下一条
        if 消息['role']=='assistant':#助手
            线路.append(序列化助手(消息))#序列化助手
            continue#下一条
        工具结果=[]#工具结果块
        for 块 in 消息['content']:#逐块
            if 块.get('type')=='tool-result':#工具结果
                工具结果.append(块)#收集
        文本=拼文本(消息['content'])#用户文本
        if len(文本)>0 or len(工具结果)==0:#有文本或没有结果
            线路.append({'role':'user','content':文本})#先发用户文本
        for 结果 in 工具结果:#独立工具消息
            内容=拼文本(结果.get('content') or [])#结果文本
            线路.append({
                'role':'tool',#工具角色
                'tool_call_id':结果['toolCallId'],#调用id
                'content':内容 if 内容 else '(no output)',#空输出用占位
            })#独立工具消息
    return 线路#线路消息

def 序列化请求(选项,默认=None):
    """构造完整线路请求。始终流式并打开用量报告；可选字段省略而不是发null。"""
    if 默认 is None:#未传默认
        默认={}#适配器默认
    消息=[]#线路消息
    if 选项.get('system') is not None:#有系统
        消息.append({'role':'system','content':选项['system']})#先发系统
    消息.extend(序列化消息(选项['messages']))#再发对话
    工具=None#可选工具
    if 选项.get('tools') is not None:#有工具
        工具=[]#映射工具
        for 项 in 选项['tools']:#逐条
            工具.append({
                'type':'function',#函数类型
                'function':{
                    'name':项['name'],#工具名
                    'description':项['description'],#说明
                    'parameters':项['parameters'],#JSON Schema
                },#函数描述
            })#一条线路工具
    已解析思考=解析思考(选项,默认)#解析思考字段
    请求={
        'model':选项['model'],#模型
        'messages':消息,#消息
        'stream':True,#始终流式
        'stream_options':{'include_usage':True},#始终要用量
    }#线路请求
    if 已解析思考.get('thinking') is not None:#有开关
        请求['thinking']={'type':已解析思考['thinking']}#有开关才带上
    if 已解析思考.get('reasoningEffort') is not None:#有力度
        请求['reasoning_effort']=已解析思考['reasoningEffort']#带线路力度
    if 工具 is not None and len(工具)>0:#有工具
        请求['tools']=工具#有工具才带上
    if 选项.get('temperature') is not None:#有温度
        请求['temperature']=选项['temperature']#有温度才带上
    if 选项.get('maxTokens') is not None:#有上限
        请求['max_tokens']=选项['maxTokens']#有上限才带上
    if 选项.get('stop') is not None:#有停止序列
        请求['stop']=选项['stop']#有停止序列才带上
    return 请求#对话补全请求体
