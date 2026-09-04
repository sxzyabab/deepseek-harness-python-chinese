"""补上非安全源上缺失的 `crypto.randomUUID`。浏览器仅在安全上下文暴露
`randomUUID`，而经普通 HTTP 在局域网地址提供的预览不算——
产品代码（打包的与 VFS 加载的一样）会按 Node 风格直接访问该全局。
Worker 修补这一份 `crypto` 实例，而不是教每个调用方。

对齐上游 `webworker-runtime/src/node/globals/crypto.ts`。公开面仅中文名。
"""
from .....工具.加密 import 随机uuid#UUID实现

__all__=['安装密码学全局']#仅中文公开名

def 安装密码学全局():#安装crypto全局补丁
    """在上下文不提供时安装 `crypto.randomUUID`。"""
    #安全上下文中平台方法已存在，保持不动。
    密码=globals()['crypto']#crypto实例
    已有=getattr(密码,'randomUUID',None)#已有方法
    if callable(已有): return#已有则跳过
    密码.randomUUID=随机uuid#补上randomUUID
