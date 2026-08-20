"""每个把模式表达为规范允许列表的强制方言共用的可写根推导：workspace-write 表示工作区根加上平台临时区，本模块是该含义的唯一所在。Seatbelt 配置与进程内文件系统围栏都在这里推导允许列表，因此它们之间不能出现写工具不能写 /tmp 但 bash 能写的不对称。"""
import os,tempfile#规范路径解析与平台临时目录

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 规范路径(路径):#解析为规范路径
    """把已授权根解析成强制层实际比较的路径：规范路径（符号链接已解析），因为 Seatbelt 过滤器与 fs 围栏的包含检查都匹配已解析路径——darwin 上 /tmp 就是 /private/tmp，按拼写授权会什么都匹配不到。解析失败则原样拼写——缺失的根在它存在之前什么都不匹配，保守结果；发明回落会授权调用方从未点名的路径。Python 仅有 os.path.realpath，对齐 Node realpathSync.native 的逐分量语义；无独立 .native，也不走 JS 实现那种先词法折叠 .. 的路径。"""
    try:#os.path.realpath 可能因缺失或不可读失败；对齐 realpathSync.native，Python 无 .native
        return os.path.realpath(路径)#按文件系统逐分量解析
    except Exception:#路径或其前缀缺失或不可读；只有这类抛出能到这里
        return 路径#保守：原样拼写，不发明回落

def 可写根(政策):#推导可写根
    """一次隔离执行可以写入其下的根——该模式作为规范、去重允许列表的含义。read-only 什么都不允许；workspace-write 允许政策的工作区根、宿主 /tmp，以及每用户平台临时目录。"""
    if 取字段(政策,'mode')!='workspace-write':#非工作区可写则无可写根
        return []#空允许列表
    return list(dict.fromkeys([规范路径(取字段(政策,'workspaceRoot')),规范路径('/tmp'),规范路径(tempfile.gettempdir())]))#去重后的规范根，保插入序
