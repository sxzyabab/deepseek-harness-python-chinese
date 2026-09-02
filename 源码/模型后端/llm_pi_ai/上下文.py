"""把 harness 请求历史转换成 pi-ai 的 Context 词表。

对齐上游 `llm-pi-ai/src/context.ts`。公开面仅中文名；无英文别名。
"""
from ...依赖.工具 import 二进制#base64 编解码
from .. import llm#语言模型服务
from .回放 import 转派助手#助手历史重建

__all__=('转派上下文','压平文本','工具结果文本','用户内容','工具列表')#仅中文公开名

def 压平文本(消息):
    """拼接一条 harness 消息的文本块。"""
    内容=消息['content'] if isinstance(消息,dict) else 消息.content#内容
    片段=[]#文本片段
    for 块 in 内容:#只拼接文本块，图片与工具结果不进压平结果
        类型=块['type'] if isinstance(块,dict) else 块.type#块类型
        if 类型=='text':#文本块才取出正文
            片段.append(块['text'] if isinstance(块,dict) else 块.text)#取出文本
    return ''.join(片段)#拼接

def 工具结果文本(块列):
    """在一条工具结果内递归压平文本。"""
    片段=[]#文本片段
    for 块 in 块列:#文本直接收，嵌套工具结果递归，其余占空串以免打乱顺序
        类型=块['type'] if isinstance(块,dict) else 块.type#块类型
        if 类型=='text':#文本块用其正文
            片段.append(块['text'] if isinstance(块,dict) else 块.text)#用其文本
        elif 类型=='tool-result':#嵌套结果继续压平，派爱工具结果只要一段文本
            内层=块['content'] if isinstance(块,dict) else 块.content#嵌套内容
            片段.append(工具结果文本(内层))#嵌套结果递归
        else:#图片等无法表示的块用空串占位
            片段.append('')#其余空串
    return ''.join(片段)#拼接

def 用户内容(块列,附件):
    """把用户块转成派爱内容。"""
    内容=[]#已组装内容
    for 块 in 块列:#按用户块顺序组装；空文本丢掉，图片走附件，工具结果递归
        类型=块['type'] if isinstance(块,dict) else 块.type#块类型
        if 类型=='text':#文本块；空串不进派爱内容
            文本=块['text'] if isinstance(块,dict) else 块.text#文本
            if len(文本)>0:#空文本不占一块，避免派爱收到空 text
                内容.append({'type':'text','text':文本})#非空才带上
        elif 类型=='image':#图片必须从持久附件读出字节再转 base64
            引用=块['attachment'] if isinstance(块,dict) else 块.attachment#附件引用
            已存=附件.readImage(引用)#读持久图片
            数据=已存['data'] if isinstance(已存,dict) else 已存.data#字节
            引用元=已存['ref'] if isinstance(已存,dict) else 已存.ref#附件元数据
            媒体=引用元['mediaType'] if isinstance(引用元,dict) else 引用元.mediaType#媒体类型
            内容.append({
                'type':'image',#图片
                'data':二进制.转base64(数据),#字节转base64
                'mimeType':媒体,#媒体类型
            })#图片块
        elif 类型=='tool-result':#嵌套工具结果再走同一转换，文本则折成 text 块
            内层块=块['content'] if isinstance(块,dict) else 块.content#嵌套内容
            嵌套=用户内容(内层块,附件)#递归转换
            if isinstance(嵌套,str):#全文本路径返回字符串
                if len(嵌套)>0:#空串不进内容
                    内容.append({'type':'text','text':嵌套})#非空才带上
            else:#含图片则展开混合数组
                内容.extend(嵌套)#展开嵌套块
    全是文本=True#是否全文本
    for 块 in 内容:#扫一遍：有图片就不能压成字符串
        if 块['type']!='text':#见到非文本则保留混合数组
            全是文本=False#含图片
            break#已判定
    if 全是文本:#全是文本则拼成字符串，派爱纯文本路径要字符串
        return ''.join(块['text'] for 块 in 内容)#全是文本则拼成字符串
    return 内容#含图片则保留混合数组

