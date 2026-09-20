"""Client Agent 作用域原语：铸造带所属 Agent 身份标签的 Cordis 上下文。

代际身份按对象同一性比较；过滤器住在作用域上下文自身。
"""
from ....依赖 import cordis#Cordis
上下文类=cordis.上下文#上下文类

__all__=['创建作用域','作用域标签','作用域身份']#仅中文公开名

_作用域符号=object()#作用域标签符号（对齐 Symbol）

def _空插件(_上下文=None,_配置=None):
    """支撑每个 Agent 作用域 fiber 的共享空操作插件。"""
    return#无注册

def 创建作用域(上下文,键):
    """在根上下文下铸造 Agent 作用域。

    返回 dict：`ctx` 带标签上下文，`fiber` 支撑纤程（有 dispose）。
    """
    纤程=上下文.启动插件(_空插件)#挂空操作插件
    身份={'sessionId':键}#代际身份对象
    def 过滤器(监听上下文):
        """无标签全局接纳；带标签仅匹配同一代际对象。"""
        标签=作用域身份(监听上下文)#读代际
        return 标签 is None or 标签 is 身份#同一性
    扩展={_作用域符号:身份}#标签
    if hasattr(上下文类,'过滤'):#有过滤符号
        扩展[上下文类.过滤]=过滤器#写入过滤
    带标签=纤程.ctx.扩展(扩展)#扩展
    return {'ctx':带标签,'fiber':纤程}#句柄

def 作用域身份(上下文):
    """读取 Client Context 继承的精确代际身份；无作用域为 None。"""
    if hasattr(上下文,'__dict__') and _作用域符号 in 上下文.__dict__:#自有
        return 上下文.__dict__[_作用域符号]#身份
    return None#无

def 作用域标签(上下文):
    """读取上下文继承到的最近 agent 标签；根为 None。"""
    身份=作用域身份(上下文)#代际
    if 身份 is None:#无
        return None#无
    return 身份['sessionId']#会话身份
