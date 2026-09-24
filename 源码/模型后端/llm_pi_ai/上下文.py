"""把 harness 请求历史转换成 pi-ai 的 Context 词表。

公开面仅中文名；无英文别名。
"""
from ...依赖.工具 import 二进制#base64 编解码
from ...附件.附件 import 请求图像尺寸#请求图几何
from .. import llm#语言模型服务
from .配置 import 默认请求图像素预算,默认请求图最大字节#路由默认预算
from .回放 import 转派助手#助手历史重建

__all__=('转派上下文','压平文本','用户内容','工具列表')#仅中文公开名

def 压平文本(消息):
    """拼接一条 harness 消息的文本块。"""
    片段=[]#文本片段
    for 块 in 消息['content']:#只拼文本
        if 块['type']=='text':#文本块
            片段.append(块['text'])#取出
    return ''.join(片段)#拼接

def 工具结果消息(消息,工具名表,内容):
    """把一等工具角色消息收成派爱 toolResult。"""
    if isinstance(内容,str):#全文本
        块列=[{'type':'text','text':内容 if 内容 else '(no output)'}]#空串占位
    else:#混合内容
        块列=内容#原样
    return {
        'role':'toolResult',#工具结果角色
        'toolCallId':消息['toolCallId'],#调用 id
        'toolName':工具名表[消息['toolCallId']] if 消息['toolCallId'] in 工具名表 else 'unknown',#恢复名字
        'content':块列,#结果内容
        'isError':消息['isError'] if 'isError' in 消息 else False,#缺省不算失败
        'timestamp':0,#历史时间戳
    }#派爱工具结果

def 断言可支持历史(消息列表):
    """拒绝开发者角色、工具变更块，以及非用户/工具消息里的图片。"""
    for 消息 in 消息列表:#逐条
        if 消息.get('role')=='developer':#开发者历史尚未序列化
            raise llm.大模型错误('Developer messages are not supported yet','UNSUPPORTED_CONTENT')#尚未支持
        内容=消息.get('content') or []#内容
        for 块 in 内容:#工具变更只能落在开发者角色
            if 块.get('type')=='tool-addition' or 块.get('type')=='tool-removal':#工具变更
                raise llm.大模型错误('Tool-change blocks require developer role','UNSUPPORTED_CONTENT')#角色不对
        if 消息.get('role')!='user' and 消息.get('role')!='tool' and llm.内容含图片(内容):#其它角色不能带图
            raise llm.大模型错误(
                'pi-ai cannot represent an image in an in-history '+str(消息.get('role'))+' message',
                'UNSUPPORTED_CONTENT',
            )#无法表示

def 用户内容(块列,请求图,解析访问):
    """把用户或工具结果块转成派爱内容。"""
    内容=[]#已组装
    for 块 in 块列:#按块顺序
        类型=块['type']#块类型
        if 类型=='text':#文本
            if len(块['text'])>0:#空串不占一块
                内容.append({'type':'text','text':块['text']})#非空才带
        elif 类型=='image':#图片
            引用=块['attachment']#附件引用
            版本=请求图[引用['attachmentId']]#精确请求版本
            内容.append({
                'type':'text',#句柄文本
                'text':llm.请求图片句柄文案(引用,版本,解析访问(引用)),#句柄
            })#句柄块
            内容.append({
                'type':'image',#图片
                'data':二进制.转base64(版本['data']),#请求字节转 base64
                'mimeType':版本['mediaType'],#媒体类型
            })#图片块
    if all(块['type']=='text' for 块 in 内容):#全文本则压成字符串
        return ''.join(块['text'] for 块 in 内容)#拼接
    return 内容#混合数组

def 收集图片引用(块列,引用表):
    """收集未卸载图片引用。"""
    for 块 in 块列:#逐块
        if 块.get('type')=='image' and 块.get('offloaded') is not True:#保留出现
            引用=块['attachment']#引用
            引用表[引用['attachmentId']]=引用#按 id 去重，后写覆盖同 id

def 准备请求图(消息列表,附件,预算,信号=None):
    """按出现顺序物化精确请求图版本。"""
    引用表={}#附件 id 到引用
    for 消息 in 消息列表:#逐条
        收集图片引用(消息.get('content') or [],引用表)#收集
    有序=list(引用表.values())#出现顺序
    版本表={}#附件 id 到请求版本
    for 引用 in 有序:#逐张
        几何=请求图像尺寸(引用['width'],引用['height'],预算['maxPixels'])#像素预算
        目标={**几何,'maxBytes':预算['maxBytes']}#请求目标
        版本表[引用['attachmentId']]=附件.读取图像请求(引用,目标,信号)#同步物化
    return 版本表#精确版本

def 工具列表(选项):
    """映射请求工具。推迟载入尚未支持。"""
    if 'tools' not in 选项 or 选项['tools'] is None:#没有工具
        return None#省略
    for 工具项 in 选项['tools']:#推迟载入尚未接到提供方
        if 工具项.get('deferLoading') is True:#推迟载入
            raise llm.大模型错误('Deferred tool loading is not supported yet','UNSUPPORTED_CONTENT')#尚未支持
    映射=[]#派爱工具
    for 工具项 in 选项['tools']:#投影
        映射.append({
            'name':工具项['name'],#工具名
            'description':工具项['description'],#说明
            'parameters':工具项['parameters'],#参数
        })#一条
    return 映射#工具列表

def 派上下文信封(系统提示,选项,消息列表):
    """组装两条转换路径共用的请求级派爱上下文信封。"""
    工具=工具列表(选项)#映射工具
    信封={'messages':消息列表}#信封
    if 系统提示 is not None:#有系统提示才写
        信封['systemPrompt']=系统提示#带上
    if 工具 is not None and len(工具)>0:#空列表不带
        信封['tools']=工具#带上
    return 信封#信封