def 工具列表(选项):
    """映射请求工具。"""
    工具=选项.get('tools') if isinstance(选项,dict) else getattr(选项,'tools',None)#工具
    if 工具 is None:#请求没带工具则上下文也不带 tools 字段
        return None#没有工具
    映射=[]#派爱工具
    for 工具项 in 工具:#把 harness 工具投影成派爱 name/description/parameters
        映射.append({
            'name':工具项['name'] if isinstance(工具项,dict) else 工具项.name,#工具名
            'description':工具项['description'] if isinstance(工具项,dict) else 工具项.description,#说明
            'parameters':工具项['parameters'] if isinstance(工具项,dict) else 工具项.parameters,#参数模式
        })#一条工具
    return 映射#工具列表

def 派上下文信封(选项,消息们):
    """组装两条转换路径共用的请求级派爱上下文信封。"""
    工具=工具列表(选项)#映射工具
    信封={'messages':消息们}#上下文信封
    系统=选项.get('system') if isinstance(选项,dict) else getattr(选项,'system',None)#系统提示
    if 系统 is not None:#有系统提示才写 systemPrompt，缺席不带该字段
        信封['systemPrompt']=系统#有系统提示才带上
    if 工具 is not None and len(工具)>0:#空工具列表不带 tools 字段
        信封['tools']=工具#有工具才带上
    return 信封#信封

def 纯文本上下文(选项):
    """同步纯文本转换。"""
    工具名={}#调用id到工具名
    消息们=[]#派爱消息
    对话=选项['messages'] if isinstance(选项,dict) else 选项.messages#对话
    for 消息 in 对话:#按对话顺序转换；系统折成用户，助手走回放，工具结果拆成独立消息
        内容=消息['content'] if isinstance(消息,dict) else 消息.content#内容
        if llm.内容含图片(内容):#纯文本路径没有附件服务，见到图片必须失败
            raise llm.大模型错误('pi-ai image conversion requires the durable attachment service','UNSUPPORTED_CONTENT')#纯文本路径不支持图片
        角色=消息['role'] if isinstance(消息,dict) else 消息.role#角色
        if 角色=='system':#派爱上下文没有 in-history 系统角色，折成用户消息保顺序
            消息们.append({'role':'user','content':压平文本(消息),'timestamp':0})#折成用户消息以保顺序
            continue#下一条
        if 角色=='assistant':#助手走回放重建，并记下工具名供后续工具结果用
            助手=转派助手(消息)#重建派爱助手
            助手内容=助手['content']#助手内容
            for 块 in 助手内容:#扫助手块，把调用 id 映射到工具名
                if 块['type']=='toolCall':#工具调用才记名字
                    工具名[llm.调用标识(块['id'])]=块['name']#记下工具名
            消息们.append(助手)#助手消息
            continue#下一条
        文本=压平文本(消息)#用户文本
        结果们=[]#工具结果块
        for 块 in 内容:#用户消息里的工具结果要拆成独立派爱消息
            if (块['type'] if isinstance(块,dict) else 块.type)=='tool-result':#工具结果单独收
                结果们.append(块)#工具结果
        if len(文本)>0 or len(结果们)==0:#有正文，或整条都不是工具结果，才发用户消息
            消息们.append({'role':'user','content':文本,'timestamp':0})#有文本或没有结果才发用户消息
        for 结果 in 结果们:#每条工具结果变成独立 toolResult 消息
            调用标识=结果['toolCallId'] if isinstance(结果,dict) else 结果.toolCallId#调用id
            结果内容=结果['content'] if isinstance(结果,dict) else 结果.content#结果内容
            失败=结果.get('isError') if isinstance(结果,dict) else getattr(结果,'isError',None)#是否失败
            消息们.append({
                'role':'toolResult',#工具结果角色
                'toolCallId':调用标识,#调用id
                'toolName':工具名.get(调用标识,'unknown'),#从先前助手调用恢复名字
                'content':[{'type':'text','text':工具结果文本(结果内容) or '(no output)'}],#结果文本或占位
                'isError':False if 失败 is None else 失败,#缺省不算失败
                'timestamp':0,#历史时间戳
            })#独立工具结果消息
    return 派上下文信封(选项,消息们)#组装信封

