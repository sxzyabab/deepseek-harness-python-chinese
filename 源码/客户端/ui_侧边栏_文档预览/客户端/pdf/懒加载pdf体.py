"""PDF 正文挂载后再加载渲染器。"""
from .pdf体 import pdf体#PDF 正文

__all__=['懒加载pdf体']#仅中文公开名

def 懒加载pdf体(属性):
    """在包内 PDF 块到达前悬挂；本地直接转调正文。"""
    return pdf体(
        属性.get('content'),
        属性.get('useTabInfo'),
        属性.get('useStore'),
        属性.get('actions'),
        属性.get('retainTab'),
        属性.get('t'),
    )#转调
