"""与环境无关的 Cordis 运行时树读取器。

对齐上游 `shared/cordis/reader.ts`。公开面仅中文名。
"""
__all__=['cordis运行时树读取器','创建cordis运行时树读取器']#仅中文公开名

class cordis运行时树读取器:#运行时树读取器
    """对最新已提交、对消费者中立的 Cordis 树的只读访问。"""
    def 获取树(自身):#获取树
        """读取最新 Worker 快照，不激活 CDP 域。"""
        raise NotImplementedError#子类实现

def 创建cordis运行时树读取器(读取):#创建运行时树读取器
    """围绕本地已提交树投影创建读取器。"""
    class _读取器(cordis运行时树读取器):#包装读取器
        def 获取树(自身):#获取树
            """同步或异步的最新树读取。"""
            return 读取()#委托
    return _读取器()#读取器
