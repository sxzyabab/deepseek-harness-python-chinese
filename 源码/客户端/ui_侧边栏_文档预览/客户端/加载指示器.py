
__all__=['加载指示器']#仅中文公开名


def 加载指示器(标签,类名=None):
    """产出动画、可访问的加载状态结构。"""
    return {'kind':'loading','label':标签,'className':类名,'role':'status'}#结构
