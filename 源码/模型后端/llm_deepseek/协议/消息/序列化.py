"""把系统快照与对话回合映射成消息协议请求。"""
import json,base64#工具入参与内联图编码
from ....llm import 大模型错误,请求图片句柄文案#错误与句柄
from .回放 import 读取回放#回放

__all__=('序列化',)#仅中文公开名

def 不支持(种类):
    """无法表示的内容。"""
    raise 大模型错误('DeepSeek Messages cannot represent '+种类,'UNSUPPORTED_CONTENT')#不支持

def 工具入参(原文):
    """历史参数 Messages 无法表示时用空 input；持久内容不变。"""
    try:#JSON
        值=json.loads(原文)#解码
    except (json.JSONDecodeError,TypeError,ValueError,UnicodeDecodeError):#非法
        return {}#空入参
    if isinstance(值,dict):#对象
        return 值#原样
    return {}#非对象则空

def 助手块(消息,模型,回放降级=None):
    """序列化一条助手消息的线路块。"""
    回放=读取回放(消息,模型,回放降级)#元数据
    结果=[]#块表
    for 下标,块 in enumerate(消息['content']):#逐块
        种类=块.get('type')#种类
        if 种类=='text':#文本
            结果.append({'type':'text','text':块['text']})#文本
        elif 种类=='reasoning':#思考
            项={'type':'thinking','thinking':块['text']}#思考
            签名=None#签名
            if 回放 is not None and 下标<len(回放):#有对齐
                签名=回放[下标].get('signature')#签名
            if 签名 is not None:#有签名
                项['signature']=签名#带上
            结果.append(项)#思考
        elif 种类=='tool-call':#工具
            结果.append({'type':'tool_use','id':块['id'],'name':块['name'],'input':工具入参(块['arguments'])})#调用
        else:#其余
            不支持('assistant content '+str(种类))#不支持
    return 结果#块

