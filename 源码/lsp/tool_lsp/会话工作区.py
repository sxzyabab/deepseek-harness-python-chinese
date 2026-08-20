"""推导一次 `lsp` 调用所相对的工作区根：调用方 agent 的按会话工作区（`exec.agent.session.header.cwd`），与文件系统工具解析路径的方式一致。
与那些工具不同，LSP 没有提供方回退——缺失 cwd 会使调用以 `LSP_WORKSPACE_REQUIRED` 失败，因为本地提供方必须先规范化真实工作区才能启动服务器。
"""

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 会话工作区(执行上下文):#从工具执行上下文取出会话工作区cwd
    """本次调用的会话工作区 cwd；不适用时为 None。
    @param 执行上下文 - 工具执行上下文；只读取其可选的 agent
    @returns 调用方 agent 的会话 cwd；非 agent 调用方则为 None
    """
    智能体=取字段(执行上下文,'agent')#可选调用方智能体
    if 智能体 is None:#非 agent 调用方
        return None#没有会话工作区
    会话=取字段(智能体,'session')#会话对象
    if 会话 is None:#没有会话
        return None#没有会话工作区
    头=取字段(会话,'header')#会话头
    if 头 is None:#没有会话头
        return None#没有会话工作区
    return 取字段(头,'cwd')#会话头上的 cwd
