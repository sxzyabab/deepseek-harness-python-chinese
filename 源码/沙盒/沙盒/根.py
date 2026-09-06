"""每个把模式表达为规范允许列表的强制方言共用的可写根推导：workspace-write 表示工作区根加上平台临时区，本模块是该含义的唯一所在。Seatbelt 配置与进程内文件系统围栏都在这里推导允许列表，因此它们之间不能出现写工具不能写 /tmp 但 bash 能写的不对称。"""
import os,tempfile#规范路径解析与平台临时目录

def 规范路径(路径):
    """把已授权根解析成强制层实际比较的路径：规范路径（符号链接已解析），因为 Seatbelt 过滤器与 fs 围栏的包含检查都匹配已解析路径——darwin 上 /tmp 就是 /private/tmp，按拼写授权会什么都匹配不到。解析失败则原样拼写——缺失的根在它存在之前什么都不匹配，保守结果；发明回落会授权调用方从未点名的路径。"""
    try:
        return os.path.realpath(路径)#按文件系统逐分量解析
    except OSError:
        #路径或其前缀缺失或不可读
        return 路径#保守：原样拼写，不发明回落

def 可写根(政策):
    """一次隔离执行可以写入其下的根。政策是 dict。read-only 什么都不允许；workspace-write 允许政策的工作区根、宿主 /tmp，以及每用户平台临时目录。"""
    if 政策['mode']!='workspace-write':#非工作区可写则无可写根
        return []#空允许列表
    return list(dict.fromkeys([规范路径(政策['workspaceRoot']),规范路径('/tmp'),规范路径(tempfile.gettempdir())]))#去重后的规范根，保插入序
