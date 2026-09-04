"""标准 SessionProvider 席位的会话自有渲染语义。

对齐上游 `ui-session/src/client/session-provider.tsx`。公开面仅中文名。
无真 React：返回结构树字典。
"""
__all__=['渲染会话区域']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 渲染会话区域(绑定,属性):#渲染当前选中会话体或其空分支
    """按会话身份加 key 的选中子树；无选中走空分支。"""
    空态=取字段(属性,'empty')#空态工厂
    子节点=取字段(属性,'children')#选中子树
    会话标识=取字段(绑定,'key')#绑定键即 SessionId，缺席表示未选中
    if 会话标识 is None:#无选中
        空树=空态() if callable(空态) else None#走空分支
        return {'type':'session-area-empty','children':空树}#空态树
    return {'type':'session-area','key':会话标识,'children':子节点}#按身份稳定挂载
