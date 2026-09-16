"""构建后的 Node 运行时子进程入口；源码执行直接调用 运行节点主程序。"""
import os,sys#环境与标准流
from ...子进程.子进程.控制 import 打开继承控制通道#继承控制管
from .进程 import 运行节点主程序#子进程主程序

class 程序进程:#本子进程的环境与输出流
    """环境、输出流与退出码。"""
    def __init__(自身):#钉到当前进程
        """绑到当前进程的环境与标准流。"""
        自身.env=os.environ#环境
        自身.stdout=sys.stdout#标准输出
        自身.stderr=sys.stderr#标准错误
        自身.exitCode=None#退出码

if __name__=='__main__':#子进程入口
    状态=程序进程()#本进程
    运行节点主程序(打开继承控制通道(),int(sys.argv[1]),状态)#主程序
    码=状态.exitCode#退出码
    sys.exit(0 if 码 is None else 码)#按码退出
