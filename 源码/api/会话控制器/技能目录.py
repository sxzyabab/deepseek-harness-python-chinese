"""会话寻址、冷可读技能目录 Remote。

对齐上游 `session-controller/src/skill-catalog.ts`。公开面仅中文名。
"""
from ...typert.协议 import 远程服务,远程 as _远程#Remote 基类
from .远程错误与并发 import 远程错误,远程错误消息#远程错误

__all__=['会话技能目录']#仅中文公开名

class 会话技能目录(远程服务):
    """在不激活冷智能体的情况下列出技能。"""
    注入=['agents','sessionQuery','typert']#依赖

    def __init__(自身,上下文):
        """登记 sessionSkillCatalog 服务。"""
        super().__init__(上下文,'sessionSkillCatalog',{'namespace':'skills'})#注册

    @_远程
    def list(自身,请求,信号):
        """列出会话可见的用户可调用技能。请求为 dict。"""
        会话标识=请求['sessionId']#会话 id
        工作目录=None#cwd
        预设=None#预设
        try:
            观测=自身.ctx.sessionQuery.observeSession(会话标识)#观测对象
            try:
                if 观测.projections is None:#缺投影
                    raise 远程错误('gateway/internal','skill catalog requires a projected Session observation',{})#拒绝
                头=观测.header#头 dict
                工作目录=头['cwd'] if 'cwd' in 头 else None#cwd
                预设=观测.projections['values']['agentPreset']#预设
            finally:
                if hasattr(观测,'close'):#可关闭
                    观测.close()#关闭
        except 远程错误:
            raise#原样
        except BaseException as 错误:
            码=getattr(错误,'code',None)#查询码
            if 码=='SESSION_QUERY_SESSION_NOT_FOUND':#未找到
                raise 远程错误('session/not-found','session "'+str(会话标识)+'" not found',{'sessionId':会话标识})#映射
            raise 远程错误('gateway/internal','session "'+str(会话标识)+'" could not be inspected: '+远程错误消息(错误),{})#内部
        if 工作目录 is None:#无 cwd
            raise 远程错误('gateway/internal','session "'+str(会话标识)+'" has no project cwd',{})#拒绝
        活跃=自身.ctx.agents.get(会话标识)#活智能体
        预设服务=自身.ctx.获取服务('agentPresets')#预设服务
        作用域注册表=预设服务.serviceFor(活跃,'skills') if (活跃 is not None and 预设服务 is not None) else None#作用域技能
        技能注册表=作用域注册表 if 作用域注册表 is not None else 自身.ctx.获取服务('skills')#回退全局
        if 技能注册表 is None:#缺席
            raise 远程错误('gateway/internal',"skill registry is absent: neither this session's agent preset nor the host composition mounts @deepseek-ai/dsh-skill",{})#拒绝
        作用域=自身._作用域(会话标识,预设)#作用域键
        try:
            列表=技能注册表.list({'cwd':工作目录,'scope':作用域})#列出
            from ...技能.技能 import isUserInvocable as 用户可调用#过滤
            技能列表=[项 for 项 in 列表 if 用户可调用(项)]#可调用，项为 dict
            投影=[]#结果
            for 项 in 技能列表:#逐项
                条目={'name':项['name'],'description':项['description'],'modelInvocable':项['invocation']['modelInvocable']}#基础
                if 'whenToUse' in 项 and 项['whenToUse'] is not None:#有时机
                    条目['whenToUse']=项['whenToUse']#时机
                投影.append(条目)#收集
            return {'skills':投影}#映射
        except 远程错误:
            raise#原样
        except (OSError,ValueError,TypeError,KeyError,AttributeError) as 错误:
            raise 远程错误('gateway/internal','skill listing failed: '+远程错误消息(错误),{})#内部

    def _作用域(自身,会话标识,智能体预设):
        """解析活或站立预设作用域，不创建智能体。"""
        活跃=自身.ctx.agents.get(会话标识)#活智能体
        if 活跃 is not None:#有活智能体
            return 活跃#作用域载体
        预设服务=自身.ctx.获取服务('agentPresets')#预设
        if 预设服务 is None:#无预设
            return None#全局
        try:
            return 预设服务.standingKeyFor(智能体预设)#键
        except (OSError,ValueError,TypeError,KeyError,AttributeError):
            return None#未知预设回退全局
