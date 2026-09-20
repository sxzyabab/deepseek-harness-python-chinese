"""把 harness 消息序列化成 DeepSeek 对话补全。"""
import base64#内联图编码
from ....llm import (
    内容含图片,#图片检测
    大模型错误,#LLM错误
    投影卸载图片,#卸载投影
    卸载图片文案,#卸载占位
    请求图片句柄文案,#句柄文案
    必需图片卸载,#预算卸载
    图片卸载必需码,#卸载码
)#llm 词表

__all__=('校验推理力度','解析思考','序列化助手','序列化消息','序列化带图消息','序列化请求','序列化带图请求')#仅中文公开名

工具结果图文案='Attached image(s) from tool result:'#工具结果图引导

def 校验推理力度(力度):#校验适配器拥有的力度
    """在解析其深求线路字段之前校验适配器拥有的力度。"""
    if 力度=='off' or 力度=='low' or 力度=='high' or 力度=='max':#合法力度
        return 力度#合法力度
    文案='DeepSeek does not support reasoning effort "'+str(力度)+'"'#不支持文案
    raise 大模型错误(文案,'UNSUPPORTED_REASONING_EFFORT')#不支持的力度

def 解析思考(选项,默认):#解析思考/力度
    """解析一对合法的思考/力度，不把 off 暴露成线路力度。"""
    if 选项.get('purpose')=='session-title':#标题任务
        return {'thinking':'disabled'}#标题任务关掉思考
    if 'reasoningEffort' not in 选项:#未给力度
        力度=默认.get('reasoningEffort')#用适配器默认
    else:#调用方力度
        力度=校验推理力度(选项['reasoningEffort'])#校验调用方力度
    if 默认.get('thinking')=='disabled' and 力度 is not None and 力度!='off':#部署关掉思考却请求了力度
        文案='DeepSeek deployment does not support reasoning effort "'+str(力度)+'"'#部署不支持文案
        raise 大模型错误(文案,'UNSUPPORTED_REASONING_EFFORT')#部署关掉思考却请求了力度
    if 力度=='off':#off
        return {'thinking':'disabled'}#off映射为关掉思考
    if 力度=='low' or 力度=='high' or 力度=='max':#打开思考
        return {'thinking':'enabled','reasoningEffort':力度}#打开思考并带线路力度
    if 'thinking' not in 默认:#无默认开关
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

def 断言支持图角色(消息列表):
    """拒绝无法承载图片输入的角色。"""
    for 消息 in 消息列表:#逐条
        if 消息.get('role')!='user' and 内容含图片(消息.get('content') or []):#非用户却含图
            raise 大模型错误('The DeepSeek chat-completions adapter cannot represent image content in a '+str(消息.get('role'))+' message.','UNSUPPORTED_CONTENT')#角色不支持

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
    if len(推理)>0:#有推理
        线路['reasoning_content']=推理#思考回传
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

def 图片部件(块,图片,位置,已有内容):
    """解析一张耐久图的描述与瞬时线路部件。"""
    版本=图片['requestImages'].get(块['attachment']['attachmentId'])#请求版本
    if 版本 is None:#未准备
        raise 大模型错误('DeepSeek request image '+str(块['attachment']['attachmentId'])+' was not prepared.','INVALID_REQUEST')#未准备
    表示=图片['representation']#表示
    if 表示['kind']=='file':#文件 id
        图={'type':'file','file_id':表示['resolveFileId'](版本,块,位置)}#文件部件
    else:#内联
        数据=版本['data']#原始字节
        if not isinstance(数据,bytes):#非字节
            数据=bytes(数据)#转字节
        图={'type':'image_url','image_url':{'url':'data:'+版本['mediaType']+';base64,'+base64.b64encode(数据).decode('ascii')}}#内联
    解析访问=图片.get('resolveImageAccess')#可选访问
    访问=解析访问(块['attachment']) if 解析访问 is not None else None#当前访问
    前缀='\n' if 已有内容 else ''#前导换行
    句柄={'type':'text','text':前缀+请求图片句柄文案(块['attachment'],版本,访问)}#句柄文本
    return 句柄,图#描述与图

def 内容部件(块列表,图片,消息号,下一图):
    """把用户或嵌套工具结果块转成有序线路部件。"""
    部件=[]#部件表
    for 块 in 块列表:#逐块
        种类=块.get('type')#种类
        if 种类=='text':#文本
            文本=块.get('text') or ''#文本
            if len(文本)>0:#非空
                部件.append({'type':'text','text':文本})#文本部件
        elif 种类=='image':#图片
            下一图['value']+=1#出现序号
            句柄,图=图片部件(块,图片,{'message':消息号,'image':下一图['value']},len(部件)>0)#解析
            部件.append(句柄)#句柄
            部件.append(图)#图
        elif 种类=='tool-result':#嵌套
            部件.extend(内容部件(块.get('content') or [],图片,消息号,下一图))#递归
    return 部件#部件

def 用户内容(部件):
    """纯文本用户消息压成字符串。"""
    文本=[]#文本段
    for 件 in 部件:#逐件
        if 件.get('type')!='text':#含非文本
            return list(部件)#多模态
        文本.append(件['text'])#文本
    return ''.join(文本)#压平

