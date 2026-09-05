"""浏览器安全的暂存文件上传请求与凭证类型。

对齐上游 `file-upload/src/types.ts`。`RemoteError` 尚未落入 `typert.协议`，本模块提供结构兼容实现。
"""
from ...工具.品牌 import 带品牌#品牌原语

__all__=[#仅中文公开名
    '文件上传凭证标识',
    '编码文件上传请求字段',
    '文件上传结果字段',
    '文件附件引用字段',
    '远程错误',
    '取远程错误',
    '客户端文件上传钩子字段',
]#公开面结束

编码文件上传请求字段=('data','name')#规范 base64 与可选显示名
文件上传结果字段=('receiptId','file')#凭证与持久引用
文件附件引用字段=('attachmentId','name','bytes')#文件引用形状

def 文件上传凭证标识(值):#打成上传凭证品牌
    """Host 为某一 Agent 作用域内一次暂存上传铸造的权威。"""
    return 带品牌(值)#零成本品牌

class 远程错误(Exception):#结构兼容 RemoteError
    """一次远程调用失败：真实异常，携带稳定码与细节。判别按 code，不按类型链。"""
    def __init__(自身,码,消息,细节=None,选项=None):#构造远程错误
        """写入码、消息、细节与可选因果。"""
        super().__init__(消息)#人类诊断
        自身.code=码#稳定失败码
        自身.message=消息#跨线路消息
        自身.details={} if 细节 is None else 细节#结构化细节
        自身.isDSHRemoteError=True#结构标记
        自身.name='RemoteError'#错误名
        if 选项 is not None and 'cause' in 选项:#有因果
            自身.__cause__=选项['cause']#挂上原因

def 取远程错误(值):#结构识别远程错误
    """结构而非类型链：跨模块副本只认标记与 code。"""
    if isinstance(值,dict):#映射形
        if 值.get('isDSHRemoteError') is True and isinstance(值.get('code'),str):#带标记
            return 值#视为远程失败
        return None#不匹配
    if getattr(值,'isDSHRemoteError',None) is True and isinstance(getattr(值,'code',None),str):#对象形
        return 值#视为远程失败
    return None#不匹配
