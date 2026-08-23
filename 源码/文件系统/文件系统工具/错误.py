"""受守卫变更失败的面向模型补救。提供方的 FS_STALE_VERSION 与 FS_NOT_OBSERVED 消息只陈述条件，不给出唯一正确的恢复（重新读 / 先读文件），因此本包在模型边界追加补救；提供方消息保持面向机器且不变。对齐上游 tool-fs/src/error.ts。"""
from .. import 文件系统 as fs#文件系统服务定义

补救表={#错误码到补救文本
    'FS_STALE_VERSION':'re-read the file, then retry',#过期：重新读再试
    'FS_NOT_OBSERVED':'read the file, then retry',#未经观察：先读再试
}#补救表结束

def 补救文件系统错误(错误):#在模型边界补救可恢复的文件系统错误
    """给受守卫变更失败的消息追加正确的恢复指示。FS_STALE_VERSION（自本会话上次观察以来文件已变，包括目标缺失）只能通过重新读取恢复；FS_NOT_OBSERVED（本会话没有先前读取）通过读取恢复。保留 FsError 码，使重试/权限/UI 层继续按它路由，原始错误作为 cause 链接。其他错误原样穿过。"""
    if not isinstance(错误,fs.文件系统错误):#不是文件系统错误
        return 错误#原样返回
    补救=补救表.get(错误.code)#按错误码取补救文本
    if not 补救:#没有补救
        return 错误#原样返回
    return fs.文件系统错误(错误.message+' — '+补救,错误.code,{'cause':错误})#拼接补救并保留错误码与cause