def 拆分系统提示词(选项):
    """选出两条转换路径共用的派爱 systemPrompt 来源。"""
    if 'system' in 选项 and 选项['system'] is not None:#一次性槽获胜
        return {'systemPrompt':选项['system'],'messages':选项['messages']}#整份历史都转换
    对话=选项['messages']#对话
    if len(对话)==0 or 对话[0].get('role')!='system':#无前导系统
        return {'systemPrompt':None,'messages':对话}#不发送
    文本=压平文本(对话[0])#压平前导
    return {'systemPrompt':文本 if len(文本)>0 else None,'messages':对话[1:]}#空文本则不发送

def 追加系统或助手(消息,消息列表,工具名表,回放降级=None):
    """系统与助手两条路径相同；吃掉则返回真。"""
    if 消息.get('role')=='system':#未供给槽的系统折成用户
        消息列表.append({'role':'user','content':压平文本(消息),'timestamp':0})#保顺序
        return True#已消费
    if 消息.get('role')=='assistant':#助手走回放
        助手=转派助手(消息,回放降级)#重建
        for 块 in 助手['content']:#记下工具名
            if 块['type']=='toolCall':#工具调用
                工具名表[llm.调用标识(块['id'])]=块['name']#记下
        消息列表.append(助手)#助手消息
        return True#已消费
    return False#未消费

def 纯文本上下文(选项,回放降级=None):
    """同步纯文本转换。"""
    断言可支持历史(选项['messages'])#先拒不支持历史
    拆分=拆分系统提示词(选项)#拆分系统提示
    工具名表={}#调用 id 到工具名
    消息列表=[]#派爱消息
    for 消息 in 拆分['messages']:#按对话顺序
        if llm.内容含图片(消息.get('content') or []):#纯文本路径没有附件
            raise llm.大模型错误('pi-ai image conversion requires the durable attachment service','UNSUPPORTED_CONTENT')#缺附件
        if 追加系统或助手(消息,消息列表,工具名表,回放降级):#系统或助手
            continue#下一条
        if 消息.get('role')=='tool':#一等工具结果
            消息列表.append(工具结果消息(消息,工具名表,压平文本(消息)))#独立 toolResult
            continue#下一条
        消息列表.append({'role':'user','content':压平文本(消息),'timestamp':0})#用户
    return 派上下文信封(拆分['systemPrompt'],选项,消息列表)#信封

def 带图片转派上下文(选项,图片上下文,回放降级=None):
    """带精确请求图与卸载占位的转换。"""
    附件=图片上下文['attachments']#附件仓
    解析访问=图片上下文['resolveImageAccess']#当前路径解析
    最大请求图字节=图片上下文['maxRequestImageBytes'] if 'maxRequestImageBytes' in 图片上下文 else None#可选上限
    if 'requestImagePolicy' in 图片上下文 and 图片上下文['requestImagePolicy'] is not None:#路由预算
        预算=图片上下文['requestImagePolicy']#已给
    else:#缺省
        预算={'maxPixels':默认请求图像素预算,'maxBytes':默认请求图最大字节}#默认预算
    断言可支持历史(选项['messages'])#先拒不支持历史
    拆分=拆分系统提示词(选项)#拆分系统提示
    信号=选项['signal'] if 'signal' in 选项 else None#可选中止
    请求图=准备请求图(拆分['messages'],附件,预算,信号)#物化请求图
    if 最大请求图字节 is not None:#检查 base64 上限
        def 版本字节(块):#精确请求版本字节
            """按附件 id 取已物化版本的字节数。"""
            return 请求图[块['attachment']['attachmentId']]['bytes']#版本字节
        还需=llm.必需图片卸载(拆分['messages'],{'representation':'base64','maxBytes':最大请求图字节},版本字节)#还需卸载
        if 还需>0:#放不下
            raise llm.大模型错误(
                'pi-ai request images exceed the '+str(最大请求图字节)+'-byte base64 bound; '+str(还需)+' more oldest occurrence(s) must be offloaded.',
                llm.图片卸载必需码,
                {'offloadImages':还需},
            )#点名还需卸载张数
    def 卸载占位(引用):#表面已卸载出现
        """卸载占位文案。"""
        return llm.卸载图片文案(引用,解析访问(引用))#占位
    精确消息=llm.投影卸载图片(拆分['messages'],卸载占位)#投影卸载
    工具名表={}#调用 id 到工具名
    消息列表=[]#派爱消息
    for 消息 in 精确消息:#按投影后顺序
        if 追加系统或助手(消息,消息列表,工具名表,回放降级):#系统或助手
            continue#下一条
        if 消息.get('role')=='tool':#一等工具结果，内容可含图
            消息列表.append(工具结果消息(消息,工具名表,用户内容(消息.get('content') or [],请求图,解析访问)))#独立 toolResult
            continue#下一条
        内容值=用户内容(消息.get('content') or [],请求图,解析访问)#用户内容
        消息列表.append({'role':'user','content':内容值,'timestamp':0})#用户
    return 派上下文信封(拆分['systemPrompt'],选项,消息列表)#信封

def 转派上下文(选项,图片上下文=None,回放降级=None):
    """把 harness 历史转换成派爱 Context。"""
    if 图片上下文 is None:#没有附件上下文则走纯文本
        return 纯文本上下文(选项,回放降级)#仅文本
    return 带图片转派上下文(选项,图片上下文,回放降级)#带图片
