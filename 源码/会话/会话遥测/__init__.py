"""会话遥测捕获侧 Service Definition（对齐 upstream session-telemetry）。"""
from ...依赖 import cordis#Cordis
服务=cordis.服务#服务基类
from .协调器 import 会话遥测协调器#协调器
__all__=[#公开面
    '会话遥测严重度','会话遥测记录','会话遥测接收器','会话遥测共享状态',
    '会话遥测后端','会话遥测协调器',
]#结束

会话遥测严重度=('info','warn','error')#严重度词汇

会话遥测记录字段=('channel','time','severity','attributes','body')#逻辑记录字段

会话遥测共享状态=('full','feedback-only','disabled')#共享策略词汇

class 会话遥测后端(服务):
    """部署选定的遥测后端；重复加载由 Cordis 拒绝。"""
    def __init__(自身,上下文):
        """登记为 ctx.sessionTelemetry。"""
        super().__init__(上下文,'sessionTelemetry')#服务键

    @property
    def 共享(自身):
        """共享策略。"""
        raise NotImplementedError('SessionTelemetryBackend.sharing')#子类实现

    def 发出(自身,记录):
        """发出一条逻辑记录。"""
        raise NotImplementedError('SessionTelemetryBackend.emit')#子类实现

    def 冲刷(自身):
        """可选 flush。"""
        return#默认无

    def 关闭(自身):
        """关闭后端。"""
        raise NotImplementedError('SessionTelemetryBackend.shutdown')#子类实现

class 会话遥测接收器:
    """协调器要求的最小后端契约。"""
    def 发出(自身,记录):
        """发出一条逻辑记录。"""
        return#协议占位

    def 冲刷(自身):
        """可选 flush。"""
        return#协议占位

    def 关闭(自身):
        """关闭后端。"""
        return#协议占位

default=会话遥测后端#Cordis 默认导出槽
