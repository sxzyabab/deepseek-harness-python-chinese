"""Node 内部模块加载器兼容层。Python 无对应内部加载器。"""

class 模块阶段:
    """Node 内部模块请求阶段。"""
    源码=1#Source
    求值=2#Evaluation
    Source=1#英文别名
    Evaluation=2#英文别名

_缓存加载器=None#fromInternal 缓存

class 模块加载器:
    """定位当前 Node 内部模块加载器的辅助。"""
    @staticmethod
    def 从内部():
        """取出 Node 级联加载器；Python 运行时没有该内部对象。"""
        global _缓存加载器#复用缓存
        if _缓存加载器:
            return _缓存加载器#已缓存
        return None#无 Node internals

ModulePhase=模块阶段#英文别名
ModuleLoader=模块加载器#英文别名
模块加载器.fromInternal=模块加载器.从内部#英文别名
