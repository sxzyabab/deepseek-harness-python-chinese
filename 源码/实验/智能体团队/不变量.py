"""Agent Teams 运行时不变式伴生。

对齐上游 `agent-team/src/invariant.ts`。公开面仅中文名。
"""
import copy#试应用克隆
from .投影 import 是否团队事件,团队投影定义#投影面

__all__=['名称','注入','应用','包名']#仅中文公开名

包名='@deepseek-ai/dsh-experimental-agent-team'#包名
名称='team-invariant'#插件名
注入=['invariants']#依赖

def 安装(上下文,失败):#安装器
    """对照已投影的已提交前缀校验候选 Team 事件。"""
    def 监听(_模式,事件名,参数,*_其余):#监听派发
        """校验 session/event 上的 Team 边。"""
        if 事件名!='session/event':#非会话事件
            return#跳过
        会话=参数[0] if 参数 else None#会话
        事件=参数[1] if 参数 and len(参数)>1 else None#事件
        if not 是否团队事件(事件):#非 Team 事件
            return#跳过
        状态=上下文.sessionProjections.stateOf(会话,'agentTeam')#当前投影
        候选=团队投影定义['apply'](copy.deepcopy(状态),事件)#试应用
        if 'failure' in 候选:#有违例
            失败('session event '+str(事件['seq'])+' violates the Agent Teams stream: '+str(候选['failure']))#报告
    上下文.监听('internal/dispatch',监听,{'全局':True})#全局监听

def 应用(上下文):#注册包的不变式伴生
    """注册包的不变式伴生。"""
    return 上下文.invariants.register(包名,安装)#注册并返回卸除

安装.inject=['sessionProjections']#框架槽
name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
