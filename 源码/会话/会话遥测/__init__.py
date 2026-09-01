"""会话遥测捕获侧 Service Definition（对齐 upstream session-telemetry）。"""
from ...依赖 import cordis#Cordis
服务=cordis.服务#服务基类
from .协调器 import 会话遥测协调器#协调器
__all__=[#公开面
    '会话遥测严重度','会话遥测记录','会话遥测接收器','会话遥测共享状态',
    '会话遥测后端','会话遥测协调器','默认',
]#结束

会话遥测严重度=('info','warn','error')#严重度词汇

会话遥测记录字段=('channel','time','severity','attributes','body')#逻辑记录字段

会话遥测共享状态=('full','feedback-only','disabled')#共享策略词汇

class 会话遥测后端(服务):#抽象后端
    """部署选定的遥测后端；重复加载由 Cordis 拒绝。"""
    def __init__(自身,上下文):#构造
        super().__init__(上下文,'sessionTelemetry')#服务键
    @property#共享策略
    def 共享(自身):#sharing
        raise NotImplementedError('SessionTelemetryBackend.sharing')#子类实现
    sharing=共享#Cordis 槽
    def 发出(自身,记录):#emit
        raise NotImplementedError('SessionTelemetryBackend.emit')#子类实现
    emit=发出#Cordis 槽
    def 冲刷(自身):#可选 flush
        return#默认无
    flush=冲刷#Cordis 槽
    async def 关闭(自身):#shutdown
        raise NotImplementedError('SessionTelemetryBackend.shutdown')#子类实现
    shutdown=关闭#Cordis 槽

class 会话遥测接收器:#接收器协议
    """协调器要求的最小后端契约。"""
    def 发出(自身,记录):pass#emit
    def 冲刷(自身):pass#flush 可选
    async def 关闭(自身):pass#shutdown

default=会话遥测后端#默认导出
默认=会话遥测后端#中文默认导出
