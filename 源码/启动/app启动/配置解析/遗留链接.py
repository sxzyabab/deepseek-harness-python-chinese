"""磁盘物化与运行时解析器共用的遗留配置链接检视。"""
import os,sys#路径与进程
__all__=[#仅中文公开名
    '配置模块回退目录名','是否打包可执行文件','真实模块目录','规范链接路径',
    '链接是否指向','是否配置模块回退链接',
]#公开面结束

配置模块回退目录名='.dsh-module-fallback'#配置私有回退目录名

def 是否打包可执行文件():
    """进程是否从打包虚拟文件系统读应用模块。"""
    return getattr(sys,'frozen',False) or hasattr(sys,'dsh_packaged')#打包标志

def 真实模块目录(路径):
    """经活动载体的文件系统实现解析目录。"""
    return os.path.realpath(路径)#规范目录

def 规范链接路径(路径):
    """解析链接目标，不跟随最终路径分量。父目录缺失则返回 None。"""
    try:#解析父目录真实路径
        return os.path.join(真实模块目录(os.path.dirname(路径)),os.path.basename(路径))#拼回基名
    except OSError as 错误:#解析失败
        if getattr(错误,'errno',None)==2 or getattr(错误,'winerror',None)==3:#父目录缺失
            return None#无法标识已有托管链接
        raise#其余失败抛出

def 链接是否指向(链接,目标):
    """符号链接或 junction 是否指向与目标同一路径。"""
    实际=os.path.normpath(os.path.join(os.path.dirname(链接),os.readlink(链接)))#解析实际目标
    规范实际=规范链接路径(实际)#规范实际路径
    规范目标=规范链接路径(os.path.abspath(目标))#规范期望路径
    return 规范实际 is not None and 规范实际==规范目标#两者相同

def 是否配置模块回退链接(配置目录,包名):
    """观察到的配置包是否不得主张本地优先。检视期间消失视为回退链接。"""
    链接=os.path.join(配置目录,'node_modules',包名)#投影路径
    目标=os.path.join(配置目录,配置模块回退目录名,'node_modules',包名)#拥有回退
    try:#检查投影
        return os.path.islink(链接) and 链接是否指向(链接,目标)#指向托管则是回退
    except OSError as 错误:#投影缺失或其他
        if getattr(错误,'errno',None)==2:#缺失则排除该候选
            return True#消失的候选不能主张本地优先
        raise#其余失败抛出
