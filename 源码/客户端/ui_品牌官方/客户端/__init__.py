import os
from . import 品牌#官方标志与名称

__all__=['品牌','依赖','应用']

环境=os.environ#构建档案
依赖=['slots']#所需服务：槽位登记表

def 应用(上下文,配置=None):
    '官方构建才把侧栏品牌标志和名称登记成同一组。对话主视觉仍用声明包自己的鱼，这里不登记'
    if 环境.get('DSH_CLIENT_BUILD_PROFILE')!='official':
        return#非官方构建不登记

    def 登记名称():
        '标志和名称一起登记，卸下时按相反顺序拆'
        yield 上下文.slots.register({'name':'sidebar.brand.mark'},品牌.官方品牌标志)#登记标志
        yield 上下文.slots.register({'name':'sidebar.brand.name'},品牌.官方品牌名称)#登记名称

    def 登记标志():
        '名称槽声明之后，再把这一组登记进去'
        return 上下文.slots.inject('sidebar.brand.name',登记名称)#等名称槽声明

    上下文.slots.inject('sidebar.brand.mark',登记标志)#等标志槽声明

inject=依赖#框架槽
apply=应用#框架槽
