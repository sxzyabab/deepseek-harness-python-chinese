"""工作区身份的路径规范化。"""
import os
__all__=['规范化真实路径']

def 规范化真实路径(路径):
    """经 realpath 规范化目录路径；不存在路径以原始错误拒绝。"""
    return os.path.realpath(路径)
