"""Agent Teams 运行时不变式伴生。

对齐上游 `agent-team/src/invariant.ts`。公开面仅中文名。
"""
import copy#试应用克隆
from ...内核.智能体循环.辅助 import 已兑现#立刻兑现
from .投影 import 是否团队事件,团队投影定义#投影面

__all__=['名称','注入','应用','包名']#仅中文公开名

包名='@deepseek-ai/dsh-experimental-agent-team'#包名
名称='team-invariant'#插件名
注入=['invariants']#依赖
name=名称#Cordis 名
inject=注入#Cordis 注入

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

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
        失败文案=取字段(候选,'failure')#违例
        if 失败文案 is not None:#有违例
            失败('session event '+str(取字段(事件,'seq'))+' violates the Agent Teams stream: '+str(失败文案))#报告
    上下文.on('internal/dispatch',监听,{'global':True})#全局监听

安装.inject=['sessionProjections']#附加依赖

def 应用(上下文):#注册包的不变式伴生
    """注册包的不变式伴生。"""
    return 已兑现(上下文.invariants.register(包名,安装))#注册并返回卸除

apply=应用#入口
