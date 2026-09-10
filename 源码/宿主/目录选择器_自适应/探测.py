"""原生后端 Linux 选择器二进制的 PATH 探测。

对齐上游 `directory-picker-auto/src/probe.ts`。公开面仅中文名。
"""
import os#路径与可执行探测

__all__=['能否执行','有Linux选择器二进制','Linux选择器二进制']#公开面

Linux选择器二进制=('zenity','kdialog')#原生后端在 Linux 上可驱动的选择器

def 能否执行(候选):#canExecute
    """当前进程是否可执行该候选路径。"""
    return os.path.isfile(候选) and os.access(候选,os.X_OK)#存在且可执行

def 有Linux选择器二进制(路径值,可执行谓词=None):#hasLinuxChooserBinary
    """在一段 PATH 值里扫描原生后端的 Linux 选择器二进制。"""
    谓词=能否执行 if 可执行谓词 is None else 可执行谓词#默认谓词
    if 路径值 is None or 路径值=='':#缺省或空
        return False#不扫描
    for 目录 in 路径值.split(os.pathsep):#按平台分隔符拆
        if 目录=='':#空段
            continue#跳过
        for 名 in Linux选择器二进制:#逐个试
            if 谓词(os.path.join(目录,名)):#命中
                return True#有选择器
    return False#没有
