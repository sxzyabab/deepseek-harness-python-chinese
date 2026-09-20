"""本包拥有的持久目标流不变量。"""
from .折叠 import 应用目标事件,空目标折叠状态,目标折叠错误#严格折叠步进、空累加器与回放失败

包名='@deepseek-ai/dsh-goal'#本包的不变量所有权名
名称='goal-invariant'#配套不变量插件名
依赖=['invariants']#依赖invariants服务

def 克隆状态(状态):
    """浅拷贝快照并复制已见 id 集合。状态是 dict。"""
    return {#新累加器，不改原状态
        'goal':状态['goal'],#当前快照引用
        'roundsStarted':状态['roundsStarted'],#已接纳轮次
        'createdAt':状态['createdAt'],#创建时间
        'updatedAt':状态['updatedAt'],#最近变更时间
        'lastRef':状态['lastRef'],#最近变更引用
        'seenGoalIds':set(状态['seenGoalIds']),#已见目标 id 的独立副本
    }#结束副本

def 带检应用(状态,事件,失败):
    """经严格目标解码器应用一条事件，并把失败归因到不变量。事件是 dict。"""
    try:#严格解码器可能抛
        应用目标事件(状态,事件)#就地应用本条
    except 目标折叠错误 as 错误:#回放失败
        消息=str(错误)#取出可读原因
        序号=事件['seq'] if 'seq' in 事件 else None#事件序号
        失败('session event '+str(序号)+' violates the durable goal stream: '+消息)#按序号报告

def 安装(上下文,失败):
    """为已加载和新追加的目标流安装校验。会话是对象。"""
    状态表={}#会话身份 → 已提交折叠
    暂存={}#事件身份 → 预校验后的下一状态

    def 种子(会话):
        """回放该会话已有事件并记下已提交折叠。"""
        状态=空目标折叠状态()#空累加器
        for 事件 in 会话.events:#逐条严格应用
            带检应用(状态,事件,失败)#带失败归因
        状态表[id(会话)]=状态#记下已提交折叠
        return 状态#供取状态回退使用

    def 取状态(会话):
        """已有则用，否则补种子。"""
        键=id(会话)#会话身份
        if 键 in 状态表:#已有
            return 状态表[键]#已提交折叠
        return 种子(会话)#补种子

    for 会话 in 上下文.sessions.列出():#对当前所有会话做种子校验
        种子(会话)#种子校验
    def 会话创建(会话,*其余):
        """新会话创建时再种子。"""
        种子(会话)#种子
    上下文.监听('session/created',会话创建,{'全局':True})#全局监听
    def 内部派发(_模式,事件名,参数,*其余):
        """提交前检查 session/event。"""
        if 事件名!='session/event':#只关心会话事件
            return#放过
        会话=参数[0]#第一实参是会话
        事件=参数[1]#第二实参是事件
        状态=克隆状态(取状态(会话))#在副本上试应用，失败不污染已提交折叠
        带检应用(状态,事件,失败)#预校验本条
        暂存[id(事件)]={'session':会话,'state':状态}#暂存，待发布时提交
    上下文.监听('internal/dispatch',内部派发,{'全局':True})#全局监听
    def 会话事件(会话,事件,*其余):
        """事件真正发布后再提交折叠。"""
        事件键=id(事件)#事件身份
        if 事件键 not in 暂存:#没有匹配的预校验
            失败('session/event reached publication without matching goal-fold validation')#发布前必须先校验
            return#已失败
        候选=暂存[事件键]#取出预校验结果
        if 候选['session'] is not 会话:#不是同一会话
            失败('session/event reached publication without matching goal-fold validation')#发布前必须先校验
            return#已失败
        暂存.pop(事件键,None)#清掉暂存
        状态表[id(会话)]=候选['state']#提交下一折叠
    上下文.监听('session/event',会话事件,{'全局':True})#全局监听

安装.inject=['sessions']#安装器还要 sessions

def 应用(上下文):
    """注册目标流不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)#登记

__all__=['包名','名称','依赖','安装','应用']#仅中文公开名
name=名称#Cordis 插件名
inject=依赖#Cordis 依赖声明
apply=应用#Cordis 插件入口
default=应用#Cordis 默认导出
