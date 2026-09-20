from . import json深度相等

包名='@deepseek-ai/dsh-settings'
名称='settings-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 安装(上下文,失败):
    """settings/updated 只对当前已注册命名空间发出，只在解析值变化时发出。"""
    def 监听更新(命名空间,下一值,上一值,*位置参数):
        """监听已提交的设置解析值变更。"""
        设置=上下文.获取服务('settings')
        if 设置 is None:
            失败('settings/updated 针对 "'+str(命名空间)+'" 发出时没有活的设置服务')
        if 命名空间 not in 设置:
            失败('settings/updated 针对 "'+str(命名空间)+'" 发出时该命名空间未注册')
        当前=设置[命名空间]
        if not json深度相等(当前,下一值):
            失败('settings/updated 针对 "'+str(命名空间)+'" 与权威解析值不一致')
        if json深度相等(下一值,上一值):
            失败('settings/updated 针对 "'+str(命名空间)+'" 在解析值未变时发出')
    上下文.监听('settings/updated',监听更新)

def 应用(上下文):
    """注册本包的不变量配套，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
