"""启动子进程与子进程共用的继承字节通道协议。"""
import os#环境与描述符

__all__=('子进程控制描述符','子进程控制环境','打开继承控制通道')#仅中文公开名

子进程控制描述符=7#为可选子进程控制通道保留的子描述符
子进程控制环境='DSH_SUBPROCESS_CONTROL'#Node 子进程执行应用代码前消费的私有启动标记

def 打开继承控制通道():#打开 fd 7 上的继承控制管
    """消费启动标记并打开 fd 7 上的继承控制管。返回调用方拥有的字节双工流。标记缺失/非法或描述符打不开则抛错。"""
    if 子进程控制环境 not in os.environ:#无标记
        raise RuntimeError('subprocess control channel was not inherited')#未继承
    标记=os.environ[子进程控制环境]#读标记
    del os.environ[子进程控制环境]#消费后删除
    if 标记!='pipe':#必须是 pipe
        raise RuntimeError('subprocess control channel was not inherited')#未继承
    return os.fdopen(子进程控制描述符,'r+b',buffering=0)#调用方拥有描述符
