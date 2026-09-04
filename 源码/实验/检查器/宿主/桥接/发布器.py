"""经专用 Worker MessagePort 的带缓冲 Host 观测发布。

对齐上游 `host/bridge/publisher.ts`。公开面仅中文名。
"""
import threading,time#微任务与时钟
from ...共享.桥接.缓冲 import 检查器源缓冲#源缓冲
from ...共享.桥接.发布器 import 检查器状态发布器#状态发布器面

__all__=['宿主桥发布器']#仅中文公开名

class 宿主桥发布器(检查器状态发布器):#Host桥发布器
    """非阻塞 Host 发布器，以微任务合并 MessagePort 写入。"""
    def __init__(自身,端口,源,选项):#构造
        """创建缓冲。"""
        自身.端口=端口#Worker端口
        自身.源=源#源描述
        自身.记录=检查器源缓冲(选项)#创建缓冲
        自身.冲刷已调度=False#是否已调度冲刷
        自身.在途下一序号=None#在途批次下一序列
        自身.已关闭=False#是否已关闭

    def 发布(自身,主题,载荷,单调毫秒=None):#发布观测
        """发布观测。"""
        if 自身.已关闭:#已关闭忽略
            return#忽略
        if 单调毫秒 is None:#默认时钟
            单调毫秒=time.perf_counter()*1000#近似
        自身.记录.发布(主题,载荷,单调毫秒)#入队
        自身.调度冲刷()#调度冲刷

    def 设置状态(自身,主题,载荷,单调毫秒=None):#设置状态
        """设置状态。"""
        if 自身.已关闭:#已关闭拒绝
            raise Exception('inspector: Host source is closed')#英文诊断
        if 单调毫秒 is None:#默认时钟
            单调毫秒=time.perf_counter()*1000#近似
        自身.记录.设置状态(主题,载荷,单调毫秒)#写入状态
        自身.调度冲刷()#调度冲刷

    def 替换(自身):#替换快照
        """把保留状态作为完整 source 替换发送。"""
        自身.在途下一序号=None#清空在途
        自身.端口.postMessage(自身.记录.替换(自身.源['sourceId'],自身.源['generation']))#发送替换
        自身.调度冲刷()#调度冲刷

    def 冲刷(自身):#冲刷
        """当无更早 MessagePort 批次等待确认时发送一个排队批次。"""
        if 自身.已关闭 or 自身.在途下一序号 is not None:#不可发
            return#返回
        帧=自身.记录.取一批(自身.源['sourceId'],自身.源['generation'])#取批次
        if 帧 is None:#无待发
            return#返回
        自身.端口.postMessage(帧)#发送
        自身.在途下一序号=帧['firstSequence']+len(帧['records'])#记录下一序列

    def 确认(自身,下一序号):#确认
        """释放一个在途批次并调度下一次有界传输。"""
        if 自身.已关闭 or 自身.在途下一序号 is None:#无可确认
            return#返回
        if 下一序号!=自身.在途下一序号:#序列不匹配
            raise Exception('inspector: Host source acknowledgement does not match the in-flight batch')#英文诊断
        自身.在途下一序号=None#清空在途
        自身.调度冲刷()#继续冲刷

    def 关闭(自身):#关闭
        """最多再发一个最终批次，丢弃之后排队的观测，并拒绝后续发布。"""
        if 自身.已关闭:#幂等
            return#返回
        自身.冲刷()#最终冲刷
        自身.已关闭=True#置位
        自身.记录.丢弃待发()#丢弃剩余

    def 调度冲刷(自身):#调度冲刷
        """调度冲刷。"""
        if not 自身.记录.有待发 or 自身.冲刷已调度:#无需或已调度
            return#返回
        自身.冲刷已调度=True#置调度
        def 微任务():#微任务
            """冲刷。"""
            自身.冲刷已调度=False#清调度
            自身.冲刷()#冲刷
        threading.Thread(target=微任务,daemon=True).start()#微任务近似
