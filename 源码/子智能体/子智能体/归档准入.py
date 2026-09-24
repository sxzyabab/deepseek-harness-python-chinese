"""工作区归档准入：仍在回合内的子智能体后代及其随会话归档的停止方式。"""
from .描述符 import 折叠子智能体描述符

def 安装子智能体归档准入(上下文):
    """回答 workspace/session-activity，并在 workspace/session-stop 时取消这些后代。"""

    def 会话活动(载荷,下一步,*其余):
        """把仍在运行的子智能体后代并入活动列表。"""
        _=其余
        会话标识=载荷['sessionId']
        运行中=运行中后代(上下文,会话标识)
        其余活动=下一步()
        if len(运行中)==0:
            return 其余活动
        自有={'kind':'subagent','items':[描述(上下文,孩子) for 孩子 in 运行中]}
        return [自有]+list(其余活动)

    def 会话停止(载荷,*其余):
        """按父会话归档取消每个仍在运行的子智能体。"""
        _=其余
        for 孩子 in 运行中后代(上下文,载荷['sessionId']):
            try:
                孩子.cancel({'kind':'parent'})
            except Exception as 错误:
                上下文.日志.警告('subagent: cancelling "'+str(孩子.id)+'" for an archived Session failed: '+str(错误))

    上下文.监听('workspace/session-activity',会话活动)
    上下文.监听('workspace/session-stop',会话停止)

def 运行中后代(上下文,根标识):
    """按耐久血统收集仍在回合内的子智能体后代。"""
    孩子表={}
    for 智能体 in 上下文.agents.list():
        头=智能体.session.header
        父会话=头.get('parentSession') if isinstance(头,dict) else getattr(头,'parentSession',None)
        来源=头.get('origin') if isinstance(头,dict) else getattr(头,'origin',None)
        if 父会话 is None or 来源!='subagent':
            continue
        同级=孩子表.get(父会话)
        if 同级 is None:
            同级=[]
            孩子表[父会话]=同级
        同级.append(智能体)
    运行中=[]
    待定=[根标识]
    已访=set()
    while len(待定)>0:
        父标识=待定.pop(0)
        if 父标识 in 已访:
            continue
        已访.add(父标识)
        for 孩子 in 孩子表.get(父标识) or []:
            if 孩子.status=='running':
                运行中.append(孩子)
            待定.append(孩子.id)
    return 运行中

def 描述(上下文,孩子):
    """活动项：标识，外加描述符上的创建标签。"""
    查询=上下文.获取服务('sessionQuery',False)
    if 查询 is None:
        return {'id':孩子.id}
    try:
        观察=查询.observeSession(孩子.id,{'projectionMode':'none'})
        事件=观察.events[观察.inheritedEventCount:]
        描述符=折叠子智能体描述符(事件)
        标签=None if 描述符 is None else 描述符.get('label')
        if 标签 is None:
            return {'id':孩子.id}
        return {'id':孩子.id,'label':标签}
    except Exception:
        return {'id':孩子.id}

__all__=['安装子智能体归档准入']
