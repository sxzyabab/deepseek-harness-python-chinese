"""面向与传输无关的 Cordis 树读取器的、基于查询的适配器。

对齐上游 `shared/bridge/query-reader.ts`。公开面仅中文名。
"""
from ..cordis.读取器 import cordis运行时树读取器#树读取器基类

__all__=['创建查询cordis运行时树读取器']#仅中文公开名

def 创建查询cordis运行时树读取器(请求器):#创建查询读取器
    """创建一个通过类型化 Inspector 查询协议获取树的读取器。"""
    class _读取器(cordis运行时树读取器):#查询适配读取器
        def 获取树(自身):#获取树
            """通过查询协议读取最新树。"""
            结果=请求器.请求({'op':'cordis-tree/get'})#发查询
            if hasattr(结果,'result'):#Future
                结果=结果.result()#取结果
            return 结果['tree']#返回树
    return _读取器()#返回结束
