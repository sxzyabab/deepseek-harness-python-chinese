"""进程域惰性取得栅格库入口。"""
from PIL import Image as 图像#栅格入口
__all__=['取锐化']#仅中文公开名

_入口=None#首次栅格操作后保留

def 取锐化():
    """第一次栅格操作时装入并保留可调用入口。"""
    global _入口#进程内单例
    if _入口 is None:#尚未装入
        _入口=图像#PIL 入口即 Sharp 可调用面
    return _入口#可调用入口
