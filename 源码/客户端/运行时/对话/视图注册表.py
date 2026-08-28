"""按目标划分的会话快照构建器的运行时注册表。

对齐上游 `runtime/src/client/conversation/view-registry.ts`。公开面仅中文名。
"""
from .定义注册表 import 会话定义注册表#基类

__all__=['会话视图注册表']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 会话视图注册表(会话定义注册表):#视图注册表
    """按目标划分的会话快照构建器的运行时注册表。"""

    def __init__(自身,上下文):#绑定上下文
        """服务名 conversationViews。"""
        super().__init__(上下文,'conversationViews')#基类

    def 登记(自身,定义):#登记视图定义
        """在调用方生命周期内登记名字唯一的视图构建器工厂。"""
        目标=取字段(定义,'target')#以目标为键
        return 自身._登记定义(#写入基类表
            目标,#键
            定义,#定义
            'conversation view target "'+str(目标)+'" is already registered',#重复键错误
            'conversationViews.register('+repr(目标)+')',#effect 名
        )#结束
