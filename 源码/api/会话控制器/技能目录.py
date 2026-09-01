"""会话寻址、冷可读技能目录 Remote。

对齐上游 `session-controller/src/skill-catalog.ts`。公开面仅中文名。
"""
from ...typert.协议 import 远程服务,远程 as _远程#Remote 基类
from .工具 import 取字段,解开,远程错误,远程错误消息#辅助

__all__=['会话技能目录']#仅中文公开名

class 会话技能目录(远程服务):#skills 命名空间
    """在不激活冷智能体的情况下列出技能。"""
    注入=['agents','sessionQuery','typert']#依赖

    def __init__(自身,上下文):#构造
        """登记 sessionSkillCatalog 服务。"""
        super().__init__(上下文,'sessionSkillCatalog',{'namespace':'skills'})#注册

    @_远程
    def list(自身,请求,信号):#列出技能
        """列出会话可见的用户可调用技能。"""
        会话标识=取字段(请求,'sessionId')#会话 id
        try:#观测
            观测=解开(自身.ctx.sessionQuery.observeSession(会话标识))#观测
            try:#使用观测
                if 取字段(观测,'projections') is None:#缺投影
                    raise Exception('skill catalog requires a projected Session observation')#拒绝
                头=取字段(观测,'header')#头
                工作目录=取字段(头,'cwd')#cwd
                预设=取字段(取字段(取字段(观测,'projections'),'values'),'agentPreset')#预设
            finally:#释放观测
                关闭=getattr(观测,'close',None)#close
                if callable(关闭):#可关闭
                    关闭()#关闭
        except Exception as 错误:#观测失败
            码=getattr(错误,'code',None)#查询码
            if 码=='SESSION_QUERY_SESSION_NOT_FOUND':#未找到
                raise 远程错误('session/not-found','session "'+str(会话标识)+'" not found',{'sessionId':会话标识})#映射
            raise 远程错误('gateway/internal','session "'+str(会话标识)+'" could not be inspected: '+远程错误消息(错误),{})#内部
        if 工作目录 is None:#无 cwd
            raise 远程错误('gateway/internal','session "'+str(会话标识)+'" has no project cwd',{})#拒绝
        活跃=自身.ctx.agents.get(会话标识)#活智能体
        预设们=自身.ctx.get('agentPresets')#预设服务
        作用域注册表=预设们.serviceFor(活跃,'skills') if (活跃 is not None and 预设们 is not None) else None#作用域技能
        技能注册表=作用域注册表 or 自身.ctx.get('skills')#回退全局
        if 技能注册表 is None:#缺席
            raise 远程错误('gateway/internal',"skill registry is absent: neither this session's agent preset nor the host composition mounts @deepseek-ai/dsh-skill",{})#拒绝
        作用域=自身._作用域(会话标识,预设)#作用域键
        try:#列技能
            列表=解开(技能注册表.list({'cwd':工作目录,'scope':作用域}))#列出
            from ...技能.技能 import isUserInvocable as 用户可调用#过滤
            技能们=[项 for 项 in 列表 if 用户可调用(项)]#可调用
            return {'skills':[{'name':取字段(项,'name'),'description':取字段(项,'description'),**({} if 取字段(项,'whenToUse') is None else {'whenToUse':取字段(项,'whenToUse')}),'modelInvocable':取字段(取字段(项,'invocation'),'modelInvocable')} for 项 in 技能们]}#映射
        except Exception as 错误:#失败
            raise 远程错误('gateway/internal','skill listing failed: '+远程错误消息(错误),{})#内部

    def _作用域(自身,会话标识,智能体预设):#解析作用域
        """解析活或站立预设作用域，不创建智能体。"""
        活跃=自身.ctx.agents.get(会话标识)#活智能体
        if 活跃 is not None:#有活智能体
            return 活跃#作用域载体
        预设们=自身.ctx.get('agentPresets')#预设
        if 预设们 is None:#无预设
            return None#全局
        try:#站立键
            return 解开(预设们.standingKeyFor(智能体预设))#键
        except Exception:#未知预设
            return None#回退全局
