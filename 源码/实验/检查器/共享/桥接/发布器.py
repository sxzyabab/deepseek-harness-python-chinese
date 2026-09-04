"""MessagePort 与 WebSocket 桥接实现共用的源侧接口。

对齐上游 `shared/bridge/publisher.ts`。公开面仅中文名。
"""
import time#默认时间戳

__all__=[#仅中文公开名
    '检查器发布器','检查器状态发布器','检查器连接','检查器源连接',
]#公开面结束

class 检查器发布器:#观测发布器
    """与传输无关的观测发布器。"""
    def 发布(自身,topic,payload,monotonicMs=None):#发布观测
        """发布一条已校验观测。"""
        raise NotImplementedError#子类实现

class 检查器状态发布器(检查器发布器):#状态发布器
    """同时保留有状态观测主题最新值的发布器。"""
    def 设置状态(自身,topic,payload,monotonicMs=None):#设置状态
        """替换一个主题的保留状态并发布该替换。"""
        raise NotImplementedError#子类实现

class 检查器连接(检查器状态发布器):#源连接面
    """暴露在 Host MessagePort 或 Client WebSocket 载体之上的共用能力。"""
    def 请求(自身,查询):#执行查询
        """通过当前活动的源世代执行一次非 CDP 查询。"""
        raise NotImplementedError#子类实现

class 检查器源连接(检查器连接):#源连接基类
    """两种源传输继承的共用观测与查询委托。"""
    def __init__(自身):#构造
        """子类须提供发布器与查询器。"""
        pass#抽象基

    def _发布器(自身):#状态发布器
        """状态发布器。"""
        raise NotImplementedError#子类实现

    def _查询器(自身):#查询请求器
        """查询请求器。"""
        raise NotImplementedError#子类实现

    def 发布(自身,topic,payload,monotonicMs=None):#发布观测
        """发布一条 JSON 观测，不等待其载体。"""
        if monotonicMs is None:#缺省时间
            monotonicMs=time.perf_counter()*1000#源时钟
        自身._发布器().发布(topic,payload,monotonicMs)#委托发布器

    def 设置状态(自身,topic,payload,monotonicMs=None):#设置状态
        """为重连或替换恢复保留并发布一个状态值。"""
        if monotonicMs is None:#缺省时间
            monotonicMs=time.perf_counter()*1000#源时钟
        自身._发布器().设置状态(topic,payload,monotonicMs)#委托发布器

    def 请求(自身,查询):#执行查询
        """通过当前活动的源世代执行一次非 CDP 查询。"""
        return 自身._查询器().请求(查询)#委托查询器
