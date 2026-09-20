"""解析 Remote 智能体与会话身份的宿主 BFF 策略。

诊断英文字面量保持线协议。
"""
import threading#后台恢复
from typing import NotRequired,TypedDict#结构类型
from concurrent.futures import Future as 原生结果#单次操作结果
from ...typert.协议 import 查找策略失败

__all__=(#仅中文公开名
    '远程会话未找到','远程子智能体会话所有权',
    '有远程子智能体所有者','远程子智能体所有权错误',
    '查看远程会话','创建远程智能体解析器',
    '远程查找错误码','远程查找错误',
    '远程智能体结果成功','远程智能体结果失败','远程智能体结果','远程智能体选项',
    '远程查找错误基类','操作任务',
)#公开面结束

远程查找错误码=('agent-busy','session-not-found','internal')#面向调用方失败码联合

class 远程查找错误基类(Exception):
    """远程智能体查找包的异常基类。"""

class 远程查找错误(TypedDict):
    """网关 RPC 适配器原样保留的面向调用方失败。"""
    code:str#agent-busy | session-not-found | internal
    message:str#诊断消息
    details:dict#按码携带 reason / sessionId / 空对象

class 远程智能体结果成功(TypedDict):
    """解析到在线智能体。"""
    agent:object#在线智能体

class 远程智能体结果失败(TypedDict):
    """查找失败。"""
    error:远程查找错误#面向调用方失败信封

远程智能体结果=dict#成功含 agent，失败含 error（运行时联合）

class 远程智能体选项(TypedDict):
    """拥有方宿主组合提供的恢复配置。"""
    agentOptions:NotRequired[object]#可选的智能体默认选项工厂
    setup:NotRequired[object]#发布前宿主专用智能体作用域装配工厂

class 操作任务:
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身._未来=原生结果()#底层 Future

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身._未来.done():#尚未结算
            自身._未来.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身._未来.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._未来.set_exception(错误)#原样拒绝
            else:#非异常
                包装=远程查找错误基类('task rejected')#包装拒绝
                包装.原因=错误#附加属性
                自身._未来.set_exception(包装)#包装拒绝

    def 等待(自身,超时=None):
        """阻塞等到结算。"""
        return 自身._未来.result(timeout=超时)#取结果或抛错

class 远程会话未找到(远程查找错误基类):
    """持久会话库中没有的冷身份。"""

class 远程子智能体会话所有权(远程查找错误基类):
    """生命周期属于子智能体路由的会话身份。"""
    def __init__(自身,会话标识):
        """记下被围栏的会话身份。"""
        super().__init__('session "'+str(会话标识)+'" is a subagent session; use subagent delivery')#诊断应走子智能体投递
        自身.会话标识=会话标识#会话身份

def 有远程子智能体所有者(上下文,头,智能体):
    """测试通用宿主路由是否必须把该身份留给子智能体路由。头为会话头 dict。"""
    if 头 is None:#无头
        return False#不占用
    if 'origin' in 头 and 头['origin']=='subagent':#源头是子智能体则占用
        return True#占用
    父标识=头['parentSession'] if 'parentSession' in 头 else None#父会话身份
    if 父标识 is None or 智能体 is None:#没有父会话或没有在线智能体则不占用
        return False#不占用
    父=上下文.agents.get(父标识)#取父智能体
    return 父 is not None and 上下文.agents.isOwnedBy(智能体.id,父)#父在线且该智能体由父拥有则占用

def 远程子智能体所有权错误(会话标识):
    """构造稳定的面向调用方所有权拒绝。"""
    return {#agent-busy 信封
        'code':'agent-busy',#智能体正忙
        'message':'session "'+str(会话标识)+'" is owned by subagent routing',#由子智能体路由占用
        'details':{'reason':'use subagent delivery for this child session'},#应走子智能体投递
    }#信封结束

def 查看远程会话(上下文,会话标识):
    """查看一个冷的可服务会话，不修复、不恢复、不发布。"""
    持久化=上下文.获取服务('sessionPersistence')#取可选持久化提供方
    if 持久化 is None:#没有配置持久化
        raise 远程查找错误基类('session persistence is not configured (load a dsh-session-persistence backend)')#必须装会话持久化后端
    元=None#列表命中
    for 候选 in 持久化.list():#在列表里找该身份，候选为 dict
        if 候选['id']==会话标识:#命中
            元=候选#记下
            break#停止
    if 元 is None or 'cwd' not in 元 or 元['cwd'] is None:#没有记录或没有项目 cwd
        raise 远程会话未找到('session "'+str(会话标识)+'" not found')#不是可服务会话
    查看=持久化.inspect(会话标识)#再读完整头与事件，查看为 dict
    头=查看['meta']#完整头
    if 'cwd' not in 头 or 头['cwd'] is None:#完整记录仍没有项目 cwd
        raise 远程会话未找到('session "'+str(会话标识)+'" not found')#不是可服务会话
    事件列表=查看['events'] if 'events' in 查看 and 查看['events'] is not None else []#事件
    return {'meta':头,'events':list(事件列表)}#返回头与事件浅拷贝

