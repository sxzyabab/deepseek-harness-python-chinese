"""Perplexity web 搜索提供方无运行时不变量配套。"""
包名='@deepseek-ai/dsh-web-search-perplexity'
名称='web-search-perplexity-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','应用','默认']

def 安装(上下文,失败):
    """无运行时不变量：本包不暴露独立事件序列或可变数据关系。"""
    return

def 应用(上下文):
    """注册本包的不变量配套，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
