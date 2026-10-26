'索引解析的工作入口。宿主用线程调用，不走进程'
from .解析 import 解析索引正文#解码并校验

__all__=['执行解析']#仅中文公开名

def 执行解析(请求):
    '校验解析请求并返回解析结果。正文必须是字节，网址必须是字符串'
    if not isinstance(请求,dict):#形态
        raise RuntimeError('index parser request is malformed')#上报原文
    正文=请求.get('body')#正文
    网址=请求.get('url')#网址
    if not isinstance(正文,(bytes,bytearray)) or not isinstance(网址,str):#字段
        raise RuntimeError('index parser request is malformed')#上报原文
    return 解析索引正文(bytes(正文),网址)#结果