def 序列化(选项,连接,历史,图片,访问,回放降级=None,文件标识=None):
    """用已准备图字节序列化一次完整请求。"""
    模型=None#目录
    for 条目 in 连接['models']:#逐条
        if 条目['id']==选项['model']:#命中
            模型=条目#记下
            break#停
    历史内=模型.get('systemPromptUpdate')=='in-history' if 模型 is not None else False#更新策略
    def 输入(块列表):#用户/工具结果输入
        """把文本与图转成线路输入。"""
        结果=[]#输入
        for 块 in 块列表:#逐块
            if 块.get('type')=='text':#文本
                if 块.get('text'):#非空
                    结果.append({'type':'text','text':块['text']})#文本
                continue#下一块
            if 块.get('type')!='image':#非图
                不支持('user/tool-result content '+str(块.get('type')))#不支持
            if 块['attachment']['attachmentId'] not in 图片:#缺失
                raise 大模型错误('DeepSeek Messages request image is missing','INVALID_REQUEST')#缺失
            版本=图片[块['attachment']['attachmentId']]#版本
            文件号=文件标识.get(块['attachment']['attachmentId']) if 文件标识 is not None else None#文件 id
            if 文件标识 is not None and 文件号 is None:#缺 id
                raise 大模型错误('DeepSeek Messages request file id is missing','INVALID_REQUEST')#缺失
            结果.append({'type':'text','text':请求图片句柄文案(块['attachment'],版本,访问(块['attachment']) if 访问 is not None else None)})#句柄
            if 文件号 is None:#内联
                数据=版本['data']#字节
                if not isinstance(数据,bytes):#非字节
                    数据=bytes(数据)#转
                结果.append({'type':'image','source':{'type':'base64','media_type':版本['mediaType'],'data':base64.b64encode(数据).decode('ascii')}})#内联
            else:#文件
                结果.append({'type':'image','source':{'type':'file','file_id':文件号}})#文件
        return 结果#输入
    消息=[]#线路消息
    历史系统=None#历史系统
    系统更新=[]#待插入更新
    def 冲刷系统更新():#冲刷
        """Harness 允许系统更新出现在用户输入前；消息协议把同一更新放到该用户/工具结果回合之后、下一助手之前。"""
        if len(系统更新)==0:#无
            return#空
        if len(消息)==0 or 消息[-1].get('role')!='user':#无前置用户
            不支持('system update without a preceding user or tool-result turn')#不支持
        消息.extend(系统更新)#插入
        系统更新.clear()#清空
    for 项 in 历史:#逐条
        if 项.get('role')=='system':#系统
            文本块=[块 for 块 in 项['content'] if 块.get('type')=='text']#文本
            if len(文本块)!=len(项['content']):#非纯文本
                不支持('non-text system message')#不支持
            文本=''.join(块.get('text') or '' for 块 in 文本块)#拼接
            if 历史内 and len(消息)>0:#历史内更新
                if len(文本)==0:#空
                    不支持('empty in-history system update')#不支持
                系统更新.append({'role':'system','content':[{'type':'text','text':文本}]})#待插入
            else:#根系统
                历史系统=文本#记下
            continue#下一条
        if 项.get('role')=='assistant':#助手前冲刷
            冲刷系统更新()#冲刷
        if 项.get('role')=='assistant':#助手
            内容=助手块(项,选项['model'],回放降级)#助手块
        else:#用户
            内容=[]#块
            for 块 in 项['content']:#逐块
                if 块.get('type')!='tool-result':#普通
                    内容.extend(输入([块]))#输入
                else:#工具结果
                    结果块={'type':'tool_result','tool_use_id':块['toolCallId'],'content':输入(块.get('content') or [])}#结果
                    if 块.get('isError') is not None:#有错误旗
                        结果块['is_error']=块['isError']#带上
                    内容.append(结果块)#结果
        if len(消息)>0 and 消息[-1].get('role')==项.get('role'):#同角色合并
            消息[-1]['content'].extend(内容)#合并
        else:#新一轮
            消息.append({'role':项.get('role'),'content':内容})#新消息
    冲刷系统更新()#收尾
    待决=set()#未配对调用
    for 项 in 消息:#配对
        if 项.get('role')=='assistant':#助手
            调用=[块 for 块 in 项['content'] if 块.get('type')=='tool_use']#调用
            待决=set(块['id'] for 块 in 调用)#id
            if len(待决)!=len(调用):#重复
                raise 大模型错误('DeepSeek Messages duplicate tool call id','INVALID_REQUEST')#重复
        elif 项.get('role')=='user':#用户
            结果=[块 for 块 in 项['content'] if 块.get('type')=='tool_result']#结果
            for 一条 in 结果:#逐条
                if 一条['tool_use_id'] not in 待决:#无匹配
                    raise 大模型错误('DeepSeek Messages tool result has no matching call','INVALID_REQUEST')#无匹配
                待决.remove(一条['tool_use_id'])#配对
            if len(待决)>0:#缺少立即结果
                raise 大模型错误('DeepSeek Messages tool calls need immediate results','INVALID_REQUEST')#缺结果
            项['content']=结果+[块 for 块 in 项['content'] if 块.get('type')!='tool_result']#结果在前
    if len(待决)>0:#末尾未解
        raise 大模型错误('DeepSeek Messages history ends with unresolved tools','INVALID_REQUEST')#未解
    if 选项.get('purpose')=='session-title':#标题
        力度='off'#关
    elif 选项.get('reasoningEffort') is not None:#调用方
        力度=选项['reasoningEffort']#力度
    elif 连接['defaults'].get('reasoningEffort') is not None:#配置
        力度=连接['defaults']['reasoningEffort']#力度
    elif 连接['defaults'].get('thinking')=='disabled':#关掉思考
        力度='off'#关
    else:#默认高
        力度='high'#高
    if 力度 not in ('off','low','high','max') or (连接['defaults'].get('thinking')=='disabled' and 力度!='off'):#非法
        raise 大模型错误('DeepSeek Messages does not support reasoning effort '+str(力度),'UNSUPPORTED_REASONING_EFFORT')#非法
    系统段=[]#系统文本
    if 选项.get('system'):#选项系统
        系统段.append(选项['system'])#收下
    if 历史系统:#历史系统
        系统段.append(历史系统)#收下
    系统='\n\n'.join(系统段)#拼接
    最大=选项['maxTokens'] if 选项.get('maxTokens') is not None else (模型.get('maxTokens') if 模型 is not None and 模型.get('maxTokens') is not None else 连接['maxTokens'])#上限
    请求={
        'model':选项['model'],#模型
        'stream':True,#流式
        'messages':消息,#消息
        'max_tokens':最大,#上限
        'thinking':{'type':'disabled' if 力度=='off' else 'enabled'},#思考
    }#请求
    if 力度!='off':#有力度
        请求['output_config']={'effort':力度}#力度
    if len(系统)>0:#有系统
        请求['system']=系统#系统
    if 选项.get('temperature') is not None:#温度
        请求['temperature']=选项['temperature']#温度
    if 选项.get('stop') is not None:#停止
        请求['stop_sequences']=选项['stop']#停止
    if 选项.get('tools') is not None:#工具
        请求['tools']=[{'name':项['name'],'description':项['description'],'input_schema':项['parameters']} for 项 in 选项['tools']]#工具
    return 请求#请求体
