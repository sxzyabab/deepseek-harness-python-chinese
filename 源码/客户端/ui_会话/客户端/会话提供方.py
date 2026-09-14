__all__=['渲染会话区域']#仅中文公开名

def 渲染会话区域(绑定,属性):#渲染当前选中会话体或其空分支
    """按会话身份加 key 的选中子树；无选中走空分支。"""
    空态=属性['empty'] if 'empty' in 属性 else None#空态工厂
    子节点=属性['children'] if 'children' in 属性 else None#选中子树
    会话标识=绑定['key'] if 绑定 is not None and 'key' in 绑定 else None#绑定键即 SessionId，缺席表示未选中
    if 会话标识 is None:#无选中
        空树=空态() if 空态 is not None else None#走空分支
        return {'type':'session-area-empty','children':空树}#空态树
    return {'type':'session-area','key':会话标识,'children':子节点}#按身份稳定挂载
