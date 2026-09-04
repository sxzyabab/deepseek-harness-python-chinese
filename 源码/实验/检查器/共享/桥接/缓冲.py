"""Host 与 Client 观测源共用的、与界域无关的有界缓冲。

对齐上游 `shared/bridge/buffer.ts`。公开面仅中文名。
"""
from .版本 import 检查器协议版本#协议版本
from ..json import 是否json值,json字节长度#JSON工具

__all__=['检查器源缓冲选项','检查器源缓冲']#仅中文公开名

源帧开销字节=4096#源帧开销字节估算

class 检查器源缓冲选项:#源缓冲选项
    """两种源传输共用的上限与声明主题。"""
    def __init__(自身,topics,maxQueuedRecords,maxQueuedBytes,maxRecordsPerFrame,maxFrameBytes):#构造
        """保存缓冲选项。"""
        自身.topics=tuple(topics)#声明主题
        自身.maxQueuedRecords=maxQueuedRecords#最大排队记录数
        自身.maxQueuedBytes=maxQueuedBytes#最大排队字节
        自身.maxRecordsPerFrame=maxRecordsPerFrame#每帧最大记录数
        自身.maxFrameBytes=maxFrameBytes#每帧最大字节

class 检查器源缓冲:#源缓冲
    """拥有保留状态、排队事件与源本地序号。"""
    def __init__(自身,选项):#缓冲选项
        """初始化队列与状态。"""
        自身.选项=选项#缓冲选项
        自身._队列=[]#排队队列
        自身._状态={}#保留状态
        自身._排队字节=0#排队字节合计
        自身._下一序号=1#下一分配序号
        自身._期望序号=1#期望消费序号

    @property
    def 有待发(自身):#是否有待发
        """是否至少有一条观测在等待传输。"""
        return len(自身._队列)>0#队列非空

    def 发布(自身,topic,payload,monotonicMs):#发布观测
        """校验并入队一条观测，必要时丢掉最旧前缀。"""
        自身._入队(自身._记录(topic,payload,monotonicMs))#入队

    def 设置状态(自身,topic,payload,monotonicMs):#设置状态
        """替换一个保留主题，并把同一观测入队供实时投递。"""
        记录=自身._记录(topic,payload,monotonicMs)#构造记录
        先前=自身._状态.get(topic)#先前状态
        自身._状态[topic]=记录#写入状态
        if not 自身._状态装得下():#状态超帧限
            if 先前 is None:#回滚删除
                自身._状态.pop(topic,None)#删除
            else:#回滚旧值
                自身._状态[topic]=先前#旧值
            raise Exception('inspector: source state exceeds the source-frame byte limit')#英文诊断
        自身._入队(记录)#入队实时投递

    def 替换帧(自身,sourceId,generation):#构造替换帧
        """构造完整状态替换，并吸收此前每一次队列丢弃。"""
        下一序号=自身._队列[0]['sequence'] if 自身._队列 else 自身._下一序号#下一追加序号
        自身._期望序号=下一序号#对齐期望
        return {#替换帧
            'v':检查器协议版本,#协议版本
            't':'source/replace',#帧类型
            'sourceId':sourceId,#源标识
            'generation':generation,#世代
            'nextSequence':下一序号,#下一追加
            'records':list(自身._状态.values()),#全部状态记录
        }#返回结束

    def 取一批(自身,sourceId,generation):#取一批
        """取出并编号下一批传输大小的观测。"""
        if len(自身._队列)==0:#空队列
            return None#无
        批次=[]#本批
        批字节=源帧开销字节#已用字节
        首条=自身._队列[0]#首条
        while len(批次)<自身.选项.maxRecordsPerFrame and len(自身._队列)>0:#填批
            候选=自身._队列[0]#候选
            if 候选['sequence']!=首条['sequence']+len(批次):#序号不连续
                break#中断
            if len(批次)>0 and 批字节+候选['bytes']>自身.选项.maxFrameBytes:#超帧
                break#中断
            自身._队列.pop(0)#出队
            批次.append(候选)#入批
            批字节+=候选['bytes']#累加字节
        自身._排队字节-=sum(项['bytes'] for 项 in 批次)#扣排队字节
        首序号=首条['sequence']#首序号
        帧={#追加帧
            'v':检查器协议版本,#协议版本
            't':'source/append',#帧类型
            'sourceId':sourceId,#源标识
            'generation':generation,#世代
            'firstSequence':首序号,#首序号
            'droppedBefore':首序号-自身._期望序号,#此前丢弃数
            'records':[项['record'] for 项 in 批次],#记录列表
        }#追加帧结束
        自身._期望序号=首序号+len(帧['records'])#推进期望
        return 帧#追加帧

    def 丢弃待发(自身):#丢弃待发
        """丢弃尚未进入传输帧的观测。"""
        自身._队列.clear()#清空队列
        自身._排队字节=0#清字节

    def _记录(自身,topic,payload,monotonicMs):#构造记录
        """校验并构造观测记录。"""
        if len(topic)==0 or len(topic)>128:#主题长度非法
            raise Exception('inspector: topic must contain 1 to 128 characters')#英文诊断
        if '*' not in 自身.选项.topics and topic not in 自身.选项.topics:#未声明主题
            raise Exception(f'inspector: source does not declare topic {topic!r}')#英文诊断
        if not 是否json值(payload):#载荷须JSON
            raise Exception('inspector: source payload must be lossless JSON data')#英文诊断
        if not isinstance(monotonicMs,(int,float)) or isinstance(monotonicMs,bool) or not (monotonicMs==monotonicMs):#时间戳须有限
            raise Exception('inspector: monotonicMs must be finite')#英文诊断
        return {'monotonicMs':monotonicMs,'topic':topic,'payload':payload}#记录

    def _入队(自身,记录):#入队并约束上限
        """入队并裁剪排队上限。"""
        字节=json字节长度(记录)#记录字节
        序号=自身._下一序号#分配序号
        自身._下一序号+=1#推进
        if 字节+源帧开销字节>自身.选项.maxFrameBytes:#单条超帧
            return#消耗序号后丢弃
        自身._队列.append({'sequence':序号,'bytes':字节,'record':记录})#入队
        自身._排队字节+=字节#累加
        while len(自身._队列)>自身.选项.maxQueuedRecords or 自身._排队字节>自身.选项.maxQueuedBytes:#超排队上限
            丢掉=自身._队列.pop(0)#丢掉最旧
            自身._排队字节-=丢掉['bytes']#扣字节

    def _状态装得下(自身):#状态是否装得进一帧
        """状态加开销不超帧。"""
        return json字节长度(list(自身._状态.values()))+源帧开销字节<=自身.选项.maxFrameBytes#状态加开销不超帧
