"""本包拥有的持久目标流不变量。"""
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现的拆除器
from .折叠 import 应用目标事件,空目标折叠状态#严格折叠步进与空累加器

包名='@deepseek-ai/dsh-goal'#本包的不变量所有权名
名称='goal-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 克隆状态(状态):#校验一条候选事件前先复制独立折叠状态
    """浅拷贝快照并复制已见 id 集合。"""
    return {#新累加器，不改原状态
        'goal':状态['goal'],#当前快照引用
        'roundsStarted':状态['roundsStarted'],#已接纳轮次
        'createdAt':状态['createdAt'],#创建时间
        'updatedAt':状态['updatedAt'],#最近变更时间
        'lastRef':状态['lastRef'],#最近变更引用
        'seenGoalIds':set(状态['seenGoalIds']),#已见目标 id 的独立副本
    }#结束副本

def 带检应用(状态,事件,失败):#经严格目标解码器应用一条事件，并把失败归因到不变量
    """经严格目标解码器应用一条事件，并把失败归因到不变量。"""
    try:#严格解码器可能抛
        应用目标事件(状态,事件)#就地应用本条
    except Exception as 错误:#本条破坏目标流
        消息=str(错误)#取出可读原因
        失败('session event '+str(取字段(事件,'seq'))+' violates the durable goal stream: '+消息)#按序号报告

def 安装(上下文对象,失败):#为每个已挂接会话安装一份独立的增量折叠
    """为已加载和新追加的目标流安装校验。"""
    状态表={}#会话 → 已提交折叠
    暂存={}#事件 → 预校验后的下一状态

    def 种子(会话对象):#回放该会话已有事件
        """回放该会话已有事件并记下已提交折叠。"""
        状态=空目标折叠状态()#空累加器
        for 事件 in 会话对象.events:#逐条严格应用
            带检应用(状态,事件,失败)#带失败归因
        状态表[id(会话对象)]=状态#记下已提交折叠
        return 状态#供取状态回退使用

    def 取状态(会话对象):#已有则用，否则补种子
        """已有则用，否则补种子。"""
        键=id(会话对象)#会话身份
        if 键 in 状态表:#已有
            return 状态表[键]#已提交折叠
        return 种子(会话对象)#补种子

    for 会话对象 in 上下文对象.sessions.list():#对当前所有会话做种子校验
        种子(会话对象)#种子校验
    def 会话创建(会话对象,*其余):#新会话创建时再种子
        """新会话创建时再种子。"""
        种子(会话对象)#种子
    上下文对象.on('session/created',会话创建,{'global':True})#全局监听
    def 内部派发(_模式,事件名,参数,*其余):#拦截内部派发以预校验
        """提交前检查 session/event。"""
        if 事件名!='session/event':#只关心会话事件
            return#放过
        会话对象=参数[0]#第一实参是会话
        事件=参数[1]#第二实参是事件
        状态=克隆状态(取状态(会话对象))#在副本上试应用，失败不污染已提交折叠
        带检应用(状态,事件,失败)#预校验本条
        暂存[id(事件)]={'session':会话对象,'state':状态}#暂存，待发布时提交
    上下文对象.on('internal/dispatch',内部派发,{'global':True})#全局监听
    def 会话事件(会话对象,事件,*其余):#事件真正发布后再提交折叠
        """事件真正发布后再提交折叠。"""
        候选=暂存.get(id(事件))#取出预校验结果
        if 候选 is None or 候选['session'] is not 会话对象:#没有匹配的预校验
            失败('session/event reached publication without matching goal-fold validation')#发布前必须先校验
            return#已失败
        暂存.pop(id(事件),None)#清掉暂存
        状态表[id(会话对象)]=候选['state']#提交下一折叠
    上下文对象.on('session/event',会话事件,{'global':True})#全局监听

安装.inject=['sessions']#安装器还要 sessions

def 应用(上下文对象):#注册目标流不变量配套
    """注册目标流不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺

apply=应用#Cordis 插件入口
