'解析 Remote 智能体与会话身份的宿主 BFF 策略'
from functools import partial as 绑定参数#把落定槽绑进然后回调，避免再套一层函数
from typing import NotRequired,TypedDict#结构类型
from ...基础设施.js特性 import PromiseEX as 期约#中文别名的期约
from ...类型化远程调用.协议.异常 import 查找策略失败#lookup 策略拒绝
from .异常 import 远程查找错误基类,远程会话未找到,远程子智能体会话所有权#本包异常

__all__=(#仅中文公开名
    '远程会话未找到','远程子智能体会话所有权',
    '有远程子智能体所有者','远程子智能体所有权错误',
    '查看远程会话','创建远程智能体解析器',
    '远程查找错误码','远程查找错误',
    '远程智能体结果成功','远程智能体结果失败','远程智能体结果','远程智能体选项',
    '远程查找错误基类',
)#公开面结束

远程查找错误码=('agent-busy','session-not-found','internal')#面向调用方失败码联合

class 远程查找错误(TypedDict):
    '网关 RPC 适配器原样保留的面向调用方失败'
    code:str#agent-busy | session-not-found | internal
    message:str#诊断消息
    details:dict#按码携带 reason / sessionId / 空对象

class 远程智能体结果成功(TypedDict):
    '解析到在线智能体'
    agent:object#在线智能体

class 远程智能体结果失败(TypedDict):
    '查找失败'
    error:远程查找错误#面向调用方失败信封

远程智能体结果=dict#成功含 agent，失败含 error（运行时联合）

class 远程智能体选项(TypedDict):
    '拥有方宿主组合提供的恢复配置'
    agentOptions:NotRequired[object]#可选的智能体默认选项工厂
    setup:NotRequired[object]#发布前宿主专用智能体作用域装配工厂

def 有远程子智能体所有者(上下文,头,智能体):
    '测试通用宿主路由是否必须把该身份留给子智能体路由。头为会话头 dict'
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
    '构造稳定的面向调用方所有权拒绝'
    return {#agent-busy 信封
        'code':'agent-busy',#智能体正忙
        'message':'session "'+str(会话标识)+'" is owned by subagent routing',#由子智能体路由占用
        'details':{'reason':'use subagent delivery for this child session'},#应走子智能体投递
    }#信封结束

def 查看远程会话(上下文,会话标识):
    '查看一个冷的可服务会话，不修复、不恢复、不发布'
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

def 恢复已成功(恢复中,会话标识,共享恢复,句柄):
    '恢复成功：允许同一身份再次恢复，以智能体解决共享期约'
    恢复中.pop(会话标识,None)#允许同一身份再次恢复
    共享恢复.解决(句柄.agent)

def 恢复已失败(恢复中,会话标识,共享恢复,错误):
    '恢复失败：允许同一身份再次恢复，所有调用方经 捕获 收到同一失败'
    恢复中.pop(会话标识,None)#允许同一身份再次恢复
    共享恢复.拒绝(错误)

def 解析成功(结果,智能体):
    '恢复成功则返回智能体'
    结果.解决({'agent':智能体})

def 解析失败(结果,会话标识,上下文,围栏在线,错误):
    '把恢复失败折成面向调用方的失败信封'
    if isinstance(错误,远程会话未找到):
        结果.解决({'error':{'code':'session-not-found','message':str(错误),'details':{'sessionId':会话标识}}})#会话未找到信封
        return
    if isinstance(错误,远程子智能体会话所有权):
        结果.解决({'error':远程子智能体所有权错误(错误.会话标识)})#折成 agent-busy
        return
    围栏=围栏在线(会话标识)#失败时再看是否已有可复用在线智能体
    if 围栏 is not None:#有则用之
        结果.解决(围栏)#结论
        return
    已附着=上下文.sessions.get(会话标识)#再看已附着会话
    if 已附着 is not None and 有远程子智能体所有者(上下文,已附着.header,None):#现已由子智能体占用
        结果.解决({'error':远程子智能体所有权错误(会话标识)})#折成 agent-busy
        return
    结果.解决({#其余视为内部失败
        'error':{#内部错误信封
            'code':'internal',#内部错误码
            'message':'resume failed for session "'+str(会话标识)+'": '+str(错误),#带上恢复失败原因
            'details':{},#无额外细节
        },#error 字段结束
    })#内部失败结束

