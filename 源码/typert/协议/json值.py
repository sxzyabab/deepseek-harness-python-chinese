"""远程载体共用的无损 JSON 检查。"""
import math

def 是否远程json值(值):
    """值能否在 JSON 传输上不强制转换、不省略。"""
    return 走访json值(值,set())

def 是否远程上行项(值):
    """值可否作为一条上行项：无损 JSON，或顶层 None（对应 TS undefined）。"""
    return 值 is None or 是否远程json值(值)

def 走访json值(值,祖先):
    """递归检查无损 JSON。"""
    if 值 is None or isinstance(值,str) or isinstance(值,bool):
        return True
    if isinstance(值,float):
        return math.isfinite(值) and not (值==0.0 and math.copysign(1.0,值)<0)
    if isinstance(值,int) and not isinstance(值,bool):
        return True
    if type(值) is list:
        身份=id(值)
        if 身份 in 祖先:
            return False
        祖先.add(身份)
        try:
            for 项 in 值:
                if not 走访json值(项,祖先):
                    return False
            return True
        finally:
            祖先.discard(身份)
    if type(值) is not dict:
        return False
    身份=id(值)
    if 身份 in 祖先:
        return False
    祖先.add(身份)
    try:
        for 键 in 值:
            if not isinstance(键,str):
                return False
            if not 走访json值(值[键],祖先):
                return False
        return True
    finally:
        祖先.discard(身份)

__all__=['是否远程json值','是否远程上行项']
