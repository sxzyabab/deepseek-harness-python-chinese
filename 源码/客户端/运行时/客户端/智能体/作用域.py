"""客户端 Agent 作用域原语：铸造带所属 Agent 身份标签的 Cordis 上下文。

对齐上游 `runtime/src/client/agents/scope.ts`。公开面仅中文名。
机制镜像宿主 dsh-scope（空操作插件光纤 + 上下文标签 + 过滤器）；
作用域键是会话 id（智能体与会话 1:1）。
"""

__all__=['铸造作用域','作用域身份','作用域键符号']#仅中文公开名

作用域键符号='dsh.client.scope'#作用域身份符号键（字符串化；无 JS Symbol）

def 作用域身份(上下文):#读作用域身份
    """读取上下文继承到的最近智能体标签；根上下文则为 None。"""
    return getattr(上下文,作用域键符号,None)#符号键上的会话 id

def 铸造作用域(上下文,键):#铸造 Agent 作用域
    """在 ctx 下铸造 Agent 作用域：空操作插件光纤 + 标签与派发过滤器。

    @param 上下文 - 作用域光纤挂到其下的客户端根上下文。
    @param 键 - 所属智能体身份（会话 id）。
    @returns {'ctx':带标签上下文,'fiber':支撑光纤}。
    """
    def 空插件():#支撑每个 Agent 作用域光纤的共享空操作插件
        """空插件体。"""
        return#无贡献
    光纤=上下文.plugin(空插件)#挂空操作插件，得到光纤
    过滤器键=getattr(type(上下文),'filter',None) or getattr(上下文,'__class__',object).__dict__.get('filter')#Cordis filter 键
    扩展={}#叠标签与过滤器
    扩展[作用域键符号]=键#写入智能体身份
    def 过滤器(监听上下文):#派发过滤器
        """未标签或同一智能体才放行。"""
        标签=作用域身份(监听上下文)#监听器上下文上的身份
        return 标签 is None or 标签==键#未标签或同一智能体
    if 过滤器键 is not None:#有 filter 槽
        扩展[过滤器键]=过滤器#写入过滤器
    带标签=光纤.ctx.extend(扩展) if hasattr(光纤.ctx,'extend') else 光纤.ctx#叠标签
    setattr(带标签,作用域键符号,键)#保证可读
    return {'ctx':带标签,'fiber':光纤}#句柄
