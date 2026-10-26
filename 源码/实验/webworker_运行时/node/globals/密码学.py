from uuid import uuid4

__all__=['安装密码学全局']

def 随机uuid():
    '随机 v4 UUID 字符串'
    return str(uuid4())

def 安装密码学全局():
    '在上下文不提供时安装 `crypto.randomUUID`'
    #安全上下文中平台方法已存在，保持不动。
    密码=globals()['crypto']
    已有=getattr(密码,'randomUUID',None)
    if callable(已有): return
    密码.randomUUID=随机uuid
