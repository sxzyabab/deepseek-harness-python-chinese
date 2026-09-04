"""跨重连 WebSocket 的带缓冲 Client 观测发布。

对齐上游 `client/bridge/publisher.ts`。公开面仅中文名。
"""
import json,time#序列化与时钟
from ...共享.桥接.缓冲 import 检查器源缓冲#源缓冲
from ...共享.桥接.发布器 import 检查器状态发布器#状态发布器面

__all__=['客户端桥发布器']#仅中文公开名

class 客户端桥发布器(检查器状态发布器):#Client桥发布器
    """非阻塞 Client 发布器，有界状态在传输重连后仍保留。"""
    def __init__(自身,选项,最大缓冲字节):#构造
        """创建缓冲。"""
        自身.记录=检查器源缓冲(选项)#创建缓冲
        自身.最大缓冲字节=最大缓冲字节#套接字缓冲上限
        自身.活动=None#活动发布
        自身.已关闭=False#是否已关闭

    def 发布(自身,主题,载荷,单调毫秒=None):#发布观测
        """发布观测。"""
        if 自身.已关闭:#已关闭忽略
            return#忽略
        if 单调毫秒 is None:#默认
            单调毫秒=time.perf_counter()*1000#近似
        自身.记录.发布(主题,载荷,单调毫秒)#入队
        自身.冲刷()#冲刷

    def 设置状态(自身,主题,载荷,单调毫秒=None):#设置状态
        """设置状态。"""
        if 自身.已关闭:#已关闭拒绝
            raise Exception('inspector: Client source is closed')#英文诊断
        if 单调毫秒 is None:#默认
            单调毫秒=time.perf_counter()*1000#近似
        自身.记录.设置状态(主题,载荷,单调毫秒)#写入状态
        自身.冲刷()#冲刷

    def 连接(自身,套接字,源):#连接
        """安装一个尚未打开的传输代数。"""
        自身.活动={'socket':套接字,'source':源,'accepted':False}#安装活动

    def 接受(自身,套接字):#接受
        """Worker 接受后发送保留状态与排队观测。"""
        活动=自身.活动#活动
        if 活动 is None or 活动['socket'] is not 套接字:#非本套接字
            return#返回
        活动['accepted']=True#置接受
        自身.替换(套接字)#发送替换
        自身.冲刷()#冲刷队列

    def 替换(自身,套接字):#替换快照
        """为活动代数重发保留状态。"""
        活动=自身.活动#活动
        if 活动 is None or 活动['socket'] is not 套接字:#不可发
            return#返回
        就绪=getattr(套接字,'readyState',1)#就绪态
        if 就绪!=1:#未开
            return#返回
        套接字.send(json.dumps(自身.记录.替换帧(活动['source']['sourceId'],活动['source']['generation']),ensure_ascii=False))#发送替换

    def 断开(自身,套接字):#断开
        """忘记一个已关闭传输，同时为重连保留缓冲状态。"""
        if 自身.活动 is not None and 自身.活动['socket'] is 套接字:#本套接字
            自身.活动=None#清空活动

    def 关闭(自身):#关闭
        """停止延迟写入并拒绝后续发布。"""
        if 自身.已关闭:#幂等
            return#返回
        自身.已关闭=True#置位
        自身.记录.丢弃待发()#丢弃剩余

    def 冲刷(自身):#冲刷
        """发送排队批次。"""
        活动=自身.活动#活动
        if 自身.已关闭 or 活动 is None or not 活动['accepted']:#不可发
            return#返回
        套接字=活动['socket']#套接字
        if getattr(套接字,'readyState',1)!=1:#未开
            return#返回
        while 自身.记录.有待发:#有待发
            帧=自身.记录.取一批(活动['source']['sourceId'],活动['source']['generation'])#取批次
            if 帧 is None:#无
                break#结束
            套接字.send(json.dumps(帧,ensure_ascii=False))#发送
