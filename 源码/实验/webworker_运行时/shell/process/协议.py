"""shell 进程与其宿主交换的帧。

命令在自有 Web Worker 中运行，该 worker 不拥有文件系统：VFS 留在宿主
worker，每次读或写都是本通道上的请求。在此阻塞子进程等待回复不可能
（那需要 SharedArrayBuffer，而这要求本部署不具备的跨源隔离），因此
文件系统面端到端都是异步的。

对齐上游 `webworker-runtime/src/shell/process/protocol.ts`。公开面仅中文名。
"""
__all__=[#仅中文公开名
    '文件系统操作名们','是否shell启动帧',
]#公开面结束

文件系统操作名们=('stat','list','readText','writeText','mkdir','remove','rename')#文件系统操作名

def 是否shell启动帧(数据):#判定启动帧
    """消息是否为把新 worker 变成 shell 进程的那一帧。"""
    return isinstance(数据,dict) and 数据.get('t')=='shell-start'#结构与类型匹配
