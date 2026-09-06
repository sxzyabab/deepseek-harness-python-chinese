"""登记在 Connection fetch 注册表上的已认证原始字节上传路由。

对齐上游 `file-upload/src/http-route.ts`。响应为连接包惯用的字典形态。
"""
import json#JSON 结果
from urllib.parse import parse_qs,urlparse#查询解析
from ...工具.标识构造 import 标识构造#会话 id 标识
from .类型 import 取远程错误#Remote 错误提取

__all__=['处理文件上传http','请求体分片']#仅中文公开名

def 取头(请求头表,名):#大小写不敏感取头
    """读字符串头。请求头冻结为 dict。"""
    if 请求头表 is None:#无头
        return None#无
    if 名 in 请求头表:#原样
        return 请求头表[名]#值
    小=名.lower()#小写键
    for 键,值 in 请求头表.items():#扫
        if str(键).lower()==小:#命中
            return 值#值
    return None#无

def 请求体分片(正文):#请求体分片迭代
    """把连接桥交付的正文变成有序字节块。"""
    if 正文 is None:#无体
        return#空生成器
    if isinstance(正文,(bytes,bytearray,memoryview)):#整段字节
        yield bytes(正文)#一块
        return#完
    if isinstance(正文,str):#文本
        yield 正文.encode('utf-8')#一块
        return#完
    for 块 in 正文:#可迭代块
        if isinstance(块,str):#文本
            块=块.encode('utf-8')#编码
        yield bytes(块)#产出

def 处理文件上传http(服务,请求):#处理上传 HTTP
    """处理一次已认证原始字节上传；校验后恒返回 200 JSON 结果。"""
    方法=请求['method'] if 'method' in 请求 else 'GET'#方法
    if 方法!='POST':#方法不对
        return {'status':405,'headers':{'allow':'POST'},'body':b''}#只允许 POST
    请求头表=请求['headers'] if 'headers' in 请求 else {}#头
    内容类型=取头(请求头表,'content-type') or ''#内容类型
    媒体类型=内容类型.split(';',1)[0].strip().lower()#媒体类型
    if 媒体类型!='application/octet-stream':#类型不对
        return {'status':415,'headers':{},'body':b'content type must be application/octet-stream'}#不支持媒体类型
    网址=请求['url'] if 'url' in 请求 else ''#url
    解析=urlparse(网址)#解析 URL
    参数=parse_qs(解析.query)#查询
    会话列表=参数['sessionId'] if 'sessionId' in 参数 else []#会话 id 查询
    会话标识=会话列表[0] if len(会话列表)>0 else None#首值
    if 会话标识 is None or 会话标识=='':#缺会话 id
        return {'status':400,'headers':{},'body':b'sessionId is required'}#坏请求
    名列表=参数['name'] if 'name' in 参数 else []#可选显示名
    显示名=名列表[0] if len(名列表)>0 else None#首值或无
    try:#业务或内部错误
        流参数={#流式存盘参数
            'sessionId':标识构造(会话标识),#品牌化会话 id
            'data':请求体分片(请求['body'] if 'body' in 请求 else None),#请求体分片
        }#基参
        if 'signal' in 请求:#有信号
            流参数['signal']=请求['signal']#可选取消
        if 显示名 is not None:#有名
            流参数['name']=显示名#可选名
        结果={'ok':True,'value':服务.流式上传(流参数)}#成功支
    except Exception as 错误:#捕获
        失败=取远程错误(错误)#尝试提取 Remote 错误
        if 失败 is not None:#Remote 错误
            if isinstance(失败,dict):#结构副本
                码=失败['code']#码
                消息=失败['message']#消息
                细节=失败['details'] if 'details' in 失败 else {}#细节
            else:#异常实例
                码=失败.code#码
                消息=失败.message#消息
                细节=失败.details#细节
            结果={'ok':False,'error':{'code':码,'message':消息,'details':细节}}#失败支
        else:#内部错误
            消息=错误.args[0] if len(错误.args)>0 else str(错误)#消息
            结果={'ok':False,'error':{'code':'gateway/internal','message':消息,'details':{}}}#内部
    正文=json.dumps(结果,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')#JSON 字节
    return {#始终 200 JSON
        'status':200,#状态
        'headers':{#头
            'content-type':'application/json; charset=utf-8',#JSON
            'cache-control':'no-store',#禁止缓存
        },#结束 headers
        'body':正文,#正文
    }#结束响应
