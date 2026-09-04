"""通用浏览器品牌槽位的官方 DeepSeek Harness 占位。

对齐上游 `ui-brand-official/src/client/index.ts`。公开面仅中文名。
把侧栏品牌槽位作为一组声明感知注册填满。
"""
from .品牌 import 官方品牌标志,官方品牌名称#官方标志与名称

__all__=['注入','应用','官方品牌标志','官方品牌名称']#仅中文公开名

注入=['slots']#所需服务：UI 槽位注册表

def 应用(上下文):#浏览器侧安装入口
    """非官方构建不注册；官方构建填满侧栏品牌槽。"""
    import os#读构建档案
    if os.environ.get('DSH_CLIENT_BUILD_PROFILE')!='official':#非官方
        return#不注册
    def 登记名称():#等 name 声明后再登记
        """嵌套登记标志与名称。"""
        yield 上下文.slots.register({'name':'sidebar.brand.mark'},官方品牌标志)#登记标志
        yield 上下文.slots.register({'name':'sidebar.brand.name'},官方品牌名称)#登记名称
    上下文.slots.inject('sidebar.brand.mark',lambda:上下文.slots.inject('sidebar.brand.name',登记名称))#嵌套 inject