def 序列化带图消息(消息列表,图片):
    """解析耐久附件后序列化可带图历史。"""
    断言支持图角色(消息列表)#角色
    线路=[]#线路消息
    待发工具图=[]#待冲刷工具图
    def 冲刷工具图():#冲刷
        """把连续工具结果图收成一条用户消息。"""
        nonlocal 待发工具图#待发
        if len(待发工具图)==0:#无
            return#空
        线路.append({'role':'user','content':[{'type':'text','text':工具结果图文案}]+待发工具图})#引导加图
        待发工具图=[]#清空
    for 消息下标,消息 in enumerate(消息列表):#逐条
        下一图={'value':0}#本消息图序号
        if 消息['role']=='system':#系统
            冲刷工具图()#先冲刷
            线路.append({'role':'system','content':拼文本(消息['content'])})#系统
            continue#下一条
        if 消息['role']=='assistant':#助手
            冲刷工具图()#先冲刷
            线路.append(序列化助手(消息))#助手
            continue#下一条
        常规=[]#非工具结果
        工具结果=[]#工具结果
        for 块 in 消息['content']:#逐块
            if 块.get('type')=='tool-result':#工具结果
                工具结果.append(块)#收集
            else:#常规
                常规.append(块)#收集
        内容=用户内容(内容部件(常规,图片,消息下标+1,下一图))#用户内容
        if (isinstance(内容,str) and len(内容)>0) or (not isinstance(内容,str) and len(内容)>0) or len(工具结果)==0:#有内容或无工具
            冲刷工具图()#先冲刷
            线路.append({'role':'user','content':内容})#用户
        for 结果 in 工具结果:#工具结果
            部件=内容部件(结果.get('content') or [],图片,消息下标+1,下一图)#结果部件
            图件=[件 for 件 in 部件 if 件.get('type')!='text']#图
            文本=''.join(件['text'] for 件 in 部件 if 件.get('type')=='text')#文本
            线路.append({
                'role':'tool',#工具角色
                'tool_call_id':结果['toolCallId'],#调用id
                'content':文本 if 文本 else '(no output)',#空输出占位
            })#工具消息
            待发工具图.extend(图件)#记下图
    冲刷工具图()#收尾
    return 线路#线路消息

def 带消息请求(选项,消息,默认):
    """组装文本与带图路径共用的请求字段。"""
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

def 序列化请求(选项,默认=None):
    """构造完整线路请求。始终流式并打开用量报告；可选字段省略而不是发null。"""
    if 默认 is None:#未传默认
        默认={}#适配器默认
    消息=[]#线路消息
    if 选项.get('system') is not None:#有系统
        消息.append({'role':'system','content':选项['system']})#先发系统
    消息.extend(序列化消息(选项['messages']))#再发对话
    return 带消息请求(选项,消息,默认)#共用字段

def 断言保留图可放下(消息列表,图片):
    """保留出现在精确表示字节下仍超预算则拒绝。"""
    表示='raw' if 图片['representation']['kind']=='file' else 'base64'#表示
    def 版本字节(块):#精确字节
        """取已准备请求版本字节。"""
        版本=图片['requestImages'].get(块['attachment']['attachmentId'])#版本
        if 版本 is None:#未准备
            raise 大模型错误('DeepSeek request image '+str(块['attachment']['attachmentId'])+' was not prepared.','INVALID_REQUEST')#未准备
        return 版本['bytes']#字节
    政策={'representation':表示,'maxBytes':图片['maxRequestImageBytes']}#预算
    if 图片.get('maxImagesPerRequest') is not None:#张数
        政策['maxImages']=图片['maxImagesPerRequest']#张数
    if 图片.get('byteQuantum') is not None:#字节量子
        政策['byteQuantum']=图片['byteQuantum']#字节量子
    if 图片.get('countQuantum') is not None:#张数量子
        政策['countQuantum']=图片['countQuantum']#张数量子
    卸载=必需图片卸载(消息列表,政策,版本字节)#还需卸载
    if 卸载>0:#超预算
        raise 大模型错误(
            'DeepSeek '+表示+' request images exceed the route budget; '+str(卸载)+' more oldest occurrence(s) must be offloaded.',
            图片卸载必需码,
            {'offloadImages':卸载},
        )#卸载必需

def 序列化带图请求(选项,图片,默认=None):
    """构造可带图请求；已卸载出现变成占位文本。"""
    if 默认 is None:#未传默认
        默认={}#适配器默认
    断言支持图角色(选项['messages'])#角色
    断言保留图可放下(选项['messages'],图片)#预算
    解析访问=图片.get('resolveImageAccess')#可选访问
    def 占位(引用):#卸载占位
        """按路由拥有的访问解析占位文案。"""
        访问=解析访问(引用) if 解析访问 is not None else None#访问
        return 卸载图片文案(引用,访问)#占位
    请求消息=投影卸载图片(选项['messages'],占位)#投影
    消息=[]#线路消息
    if 选项.get('system') is not None:#有系统
        消息.append({'role':'system','content':选项['system']})#先发系统
    消息.extend(序列化带图消息(请求消息,图片))#带图历史
    return 带消息请求(选项,消息,默认)#共用字段
