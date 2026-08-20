"""独立拥有的会话业务定义的运行时注册表。

对齐上游 `runtime/src/client/conversation/event-registry.ts`。公开面仅中文名。
"""
from .定义注册表 import 会话定义注册表#基类

__all__=['会话事件注册表']#仅中文公开名

def 断言定义目标(定义):#target 与 buildViewNode 必须同时有或同时无
    """一对一错配时加载期大声失败。"""
    目标=定义.get('target') if isinstance(定义,dict) else getattr(定义,'target',None)#目标
    构建=定义.get('buildViewNode') if isinstance(定义,dict) else getattr(定义,'buildViewNode',None)#构建器
    if (目标 is None)!=(构建 is None):#一对一错配
        种类=定义.get('kind') if isinstance(定义,dict) else getattr(定义,'kind','')#kind
        raise Exception('conversation Definition "'+str(种类)+'" must declare target and buildViewNode together')#失败

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 会话事件注册表(会话定义注册表):#事件定义注册表
    """独立拥有的会话业务定义的运行时注册表。"""

    def __init__(自身,上下文):#绑定上下文
        """服务名 conversationEvents。"""
        自身._回退=None#未匹配事件的唯一回退
        super().__init__(上下文,'conversationEvents')#基类

    def 登记(自身,定义):#登记普通定义
        """在调用方生命周期内登记名字唯一的业务定义。"""
        断言定义目标(定义)#成对检查
        种类=取字段(定义,'kind')#以 kind 为键
        return 自身._登记定义(#写入基类表
            种类,#键
            定义,#定义
            'conversation Definition "'+str(种类)+'" is already registered',#重复键错误
            'conversationEvents.register('+repr(种类)+')',#effect 名
        )#结束

    def 登记回退(自身,定义):#登记回退
        """登记仅在没有普通定义匹配时使用的唯一回退。"""
        断言定义目标(定义)#成对检查
        目标=取字段(定义,'target')#回退必须声明目标
        if 目标 is None:#缺目标
            raise Exception('conversation fallback Definition must declare a target')#失败
        if 自身._回退 is not None:#已有回退
            raise Exception('conversation fallback Definition is already registered')#单占用者
        拥有方=自身.ctx#调用方光纤
        种类=取字段(定义,'kind')#kind
        def 效应():#归调用方光纤
            自身._回退=定义#写入回退
            自身._刷新()#刷新缓存
            def 拆除():#拆除
                if 自身._回退 is not 定义:#已被替换
                    return#不动
                自身._回退=None#清回退
                自身._刷新()#刷新
            return 拆除#拆除器
        拆除器=拥有方.effect(效应,'conversationEvents.registerFallback('+repr(种类)+')')#effect
        def 同步拆除():#包成同步 disposer（对齐 void dispose()）
            if callable(拆除器):#同步拆除器
                拆除器()#调用
        return 同步拆除#disposer

    def 回退条目(自身):#读回退
        """返回当前未匹配事件的回退（若有）。"""
        return 自身._回退#当前回退
