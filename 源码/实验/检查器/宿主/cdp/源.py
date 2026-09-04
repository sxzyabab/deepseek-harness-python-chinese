"""Host Sources 由 Worker 侧 Node inspector 适配器直接提供。

对齐上游 `host/cdp/sources.ts`。公开面仅中文名。
"""
__all__=['源桥能力','拒绝源桥命令']#仅中文公开名

def 源桥能力(_可用):#Sources桥能力
    """描述 Host Sources 传输所有权。"""
    return None#无桥

def 拒绝源桥命令():#拒绝Sources桥命令
    """拒绝被路由到 Host source 的 Client Sources 请求。"""
    raise Exception('inspector protocol: Client Sources cannot use the Host source bridge')#抛错
