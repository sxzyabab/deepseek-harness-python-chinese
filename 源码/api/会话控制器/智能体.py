"""API 会话智能体激活与模型选择策略。

对齐上游 `session-controller/src/agent.ts`。公开面仅中文名。
"""
import os#目录
from .工具 import 取字段,解开,远程错误,远程错误消息#辅助

__all__=[#仅中文公开名
    '会话未找到','子智能体会话所有权','cwd冲突','预设冲突',
    '有子智能体所有者','子智能体所有权错误','检视会话','会话智能体控制器',
]#结束

class 会话未找到(Exception):pass#冷会话未找到
class 子智能体会话所有权(Exception):#子智能体所有权
    def __init__(自身,会话标识):#构造
        """记下会话标识。"""
        super().__init__('session "'+str(会话标识)+'" is a subagent session; use subagent delivery')#消息
        自身.sessionId=会话标识#id
class cwd冲突(Exception):#cwd 冲突
    def __init__(自身,会话标识,请求cwd,已有cwd):#构造
        """记下冲突 cwd。"""
        super().__init__('session cwd conflict')#消息
        自身.sessionId=会话标识#id
        自身.requestedCwd=请求cwd#请求
        自身.existingCwd=已有cwd#已有
class 预设冲突(Exception):#预设冲突
    def __init__(自身,会话标识,请求预设,已有预设):#构造
        """记下冲突预设。"""
        super().__init__('session preset conflict')#消息
        自身.sessionId=会话标识#id
        自身.requestedPreset=请求预设#请求
        自身.existingPreset=已有预设#已有

def 有子智能体所有者(上下文,会话,智能体):#是否子智能体路由
    """普通会话路由是否应让给子智能体。"""
    头=取字段(会话,'header') if not isinstance(会话,dict) else 会话#头
    if 取字段(头,'origin')=='subagent':#子智能体来源
        return True#是
    父标识=取字段(头,'parentSession')#父会话
    if 父标识 is None or 智能体 is None:#无父或无智能体
        return False#否
    父=上下文.agents.get(父标识)#父智能体
    return 父 is not None and 上下文.agents.isOwnedBy(取字段(智能体,'id'),父)#拥有

def 子智能体所有权错误(会话标识):#稳定拒绝
    """构建 session/agent-busy 失败。"""
    return 远程错误('session/agent-busy','session "'+str(会话标识)+'" is owned by subagent routing',{'reason':'use subagent delivery for this child session'})#失败

def 检视会话(上下文,会话标识,信号=None):#冷检视
    """不修复、不恢复、不发布地检视冷会话。"""
    选项={'projectionMode':'none'}#不投影
    if 信号 is not None:#有信号
        选项['signal']=信号#带上
    try:#观测
        观测=解开(上下文.sessionQuery.observeSession(会话标识,选项))#观测
        try:#读
            if 取字段(取字段(观测,'header'),'cwd') is None:#无 cwd
                raise 会话未找到('session "'+str(会话标识)+'" not found')#未找到
            return {'meta':取字段(观测,'header'),'events':list(取字段(观测,'events') or [])}#结果
        finally:#关
            关闭=getattr(观测,'close',None)#close
            if callable(关闭):关闭()#关
    except Exception as 错误:#失败
        if getattr(错误,'code',None)=='SESSION_QUERY_SESSION_NOT_FOUND':#未找到
            raise 会话未找到('session "'+str(会话标识)+'" not found')#映射
        raise#原样

