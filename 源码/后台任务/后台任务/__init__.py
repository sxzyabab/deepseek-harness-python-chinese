"""后台任务服务定义（ctx.jobs）。抽象注册表：子类实现抽象成员并以插件加载，登记为 ctx.jobs。"""
from ...依赖 import cordis
服务=cordis.服务
from .标识构造 import 任务标识
from .类型 import (
    任务标识 as _再导出标识,
    任务状态,任务通道,任务分块字段,任务视图字段,任务输出坐标字段,
    任务结局字段,任务源读取字段,任务输出源字段,任务追加选项字段,
    任务句柄字段,任务钩子字段,任务规格字段,任务读取字段,
    任务偏移读取字段,任务结算起因,
)
from .归档准入 import 安装任务归档准入

class 任务错误(Exception):
    """后台任务包的异常基类。"""

class 任务注册表(服务):
    """抽象后台任务注册表。实现方必须兑现所有权围栏、先到先得结算与输出环语义。"""
    def __init__(自身,上下文):
        """以 jobs 名安装服务；抽象类不可直接实例化。"""
        if type(自身) is 任务注册表:
            raise 任务错误('@deepseek-ai/dsh-jobs is the abstract job registry seam; load an implementation such as @deepseek-ai/dsh-jobs-local instead')
        super().__init__(上下文,'jobs')
        安装任务归档准入(上下文,自身)

    def 启动(自身,规格):
        """预检后启动并原子登记工作，返回签发的 <kind>-N 标识。"""
        raise NotImplementedError('任务注册表.启动')

    def 列出(自身,调用方=None):
        """按登记顺序列出调用方可见与无主任务的新鲜投影。"""
        raise NotImplementedError('任务注册表.列出')

    def 获取(自身,标识,调用方=None):
        """投影一份任务且不移动游标。未知或外会话则抛错。"""
        raise NotImplementedError('任务注册表.获取')

    def 读取(自身,标识,调用方=None):
        """从模型游标消费输出环并推进到当前总量。"""
        raise NotImplementedError('任务注册表.读取')

    def 按偏移读取(自身,标识,起点,调用方=None):
        """不移动模型游标，从绝对字节偏移读保留输出。"""
        raise NotImplementedError('任务注册表.按偏移读取')

    def 终止(自身,标识,调用方=None,原因=None):
        """请求取消并标为 stopping。返回 requested 或 already-finished。"""
        raise NotImplementedError('任务注册表.终止')

    def 等待(自身,标识,超时毫秒,调用方=None,信号=None):
        """等待结算或超时，不取消任务。"""
        raise NotImplementedError('任务注册表.等待')

    def 移除(自身,标识,调用方=None):
        """丢掉一条已结算记录并宣布 removed。"""
        raise NotImplementedError('任务注册表.移除')

    def 挂接控制器(自身,名称):
        """挂接可读写并停止任务的控制器，返回拆除器。"""
        raise NotImplementedError('任务注册表.挂接控制器')

    @property
    def 事件(自身):
        """按订阅过滤的生命周期与输出事件流。"""
        raise NotImplementedError('任务注册表.事件')

__all__=[
    '任务错误','任务注册表','任务标识',
    '任务状态','任务通道','任务分块字段','任务视图字段','任务输出坐标字段',
    '任务结局字段','任务源读取字段','任务输出源字段','任务追加选项字段',
    '任务句柄字段','任务钩子字段','任务规格字段','任务读取字段',
    '任务偏移读取字段','任务结算起因',
]
default=任务注册表
