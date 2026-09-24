"""按配置路由能力把系统快照与对话轮次映射到 Messages。"""
import json,base64
from ..llm import 大模型错误,请求图片句柄文案
from .回放 import 读回放

__all__=['序列化']

def 不支持(类型):
    """无法表示的内容。"""
    raise 大模型错误('DeepSeek Messages cannot represent '+类型,'UNSUPPORTED_CONTENT')

def 工具输入(原始):
    """Messages 无法表示的历史参数用空对象；耐久内容不变。"""
    try:
        值=json.loads(原始)
    except Exception:
        return {}
    if isinstance(值,dict):
        return 值
    return {}

def 助手(消息,模型,回放降级=None):
    """助手块转线路块。"""
    回放=读回放(消息,模型,回放降级)
    结果=[]
    下标=0
    for 块 in 消息['content']:
        种类=块['type']
        if 种类=='text':
            结果.append({'type':'text','text':块['text']})
        elif 种类=='reasoning':
            条目={'type':'thinking','thinking':块['text']}
            签名=None
            if 回放 is not None and 下标<len(回放):
                签名=回放[下标].get('signature')
            if 签名 is not None:
                条目['signature']=签名
            结果.append(条目)
        elif 种类=='tool-call':
            结果.append({'type':'tool_use','id':块['id'],'name':块['name'],'input':工具输入(块['arguments'])})
        else:
            不支持('assistant content '+str(种类))
        下标+=1
    return 结果

