"""运行器读写的进程流，放在包入口之外，测试替换不扩大公开面。"""
import sys#标准流
__all__=['内部流']#仅中文公开名

def 读标准输入():
    """阻塞读完标准输入，收成 UTF-8 文本。"""
    return sys.stdin.read()#同步读完

内部流={#进程出入；测试可替换
    'stdout':sys.stdout,#标准输出
    'stderr':sys.stderr,#标准错误
    'readStdin':读标准输入,#读标准输入
}#内部流结束
