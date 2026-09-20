__all__=['发送Client会话关闭']#仅中文公开名

def 发送Client会话关闭(源注册表,源,帧):#发送Client会话关闭
    """当传输仍可用时，向活动 Client 代数发送清理帧。"""
    try:#尽力发送
        源注册表.发送(源,帧)#投递帧
    except Exception:#源注册表.发送在源已拆时可能抛 OSError/RuntimeError，契约未定所以收不窄
        pass#源移除已使该代数拥有的每个会话失效
