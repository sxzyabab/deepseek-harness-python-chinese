"""use-sync-external-store 本地类型声明伴生。

对齐上游 `ui-renderer/src/client/use-sync-external-store.d.ts`。公开面仅中文名。
Python 侧无模块声明；保留带选择器的 uSES 形状说明。
"""
__all__=['带选择器同步外部存储']#仅中文公开名

def 带选择器同步外部存储(订阅,取快照,取服务器快照,选择器,相等=None):#带选择器的 uSES
    """本包传 取服务器快照=None；相等性可选。"""
    快照=取快照()#客户端快照
    return 选择器(快照)#选中切片
