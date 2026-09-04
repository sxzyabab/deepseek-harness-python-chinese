"""已校验 Worker 帧到浏览器 realm 能力处理器的分发。

对齐上游 `client/bridge/dispatcher.ts`。公开面仅中文名。
"""
__all__=['客户端桥帧处理器','分发桥帧']#仅中文公开名

class 客户端桥帧处理器:#Client桥帧处理器
    """针对每个 Worker→Client 帧族调用的操作。"""
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
    def 运行时(自身,帧):#Runtime请求
        """Runtime请求。"""
        raise NotImplementedError#子类实现
    def 运行时取消(自身,帧):#Runtime取消
        """Runtime取消。"""
        raise NotImplementedError#子类实现
    def 运行时确认(自身,帧):#Runtime响应确认
        """Runtime响应确认。"""
        raise NotImplementedError#子类实现
    def 运行时关闭(自身,帧):#Runtime会话关闭
        """Runtime会话关闭。"""
        raise NotImplementedError#子类实现
    def 控制台启用(自身,帧):#Console启用
        """Console启用。"""
        raise NotImplementedError#子类实现
    def 控制台禁用(自身,帧):#Console禁用
        """Console禁用。"""
        raise NotImplementedError#子类实现
    def 源(自身,帧):#Sources请求
        """Sources请求。"""
        raise NotImplementedError#子类实现
    def 源关闭(自身,帧):#Sources会话关闭
        """Sources会话关闭。"""
        raise NotImplementedError#子类实现

def 分发桥帧(帧,处理器):#分发桥帧
    """分发一帧已校验的 Worker 帧，且不向领域适配器暴露传输细节。"""
    类型=帧.get('t')#类型
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
    if 类型=='client-runtime/request':#Runtime请求
        处理器.运行时(帧)#回调
        return#结束
    if 类型=='client-runtime/cancel':#取消
        处理器.运行时取消(帧)#回调
        return#结束
    if 类型=='client-runtime/response-acknowledged':#响应确认
        处理器.运行时确认(帧)#回调
        return#结束
    if 类型=='client-runtime/session-closed':#运行时会话关闭
        处理器.运行时关闭(帧)#回调
        return#结束
    if 类型=='client-console/enable':#Console启用
        处理器.控制台启用(帧)#回调
        return#结束
    if 类型=='client-console/disable':#Console禁用
        处理器.控制台禁用(帧)#回调
        return#结束
    if 类型=='client-sources/request':#Sources请求
        处理器.源(帧)#回调
        return#结束
    if 类型=='client-sources/session-closed':#Sources会话关闭
        处理器.源关闭(帧)#回调
        return#结束
    raise Exception(f'Unexpected Worker source frame: {类型!r}')#未知帧
