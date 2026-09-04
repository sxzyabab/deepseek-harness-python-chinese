"""进程级槽位，持有已挂载的文件系统。与任何后端实现分开：
`node:fs` 代理依赖槽位，而非 worker 入口挂载了哪个后端。

对齐上游 `webworker-runtime/src/storage/active.ts`。公开面仅中文名。
"""
__all__=['设活动vfs','要求活动vfs']#仅中文公开名

_活动=None#已挂载文件系统槽位

def 设活动vfs(文件系统):#发布活动VFS
    """发布 `node:fs` 代理所读的文件系统。

    参数:
        文件系统: worker 入口挂载的文件系统。
    """
    global _活动#槽位
    _活动=文件系统#写入槽位

def 要求活动vfs():#读取活动VFS
    """读取已挂载的文件系统。

    返回:
        活动文件系统。
    """
    if _活动 is None:#尚未挂载
        raise Exception('webworker vfs: no filesystem is mounted; the worker entry must call setActiveVfs before any node:fs access')#要求先挂载
    return _活动#返回活动实例
