"""Client 风格 CDP 桥命令误路由到 Host 时的显式失败。

对齐上游 `host/cdp/errors.ts`。公开面仅中文名。
"""
from .栈 import 宿主cdp桥原因#拒绝原因常量

__all__=['宿主cdp桥不可用错误']#仅中文公开名

class 宿主cdp桥不可用错误(Exception):#Host CDP桥不可用
    """Host Runtime 使用 Worker 侧 Node inspector session，而非 source RPC。"""
    def __init__(自身,操作):#构造
        """保存操作名。"""
        super().__init__(f'inspector protocol: {操作} cannot use the Host source bridge; {宿主cdp桥原因}')#消息
