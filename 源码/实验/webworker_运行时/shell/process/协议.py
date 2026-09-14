__all__=[#仅中文公开名
    '文件系统操作名表','是否shell启动帧',
]#公开面结束

文件系统操作名表=('stat','list','readText','writeText','mkdir','remove','rename')#文件系统操作名

def 是否shell启动帧(数据):#判定启动帧
    """消息是否为把新 worker 变成 shell 进程的那一帧。"""
    return isinstance(数据,dict) and 数据.get('t')=='shell-start'#结构与类型匹配
