"""经 Worker MessagePort 的 Host 侧非 CDP 查询桥。

对齐上游 `host/bridge/rpc.ts`。公开面仅中文名。
"""
from ...共享.桥接.rpc import 检查器查询连接#查询连接基类

__all__=['宿主桥rpc']#仅中文公开名

class 宿主桥rpc(检查器查询连接):#Host桥RPC
    """拥有一个 Host source 代数的查询关联。"""
    def __init__(自身,端口,选项):#绑定端口
        """构造。"""
        super().__init__(选项)#基类
        自身.端口=端口#端口

    def 接通端口(自身,源):#接通端口
        """Worker 接受 Host source 后接通查询写入。"""
        class _发送器:#发送器
            def 发送(内,帧):#发送帧
                """发送帧。"""
                自身.端口.postMessage(帧)#发送帧
        自身.连接(源['sourceId'],源['generation'],_发送器())#连接
