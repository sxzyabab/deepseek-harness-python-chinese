"""远程流物理载体失败与终端分类。

对齐上游 `api/gateway/src/client/stream-client.ts` 的载体错误面；
完整 WebSocket 复用客户端（mux）硬阻塞，不在本文件交付。公开面仅中文名。
"""
__all__=['远程流载体错误']#仅中文公开名


class 远程流载体错误(Exception):
    """可由域传输重试的物理 Remote 流套接字失败。"""

    def __init__(自身,消息,原因=None):
        """记下消息与可选因果。"""
        super().__init__(消息)#构造
        自身.name='RemoteStreamCarrierError'#稳定名
        if isinstance(原因,BaseException):#有因果
            自身.__cause__=原因#挂上
