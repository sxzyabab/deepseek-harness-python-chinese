"""文本类型的芯片标题：打开时注册表捕获的名字前的文件类型彩色表。

对齐上游 `ui-sidebar-documentpreview/src/client/TextTitle.tsx`。公开面仅中文名。
"""

__all__=['文本标题']#仅中文公开名


def 文本标题(取标签信息):
    """产出芯片与浮动面板标题结构。"""
    标签=取标签信息()['tab']#标签
    return {#结构
        'kind':'text-title',
        'title':标签['title'],
        'iconSize':16,
    }#结束
