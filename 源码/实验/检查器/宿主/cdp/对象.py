"""Host RemoteObject handle 从不经 Host source 桥。

对齐上游 `host/cdp/objects.ts`。公开面仅中文名。
"""
from .错误 import 宿主cdp桥不可用错误#桥不可用错误

__all__=['拒绝对象桥操作']#仅中文公开名

def 拒绝对象桥操作(操作):#拒绝对象桥操作
    """拒绝必须使用 Worker 拥有的原生 inspector session 的对象操作。"""
    raise 宿主cdp桥不可用错误(操作)#抛错
