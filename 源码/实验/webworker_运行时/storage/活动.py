from ..node.未实现失败 import 运行时错误#本包错误

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
        raise 运行时错误('webworker vfs: 尚未挂载文件系统；worker 入口必须在任何 node:fs 访问之前调用 setActiveVfs')#要求先挂载
    return _活动#返回活动实例
