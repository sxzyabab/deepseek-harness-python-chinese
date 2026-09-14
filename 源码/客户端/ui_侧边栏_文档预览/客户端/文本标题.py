
__all__=['文本标题']#仅中文公开名


def 文本标题(取标签信息):
    """产出芯片与浮动面板标题结构。"""
    标签=取标签信息()['tab']#标签
    return {#结构
        'kind':'text-title',
        'title':标签['title'],
        'iconSize':16,
    }#结束
