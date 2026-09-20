"""原生后端 Linux 选择器二进制的 PATH 探测。"""
import os#路径与可执行探测

__all__=['能否执行','有Linux选择器二进制','Linux选择器二进制']#公开面

Linux选择器二进制=('zenity','kdialog')#原生后端在 Linux 上可驱动的选择器

def 能否执行(候选):
    """当前进程是否可执行该候选路径。"""
    return os.path.isfile(候选) and os.access(候选,os.X_OK)#存在且可执行

def 有Linux选择器二进制(路径值,可执行谓词=None):
    """在一段 PATH 值里扫描原生后端的 Linux 选择器二进制。"""
    谓词=能否执行 if 可执行谓词 is None else 可执行谓词
    if 路径值 is None or 路径值=='':
        return False
    for 目录 in 路径值.split(os.pathsep):
        if 目录=='':
            continue
        for 名 in Linux选择器二进制:
            if 谓词(os.path.join(目录,名)):
                return True
    return False
