"""经专用 MessagePort 的 Host realm 观测发布器。

对齐上游 `host/bridge/transport.ts`。公开面仅中文名。
"""
from ...共享.桥接.消息.观察 import 检查器协议版本,解析工作者源帧#观测消息
from ...共享.桥接.发布器 import 检查器源连接#源连接基类
from ..检视.领域 import 创建宿主领域源#Host源描述工厂
from .发布器 import 宿主桥发布器#桥发布器
from .rpc import 宿主桥rpc#桥RPC
from .分发器 import 分发桥帧#帧分发

__all__=['宿主源选项','宿主检查器源']#仅中文公开名

class 宿主源选项:#Host源选项
    """单个 source 发布器的缓冲上限。"""
    def __init__(自身,label,topics,maxQueuedRecords,maxQueuedBytes,maxRecordsPerFrame,maxFrameBytes,queryTimeoutMs):#构造
        """保存选项。"""
        自身.label=label#标签
        自身.topics=tuple(topics)#主题
        自身.maxQueuedRecords=maxQueuedRecords#队列记录上限
        自身.maxQueuedBytes=maxQueuedBytes#队列字节上限
        自身.maxRecordsPerFrame=maxRecordsPerFrame#每帧记录上限
        自身.maxFrameBytes=maxFrameBytes#帧字节上限
        自身.queryTimeoutMs=queryTimeoutMs#查询超时

class 宿主检查器源(检查器源连接):#Host检查器源
    """非阻塞 Host 源；队列溢出由下一批次的 droppedBefore 表示。"""
    def __init__(自身,端口,选项):#绑定端口与选项
        """构造并打开源。"""
        源=创建宿主领域源(选项.label)#创建源描述
        发布器=宿主桥发布器(端口,源,选项)#发布器
        查询=宿主桥rpc(端口,{'timeoutMs':选项.queryTimeoutMs,'maxFrameBytes':选项.maxFrameBytes})#查询
        super().__init__(发布器,查询)#基类
        自身.端口=端口#端口
        自身.源=源#realm源描述
        自身.发布器实例=发布器#桥发布器
        自身.查询实例=查询#查询RPC
        自身.已关闭=False#是否已关闭
        def 入站(值):#入站消息
            """入站消息。"""
            try:#解析分发
                if 自身.查询实例.接收(值):#RPC已消费
                    return#结束
                自身.接收帧(解析工作者源帧(值))#源帧
            except Exception:#畸形则关闭
                自身.关闭()#关闭源
        端口.on('message',入站)#入站消息
        端口.on('close',lambda:自身.查询实例.断开('Inspector Host source disconnected'))#端口关闭
        端口.start()#启动端口
        打开={'v':检查器协议版本,'t':'source/open','source':源,'topics':list(选项.topics)}#打开帧
        端口.postMessage(打开)#发送打开
        发布器.替换()#请求重快照

    def 关闭(自身):#关闭
        """冲刷待发观测并关闭 source 端口。"""
        if 自身.已关闭:#幂等
            return#返回
        自身.发布器实例.关闭()#关闭发布器
        自身.已关闭=True#置位
        自身.查询实例.关闭('Inspector Host source closed')#关闭查询
        帧={'v':检查器协议版本,'t':'source/close','sourceId':自身.源['sourceId'],'generation':自身.源['generation']}#关闭帧
        自身.端口.postMessage(帧)#发送关闭
        自身.端口.close()#关闭端口

    def 接收帧(自身,帧):#接收Worker帧
        """接收 Worker 帧。"""
        if 帧.get('t')!='source/rejected' and (帧.get('sourceId')!=自身.源['sourceId'] or 帧.get('generation')!=自身.源['generation']):#身份不匹配
            return#忽略
        class _处理器:#分发处理器
            def 接纳(内,_帧):#接受后接通查询
                """接受后接通查询。"""
                自身.查询实例.接通端口(自身.源)#接通
            def 确认(内,确认帧):#确认序列
                """确认序列。"""
                自身.发布器实例.确认(确认帧['nextSequence'])#确认
            def 重快照(内,_帧):#重快照
                """重快照。"""
                自身.发布器实例.替换()#替换
            def 拒绝(内,拒绝帧):#拒绝
                """拒绝。"""
                自身.查询实例.断开(f'Inspector Host source rejected: {拒绝帧["message"]}')#断开
        分发桥帧(帧,_处理器())#分发