class 会话智能体控制器:#智能体控制器
    """拥有创建、恢复与会话本地模型选择。"""

    def __init__(自身,上下文):#构造
        """配置 typert lookup 与 host context。"""
        自身._上下文=上下文#Cordis
        自身._恢复中={}#去重恢复
        自身._创建中={}#去重创建
        自身._选择们={}#弱映射占位（Python 用 id 字典）
        自身._图像准入链={}#图像串行链
        上下文.typert.lookups.configure('agent',lambda 会话标识:自身._查找智能体(会话标识))#agent lookup
        上下文.typert.lookups.configure('session',lambda 会话标识:自身._查找会话(会话标识))#session lookup
        上下文.typert.contexts.configureHost('agent',lambda 会话标识:自身._查找智能体上下文(会话标识))#host ctx

    def _查找智能体(自身,会话标识):#lookup agent
        """typert agent lookup。"""
        结果=解开(自身.解析智能体(会话标识))#解析
        if isinstance(结果,dict) and 'error' in 结果:#失败
            raise 结果['error']#抛出
        return 结果['agent']#智能体

    def _查找会话(自身,会话标识):#lookup session
        """typert session lookup。"""
        return 自身._查找智能体(会话标识).session#会话

    def _查找智能体上下文(自身,会话标识):#lookup agent ctx
        """typert host agent context。"""
        return 自身._查找智能体(会话标识).ctx#上下文

    def 解析智能体(自身,会话标识):#解析
        """解析或恢复普通会话。"""
        活=自身._活智能体(会话标识)#先看活的
        if 活 is not None:#有
            return 活#返回
        附着=自身._上下文.sessions.get(会话标识)#附着
        if 附着 is not None and 有子智能体所有者(自身._上下文,附着,None):#子智能体
            return {'error':子智能体所有权错误(会话标识)}#拒绝
        if 会话标识 not in 自身._恢复中:#新恢复
            自身._恢复中[会话标识]=自身._恢复(会话标识)#登记
        try:#等待
            return {'agent':解开(自身._恢复中[会话标识])}#成功
        except 会话未找到 as 错误:#未找到
            return {'error':远程错误('session/not-found',str(错误),{'sessionId':会话标识})}#映射
        except 子智能体会话所有权 as 错误:#子智能体
            return {'error':子智能体所有权错误(错误.sessionId)}#映射
        except Exception as 错误:#其它
            竞态=自身._活智能体(会话标识)#竞态
            if 竞态 is not None:#又有了
                return 竞态#返回
            return {'error':远程错误('gateway/internal','resume failed for session "'+str(会话标识)+'": '+远程错误消息(错误),{})}#内部
        finally:#清理
            自身._恢复中.pop(会话标识,None)#移除

    def 解析观测智能体(自身,观测):#从观测解析
        """从已保留观测解析智能体。"""
        return 自身.解析智能体(取字段(取字段(观测,'header'),'id'))#委托

    def 确保会话(自身,会话标识,工作目录,检查持久身份,预设标识=None):#创建或采用
        """解析请求的身份，必要时创建或恢复一次。"""
        if 会话标识 not in 自身._创建中:#新创建
            自身._创建中[会话标识]=自身._创建或采用(会话标识,工作目录,检查持久身份,预设标识)#登记
        try:#等待
            智能体=解开(自身._创建中[会话标识])#结果
            if 有子智能体所有者(自身._上下文,智能体.session,智能体):#子智能体
                raise 子智能体会话所有权(会话标识)#拒绝
            if 预设标识 is not None:#校验预设
                自身._断言预设未变(会话标识,预设标识,自身.会话预设(智能体.session))#断言
            if 取字段(智能体.session.header,'cwd')!=工作目录:#cwd 冲突
                raise cwd冲突(会话标识,工作目录,取字段(智能体.session.header,'cwd'))#冲突
            return 智能体#返回
        finally:#清理
            自身._创建中.pop(会话标识,None)#移除

    def 会话预设(自身,会话):#读预设
        """从投影读当前预设。"""
        return 自身._上下文.sessionProjections.stateOf(会话,'agentPreset')#状态

    def 消费选择(自身,智能体,提供方,模型,推理力度):#消费选择
        """匹配请求头时消费 pending 选择。"""
        已安装=自身._选择们.get(id(智能体))#已安装
        if 已安装 is None:#无
            return False#未消费
        return 已安装['consume'](提供方,模型,推理力度)#消费

    def _活智能体(自身,会话标识):#读活智能体结果
        """若已附着则返回智能体或所有权错误。"""
        智能体=自身._上下文.agents.get(会话标识)#查找
        if 智能体 is None:#无
            return None#无
        if 有子智能体所有者(自身._上下文,智能体.session,智能体):#子智能体
            return {'error':子智能体所有权错误(会话标识)}#错误
        return {'agent':智能体}#成功

    def _恢复(自身,会话标识,观测=None):#恢复
        """从冷或观测恢复。"""
        if 观测 is not None:#有观测
            return 自身._从观测恢复(会话标识,观测)#观测恢复
        观测=解开(自身._上下文.sessionQuery.observeSession(会话标识))#观测
        try:#恢复
            return 自身._从观测恢复(会话标识,观测)#恢复
        finally:#关
            关闭=getattr(观测,'close',None)#close
            if callable(关闭):关闭()#关

    def _从观测恢复(自身,会话标识,观测):#从观测恢复
        """用观测恢复智能体。"""
        头=取字段(观测,'header')#头
        if 取字段(头,'id')!=会话标识 or 取字段(头,'cwd') is None:#无效
            raise 会话未找到('session "'+str(会话标识)+'" not found')#未找到
        if 有子智能体所有者(自身._上下文,{'header':头},None):#子智能体
            raise 子智能体会话所有权(会话标识)#拒绝
        组合=解开(自身.组合智能体(自身._观测预设(观测)))#组合
        句柄=解开(自身._上下文.agents.resume({#恢复
            'resumeSessionId':会话标识,#id
            'agentOptions':自身._智能体选项(),#选项
            'setup':取字段(组合,'setup'),#setup
        }))#resume
        return 句柄.agent#智能体

    def _创建或采用(自身,会话标识,工作目录,检查持久身份,预设标识):#创建或采用
        """创建新会话或采用持久身份。"""
        附着=自身._上下文.sessions.get(会话标识)#附着
        活=自身._上下文.agents.get(会话标识)#活
        if 附着 is not None and 有子智能体所有者(自身._上下文,附着,活):#子智能体
            raise 子智能体会话所有权(会话标识)#拒绝
        if 活 is not None:#已活
            return 活#返回
        if 检查持久身份:#检查冷身份
            try:#观测
                观测=解开(自身._上下文.sessionQuery.observeSession(会话标识))#观测
                try:#校验
                    if 有子智能体所有者(自身._上下文,{'header':取字段(观测,'header')},None):#子智能体
                        raise 子智能体会话所有权(会话标识)#拒绝
                    if 取字段(取字段(观测,'header'),'cwd')!=工作目录:#cwd
                        raise cwd冲突(会话标识,工作目录,取字段(取字段(观测,'header'),'cwd'))#冲突
                    存储预设=自身._观测预设(观测)#预设
                    自身._断言预设未变(会话标识,预设标识,存储预设)#预设
                    组合=解开(自身.组合智能体(存储预设))#组合
                    return (解开(自身._上下文.agents.resume({#恢复
                        'resumeSessionId':会话标识,'agentOptions':自身._智能体选项(),'setup':取字段(组合,'setup'),
                    }))).agent#智能体
                finally:#关
                    关闭=getattr(观测,'close',None)#close
                    if callable(关闭):关闭()#关
            except Exception as 错误:#未找到则创建
                if getattr(错误,'code',None)!='SESSION_QUERY_SESSION_NOT_FOUND' and not isinstance(错误,(cwd冲突,预设冲突,子智能体会话所有权)):#其它
                    raise#原样
        os.makedirs(工作目录,exist_ok=True)#确保目录
        组合=解开(自身.组合智能体(预设标识))#组合
        元={'cwd':工作目录}#元
        if 取字段(组合,'agentPreset') is not None:#有预设
            元['agentPreset']=取字段(组合,'agentPreset')#写入
        return (解开(自身._上下文.agents.create({#创建
            'sessionId':会话标识,'agentOptions':自身._智能体选项(),'meta':元,'setup':取字段(组合,'setup'),
        }))).agent#智能体

    def 组合智能体(自身,预设标识):#组合智能体
        """解析预设并返回 setup。"""
        预设们=自身._上下文.get('agentPresets')#预设服务
        if 预设们 is None:#无
            return {'setup':lambda 智能体上下文:自身._安装选择(智能体上下文)}#仅选择
        解析标识=解开(预设们.resolve(预设标识)).id#解析 id
        def 设置(智能体上下文):#setup
            """安装选择并挂载预设。"""
            自身._安装选择(智能体上下文)#选择
            解开(预设们.mount(智能体上下文,解析标识))#挂载
        return {'agentPreset':解析标识,'setup':设置}#组合

    def _智能体选项(自身):#默认模型选项
        """当前默认模型选择。"""
        选择=自身._上下文.agentDefaultModel.currentSelection()#选择
        return {'provider':取字段(选择,'provider'),'model':取字段(选择,'model')}#选项

    def _安装选择(自身,智能体上下文):#安装模型选择
        """在智能体上下文安装 selection。"""
        智能体=取字段(智能体上下文,'agent')#智能体
        if 智能体 is None:#无
            raise Exception('api-session: Agent setup has no scoped Agent')#拒绝
        自身.选择用于(智能体)#安装

    def 选择用于(自身,智能体):#安装/返回选择
        """安装或返回会话本地模型选择引用。"""
        键=id(智能体)#键
        if 键 in 自身._选择们:#已有
            return 自身._选择们[键]#返回
        状态=自身._上下文.sessionProjections.stateOf(智能体.session,'modelSelection')#投影状态
        if 状态 is None:#缺列
            raise Exception('api-session: required modelSelection projection is not registered')#拒绝
        箱={'picked':取字段(状态,'pending')}#可变 pending
        默认=自身._上下文.agentDefaultModel#默认
        class 已安装选择:#选择引用
            """可变 current 与 consume。"""
            @property#current
            def current(选择自身):#读 current
                """读当前选择。"""
                if 箱['picked'] is not None:#有 pending
                    return 箱['picked']#返回
                return 默认.currentSelection()#默认
            @current.setter#写 current
            def current(选择自身,值):#写 current
                """写 current。"""
                箱['picked']=值#写入
            def consume(选择自身,提供方,模型,推理):#消费
                """匹配时清空 pending。"""
                当前=箱['picked']#pending
                if 当前 is None or 取字段(当前,'provider')!=提供方 or 取字段(当前,'model')!=模型 or 取字段(当前,'reasoningEffort')!=推理:#不匹配
                    return False#未消费
                箱['picked']=None#消费
                return True#已消费
        选择=已安装选择()#实例
        自身._选择们[键]=选择#缓存
        from ...内核.智能体 import 安装模型选择#安装
        安装模型选择(智能体.ctx,{'current':选择,'assembled':None})#安装
        return 选择#返回

    def _观测预设(自身,观测):#从观测读预设
        """从全投影观测读 agentPreset。"""
        if 取字段(观测,'projections') is None:#缺投影
            raise Exception('api-session: Agent activation requires a projected Session observation')#拒绝
        return 取字段(取字段(取字段(观测,'projections'),'values'),'agentPreset')#预设

    def _断言预设未变(自身,会话标识,请求,已有):#预设断言
        """显式创建时预设不得漂移。"""
        if 请求 is None or 请求==已有:#可接受
            return#通过
        raise 预设冲突(会话标识,请求,已有)#冲突
