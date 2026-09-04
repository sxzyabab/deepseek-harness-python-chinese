"""GitHub 签名校验用的有界 HTTP 正文读取。

对齐上游 `webhook-github/src/body.ts`。公开面仅中文名。
"""

__all__=['WebhookHttp错误','内容长度','读取有界utf8正文']#仅中文公开名

class WebhookHttp错误(Exception):#HTTP拒绝错误
    """消息可原样回写、不含请求数据的 HTTP 拒绝。"""
    name='WebhookHttpError'#错误名
    def __init__(自身,状态码,消息):#构造
        super().__init__(消息)#消息
        自身.status=状态码#HTTP状态码

def 内容长度(请求):#解析Content-Length
    """解析十进制 Content-Length；歧义头直接拒绝。"""
    值=取字段(请求,'content_length') or 取字段(请求,'headers',{}).get('content-length')#头值
    if 值 is None:#缺席
        return None#无长度
    if isinstance(值,list):#多值
        值=值[0] if len(值)>0 else None#取首个
    if 值 is None or not str(值).isdigit() or (str(值)!='0' and str(值).startswith('0')):#非法
        raise WebhookHttp错误(400,'invalid Content-Length')#拒绝
    长度=int(值)#转成整数
    if 长度<0 or 长度>2**53-1:#不安全整数
        raise WebhookHttp错误(413,'request body is too large')#过大
    return 长度#合法长度

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 读取有界utf8正文(请求,最大字节):#读取有界UTF-8正文
    """读取一次请求正文为精确、有界的 UTF-8 文本。"""
    声明长度=内容长度(请求)#声明长度
    if 声明长度 is not None and 声明长度>最大字节:#超长
        if hasattr(请求,'resume'):#可排空
            请求.resume()#排空
        raise WebhookHttp错误(413,'request body is too large')#拒绝
    块们=[]#收集块
    大小=0#当前大小
    读取器=取字段(请求,'body')#正文迭代器
    if 读取器 is None and callable(getattr(请求,'read',None)):#流式读取
        while True:#读至EOF
            块=请求.read(65536)#读一块
            if not 块:#EOF
                break#结束
            if isinstance(块,str):#文本块
                块=块.encode('utf-8')#转字节
            大小+=len(块)#累计
            if 大小>最大字节:#超限
                if hasattr(请求,'resume'):#可排空
                    请求.resume()#排空
                raise WebhookHttp错误(413,'request body is too large')#拒绝
            块们.append(块)#收下
    else:#已有正文
        正文=读取器 if isinstance(读取器,(bytes,bytearray)) else str(读取器 or '').encode('utf-8')#转字节
        if len(正文)>最大字节:#超限
            raise WebhookHttp错误(413,'request body is too large')#拒绝
        块们=[正文]#单块
    try:#解码
        return b''.join(块们).decode('utf-8')#严格UTF-8
    except UnicodeDecodeError:#非法UTF-8
        raise WebhookHttp错误(400,'request body is not valid UTF-8')#拒绝
