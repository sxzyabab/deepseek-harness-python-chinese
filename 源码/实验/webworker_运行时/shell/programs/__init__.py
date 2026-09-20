from .内建 import 内建程序
from .文件 import 文件程序
from .文本 import 文本程序

__all__=['标准程序','标准程序表']

_命令表=None

def which程序(argv,io,state=None,fs=None):
    """报告所请求名称中本 shell 能运行的那些。"""
    已知=标准程序()
    状态=0
    for 名 in argv[1:]:
        #每个程序都内建于 shell，因此已知名报告自身，而非 VFS 中不存在的路径。
        if 名 in 已知:
            io['out'](f'{名}: shell 内建命令\n')
            continue
        io['err'](f'which: 工作线程宿主命令表中没有 {名}\n')
        状态=1
    return 状态

def 标准程序():
    """标准命令表，构建一次并由每一行命令共享。"""
    global _命令表
    if _命令表 is None:
        表=dict(内建程序)
        表.update(文件程序)
        表.update(文本程序)
        表['which']=which程序
        _命令表=表
    return _命令表

标准程序表=标准程序
