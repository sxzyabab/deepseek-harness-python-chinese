"""启动提供方读取的进程事实，放在启动入口之外，测试替换不扩大公开面。"""
import sys#标准流
__all__=['内部流']#仅中文公开名

def 标准输入是否终端():
    """标准输入是否接到终端。"""
    return bool(getattr(sys.stdin,'isatty',lambda:False)())#TTY 探测

内部流={#进程事实；测试可替换
    'stdinIsTty':标准输入是否终端,#是否终端
    'stdout':sys.stdout,#标准输出
}#内部流结束
