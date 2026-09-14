from .....工具.加密 import 随机uuid#UUID实现

__all__=['安装密码学全局']#仅中文公开名

def 安装密码学全局():#安装crypto全局补丁
    """在上下文不提供时安装 `crypto.randomUUID`。"""
    #安全上下文中平台方法已存在，保持不动。
    密码=globals()['crypto']#crypto实例
    已有=getattr(密码,'randomUUID',None)#已有方法
    if callable(已有): return#已有则跳过
    密码.randomUUID=随机uuid#补上randomUUID
