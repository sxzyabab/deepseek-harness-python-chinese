"""GitHub 签名校验用的有界 HTTP 正文读取。"""

__all__=['WebhookHttp错误','内容长度','读取有界utf8正文']

class WebhookHttp错误(Exception):
    """消息可原样回写、不含请求数据的 HTTP 拒绝。"""
    def __init__(自身,状态码,消息):
        """记下 HTTP 状态码与安全消息。"""
        super().__init__(消息)
        自身.status=状态码#HTTP 状态码

def 内容长度(请求):
    """解析十进制 Content-Length；歧义头或越界值直接拒绝。请求为 webServer 对象。"""
    头表=请求.headers
    if 'content-length' not in 头表:
        return None
    值=头表['content-length']
    if isinstance(值,list):
        if len(值)==0:
            return None
        值=值[0]
    文本=str(值)
    if 文本=='' or not 文本.isdigit() or (文本!='0' and 文本.startswith('0')):#禁止前导零
        raise WebhookHttp错误(400,'invalid Content-Length')
    长度=int(文本)
    if 长度<0 or 长度>9007199254740991:#外来 JSON 安全整数上限
        raise WebhookHttp错误(413,'request body is too large')
    return 长度

def 读取有界utf8正文(请求,最大字节):
    """读取一次请求正文为精确、有界的 UTF-8 文本。"""
    声明长度=内容长度(请求)
    if 声明长度 is not None and 声明长度>最大字节:
        raise WebhookHttp错误(413,'request body is too large')
    块列表=[]
    大小=0
    while True:
        块=请求.read(65536)
        if len(块)==0:
            break
        if isinstance(块,str):
            块=块.encode('utf-8')
        大小+=len(块)
        if 大小>最大字节:
            raise WebhookHttp错误(413,'request body is too large')
        块列表.append(块)
    try:
        return b''.join(块列表).decode('utf-8')#严格 UTF-8
    except UnicodeDecodeError:
        raise WebhookHttp错误(400,'request body is not valid UTF-8')
