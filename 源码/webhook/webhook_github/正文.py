"""GitHub 签名校验用的有界 HTTP 正文读取。

对齐上游 `webhook-github/src/body.ts`。公开面仅中文名。
"""

__all__=['WebhookHttp错误','内容长度','读取有界utf8正文']#仅中文公开名

class WebhookHttp错误(Exception):
    """消息可原样回写、不含请求数据的 HTTP 拒绝。"""
    def __init__(自身,状态码,消息):
        """记下 HTTP 状态码与安全消息。"""
        super().__init__(消息)#消息
        自身.status=状态码#HTTP状态码

def 内容长度(请求):
    """解析十进制 Content-Length；歧义头直接拒绝。请求为 webServer 对象。"""
    头表=请求.headers#请求头
    if 'content-length' not in 头表:#键不存在
        return None#无长度
    值=头表['content-length']#头值
    if isinstance(值,list):#多值
        if len(值)==0:#空列表
            return None#无长度
        值=值[0]#取首个
    文本=str(值)#转成文本
    if 文本=='' or not 文本.isdigit() or (文本!='0' and 文本.startswith('0')):#非法
        raise WebhookHttp错误(400,'invalid Content-Length')#拒绝
    长度=int(文本)#转成整数
    if 长度<0 or 长度>9007199254740991:#超出外来 JSON 安全整数
        raise WebhookHttp错误(413,'request body is too large')#过大
    return 长度#合法长度

def 读取有界utf8正文(请求,最大字节):
    """读取一次请求正文为精确、有界的 UTF-8 文本。"""
    声明长度=内容长度(请求)#声明长度
    if 声明长度 is not None and 声明长度>最大字节:#超长
        raise WebhookHttp错误(413,'request body is too large')#拒绝
    块列表=[]#收集块
    大小=0#当前大小
    while True:#读至EOF
        块=请求.read(65536)#读一块
        if len(块)==0:#EOF
            break#结束
        if isinstance(块,str):#文本块
            块=块.encode('utf-8')#转字节
        大小+=len(块)#累计
        if 大小>最大字节:#超限
            raise WebhookHttp错误(413,'request body is too large')#拒绝
        块列表.append(块)#收下
    try:#解码
        return b''.join(块列表).decode('utf-8')#严格UTF-8
    except UnicodeDecodeError:#非法UTF-8
        raise WebhookHttp错误(400,'request body is not valid UTF-8')#拒绝