def 序列化(选项,连接,历史,图片表,访问,回放降级=None,文件标识表=None):
    """用已准备的图片字节序列化一次完整请求。"""
    模型=None
    for 条目 in 连接['models']:
        if 条目['id']==选项['model']:
            模型=条目
            break
    历史内=模型 is not None and 模型.get('systemPromptUpdate')=='in-history'
    def 输入(块列表):
        """用户与工具结果内容。"""
        结果=[]
        for 块 in 块列表:
            种类=块['type']
            if 种类=='text':
                if 块['text']:
                    结果.append({'type':'text','text':块['text']})
                continue
            if 种类=='reasoning' or 种类=='tool-call':
                continue
            if 种类!='image':
                不支持('user/tool-result content '+str(种类))
            版本=图片表.get(块['attachment']['attachmentId'])
            if 版本 is None:
                raise 大模型错误('DeepSeek Messages request image is missing','INVALID_REQUEST')
            文件号=文件标识表.get(块['attachment']['attachmentId']) if 文件标识表 is not None else None
            if 文件标识表 is not None and 文件号 is None:
                raise 大模型错误('DeepSeek Messages request file id is missing','INVALID_REQUEST')
            结果.append({'type':'text','text':请求图片句柄文案(块['attachment'],版本,访问(块['attachment']) if 访问 is not None else None)})
            if 文件号 is None:
                结果.append({'type':'image','source':{'type':'base64','media_type':版本['mediaType'],'data':base64.b64encode(版本['data']).decode('ascii')}})
            else:
                结果.append({'type':'image','source':{'type':'file','file_id':文件号}})
        return 结果
    消息列表=[]
    历史系统=None
    系统更新=[]
    def 冲刷系统更新():
        """系统更新必须跟在用户或工具结果轮次后。"""
        if len(系统更新)==0:
            return
        if len(消息列表)==0 or 消息列表[-1]['role']!='user':
            不支持('system update without a preceding user or tool-result turn')
        消息列表.extend(系统更新)
        系统更新.clear()
    工具列表=选项.get('tools')
    if 工具列表 is not None:
        for 工具 in 工具列表:
            if 工具.get('deferLoading') is True:
                不支持('deferred tool loading')
    for 消息 in 历史:
        if 消息.get('role')=='developer':
            不支持('developer message')
        if any(块.get('type')=='tool-addition' or 块.get('type')=='tool-removal' for 块 in 消息.get('content') or []):
            不支持('tool-change blocks outside developer messages')
        if 消息.get('role')=='system':
            文本块=[块 for 块 in 消息['content'] if 块.get('type')=='text']
            if len(文本块)!=len(消息['content']):
                不支持('non-text system message')
            文本=''.join(块['text'] for 块 in 文本块)
            if 历史内 and len(消息列表)>0:
                if len(文本)==0:
                    不支持('empty in-history system update')
                系统更新.append({'role':'system','content':[{'type':'text','text':文本}]})
            else:
                历史系统=文本
            continue
        if 消息.get('role')=='assistant':
            冲刷系统更新()
        if 消息.get('role')=='assistant':
            内容=助手(消息,选项['model'],回放降级)
        elif 消息.get('role')=='tool':
            条目={'type':'tool_result','tool_use_id':消息['toolCallId'],'content':输入(消息['content'])}
            if 消息.get('isError') is not None:
                条目['is_error']=消息['isError']
            内容=[条目]
        else:
            内容=[]
            for 块 in 消息['content']:
                内容.extend(输入([块]))
        if 消息.get('role')=='user' and len(内容)==0:
            continue
        线路角色='user' if 消息.get('role')=='tool' else 消息['role']
        if len(消息列表)>0 and 消息列表[-1]['role']==线路角色:
            消息列表[-1]['content'].extend(内容)
        else:
            消息列表.append({'role':线路角色,'content':内容})
    冲刷系统更新()
    未决=set()
    for 消息 in 消息列表:
        if 消息['role']=='assistant':
            调用=[块 for 块 in 消息['content'] if 块.get('type')=='tool_use']
            未决=set(块['id'] for 块 in 调用)
            if len(未决)!=len(调用):
                raise 大模型错误('DeepSeek Messages duplicate tool call id','INVALID_REQUEST')
        elif 消息['role']=='user':
            结果块=[块 for 块 in 消息['content'] if 块.get('type')=='tool_result']
            for 结果 in 结果块:
                if 结果['tool_use_id'] not in 未决:
                    raise 大模型错误('DeepSeek Messages tool result has no matching call','INVALID_REQUEST')
                未决.remove(结果['tool_use_id'])
            if len(未决)>0:
                raise 大模型错误('DeepSeek Messages tool calls need immediate results','INVALID_REQUEST')
            消息['content']=结果块+[块 for 块 in 消息['content'] if 块.get('type')!='tool_result']
    if len(未决)>0:
        raise 大模型错误('DeepSeek Messages history ends with unresolved tools','INVALID_REQUEST')
    默认=连接['defaults']
    if 选项.get('purpose')=='session-title':
        力度='off'
    elif 选项.get('reasoningEffort') is not None:
        力度=选项['reasoningEffort']
    elif 默认.get('reasoningEffort') is not None:
        力度=默认['reasoningEffort']
    elif 默认.get('thinking')=='disabled':
        力度='off'
    else:
        力度='high'
    if 力度 not in ('off','low','high','max') or (默认.get('thinking')=='disabled' and 力度!='off'):
        raise 大模型错误('DeepSeek Messages does not support reasoning effort '+str(力度),'UNSUPPORTED_REASONING_EFFORT')
    系统段=[段 for 段 in (选项.get('system'),历史系统) if 段]
    系统='\n\n'.join(系统段)
    上限=选项.get('maxTokens')
    if 上限 is None and 模型 is not None:
        上限=模型.get('maxTokens')
    if 上限 is None:
        上限=连接['maxTokens']
    体={
        'model':选项['model'],
        'stream':True,
        'messages':消息列表,
        'max_tokens':上限,
        'thinking':{'type':'disabled' if 力度=='off' else 'enabled'},
    }
    if 力度!='off':
        体['output_config']={'effort':力度}
    if len(系统)>0:
        体['system']=系统
    if 选项.get('temperature') is not None:
        体['temperature']=选项['temperature']
    if 选项.get('stop') is not None:
        体['stop_sequences']=选项['stop']
    if 工具列表 is not None:
        体['tools']=[{'name':工具['name'],'description':工具['description'],'input_schema':工具['parameters']} for 工具 in 工具列表]
    return 体
