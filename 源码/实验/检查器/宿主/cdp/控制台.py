"""Host Console 由 Worker 侧 Node inspector 适配器直接提供。

对齐上游 `host/cdp/console.ts`。公开面仅中文名。
"""
__all__=['控制台桥能力','拒绝控制台桥命令']#仅中文公开名

def 控制台桥能力():#Console桥能力
    """描述 Host Console 传输所有权。"""
    return None#无桥

def 拒绝控制台桥命令(操作):#拒绝Console桥命令
    """拒绝被路由到 Host source 的 Client Console 控制帧。"""
    raise Exception(f'inspector protocol: {操作} cannot use the Host source bridge')#抛错
