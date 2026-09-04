"""源-到-Worker 非 CDP 查询的带版本帧。

对齐上游 `shared/bridge/messages/query/frames.ts`。公开面仅中文名。
"""
from ...版本 import 检查器协议版本#协议版本

__all__=['检查器查询请求标识','检查器查询请求帧','检查器查询响应帧']#仅中文公开名

def 检查器查询请求标识(值):#查询请求标识
    """一次在途 Inspector 查询的身份。"""
    return 值#烙印

def 检查器查询请求帧(sourceId,generation,requestId,query):#查询请求帧
    """源对一次 Worker 拥有的查询操作的请求。"""
    return {#请求帧
        'v':检查器协议版本,#协议版本
        't':'query/request',#帧类型
        'sourceId':sourceId,#源标识
        'generation':generation,#世代
        'requestId':requestId,#请求标识
        'query':query,#查询体
    }#返回结束

def 检查器查询响应帧(sourceId,generation,requestId,outcome):#查询响应帧
    """Worker 与一次源查询请求相关的响应。"""
    return {#响应帧
        'v':检查器协议版本,#协议版本
        't':'query/response',#帧类型
        'sourceId':sourceId,#源标识
        'generation':generation,#世代
        'requestId':requestId,#请求标识
        'outcome':outcome,#结果封装
    }#返回结束
