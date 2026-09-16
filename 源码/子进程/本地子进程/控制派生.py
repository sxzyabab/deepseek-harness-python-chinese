"""显式请求的继承控制管在父侧的装配。"""
from ..子进程.控制 import 子进程控制环境,子进程控制描述符#标记与 fd

__all__=('控制管道','控制环境')#仅中文公开名

def 控制管道(孩子,控制=None):#从 stdio 元组读额外管
    """读取 Node 风格 stdio 元组里的可选额外管。未请求或原生启动失败则缺席。"""
    if 控制!='pipe':#未请求
        return None#缺席
    if hasattr(孩子,'stdio'):#有 stdio 元组
        流表=孩子.stdio#只读元组
        if 子进程控制描述符<len(流表):#槽存在
            return 流表[子进程控制描述符]#父端双工
        return None#原生启动失败
    if hasattr(孩子,'控制'):#本包句柄直接挂控制端
        return 孩子.控制#父端
    return None#缺席

def 控制环境(环境,控制=None):#盖启动标记
    """拒绝调用方覆盖后，在新子环境上盖私有标记。"""
    for 键,值 in 环境.items():#逐条
        if 键.upper()==子进程控制环境 and 值 is not None:#调用方占用保留名
            raise RuntimeError(子进程控制环境+' is reserved for subprocess control-channel setup')#保留
    if 控制=='pipe':#请求控制管
        环境[子进程控制环境]='pipe'#盖标记
    return 环境#同一份环境
