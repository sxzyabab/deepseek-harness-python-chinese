'受守卫变更失败的面向模型补救'
from .. import 文件系统 as fs#文件系统服务定义

class 工具文件系统错误(Exception):
    '面向模型的文件系统工具入参或组合非法'
    def __init__(自身,消息):
        '用原样英文消息构造'
        super().__init__(消息)#英文消息

def 补救文件系统错误(错误,展示路径):#在模型边界补救可恢复的文件系统错误
    """给受守卫变更失败换上稳定的面向模型诊断。
    FS_NOT_OBSERVED 换成带路径的先读再试；FS_STALE_VERSION 保留原因并要求重读。
    保留错误码，原始错误作为 cause。其他错误原样穿过
    """
    if not isinstance(错误,fs.文件系统错误):#不是文件系统错误
        return 错误#原样返回
    if 错误.code=='FS_NOT_OBSERVED':#本会话没有先前读取
        return fs.文件系统错误('cannot modify "'+展示路径+'": file has not been read — read the file, then retry',错误.code,{'cause':错误})#换成带路径的诊断
    if 错误.code=='FS_STALE_VERSION':#自上次观察以来文件已变
        return fs.文件系统错误(错误.message+' — re-read the file, then retry',错误.code,{'cause':错误})#保留原因并要求重读
    return 错误#原样返回
