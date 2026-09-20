__all__=['读持久会话']

def 读持久会话(持久化,标识,信号):
    """经短命读句柄读取已存会话的头与完整事件日志，返回前关闭句柄。"""
    句柄=持久化.open(标识,'read',{'signal':信号})
    try:
        return {
            'header':句柄.header,
            'inheritedEventCount':句柄.inheritedEventCount,
            'events':句柄.read(0,None,{'signal':信号}),
        }
    finally:
        句柄.close()