def 已找到(落定,找到):
    '面向调用方失败原样保留，成功则交出智能体'
    if 'error' in 找到:
        落定.拒绝(查找策略失败(找到['error']))#失败信封
        return
    落定.解决(找到['agent'])#解析到智能体

def 已找到会话(落定,智能体):
    '取智能体上的会话'
    落定.解决(智能体.session)

def 已找到上下文(落定,智能体):
    '取智能体上的作用域上下文'
    落定.解决(智能体.ctx)

def 创建远程智能体解析器(上下文,选项):
    '在线智能体复用，普通冷会话按身份恢复一次，子智能体占用的身份保留旧的 agent-busy 围栏。选项为 dict'
    恢复中={}#进行中的按身份去重恢复：会话标识 → 共享期约

    def 围栏在线(会话标识):
        '在线智能体复用或 agent-busy'
        在线=上下文.agents.get(会话标识)#取该身份的在线智能体
        if 在线 is None:#没有在线智能体
            return None#无结论
        if 有远程子智能体所有者(上下文,在线.session.header,在线):#在线但由子智能体路由占用
            return {'error':远程子智能体所有权错误(会话标识)}#返回 agent-busy
        return {'agent':在线}#可复用在线智能体

    def 解析智能体(会话标识):
        '先看在线，再冷恢复。返回期约，解决值是 {agent} 或 {error}'
        结果=期约()#本次解析的结算点
        围栏=围栏在线(会话标识)#先看在线智能体
        if 围栏 is not None:#已有结论则返回
            结果.解决(围栏)#结论
            return 结果
        已附着=上下文.sessions.get(会话标识)#取已附着但可能尚未发布智能体的会话
        if 已附着 is not None and 有远程子智能体所有者(上下文,已附着.header,None):#已附着且由子智能体占用
            结果.解决({'error':远程子智能体所有权错误(会话标识)})#返回 agent-busy
            return 结果
        恢复=恢复中[会话标识] if 会话标识 in 恢复中 else None#该身份是否已有进行中的恢复
        if 恢复 is None:#没有则启动一次并写入共享期约
            恢复=期约()#共享恢复期约
            恢复中[会话标识]=恢复#先入表，后跑体，使并发调用方挂上同一期约
            共享恢复=恢复#供回调落定本次期约
            成功回调=绑定参数(恢复已成功,恢复中,会话标识,共享恢复)#同级函数
            失败回调=绑定参数(恢复已失败,恢复中,会话标识,共享恢复)#同级函数
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
                恢复期约=上下文.agents.resume(恢复参数)#按该身份恢复智能体
            except BaseException as 错误:#同步段失败以拒绝交出
                失败回调(错误)
            else:
                恢复期约.然后(成功回调,失败回调)#恢复落定后结算共享期约
        恢复.然后(绑定参数(解析成功,结果),绑定参数(解析失败,结果,会话标识,上下文,围栏在线))#共享恢复落定后解析
        return 结果#调用方对期约链接 然后 与 捕获

    def 解析到智能体(会话标识):
        '返回期约；查找失败以 查找策略失败 拒绝，成功则以智能体解决'
        落定=期约()#本次查找的结算点
        解析智能体(会话标识).然后(绑定参数(已找到,落定),落定.拒绝)#走共享解析器
        return 落定

    def 解析到会话(会话标识):
        '会话查找，返回期约'
        落定=期约()#本次查找的结算点
        解析到智能体(会话标识).然后(绑定参数(已找到会话,落定),落定.拒绝)
        return 落定

    def 解析到上下文(会话标识):
        '宿主上下文，返回期约'
        落定=期约()#本次查找的结算点
        解析到智能体(会话标识).然后(绑定参数(已找到上下文,落定),落定.拒绝)
        return 落定

    def 挂查找(类型上下文,*位置参数):
        '配置智能体/会话查找与宿主上下文提供方'
        类型上下文.typert.lookups.configure('agent',解析到智能体)
        类型上下文.typert.lookups.configure('session',解析到会话)
        类型上下文.typert.contexts.configureHost('agent',解析到上下文)#宿主上下文提供方
    上下文.依赖启动(['typert'],挂查找)#等 typert 可用
    return 解析智能体#返回共享解析器
