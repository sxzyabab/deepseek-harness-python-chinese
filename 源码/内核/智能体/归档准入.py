"""工作区注册表归档准入的 turn 族：会话自身智能体是否在回合中，归档时按用户停止取消。"""
from .运行时类型 import 运行中

__all__=['安装回合归档准入']

def 安装回合归档准入(上下文,查找):
    """在 workspace/session-activity 上报告 turn，在 workspace/session-stop 上取消该回合。查找按会话标识取在线智能体。"""
    def 会话活动(载荷,下一步):
        """回合进行中则把 turn 接到瀑布结果前。"""
        智能体=查找(载荷['sessionId'])
        进行中=智能体 is not None and 智能体.status==运行中
        其余=下一步()
        if not 进行中:
            return 其余
        return [{'kind':'turn'}]+list(其余)
    def 会话停止(载荷):
        """按用户停止取消，不保留收件箱。"""
        智能体=查找(载荷['sessionId'])
        if 智能体 is not None and 智能体.status==运行中:
            智能体.取消({'kind':'user'})
    上下文.监听('workspace/session-activity',会话活动)
    上下文.监听('workspace/session-stop',会话停止)
