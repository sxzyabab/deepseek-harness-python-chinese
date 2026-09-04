"""命令表：本 shell 能运行的每个程序名。浏览器 worker 不派生进程，因此此表
就是机器的 `/bin`——不在表中的名称报告 `command not found`，与真 shell
对未安装二进制的报告完全一致。

对齐上游 `webworker-runtime/src/shell/programs/index.ts`。公开面仅中文名。
"""
from .内建 import 内建程序#内建程序表
from .文件 import 文件程序#文件程序表
from .文本 import 文本程序#文本程序表

__all__=['标准程序','标准程序表']#仅中文公开名

_命令表=None#懒构建命令表

def which程序(argv,io,state=None,fs=None):#which程序
    """报告所请求名称中本 shell 能运行的那些。"""
    已知=标准程序()#读取命令表
    状态=0#累积退出状态
    for 名 in argv[1:]:#逐个查询名
        # 每个程序都内建于 shell，因此已知名报告自身，而非 VFS 中不存在的路径。
        if 名 in 已知:#表中有名
            io['out'](f'{名}: shell built-in command\n')#报告内建
            continue#下一名称
        io['err'](f'which: no {名} in the worker host command table\n')#报告未找到
        状态=1#标记失败
    return 状态#返回状态

def 标准程序():#获取标准命令表
    """标准命令表，构建一次并由每一行命令共享。"""
    global _命令表#懒表
    if _命令表 is None:#首次构建表
        表=dict(内建程序)#并入内建
        表.update(文件程序)#并入文件工具
        表.update(文本程序)#并入文本工具
        表['which']=which程序#注册which
        _命令表=表#落表
    return _命令表#返回共享表

标准程序表=标准程序#别名（供索引再导出）
