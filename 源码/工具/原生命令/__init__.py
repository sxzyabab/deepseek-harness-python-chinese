import os,subprocess,threading,errno
__all__=[
    '已中止','挂失败','运行原生命令','原生命令运行器','原生命令错误',
    '可打开原生路径','原生文件管理器','揭示原生路径','打开原生路径','打开原生文本文件',
]

class 原生命令错误(Exception):
    """宿主原生命令失败，附加码与捕获输出。"""
    def __init__(自身,消息,码,标准输出,标准错误,原因):
        """把退出/系统码与两路捕获输出挂到异常上。"""
        super().__init__(消息)
        自身.code=码
        自身.stdout=标准输出
        自身.stderr=标准错误
        自身.cause=原因

def 已中止(信号):
    """信号按 threading.Event 定死。"""
    if 信号 is None:
        return False
    return 信号.is_set()

def 挂失败(消息,码,标准输出,标准错误,原因):
    """把退出/系统码与两路捕获输出挂到异常上。"""
    return 原生命令错误(消息,码,标准输出,标准错误,原因)

def 运行原生命令(命令,参数列表,信号):
    """以 utf8 标准输入输出、中止传播和 Windows 隐藏方式运行宿主命令。

    命令是可执行路径或 PATH 名；参数列表是 argv（绝不是 shell 字符串）；信号是调用方/连接寿命，中止则终止子进程。
    退出码为 0 时返回捕获的 stdout/stderr（映射 `{'stdout','stderr'}`）。
    """
    if 已中止(信号):
        底层=原生命令错误('The operation was aborted','ABORT_ERR','','',None)#ABORT_ERR 字面量不翻译
        raise 挂失败(str(底层),'ABORT_ERR','','',底层)
    参数表=list(参数列表)
    关键字={'stdout':subprocess.PIPE,'stderr':subprocess.PIPE,'shell':False,'text':True,'encoding':'utf-8'}
    if os.name=='nt':
        关键字['creationflags']=subprocess.CREATE_NO_WINDOW#对应 windowsHide:true
    try:
        进程=subprocess.Popen([命令]+参数表,**关键字)
    except FileNotFoundError as 错误:
        raise 挂失败(str(错误),'ENOENT','','',错误)
    except OSError as 错误:
        if 错误.errno==errno.ENOENT:
            码='ENOENT'
        else:
            码=错误.errno
        raise 挂失败(str(错误),码,'','',错误)
    因中止杀掉=threading.Event()

    def 监视():
        """轮询中止与进程结束：避免只阻塞在信号.等待上导致进程已退后监视线程僵死。"""
        while 进程.poll() is None:
            if 已中止(信号):
                因中止杀掉.set()
                进程.kill()
                return
            threading.Event().wait(0.01)

    监视线程=threading.Thread(target=监视,daemon=True)
    监视线程.start()
    标准输出,标准错误=进程.communicate()
    if 标准输出 is None:
        标准输出=''
    if 标准错误 is None:
        标准错误=''
    if 进程.returncode==0:
        return {'stdout':标准输出,'stderr':标准错误}
    if 因中止杀掉.is_set():
        底层=原生命令错误('The operation was aborted','ABORT_ERR',标准输出,标准错误,None)#ABORT_ERR 字面量不翻译
        raise 挂失败(str(底层),'ABORT_ERR',标准输出,标准错误,底层)
    底层=原生命令错误('命令失败','FAILED',标准输出,标准错误,None)
    raise 挂失败(str(底层),进程.returncode,标准输出,标准错误,底层)

原生命令运行器=运行原生命令

from .路径打开 import (
    可打开原生路径,原生文件管理器,揭示原生路径,打开原生路径,打开原生文本文件,
)
