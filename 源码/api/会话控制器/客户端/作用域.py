"""Client Agent 作用域原语：铸造带所属 Agent 身份标签的 Cordis 上下文。

对齐上游 `session-controller/src/client/scope.ts`。公开面仅中文名。
机制镜像主机作用域，但过滤器住在作用域上下文自身；作用域键是会话 id（按值比较）。
"""
from ....依赖 import cordis#Cordis
上下文类=cordis.上下文#上下文类

__all__=['创建作用域','作用域标签']#仅中文公开名

_作用域符号=object()#作用域标签符号（对齐 Symbol）

def _空插件(_上下文=None,_配置=None):
    """支撑每个 Agent 作用域 fiber 的共享空操作插件。"""
    return#无注册

def 创建作用域(上下文,键):
    """在根上下文下铸造 Agent 作用域。

    返回 dict：`ctx` 带标签上下文，`fiber` 支撑光纤（有 dispose）。
    """
    光纤=上下文.启动插件(_空插件)#挂空操作插件
    def 过滤器(监听上下文):
        """无标签全局接纳；带标签仅匹配本 agent。"""
        标签=作用域标签(监听上下文)#读标签
        return 标签 is None or 标签==键#匹配
    扩展={_作用域符号:键}#标签
    if hasattr(上下文类,'过滤'):#有过滤符号
        扩展[上下文类.过滤]=过滤器#写入过滤
    带标签=光纤.ctx.扩展(扩展)#扩展
    return {'ctx':带标签,'fiber':光纤}#句柄

def 作用域标签(上下文):
    """读取上下文继承到的最近 agent 标签；根为 None。"""
    if hasattr(上下文,'__dict__') and _作用域符号 in 上下文.__dict__:#自有
        return 上下文.__dict__[_作用域符号]#标签
    return None#无
