"""API 会话智能体激活与模型选择策略。

对齐上游 `session-controller/src/agent.ts`。公开面仅中文名。
"""
import os#目录
from threading import Event as 同步事件,Lock as 互斥锁#飞行结算与串行互斥
from .远程错误与并发 import 远程错误,远程错误消息#远程错误

__all__=[#仅中文公开名
    '会话未找到','子智能体会话所有权','cwd冲突','预设冲突',
    '有子智能体所有者','子智能体所有权错误','检视会话','会话智能体控制器',
]#结束

class 会话未找到(Exception):
    """冷会话未找到。"""

class 子智能体会话所有权(Exception):
    """子智能体所有权围栏。"""
    def __init__(自身,会话标识):
        """记下会话标识。"""
        super().__init__('session "'+str(会话标识)+'" is a subagent session; use subagent delivery')#消息
        自身.sessionId=会话标识#id

class cwd冲突(Exception):
    """cwd 冲突。"""
    def __init__(自身,会话标识,请求cwd,已有cwd):
        """记下冲突 cwd。"""
        super().__init__('session cwd conflict')#消息
        自身.sessionId=会话标识#id
        自身.requestedCwd=请求cwd#请求
        自身.existingCwd=已有cwd#已有

class 预设冲突(Exception):
    """预设冲突。"""
    def __init__(自身,会话标识,请求预设,已有预设):
        """记下冲突预设。"""
        super().__init__('session preset conflict')#消息
        自身.sessionId=会话标识#id
        自身.requestedPreset=请求预设#请求
        自身.existingPreset=已有预设#已有

def 有子智能体所有者(上下文,头,智能体):
    """普通会话路由是否应让给子智能体。头为会话头 dict。"""
    if 头 is None:#无头
        return False#否
    if 'origin' in 头 and 头['origin']=='subagent':#子智能体来源
        return True#是
    父标识=头['parentSession'] if 'parentSession' in 头 else None#父会话
    if 父标识 is None or 智能体 is None:#无父或无智能体
        return False#否
    父=上下文.agents.get(父标识) if hasattr(上下文.agents,'get') else 上下文.agents.获取(父标识)#父智能体
    if 父 is None:#无父
        return False#否
    拥有=getattr(上下文.agents,'isOwnedBy',None) or getattr(上下文.agents,'是否被拥有',None)#拥有查询
    return 拥有 is not None and 拥有(智能体.id,父)#拥有

def 子智能体所有权错误(会话标识):
    """构建 session/agent-busy 失败。"""
    return 远程错误('session/agent-busy','session "'+str(会话标识)+'" is owned by subagent routing',{'reason':'use subagent delivery for this child session'})#失败

def 检视会话(上下文,会话标识,信号=None):
    """不修复、不恢复、不发布地检视冷会话。"""
    选项={'projectionMode':'none'}#不投影
    if 信号 is not None:#有信号
        选项['signal']=信号#带上
    try:
        观测=上下文.sessionQuery.observeSession(会话标识,选项)#观测对象
        try:
            头=观测.header#头 dict
            if 'cwd' not in 头 or 头['cwd'] is None:#无 cwd
                raise 会话未找到('session "'+str(会话标识)+'" not found')#未找到
            事件列表=观测.events if 观测.events is not None else []#事件
            继承=getattr(观测,'inheritedEventCount',0)#继承切口
            return {'meta':头,'inheritedEventCount':继承,'events':list(事件列表)}#结果
        finally:
            if hasattr(观测,'close'):#可关
                观测.close()#关
    except 会话未找到:
        raise#原样
    except BaseException as 错误:
        if getattr(错误,'code',None)=='SESSION_QUERY_SESSION_NOT_FOUND':#未找到
            raise 会话未找到('session "'+str(会话标识)+'" not found')#映射
        raise#原样

