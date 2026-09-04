"""Cordis 插件入口的浏览器 Client 桥构造。

对齐上游 `client/bridge/controller.ts`。公开面仅中文名。
"""
from .传输 import 客户端检查器源#Client源
from ..检视.领域 import 客户端领域源#realm源

__all__=['启动检查器客户端']#仅中文公开名

def 启动检查器客户端(引导):#启动Client检查器
    """为一个已校验的 Host bootstrap 启动浏览器 source 传输。"""
    标签='Client'#标签；浏览器可用 document.title
    try:#取标题
        import builtins#全局
        文档=getattr(builtins,'document',None)#document
        if 文档 is not None and getattr(文档,'title',None):#有标题
            标签=文档.title or 'Client'#标签
    except Exception:#忽略
        pass#忽略
    领域源=客户端领域源.声明(标签)#声明realm身份
    try:#构造传输
        return 客户端检查器源(引导,标签,None,领域源)#创建源
    except Exception:#失败
        领域源.关闭()#释放身份
        raise#继续抛出
