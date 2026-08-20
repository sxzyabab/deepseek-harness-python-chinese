"""文件系统沙箱的路径包含判定。规范拼写走快速词法路径；文件系统身份为 Windows 8.3 名与大小写等别名等价根提供保守回退。"""
import os,sys,errno#目录名、分隔符、平台大小写惯例与缺失errno

缺失码=set(('ENOENT','ENOTDIR'))#视为路径缺失的错误码集合

def 取错误码(错误):#取出系统错误码
    """从 OSError 或带 code 的错误取出码字符串。"""
    码=getattr(错误,'code',None)#Node风格code
    if isinstance(码,str):#已有字符串码
        return 码#直接用
    if isinstance(错误,OSError) and 错误.errno is not None:#POSIX errno
        return errno.errorcode.get(错误.errno)#映射为名
    return None#无码

def 是否缺失(错误):#判断错误是否表示路径缺失
    """判断错误是否表示路径缺失。"""
    码=取错误码(错误)#取出系统错误码
    if 码 is not None and 码 in 缺失码:#属于缺失码集合
        return True#缺失
    if isinstance(错误,OSError) and 错误.errno in (errno.ENOENT,errno.ENOTDIR):#按errno判定
        return True#缺失
    return False#不是缺失

def 可比较路径(路径,区分大小写):#按是否区分大小写得到可比较路径
    """按是否区分大小写得到可比较路径。"""
    if 区分大小写:#区分大小写
        return 路径#原样
    return 路径.lower()#折成小写

def 是否词法位于下(路径,根,区分大小写):#词法判断path是否位于root之下
    """词法判断路径是否位于根之下。"""
    可比较目标=可比较路径(路径,区分大小写)#可比较的目标路径
    可比较根=可比较路径(根,区分大小写)#可比较的根路径
    if 可比较目标==可比较根:#两者相同则算包含
        return True#包含
    分隔=os.sep#路径分隔符
    前缀=可比较根 if 可比较根.endswith(分隔) else 可比较根+分隔#根路径加分隔符作为前缀
    return 可比较目标.startswith(前缀)#目标是否以根前缀开头

def 若存在则状态(路径):#路径存在则stat，缺失则空
    """路径存在则返回 os.stat 结果，缺失则 None。"""
    try:#尝试stat该路径
        return os.stat(路径)#用宿主stat取身份字段
    except Exception as 错误:#捕获stat失败
        if 是否缺失(错误):#缺失则当作不存在
            return None#不存在
        raise 错误#其他错误原样抛出

def 同一身份(左,右):#比较两个stat是否同一文件系统身份
    """比较两个 stat 是否同一文件系统身份。"""
    return 左.st_dev==右.st_dev and 左.st_ino==右.st_ino#设备号与inode都相同才算同一身份

def 是否路径位于下(路径,根,区分大小写=None):#判断规范路径是否位于可写根之下
    """判断规范目标是否就是可写根，或位于其下。词法快路径处理普通规范拼写。拼写不同时，走目标已存在的祖先并与根比较文件系统身份；这样能识别 Windows 长名/8.3 别名与大小写，而不会把包含关系削弱成文本近似。

    路径：规范目标键，末尾可能是尚不存在的后缀。
    根：规范可写根。
    区分大小写：词法比较是否保留大小写；缺省采用宿主文件系统惯例（非 win32 区分大小写）。
    返回：目标是否就是根或其后代。
    """
    if 区分大小写 is None:#缺省采用宿主文件系统惯例
        区分大小写=sys.platform!='win32'#非win32区分大小写
    if 是否词法位于下(路径,根,区分大小写):#词法已包含则直接成立
        return True#包含
    根信息=若存在则状态(根)#stat可写根
    if 根信息 is None:#根不存在则无法按身份包含
        return False#不包含
    祖先=路径#从目标路径开始向上走祖先
    while True:#逐级检查祖先身份
        祖先信息=若存在则状态(祖先)#stat当前祖先
        if 祖先信息 is not None and 同一身份(祖先信息,根信息):#身份与根相同则包含成立
            return True#包含
        父=os.path.dirname(祖先)#取上一层目录
        if 父==祖先:#已到文件系统根仍未匹配则不包含
            return False#不包含
        祖先=父#继续向上
