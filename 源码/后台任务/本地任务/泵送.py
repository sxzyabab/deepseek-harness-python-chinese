"""注册表自有的拉取泵：按有界节拍把任务的输出源拷进环，生产者结算后再抽干一次。"""
import math,threading
from concurrent.futures import Future as 原生结果

def 启动泵送(源列表,汇,轮询毫秒,直到):
    """按数组顺序抽干每个源，睡 pollMs 或等到 until 结算，再抽最后一次。"""
    if (isinstance(轮询毫秒,bool) or not isinstance(轮询毫秒,(int,float))
        or not math.isfinite(轮询毫秒) or 轮询毫秒<=0):
        raise ValueError('invalid pump pollMs: expected a positive finite number of milliseconds, got '+repr(轮询毫秒))
    状态列表=[{'source':源,'cursor':0} for 源 in 源列表]
    已结算=threading.Event()
    完成=原生结果()

    def 抽干():
        """按源顺序读增量并写入汇。"""
        下标=0
        while 下标<len(状态列表):
            状态=状态列表[下标]
            源=状态['source']
            读=源['read'](状态['cursor']) if isinstance(源,dict) else 源.read(状态['cursor'])
            状态['cursor']=读['nextOffset']
            路径=读['spillPath'] if 'spillPath' in 读 else None
            汇['spill'](下标,路径)
            文本=读['text']
            if len(文本)==0:
                下标+=1
                continue
            通道=源['channel'] if isinstance(源,dict) and 'channel' in 源 else getattr(源,'channel',None)
            有损=读['lossy'] if 'lossy' in 读 else False
            if 通道 is None and (not 有损):
                汇['append'](文本)
            else:
                选项={}
                if 通道 is not None:
                    选项['channel']=通道
                if 有损:
                    选项['gapBefore']=True
                汇['append'](文本,选项)
            下标+=1

    def 循环():
        """轮询直到结算再最后抽一次。"""
        try:
            while not 已结算.is_set():
                抽干()
                已结算.wait(轮询毫秒/1000.0)
            抽干()
            完成.set_result(None)
        except BaseException as 错误:
            if not 完成.done():
                完成.set_exception(错误)

    def 等到结算():
        """until 结算（兑现或拒绝都算）后结束轮询。"""
        try:
            if hasattr(直到,'等待'):
                直到.等待()
            elif hasattr(直到,'result'):
                直到.result()
        except BaseException:
            pass
        已结算.set()

    轮询线程=threading.Thread(target=循环,daemon=True)
    监视线程=threading.Thread(target=等到结算,daemon=True)
    轮询线程.start()
    监视线程.start()

    class 泵送句柄:
        """一次泵运行；done.等待 在最后一次抽干后返回。"""
        def 等待(自身,超时=None):
            """阻塞到泵结束。"""
            return 完成.result(timeout=超时)

    句柄=泵送句柄()
    句柄.done=句柄
    return 句柄

__all__=['启动泵送']
