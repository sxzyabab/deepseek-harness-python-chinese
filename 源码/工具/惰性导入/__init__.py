__all__=['创建惰性导入']

def 创建惰性导入(规格名,父网址):
    """按调用方相对解析创建成功结果缓存。失败的加载不缓存。父网址对应调用方 import.meta.url。"""
    已加载=False
    值=None
    def 加载():
        """首次成功后复用同一模块值。"""
        nonlocal 已加载,值
        if not 已加载:
            值=__import__(规格名)
            已加载=True
        return 值
    return 加载
