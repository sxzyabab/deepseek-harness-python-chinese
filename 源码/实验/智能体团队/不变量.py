import copy
from .投影 import 是否团队事件,团队投影定义

__all__=['名称','依赖','应用','包名']

包名='@deepseek-ai/dsh-experimental-agent-team'
名称='team-invariant'
依赖=['invariants']

def 安装(上下文,失败):
    """对照已投影的已提交前缀校验候选 Team 事件。"""
    def 监听(_模式,事件名,参数,*_其余):
        """校验 session/event 上的 Team 边。"""
        if 事件名!='session/event':
            return
        会话=参数[0] if 参数 else None
        事件=参数[1] if 参数 and len(参数)>1 else None
        if not 是否团队事件(事件):
            return
        状态=上下文.sessionProjections.stateOf(会话,'agentTeam')
        候选=团队投影定义['apply'](copy.deepcopy(状态),事件)
        if 'failure' in 候选:
            失败('会话事件 '+str(事件['seq'])+' 违反智能体团队流: '+str(候选['failure']))
    上下文.监听('internal/dispatch',监听,{'全局':True})

def 应用(上下文):
    """注册包的不变式伴生。"""
    return 上下文.invariants.register(包名,安装)

安装.依赖=['sessionProjections']
安装.inject=安装.依赖
name=名称
inject=依赖
apply=应用
