"""Worker 拥有的 Client 会话共享清理投递。"""
#对齐上游 worker/bridge/session.ts

__all__=['发送Client会话关闭']#仅中文公开名

def 发送Client会话关闭(源注册表,源,帧):#发送Client会话关闭
    """当传输仍可用时，向活动 Client 代数发送清理帧。"""
    try:#尽力发送
        源注册表.发送(源,帧)#投递帧
    except Exception:#源已失效
        pass#源移除已使该代数拥有的每个会话失效
