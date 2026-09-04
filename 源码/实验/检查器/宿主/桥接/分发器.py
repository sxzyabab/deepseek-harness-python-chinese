"""Host MessagePort 接受的已校验 Worker 帧分发。

对齐上游 `host/bridge/dispatcher.ts`。公开面仅中文名。
"""
from ..cdp.控制台 import 拒绝控制台桥命令#拒绝Console桥
from ..cdp.运行时 import 拒绝运行时桥命令#拒绝Runtime桥
from ..cdp.源 import 拒绝源桥命令#拒绝Sources桥

__all__=['宿主桥帧处理器','分发桥帧']#仅中文公开名

class 宿主桥帧处理器:#Host桥帧处理器
    """针对发往 Host 的 source 生命周期帧调用的操作。"""
    def 接纳(自身,帧):#接受
        """接受。"""
        raise NotImplementedError#子类实现
    def 确认(自身,帧):#确认追加
        """确认追加。"""
        raise NotImplementedError#子类实现
    def 重快照(自身,帧):#重快照
        """重快照。"""
        raise NotImplementedError#子类实现
    def 拒绝(自身,帧):#拒绝
        """拒绝。"""
        raise NotImplementedError#子类实现

def 分发桥帧(帧,处理器):#分发桥帧
    """分发一帧已校验的 Worker 帧，并在 Host 载体上拒绝仅 Client 的命令。"""
    类型=帧.get('t') if isinstance(帧,dict) else getattr(帧,'t',None)#类型
    if 类型=='source/accepted':#接受
        处理器.接纳(帧)#回调
        return#结束
    if 类型=='source/append-acknowledged':#追加确认
        处理器.确认(帧)#回调
        return#结束
    if 类型=='source/resnapshot':#重快照
        处理器.重快照(帧)#回调
        return#结束
    if 类型=='source/rejected':#拒绝
        处理器.拒绝(帧)#回调
        return#结束
    if 类型=='client-runtime/request':#Client运行时请求
        return 拒绝运行时桥命令(帧['command'])#Host拒绝
    if 类型 in ('client-runtime/cancel','client-runtime/response-acknowledged'):#取消或确认
        return#忽略
    if 类型 in ('client-console/enable','client-console/disable'):#Console
        return 拒绝控制台桥命令(类型)#Host拒绝
    if 类型=='client-sources/request':#Sources请求
        return 拒绝源桥命令()#Host拒绝
    if 类型 in ('client-runtime/session-closed','client-sources/session-closed'):#会话关闭
        return#忽略
    raise Exception(f'Unexpected Worker source frame: {类型!r}')#未知帧
