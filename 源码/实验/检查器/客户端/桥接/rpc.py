"""经活动 Worker WebSocket 的 Client 侧非 CDP 查询桥。

对齐上游 `client/bridge/rpc.ts`。公开面仅中文名。
"""
import json#序列化
from ...共享.桥接.rpc import 检查器查询连接#查询连接基类

__all__=['客户端桥rpc']#仅中文公开名

class 客户端桥rpc(检查器查询连接):#Client桥RPC
    """跨重连 Client source 代数拥有查询关联。"""
    def 接通套接字(自身,源,套接字):#接通套接字
        """将查询写入接到一个已接受的 Client WebSocket 代数。"""
        class _发送器:#发送器
            def 发送(内,帧):#发送帧
                """发送帧。"""
                if getattr(套接字,'readyState',1)!=1:#未开
                    raise Exception('Inspector Client query socket is not connected')#未开
                套接字.send(json.dumps(帧,ensure_ascii=False))#发送
        自身.连接(源['sourceId'],源['generation'],_发送器())#连接