class 会话智能体控制器:
    """拥有创建、恢复与会话本地模型选择。"""

    def __init__(自身,上下文):
        """配置 typert lookup 与 host context。"""
        自身._上下文=上下文#Cordis
        自身._恢复锁=互斥锁()#恢复飞行表互斥
        自身._恢复中={}#去重恢复：会话标识→{完成,结果,错误}
        自身._创建锁=互斥锁()#创建飞行表互斥
        自身._创建中={}#去重创建：会话标识→{完成,结果,错误}
        自身._选择表={}#按 id(智能体) 索引
        自身._图像锁表总锁=互斥锁()#图像锁表互斥
        自身._图像准入锁表={}#按 id(智能体)→互斥锁
        上下文.typert.lookups.configure('agent',自身._查找智能体)#agent lookup
        上下文.typert.lookups.configure('session',自身._查找会话)#session lookup
        上下文.typert.contexts.configureHost('agent',自身._查找智能体上下文)#host ctx

    def _查找智能体(自身,会话标识):
        """typert agent lookup。"""
        结果=自身.解析智能体(会话标识)#解析
        if isinstance(结果,dict) and 'error' in 结果:#失败
            raise 结果['error']#抛出
        return 结果['agent']#智能体

    def _查找会话(自身,会话标识):
        """typert session lookup。"""
        return 自身._查找智能体(会话标识).session#会话

    def _查找智能体上下文(自身,会话标识):
        """typert host agent context。"""
        return 自身._查找智能体(会话标识).ctx#上下文

    def 解析智能体(自身,会话标识):
        """解析或恢复普通会话。"""
        活=自身._活智能体(会话标识)#先看活的
        if 活 is not None:#有
            return 活#返回
        附着=自身._上下文.sessions.get(会话标识)#附着
        if 附着 is not None and 有子智能体所有者(自身._上下文,附着.header,None):#子智能体
            return {'error':子智能体所有权错误(会话标识)}#拒绝
        with 自身._恢复锁:#飞行去重
            if 会话标识 in 自身._恢复中:#共享在途
                条目=自身._恢复中[会话标识]#同条目
                主人=False#等别人结算
            else:#新开恢复
                条目={'完成':同步事件(),'结果':None,'错误':None}#Event+字段
                自身._恢复中[会话标识]=条目#先入表
                主人=True#本调用跑体
        if 主人:#跑恢复体
            try:
                条目['结果']=自身._恢复(会话标识)#写入结果
            except BaseException as 错误:
                条目['错误']=错误#原样记下
            finally:
                条目['完成'].set()#广播
                with 自身._恢复锁:#允许同身份再开
                    if 自身._恢复中.get(会话标识) is 条目:#仍是本条目
                        自身._恢复中.pop(会话标识,None)#移除
        条目['完成'].wait()#等结算
        if 条目['错误'] is not None:#失败
            错误=条目['错误']#取出
            if isinstance(错误,会话未找到):#未找到
                return {'error':远程错误('session/not-found',str(错误),{'sessionId':会话标识})}#映射
            if isinstance(错误,子智能体会话所有权):#所有权
                return {'error':子智能体所有权错误(错误.sessionId)}#映射
            竞态=自身._活智能体(会话标识)#竞态
            if 竞态 is not None:#又有了
                return 竞态#返回
            竞态会话=自身._上下文.sessions.get(会话标识)#附着竞态
            if 竞态会话 is not None and 有子智能体所有者(自身._上下文,竞态会话.header,None):#子智能体
                return {'error':子智能体所有权错误(会话标识)}#拒绝
            if getattr(错误,'name',None)=='SessionAlreadyOwnedError' or type(错误).__name__=='SessionAlreadyOwnedError':#写者占用
                return {'error':远程错误('session/writer-held',远程错误消息(错误),{'sessionId':会话标识})}#映射
            return {'error':远程错误('gateway/internal','resume failed for session "'+str(会话标识)+'": '+远程错误消息(错误),{})}#内部
        发布=自身._活智能体(会话标识)#共享恢复后再查存活所有权
        if 发布 is not None:#已有策略结果
            return 发布#优先
        return {'agent':条目['结果']}#成功

    def 解析观测智能体(自身,观测):
        """从已保留观测解析智能体。观测有 header。"""
        return 自身.解析智能体(观测.header['id'])#委托

    def 确保会话(自身,会话标识,工作目录,检查持久身份,预设标识=None):
        """解析请求的身份，必要时创建或恢复一次。"""
        with 自身._创建锁:#飞行去重
            if 会话标识 in 自身._创建中:#共享在途
                条目=自身._创建中[会话标识]#同条目
                主人=False#等别人结算
            else:#新开创建
                条目={'完成':同步事件(),'结果':None,'错误':None}#Event+字段
                自身._创建中[会话标识]=条目#先入表
                主人=True#本调用跑体
        if 主人:#跑创建体
            try:
                条目['结果']=自身._创建或采用(会话标识,工作目录,检查持久身份,预设标识)#写入
            except BaseException as 错误:
                条目['错误']=错误#原样记下
            finally:
                条目['完成'].set()#广播
                with 自身._创建锁:#允许同身份再开
                    if 自身._创建中.get(会话标识) is 条目:#仍是本条目
                        自身._创建中.pop(会话标识,None)#移除
        条目['完成'].wait()#等结算
        if 条目['错误'] is not None:#失败
            raise 条目['错误']#原样抛
        智能体=条目['结果']#结果
        if 有子智能体所有者(自身._上下文,智能体.session.header,智能体):#子智能体
            raise 子智能体会话所有权(会话标识)#拒绝
        if 预设标识 is not None:#校验预设
            自身._断言预设未变(会话标识,预设标识,自身.会话预设(智能体.session))#断言
        头=智能体.session.header#头 dict
        if 头['cwd']!=工作目录:#cwd 冲突
            raise cwd冲突(会话标识,工作目录,头['cwd'])#冲突
        return 智能体#返回

    def 会话预设(自身,会话):
        """从投影读当前预设。"""
        return 自身._上下文.sessionProjections.stateOf(会话,'agentPreset')#状态

    def 消费选择(自身,智能体,提供方,模型,推理力度):
        """匹配请求头时消费 pending 选择。"""
        键=id(智能体)#键
        if 键 not in 自身._选择表:#无
            return False#未消费
        return 自身._选择表[键].consume(提供方,模型,推理力度)#消费

    def _活智能体(自身,会话标识):
        """若已附着则返回智能体或所有权错误。"""
        智能体=自身._上下文.agents.get(会话标识)#查找
        if 智能体 is None:#无
            return None#无
        if 有子智能体所有者(自身._上下文,智能体.session.header,智能体):#子智能体
            return {'error':子智能体所有权错误(会话标识)}#错误
        return {'agent':智能体}#成功

    def _恢复(自身,会话标识,观测=None):
        """从冷或观测恢复。"""
        if 观测 is not None:#有观测
            return 自身._从观测恢复(会话标识,观测)#观测恢复
        观测=自身._上下文.sessionQuery.observeSession(会话标识)#观测
        try:
            return 自身._从观测恢复(会话标识,观测)#恢复
        finally:
            if hasattr(观测,'close'):#可关
                观测.close()#关

    def _从观测恢复(自身,会话标识,观测):
        """用观测恢复智能体。"""
        头=观测.header#头 dict
        if 头['id']!=会话标识 or 'cwd' not in 头 or 头['cwd'] is None:#无效
            raise 会话未找到('session "'+str(会话标识)+'" not found')#未找到
        if 有子智能体所有者(自身._上下文,头,None):#子智能体
            raise 子智能体会话所有权(会话标识)#拒绝
        组合=自身.组合智能体(自身._观测预设(观测))#组合 dict
        句柄=自身._上下文.agents.resume({#恢复
            'resumeSessionId':会话标识,#id
            'agentOptions':自身._智能体选项(),#选项
            'setup':组合['setup'],#setup
        })#resume
        return 句柄.agent#智能体

    def _创建或采用(自身,会话标识,工作目录,检查持久身份,预设标识):
        """创建新会话或采用持久身份。"""
        附着=自身._上下文.sessions.get(会话标识)#附着
        活=自身._上下文.agents.get(会话标识)#活
        if 附着 is not None and 有子智能体所有者(自身._上下文,附着.header,活):#子智能体
            raise 子智能体会话所有权(会话标识)#拒绝
        if 活 is not None:#已活
            return 活#返回
        if 检查持久身份:#检查冷身份
            try:
                观测=自身._上下文.sessionQuery.observeSession(会话标识)#观测
                try:
                    头=观测.header#头
                    if 有子智能体所有者(自身._上下文,头,None):#子智能体
                        raise 子智能体会话所有权(会话标识)#拒绝
                    if 头['cwd']!=工作目录:#cwd
                        raise cwd冲突(会话标识,工作目录,头['cwd'])#冲突
                    存储预设=自身._观测预设(观测)#预设
                    自身._断言预设未变(会话标识,预设标识,存储预设)#预设
                    组合=自身.组合智能体(存储预设)#组合
                    return 自身._上下文.agents.resume({#恢复
                        'resumeSessionId':会话标识,'agentOptions':自身._智能体选项(),'setup':组合['setup'],
                    }).agent#智能体
                finally:
                    if hasattr(观测,'close'):#可关
                        观测.close()#关
            except (cwd冲突,预设冲突,子智能体会话所有权):
                raise#原样
            except BaseException as 错误:
                if getattr(错误,'code',None)!='SESSION_QUERY_SESSION_NOT_FOUND':#其它
                    raise#原样
        os.makedirs(工作目录,exist_ok=True)#确保目录
        组合=自身.组合智能体(预设标识)#组合
        元={'cwd':工作目录}#元
        if 'agentPreset' in 组合 and 组合['agentPreset'] is not None:#有预设
            元['agentPreset']=组合['agentPreset']#写入
        return 自身._上下文.agents.create({#创建
            'sessionId':会话标识,'agentOptions':自身._智能体选项(),'meta':元,'setup':组合['setup'],
        }).agent#智能体

    def 组合智能体(自身,预设标识):
        """解析预设并返回 setup。"""
        预设服务=自身._上下文.获取服务('agentPresets')#预设服务
        if 预设服务 is None:#无
            def 仅选择(_智能体上下文,智能体):
                """只安装选择；第二参为工厂传入的智能体。"""
                自身._安装选择(智能体)#选择
            return {'setup':仅选择}#仅选择
        解析标识=预设服务.resolve(预设标识).id#解析 id
        def 设置(智能体上下文,智能体):
            """安装选择并挂载预设。"""
            自身._安装选择(智能体)#选择
            预设服务.mount(智能体上下文,解析标识)#挂载
        return {'agentPreset':解析标识,'setup':设置}#组合

    def _智能体选项(自身):
        """当前默认模型选择。"""
        选择=自身._上下文.agentDefaultModel.currentSelection()#选择 dict
        return {'provider':选择['provider'],'model':选择['model']}#选项

    def _安装选择(自身,智能体):
        """在智能体上安装 selection。"""
        自身.选择用于(智能体)#安装

    def 选择用于(自身,智能体):
        """安装或返回会话本地模型选择引用。"""
        键=id(智能体)#键
        if 键 in 自身._选择表:#已有
            return 自身._选择表[键]#返回
        状态=自身._上下文.sessionProjections.stateOf(智能体.session,'modelSelection')#投影状态 dict
        if 状态 is None:#缺列
            raise 远程错误('gateway/internal','api-session: required modelSelection projection is not registered',{})#拒绝
        箱={'picked':状态['pending'] if 'pending' in 状态 else None}#可变 pending
        默认=自身._上下文.agentDefaultModel#默认
        class 已安装选择:
            """可变 current 与 consume。"""
            @property
            def current(选择自身):
                """读当前选择。"""
                if 箱['picked'] is not None:#有 pending
                    return 箱['picked']#返回
                return 默认.currentSelection()#默认

            @current.setter
            def current(选择自身,值):
                """写 current。"""
                箱['picked']=值#写入

            def consume(选择自身,提供方,模型,推理):
                """匹配时清空 pending。"""
                当前=箱['picked']#pending
                if 当前 is None:#无
                    return False#未消费
                力度=当前['reasoningEffort'] if 'reasoningEffort' in 当前 else None#力度
                if 当前['provider']!=提供方 or 当前['model']!=模型 or 力度!=推理:#不匹配
                    return False#未消费
                箱['picked']=None#消费
                return True#已消费
        选择=已安装选择()#实例
        自身._选择表[键]=选择#缓存
        from ...内核.智能体 import 安装模型选择#安装
        安装模型选择(智能体.ctx,{'current':选择,'assembled':None})#安装
        return 选择#返回

    def 选择下次请求(自身,智能体,选择):
        """提交并缓存下一次提示组装的已验证选择。"""
        智能体.session.追加('model/selection',选择)#记录
        自身.选择用于(智能体).current=选择#安装

    def 串行图像准入(自身,智能体,操作):
        """串行化同一智能体的图片准入与模型选择。操作为无参可调用，返回其结果。"""
        键=id(智能体)#键
        with 自身._图像锁表总锁:#取或建该智能体锁
            if 键 not in 自身._图像准入锁表:#尚无
                自身._图像准入锁表[键]=互斥锁()#新建
            锁=自身._图像准入锁表[键]#取出
        with 锁:#同智能体互斥
            return 操作()#直接执行

    def _观测预设(自身,观测):
        """从全投影观测读 agentPreset。"""
        if 观测.projections is None:#缺投影
            raise 远程错误('gateway/internal','api-session: Agent activation requires a projected Session observation',{})#拒绝
        return 观测.projections['values']['agentPreset']#预设

    def _断言预设未变(自身,会话标识,请求,已有):
        """显式创建时预设不得漂移。"""
        if 请求 is None or 请求==已有:#可接受
            return#通过
        raise 预设冲突(会话标识,请求,已有)#冲突
