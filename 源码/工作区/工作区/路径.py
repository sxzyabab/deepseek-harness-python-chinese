"""工作区身份的路径规范化。对齐上游 workspace/src/paths.ts。"""
import os#realpath
__all__=['规范化真实路径']#仅中文公开名

def 规范化真实路径(路径):#realpath 规范化目录路径
    """经 realpath 规范化目录路径；不存在路径以原始错误拒绝。"""
    return os.path.realpath(路径)#解析真实路径