def 带图片转派上下文(选项,附件):
    """带图片的转换。"""
    工具名={}#调用id到工具名
    消息们=[]#派爱消息
    对话=选项['messages'] if isinstance(选项,dict) else 选项.messages#对话
    for 消息 in 对话:#带图片路径：系统仍折成用户，用户内容走附件，工具结果可含图片
        内容=消息['content'] if isinstance(消息,dict) else 消息.content#内容
        角色=消息['role'] if isinstance(消息,dict) else 消息.role#角色
        if 角色=='system':#历史里的系统消息不能带图片，派爱无法表示
            if llm.内容含图片(内容):#系统消息含图片则拒绝
                raise llm.大模型错误('pi-ai cannot represent an image in an in-history system message','UNSUPPORTED_CONTENT')#派爱无法表示
            消息们.append({'role':'user','content':压平文本(消息),'timestamp':0})#折成用户消息
            continue#下一条
        if 角色=='assistant':#助手走回放，并记下工具名
            助手=转派助手(消息)#重建派爱助手
            for 块 in 助手['content']:#扫助手块恢复工具名
                if 块['type']=='toolCall':#工具调用才记名字
                    工具名[llm.调用标识(块['id'])]=块['name']#记下工具名
            消息们.append(助手)#助手消息
            continue#下一条
        常规=[]#非工具结果块
        结果们=[]#工具结果块
        for 块 in 内容:#把工具结果从用户内容里拆开
            if (块['type'] if isinstance(块,dict) else 块.type)=='tool-result':#工具结果单独发
                结果们.append(块)#工具结果
            else:#文本与图片留在用户内容
                常规.append(块)#用户内容
        内容值=用户内容(常规,附件)#转换用户内容
        if len(内容值)>0 or len(结果们)==0:#有用户正文或整条没有工具结果，才发用户消息
            消息们.append({'role':'user','content':内容值,'timestamp':0})#先发用户内容
        for 结果 in 结果们:#每条工具结果独立成消息；内容可以是文本或含图片
            结果内容=结果['content'] if isinstance(结果,dict) else 结果.content#结果内容
            转换=用户内容(结果内容,附件)#转换结果内容
            调用标识=结果['toolCallId'] if isinstance(结果,dict) else 结果.toolCallId#调用id
            失败=结果.get('isError') if isinstance(结果,dict) else getattr(结果,'isError',None)#是否失败
            if isinstance(转换,str):#全文本则包成一块，空串用占位
                结果块=[{'type':'text','text':转换 or '(no output)'}]#文本或占位
            else:#含图片则原样用混合数组
                结果块=转换#混合内容原样
            消息们.append({
                'role':'toolResult',#工具结果角色
                'toolCallId':调用标识,#调用id
                'toolName':工具名.get(调用标识,'unknown'),#从先前助手调用恢复名字
                'content':结果块,#结果内容
                'isError':False if 失败 is None else 失败,#缺省不算失败
                'timestamp':0,#历史时间戳
            })#独立工具结果消息
    return 派上下文信封(选项,消息们)#组装信封

def 转派上下文(选项,附件=None):
    """把 harness 历史转换成派爱 Context。"""
    if 附件 is None:#没有附件服务则走纯文本路径，有则解析图片
        return 纯文本上下文(选项)#仅文本
    return 带图片转派上下文(选项,附件)#带图片
