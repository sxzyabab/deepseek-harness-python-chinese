"""LSP 基础协议成帧：字节流上按 Content-Length 分隔的 JSON-RPC。编码器产出一帧缓冲；解码器缓冲入站字节并产出完整消息体，同时限制头与整消息大小，使敌意或损坏的服务器无法耗尽内存。"""
import json#JSON正文编解码

头体分隔符='\r\n\r\n'#头与体之间的CRLF分隔
头段上限字节=1<<16#头段最大字节数

def 编码消息(消息):#编码一条成帧LSP消息
    """把一条 JSON-RPC 消息编码成成帧的 LSP 缓冲（Content-Length: N\\r\\n\\r\\n<utf-8 json>）。"""
    正文=json.dumps(消息,ensure_ascii=False,separators=(',',':')).encode('utf-8')#把消息序列化为UTF-8正文
    头=('Content-Length: '+str(len(正文))+'\r\n\r\n').encode('ascii')#按正文字节数写Content-Length头
    return 头+正文#头与体拼接成一帧

class 消息解码器:#流式LSP成帧解码器
    """Content-Length 成帧 JSON-RPC 的流式解码器。喂入 stdout 分块；返回此刻已完整的消息体。只解析 Content-Length 头，忽略其他头（例如 Content-Type），与基础协议一致。"""
    def __init__(自身,最大消息字节):#构造解码器
        """记下单条成帧正文上限。"""
        自身.缓冲=b''#尚未消费的入站字节
        自身.最大消息字节=最大消息字节#单条消息体上限

    def 推入(自身,块):#喂入一块stdout并取出完整消息
        """追加一块数据，并返回此刻已完整的每一条消息体。"""
        if isinstance(块,str):#文本则按utf-8
            块=块.encode('utf-8')#转字节
        elif not isinstance(块,(bytes,bytearray)):#memoryview等
            块=bytes(块)#强制字节
        自身.缓冲=块 if len(自身.缓冲)==0 else 自身.缓冲+块#拼接到未消费缓冲
        消息们=[]#本轮解析出的消息
        while True:#循环取出所有已完整消息
            步进=自身.下一条()#尝试消费下一条
            if not 步进.get('ready'):#字节不够则停止
                break#停止
            消息们.append(步进['message'])#收下一完整消息
        return 消息们#返回本轮全部完整消息

    def 下一条(自身):#尝试消费下一条完整帧
        """解析并消费下一条完整消息，或报告还需要更多字节。"""
        分隔=自身.缓冲.find(头体分隔符.encode('ascii'))#查找头体分隔符
        if 分隔<0:#尚未看到分隔符
            if len(自身.缓冲)>头段上限字节:#头已超过上限
                raise Exception('LSP header exceeded '+str(头段上限字节)+' bytes without a terminator')#拒绝无限增长的头
            return {'ready':False}#还需要更多字节
        if 分隔>头段上限字节:#分隔符出现得太晚
            raise Exception('LSP header exceeded '+str(头段上限字节)+' bytes')#拒绝过长的头
        头文本=自身.缓冲[0:分隔].decode('ascii','replace')#把头解码成ASCII文本
        内容长度=解析内容长度(头文本)#解析Content-Length
        if 内容长度>自身.最大消息字节:#正文超过配置上限
            raise Exception('LSP message length '+str(内容长度)+' exceeds the '+str(自身.最大消息字节)+'-byte limit')#拒绝过大消息
        正文起=分隔+len(头体分隔符)#正文起始偏移
        正文止=正文起+内容长度#正文结束偏移
        if len(自身.缓冲)<正文止:#正文尚未收齐
            return {'ready':False}#还需要更多字节
        正文=自身.缓冲[正文起:正文止].decode('utf-8')#取出UTF-8正文
        自身.缓冲=自身.缓冲[正文止:]#丢掉已消费字节
        try:#解析JSON正文
            return {'ready':True,'message':json.loads(正文)}#解析成功则交出消息
        except Exception as 错误:#JSON无效
            消息=错误.args[0] if isinstance(错误,Exception) and len(getattr(错误,'args',()))>0 else str(错误)#取消息
            raise Exception('LSP message body was not valid JSON: '+str(消息))#包装成LSP正文错误

def 解析内容长度(头文本):#从头块解析Content-Length
    """读取 Content-Length 头值（大小写不敏感），缺失或非数字则拒绝。"""
    for 行 in 头文本.split('\r\n'):#逐行扫描头
        冒号=行.find(':')#找冒号
        if 冒号<0:#没有冒号则跳过
            continue#跳过
        if 行[0:冒号].strip().lower()!='content-length':#不是Content-Length则跳过
            continue#跳过
        try:#解析冒号后的数字
            值=int(行[冒号+1:].strip())#整型
        except Exception:#非数字
            raise Exception('invalid Content-Length header: '+json.dumps(行,ensure_ascii=False))#拒绝无效长度
        if 值<0:#负数非法
            raise Exception('invalid Content-Length header: '+json.dumps(行,ensure_ascii=False))#拒绝无效长度
        return 值#返回正文长度
    raise Exception('LSP header block missing Content-Length: '+json.dumps(头文本,ensure_ascii=False))#整块头都没有Content-Length
