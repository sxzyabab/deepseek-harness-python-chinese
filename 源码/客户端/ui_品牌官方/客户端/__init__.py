import os#读构建档案
from .品牌 import 官方品牌标志,官方品牌名称#官方标志与名称

__all__=['依赖','应用','官方品牌标志','官方品牌名称']#仅中文公开名

依赖=['slots']#所需服务：UI 槽位注册表

def 应用(上下文):
    """非官方构建不注册；官方构建填满侧栏品牌槽。"""
    if os.environ.get('DSH_CLIENT_BUILD_PROFILE')!='official':
        return#不注册
    def 登记名称():
        """嵌套登记标志与名称。"""
        yield 上下文.slots.register({'name':'sidebar.brand.mark'},官方品牌标志)#登记标志
        yield 上下文.slots.register({'name':'sidebar.brand.name'},官方品牌名称)#登记名称
    def 登记标志():
        """等 name 声明后再登记。"""
        return 上下文.slots.inject('sidebar.brand.name',登记名称)#嵌套 inject
    上下文.slots.inject('sidebar.brand.mark',登记标志)#嵌套 inject

inject=依赖#框架槽
apply=应用#框架槽
