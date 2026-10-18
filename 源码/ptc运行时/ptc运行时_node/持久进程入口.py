'持久 Node REPL 的私有构建入口'
import os,sys#环境、目录与参数
from ...子进程.子进程.控制 import 打开继承控制通道#继承控制管
from .持久进程 import 运行持久主程序#子进程主程序

class 持久进程:#本子进程的环境、输出与目录
    '环境、输出流与工作目录；只在 REPL 上下文里暴露'
    def __init__(自身):#钉到当前进程
        '绑到当前进程的环境与标准流'
        自身.env=os.environ#环境
        自身.stdout=sys.stdout#标准输出
        自身.stderr=sys.stderr#标准错误
        自身.控制读线程=None#通道读线程

    def chdir(自身,目录):#换工作目录
        '换到宿主给出的目录'
        os.chdir(目录)#进程工作目录

if __name__=='__main__':#子进程入口
    状态=持久进程()#本进程
    运行持久主程序(打开继承控制通道(),int(sys.argv[1]),状态)#主程序期约
    if 状态.控制读线程 is not None:#读线程已启动
        状态.控制读线程.join()#读线程结束再退出
