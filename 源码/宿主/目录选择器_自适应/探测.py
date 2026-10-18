'在 PATH 里探测原生后端能驱动的 Linux 选择器'
import os#路径与执行权限

__all__=['能否执行','有Linux选择器二进制']#公开探测

Linux选择器二进制=('zenity','kdialog')#原生后端在 Linux 上可驱动的选择器


def 能否执行(候选):
    '候选路径具有执行权限时为真。不存在或不可执行时为假'
    try:#对应 accessSync(候选, X_OK)
        可执行=os.access(候选,os.X_OK)#只查执行权限
    except OSError as 权限错误:#不存在或权限检查失败
        return False#权限错误即不可执行
    return 可执行#检查结果


def 有Linux选择器二进制(路径值,可执行谓词):
    '扫描一段 PATH。空段跳过。缺席或空串扫不到任何目录'
    if 路径值 is None:#对应 ?? ''
        路径文本=''#当作空 PATH
    else:#调用方给出的原文
        路径文本=路径值#原样拆段
    for 目录 in 路径文本.split(os.pathsep):#逐段
        if 目录=='':#空段
            continue#跳过
        for 二进制名 in Linux选择器二进制:#先 zenity，再 kdialog
            if 可执行谓词(os.path.join(目录,二进制名)):#这一段里有可执行选择器
                return True#找到
    return False#没有任何一段有
