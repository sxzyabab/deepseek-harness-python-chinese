from ...工具.标识构造 import 标识构造#标识构造原语
from .异常 import 文件上传错误,远程错误#本包异常

__all__=[#仅中文公开名
    '文件上传凭证标识',
    '编码文件上传请求字段',
    '文件上传结果字段',
    '文件附件引用字段',
    '文件上传错误',
    '远程错误',
    '取远程错误',
    '客户端文件上传钩子字段',
    '已中止',
    '若已中止则抛出',
]

编码文件上传请求字段=('data','name')#规范 base64 与可选显示名
文件上传结果字段=('receiptId','file')#凭证与持久引用
文件附件引用字段=('attachmentId','name','bytes')#文件引用形状

def 文件上传凭证标识(值):#打成上传凭证品牌
    'Host 为某一 Agent 作用域内一次暂存上传铸造的权威'
    return 标识构造(值)#零成本品牌

def 取远程错误(值):#结构识别远程错误
    '结构而非类型链：跨模块副本只认标记与 code。联合为 dict | 远程错误'
    if isinstance(值,远程错误):#本包实例
        return 值#视为远程失败
    if isinstance(值,dict):#映射形副本
        标=值['isDSHRemoteError'] if 'isDSHRemoteError' in 值 else None#标记
        码=值['code'] if 'code' in 值 else None
        if 标 is True and isinstance(码,str):#带标记
            return 值#视为远程失败
        return None#不匹配
    return None#不匹配

def 已中止(信号):#读 threading.Event
    '无信号视为未中止；已置位则已中止'
    if 信号 is None:#无
        return False#未中止
    return 信号.is_set()#Event 置位

def 若已中止则抛出(信号):#已取消则抛
    '已中止则抛文件上传错误'
    if 已中止(信号):#已取消
        raise 文件上传错误('The operation was aborted.')#AbortError 文案
