"""文档读取与渲染共享的不确定加载反馈。

对齐上游 `ui-sidebar-documentpreview/src/client/LoadingIndicator.tsx`。公开面仅中文名。
"""

__all__=['加载指示器']#仅中文公开名


def 加载指示器(标签,类名=None):
    """产出动画、可访问的加载状态结构。"""
    return {'kind':'loading','label':标签,'className':类名,'role':'status'}#结构
