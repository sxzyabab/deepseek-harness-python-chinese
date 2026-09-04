"""Host Runtime 由 Worker 侧 Node inspector 适配器直接提供。

对齐上游 `host/cdp/runtime.ts`。公开面仅中文名。
"""
from .错误 import 宿主cdp桥不可用错误#桥不可用错误
from .对象 import 拒绝对象桥操作#拒绝对象操作
from .属性 import 拒绝属性桥操作#拒绝属性操作

__all__=['运行时桥能力','拒绝运行时桥命令']#仅中文公开名

def 运行时桥能力(_来源):#Runtime桥能力
    """描述 Host Runtime 传输所有权。"""
    return None#无桥

def 拒绝运行时桥命令(命令):#拒绝Runtime桥命令
    """拒绝被路由到 Host source 的 Client Runtime 命令。"""
    操作=命令.get('op') if isinstance(命令,dict) else getattr(命令,'op',None)#操作
    if 操作=='get-properties':#取属性
        return 拒绝属性桥操作()#拒绝属性
    if 操作 in ('release-object','release-object-group'):#释放对象
        return 拒绝对象桥操作(f'client-runtime/{操作}')#拒绝对象
    if 操作 in ('evaluate','call-function','await-promise','global-lexical-scope-names'):#求值类
        raise 宿主cdp桥不可用错误(f'client-runtime/{操作}')#不可用
    raise Exception(f'Unexpected Host Runtime bridge command: {命令!r}')#未知命令
