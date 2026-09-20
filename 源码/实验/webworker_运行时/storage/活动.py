from ..node.未实现失败 import 运行时错误

__all__=['设活动vfs','要求活动vfs']

_活动=None

def 设活动vfs(文件系统):
    """发布 `node:fs` 代理所读的文件系统。

    参数:
        文件系统: worker 入口挂载的文件系统。
    """
    global _活动
    _活动=文件系统

def 要求活动vfs():
    """读取已挂载的文件系统。

    返回:
        活动文件系统。
    """
    if _活动 is None:
        raise 运行时错误('webworker vfs: 尚未挂载文件系统；worker 入口必须在任何 node:fs 访问之前调用 setActiveVfs')
    return _活动
