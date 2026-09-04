"""发往检查器 Worker 的全量捕获 fetch 观测。

对齐上游 `shared/network/observation.ts`。公开面仅中文名。
"""
__all__=[#仅中文公开名
    '检查器头','请求身份','请求开始载荷','请求体分片载荷','请求体结束载荷',
    '请求响应载荷','请求结束载荷','检查器事件源消息','请求错误载荷',
]#公开面结束

检查器头=tuple#名值头对

class 请求身份:#请求身份
    """共用请求身份。"""
    def __init__(自身,requestId):#构造
        """保存请求标识。"""
        自身.requestId=requestId#请求标识

class 请求开始载荷(请求身份):#fetch开始载荷
    """一次高层全局 fetch 调用已开始。"""
    def __init__(自身,requestId,url,method,headers,hasBody,wallTimeMs):#构造
        """保存 fetch 开始载荷字段。"""
        super().__init__(requestId)#请求标识
        自身.url=url#请求URL
        自身.method=method#HTTP方法
        自身.headers=list(headers)#请求头
        自身.hasBody=hasBody#是否有体
        自身.wallTimeMs=wallTimeMs#墙钟毫秒

class 请求体分片载荷(请求身份):#请求体分片载荷
    """一块已捕获的请求体分片。"""
    def __init__(自身,requestId,data):#构造
        """保存请求体分片字段。"""
        super().__init__(requestId)#请求标识
        自身.data=data#分片数据

class 请求体结束载荷(请求身份):#请求体结束载荷
    """一次已捕获请求体的终态。"""
    def __init__(自身,requestId,capturedBytes,truncated,captureError=None):#构造
        """保存请求体结束字段。"""
        super().__init__(requestId)#请求标识
        自身.capturedBytes=capturedBytes#已捕获字节
        自身.truncated=truncated#是否截断
        自身.captureError=captureError#捕获错误

class 请求响应载荷(请求身份):#响应头载荷
    """fetch 已解析出响应头。"""
    def __init__(自身,requestId,url,status,statusText,headers,mimeType):#构造
        """保存响应头载荷字段。"""
        super().__init__(requestId)#请求标识
        自身.url=url#最终URL
        自身.status=status#状态码
        自身.statusText=statusText#状态文本
        自身.headers=list(headers)#响应头
        自身.mimeType=mimeType#MIME类型

class 请求结束载荷(请求身份):#响应结束载荷
    """fetch 捕获到达响应体终态。"""
    def __init__(自身,requestId,capturedBytes,responseBodyTruncated,responseCaptureError=None):#构造
        """保存响应结束字段。"""
        super().__init__(requestId)#请求标识
        自身.capturedBytes=capturedBytes#已捕获字节
        自身.responseBodyTruncated=responseBodyTruncated#响应体是否截断
        自身.responseCaptureError=responseCaptureError#响应捕获错误

class 检查器事件源消息:#SSE消息
    """一条与 CDP 投影无关的已解析 Server-Sent Event。"""
    def __init__(自身,eventName,eventId,data):#构造
        """保存 SSE 消息字段。"""
        自身.eventName=eventName#事件名
        自身.eventId=eventId#事件标识
        自身.data=data#数据

class 请求错误载荷(请求身份):#fetch错误载荷
    """fetch 在返回 Response 前被拒绝。"""
    def __init__(自身,requestId,message,canceled):#构造
        """保存 fetch 错误字段。"""
        super().__init__(requestId)#请求标识
        自身.message=message#错误信息
        自身.canceled=canceled#是否取消
