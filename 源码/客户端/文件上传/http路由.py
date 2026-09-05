"""登记在 Connection fetch 注册表上的已认证原始字节上传路由。

对齐上游 `file-upload/src/http-route.ts`。响应为连接包惯用的字典形态。
"""
import json#JSON 结果
from urllib.parse import parse_qs,urlparse#查询解析
from ...工具.品牌 import 带品牌#会话 id 品牌
from .类型 import 取远程错误#Remote 错误提取

__all__=['处理文件上传http','请求体分片']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#值
        return 缺省#缺席
    return getattr(对象,键,缺省)#属性

def 取头(头们,名):#大小写不敏感取头
    """读字符串头。"""
    if 头们 is None:#无头
        return None#缺席
    if hasattr(头们,'get') and not isinstance(头们,dict):#Headers 形
        值=头们.get(名)#按名
        if 值 is not None:#命中
            return 值#返回
        值=头们.get(名.lower())#小写再试
        return 值#可能仍无
    if isinstance(头们,dict):#映射
        if 名 in 头们:#原样
            return 头们[名]#值
        小=名.lower()#小写键
        for 键,值 in 头们.items():#扫
            if str(键).lower()==小:#命中
                return 值#值
    return None#缺席

def 请求体分片(正文):#请求体分片迭代
    """把连接桥交付的正文变成有序字节块。"""
    if 正文 is None:#无体
        return#空生成器
    if isinstance(正文,(bytes,bytearray,memoryview)):#整段字节
        yield bytes(正文)#一块
        return#完
    if hasattr(正文,'read') and callable(正文.read):#类文件
        while True:#直到空
            块=正文.read(65536)#64KiB
            if not 块:#结束
                return#停
            if isinstance(块,str):#文本
                块=块.encode('utf-8')#编码
            yield bytes(块)#产出
        return#完
    if hasattr(正文,'__iter__') and not isinstance(正文,(str,bytes,bytearray,dict)):#可迭代块
        for 块 in 正文:#逐块
            if isinstance(块,str):#文本
                块=块.encode('utf-8')#编码
            yield bytes(块)#产出
        return#完
    yield bytes(正文)#兜底一次

def 处理文件上传http(服务,请求):#处理上传 HTTP
    """处理一次已认证原始字节上传；校验后恒返回 200 JSON 结果。"""
    方法=取字段(请求,'method') or 'GET'#方法
    if 方法!='POST':#方法不对
        return {'status':405,'headers':{'allow':'POST'},'body':b''}#只允许 POST
    内容类型=取头(取字段(请求,'headers',{}),'content-type') or ''#内容类型
    媒体类型=内容类型.split(';',1)[0].strip().lower()#媒体类型
    if 媒体类型!='application/octet-stream':#类型不对
        return {'status':415,'headers':{},'body':b'content type must be application/octet-stream'}#不支持媒体类型
    网址=取字段(请求,'url') or ''#url
    解析=urlparse(网址)#解析 URL
    参数=parse_qs(解析.query)#查询
    会话列表=参数.get('sessionId') or []#会话 id 查询
    会话标识=会话列表[0] if 会话列表 else None#首值
    if 会话标识 is None or 会话标识=='':#缺会话 id
        return {'status':400,'headers':{},'body':b'sessionId is required'}#坏请求
    名列表=参数.get('name') or []#可选显示名
    显示名=名列表[0] if 名列表 else None#首值或无
    try:#业务或内部错误
        流参数={#流式存盘参数
            'sessionId':带品牌(会话标识),#品牌化会话 id
            'data':请求体分片(取字段(请求,'body')),#请求体分片
        }#基参
        信号=取字段(请求,'signal')#取消信号
        if 信号 is not None:#有信号
            流参数['signal']=信号#可选取消
        if 显示名 is not None:#有名
            流参数['name']=显示名#可选名
        结果={'ok':True,'value':服务.流式上传(流参数)}#成功支
    except BaseException as 错误:#捕获
        失败=取远程错误(错误)#尝试提取 Remote 错误
        if 失败 is not None:#Remote 错误
            结果={#失败支
                'ok':False,#失败
                'error':{#错误体
                    'code':取字段(失败,'code') if isinstance(失败,dict) else 失败.code,#码
                    'message':取字段(失败,'message') if isinstance(失败,dict) else 失败.message,#消息
                    'details':取字段(失败,'details',{}) if isinstance(失败,dict) else 失败.details,#细节
                },#结束 error
            }#结束失败
        else:#内部错误
            结果={#内部
                'ok':False,#失败
                'error':{#错误体
                    'code':'gateway/internal',#内部码
                    'message':错误.args[0] if isinstance(错误,Exception) and 错误.args else str(错误),#消息
                    'details':{},#空细节
                },#结束 error
            }#结束内部
    正文=json.dumps(结果,ensure_ascii=False).encode('utf-8')#JSON 字节
    return {#始终 200 JSON
        'status':200,#状态
        'headers':{#头
            'content-type':'application/json; charset=utf-8',#JSON
            'cache-control':'no-store',#禁止缓存
        },#结束 headers
        'body':正文,#正文
    }#结束响应

handleFileUploadHttp=处理文件上传http#上游名
