"""兼容入口：完整实现见 `自定义提供方卡片`。

对齐上游 `CustomProviderCard.tsx`；本文件避免与完整卡双份逻辑。
"""
from .自定义提供方卡片 import 自定义提供方卡片,路由模式#完整卡

__all__=['自定义提供方卡','自定义提供方卡片','路由形','校验路由','路由模式']#公开面

自定义提供方卡=自定义提供方卡片#短名别名
路由形=路由模式#短名

def 校验路由(路由,已占):#路由是否可提交
    """返回阻挡键；可提交则为 None。"""
    if 路由=='':#空
        return 'routeRequired'#必填
    if 路由模式.match(路由) is None:#不合规则
        return 'routeInvalid'#非法
    if 路由 in (已占 or []):#碰撞
        return 'routeTaken'#占用
    return None#可提交