def 创建远程智能体解析器(上下文,选项):
    """在线智能体复用，普通冷会话按身份恢复一次，子智能体占用的身份保留旧的 agent-busy 围栏。选项为 dict。"""
    恢复中={}#进行中的按身份去重恢复：会话标识 → 共享任务

    def 围栏在线(会话标识):
        """在线智能体复用或 agent-busy。"""
        在线=上下文.agents.get(会话标识)#取该身份的在线智能体
        if 在线 is None:#没有在线智能体
            return None#无结论
        if 有远程子智能体所有者(上下文,在线.session.header,在线):#在线但由子智能体路由占用
            return {'error':远程子智能体所有权错误(会话标识)}#返回 agent-busy
        return {'agent':在线}#可复用在线智能体

    def 解析智能体(会话标识):
        """先看在线，再冷恢复。"""
        围栏=围栏在线(会话标识)#先看在线智能体
        if 围栏 is not None:#已有结论则返回
            return 围栏#结论
        已附着=上下文.sessions.get(会话标识)#取已附着但可能尚未发布智能体的会话
        if 已附着 is not None and 有远程子智能体所有者(上下文,已附着.header,None):#已附着且由子智能体占用
            return {'error':远程子智能体所有权错误(会话标识)}#返回 agent-busy
        恢复=恢复中[会话标识] if 会话标识 in 恢复中 else None#该身份是否已有进行中的恢复
        if 恢复 is None:#没有则启动一次并写入共享任务
            恢复=操作任务()#共享恢复任务
            恢复中[会话标识]=恢复#先入表，后跑体，使并发调用方挂上同一任务
            def 后台恢复会话():
                """查看、装配、再恢复；成败都结算共享任务。"""
                try:
                    查看=查看远程会话(上下文,会话标识)#只读查看持久会话
                    if 有远程子智能体所有者(上下文,查看['meta'],None):#冷会话也由子智能体占用
                        raise 远程子智能体会话所有权(会话标识)#用围栏错误跳出
                    装配工厂=选项['setup'] if 选项 is not None and 'setup' in 选项 else None#可选装配工厂
                    装配=装配工厂(查看) if 装配工厂 is not None else None#需要时跑宿主装配
                    已发布会话=上下文.sessions.get(会话标识)#装配等待后可能已有人发布会话
                    已发布智能体=上下文.agents.get(会话标识)#以及可能已发布的智能体
                    已发布头=已发布会话.header if 已发布会话 is not None else None#已发布头
                    if 已发布会话 is not None and 有远程子智能体所有者(上下文,已发布头,已发布智能体):#现已由子智能体占用
                        raise 远程子智能体会话所有权(会话标识)#围栏错误
                    恢复参数={'resumeSessionId':会话标识}#要恢复的会话身份
                    选项工厂=选项['agentOptions'] if 选项 is not None and 'agentOptions' in 选项 else None#默认选项工厂
                    if 选项工厂 is not None:#有默认选项则带上
                        恢复参数['agentOptions']=选项工厂()#带上
                    if 装配 is not None:#有装配则带上
                        恢复参数['setup']=装配#带上
                    句柄=上下文.agents.resume(恢复参数)#按该身份恢复智能体
                    恢复.兑现(句柄.agent)#结算共享任务
                except BaseException as 错误:
                    恢复.拒绝(错误)#所有调用方经 等待 收到同一失败
                finally:
                    恢复中.pop(会话标识,None)#允许同一身份再次恢复
            工作=threading.Thread(target=后台恢复会话)#后台恢复
            工作.daemon=True#不挡住退出
            工作.start()
        try:
            return {'agent':恢复.等待()}#恢复成功则返回智能体
        except 远程会话未找到 as 错误:
            return {'error':{'code':'session-not-found','message':str(错误),'details':{'sessionId':会话标识}}}#会话未找到信封
        except 远程子智能体会话所有权 as 错误:
            return {'error':远程子智能体所有权错误(错误.会话标识)}#折成 agent-busy
        except Exception as 错误:
            围栏=围栏在线(会话标识)#失败时再看是否已有可复用在线智能体
            if 围栏 is not None:#有则用之
                return 围栏#结论
            已附着=上下文.sessions.get(会话标识)#再看已附着会话
            if 已附着 is not None and 有远程子智能体所有者(上下文,已附着.header,None):#现已由子智能体占用
                return {'error':远程子智能体所有权错误(会话标识)}#折成 agent-busy
            return {#其余视为内部失败
                'error':{#内部错误信封
                    'code':'internal',#内部错误码
                    'message':'resume failed for session "'+str(会话标识)+'": '+str(错误),#带上恢复失败原因
                    'details':{},#无额外细节
                },#error 字段结束
            }#内部失败结束

    def 挂查找(类型上下文,*位置参数):
        """配置智能体/会话查找与宿主上下文提供方。"""
        def 解析到智能体(会话标识):
            """查找失败抛 查找策略失败。"""
            找到=解析智能体(会话标识)#走共享解析器
            if 'error' in 找到:#面向调用方失败原样保留
                raise 查找策略失败(找到['error'])#抛出
            return 找到['agent']#解析到智能体
        def 解析到会话(会话标识):
            """会话查找。"""
            return 解析到智能体(会话标识).session#智能体上的会话
        def 解析到上下文(会话标识):
            """宿主上下文。"""
            return 解析到智能体(会话标识).ctx#智能体上下文
        类型上下文.typert.lookups.configure('agent',解析到智能体)
        类型上下文.typert.lookups.configure('session',解析到会话)
        类型上下文.typert.contexts.configureHost('agent',解析到上下文)#宿主上下文提供方
    上下文.依赖启动(['typert'],挂查找)#等 typert 可用
    return 解析智能体#返回共享解析器
