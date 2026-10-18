from .传输 import 客户端检查器源#Client源
from ..检视.领域 import 客户端领域源#realm源

__all__=['启动检查器客户端']#仅中文公开名

def 启动检查器客户端(引导,窗口):#启动Client检查器
    '为一个已校验的 Host bootstrap 启动浏览器 source 传输。窗口用这次握手传进来的'
    标题=窗口.document.title
    if isinstance(标题,str) and 标题!='':
        标签=标题
    else:
        标签='Client'
    领域源=客户端领域源.声明(标签)#声明realm身份
    try:#构造传输
        return 客户端检查器源(引导,标签,None,领域源)#创建源
    except Exception:#客户端检查器源构造可能抛传输/引导错误，契约未定所以收不窄
        领域源.关闭()#拆除身份
        raise#继续抛出
