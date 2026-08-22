"""Node 内部模块加载器的对应层。Python 运行时没有这样一个内部对象。"""

class 模块阶段:
    """Node 内部模块请求的阶段。"""
    源码=1#只要源码，不求值
    求值=2#求值到模块命名空间

class 模块加载器:
    """定位当前 Node 内部模块加载器。"""
    @staticmethod
    def 从内部():
        """取出 Node 的级联加载器。Python 里没有对应对象，恒为空。"""
        return None#没有 Node 内部加载器
