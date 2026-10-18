'已认证原始字节上传路由。校验之后一律回 200 的 JSON'
import json#结果编码
from urllib.parse import parse_qs as 解析查询,urlparse as 解析网址
from ...类型化远程调用.协议 import 取远程错误#按标记识别远程失败
from ...工具.标识构造 import 标识构造#会话标识，运行时原样返回

def 处理文件上传http(服务,请求):
    '处理一次已认证原始字节上传。校验失败用对应状态，通过后恒为 200 JSON'
    if 请求['method']!='POST':#只接受 POST
        return {'status':405,'headers':{'allow':'POST'},'body':None}#方法不对
    请求头=请求['headers'] if 'headers' in 请求 else {}#头表
    内容类型=None#媒体类型原文
    if isinstance(请求头,dict):#映射头
        for 键,值 in 请求头.items():#大小写不敏感
            if str(键).lower()=='content-type':#命中
                内容类型=值#原文
                break#停
    媒体类型=(内容类型 or '').split(';',1)[0].strip().lower()#去掉参数
    if 媒体类型!='application/octet-stream':#必须是原始字节
        return {'status':415,'headers':{},'body':'content type must be application/octet-stream'}#不支持的类型
    参数=解析查询(解析网址(请求['url']).query,keep_blank_values=True)#查询
    会话列表=参数['sessionId'] if 'sessionId' in 参数 else []#会话标识
    会话标识=会话列表[0] if len(会话列表)>0 else None#第一个
    if 会话标识 is None or 会话标识=='':#缺会话
        return {'status':400,'headers':{},'body':'sessionId is required'}#坏请求
    名列表=参数['name'] if 'name' in 参数 else []#显示名
    显示名=名列表[0] if len(名列表)>0 else None#没有则不传
    def 正文分片():
        '按顺序交出请求体块，不把多块拼成一段'
        正文=请求['body'] if 'body' in 请求 else None#正文
        if 正文 is None:#没有正文
            return#空
        if hasattr(正文,'getReader'):#可读流
            阅读器=正文.getReader()#锁住阅读器
            try:#读完或失败都放开锁
                while True:#逐块
                    块=阅读器.read()#下一块
                    if hasattr(块,'等待'):#期约
                        块=块.等待()#落到结果
                    完成=块['done'] if isinstance(块,dict) else 块.done#是否结束
                    if 完成:#流结束
                        return#停
                    yield 块['value'] if isinstance(块,dict) else 块.value#这一块
            finally:#放开锁
                阅读器.releaseLock()#解锁
        if isinstance(正文,(bytes,bytearray,memoryview)):#桥已经收成一段
            yield bytes(正文)#作为一块交出
            return#完
        for 块 in 正文:#调用方已经分成块
            yield 块#原样交出
    try:#业务失败也收成 JSON
        流参数={'sessionId':标识构造(会话标识),'data':正文分片()}#会话与分片
        if 'signal' in 请求:#可选取消
            流参数['signal']=请求['signal']#交给存储
        if 显示名 is not None:#有显示名，空串也算有
            流参数['name']=显示名#写入
        结果={'ok':True,'value':服务.流式上传(流参数)}#暂存回执
    except Exception as 错误:#远程或内部失败
        失败=取远程错误(错误)#结构识别
        if 失败 is not None:#远程失败
            结果={'ok':False,'error':{'code':失败.code,'message':失败.message,'details':失败.details}}#原样码和细节
        else:#不是远程失败
            if isinstance(getattr(错误,'message',None),str):#带消息
                消息=错误.message#用消息
            else:#其余
                消息=str(错误)#转成文本
            结果={'ok':False,'error':{'code':'gateway/internal','message':消息,'details':{}}}#内部失败
    return {'status':200,'headers':{'content-type':'application/json; charset=utf-8','cache-control':'no-store'},'body':json.dumps(结果,ensure_ascii=False,separators=(',',':'))}#校验通过后恒为 200
