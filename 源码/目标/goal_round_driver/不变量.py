"""本包拥有的目标轮次提示词不变量。"""
from ...依赖 import cordis#外部依赖胶水
from ..目标 import 折叠目标#按前缀重建目标
from .提示 import 渲染目标轮次提示#本包拥有的续跑提示渲染器

包名='@deepseek-ai/dsh-goal-round-driver'#本包的不变量所有权名
名称='goal-round-driver-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 深相等(左,右):#对齐 isDeepStrictEqual 的 JSON 形比较
    """比较两条载荷是否深相等。"""
    return 左==右#结构化相等

def 折叠带检(事件们,失败):#把严格目标折叠失败归因到本配套的重建
    """经严格目标解码器折叠，并把失败归因到续跑前缀。"""
    try:#严格解码器可能抛
        return 折叠目标(事件们)#按前缀重建目标
    except Exception as 错误:#折叠失败则报告不变量
        消息=str(错误)#取出可读原因
        return 失败('cannot reconstruct the goal before a continuation message: '+消息)#归因到续跑前缀

def 目标视图(折叠,来源,失败):#重建本包纯提示渲染器所消费的实时形视图
    """前缀折叠成驱动器入队时的实时形视图。"""
    目标=取字段(折叠,'goal')#当前快照，可能缺席
    if (目标 is None or 取字段(折叠,'createdAt') is None or 取字段(折叠,'updatedAt') is None#缺快照或时间戳
        or 取字段(目标,'phase')!='active' or 取字段(目标,'id')!=取字段(来源,'goalId') or 取字段(目标,'revision')!=取字段(来源,'revision')#非本轮活跃修订
        or 取字段(来源,'round')!=取字段(折叠,'roundsStarted')+1 or 取字段(来源,'round')>取字段(目标,'maxGoalRounds')):#不是下一轮或越上限
        return 失败('goal round '+str(取字段(来源,'round'))+' cannot be reconstructed from the preceding durable goal state')#前缀对不上来源
    视图=dict(目标)#驱动器入队时的实时形
    视图['roundsStarted']=取字段(折叠,'roundsStarted')#已接纳轮次
    视图['createdAt']=取字段(折叠,'createdAt')#创建时间
    视图['updatedAt']=取字段(折叠,'updatedAt')#最近变更时间
    视图['activation']='armed'#续跑消息只在武装时产生
    return 视图#结束视图

def 校验事件(前缀,事件,失败):#用持久前缀校验本包拥有的一条续跑消息
    """非本包续跑则跳过；正文必须与本包渲染器逐字节一致。"""
    if 取字段(事件,'type')!='user/message':#只看用户消息
        return#放过
    来源=取字段(取字段(事件,'data'),'source')#消息归因
    if 取字段(来源,'kind')!='goal' or 取字段(来源,'round')<=0:#非正数目标轮次则跳过
        return#放过
    期望=渲染目标轮次提示(目标视图(折叠带检(前缀,失败),来源,失败),取字段(来源,'round'))#按前缀重渲染
    if not 深相等(取字段(取字段(事件,'data'),'content'),期望):#正文必须与本包渲染器一致
        失败('goal round '+str(取字段(来源,'round'))+' content does not match the package-owned continuation prompt')#正文被改过

def 安装(上下文对象,失败):#检查已有会话，并在 Session 发布每条候选事件之前再检查
    """安装器：种子并拦截派发。"""
    for 会话对象 in 上下文对象.sessions.list():#已加载会话
        前缀=[]#逐步增长的前缀
        for 事件 in 会话对象.events:#按序回放
            校验事件(前缀,事件,失败)#用当前前缀校验本条
            前缀.append(事件)#纳入后续前缀
    def 内部派发(_模式,事件名,参数,*其余):#拦截内部派发
        """提交前检查 session/event。"""
        if 事件名!='session/event':#只关心会话事件
            return#放过
        会话对象=参数[0]#第一实参是会话
        事件=参数[1]#第二实参是刚追加的事件
        校验事件(会话对象.events,事件,失败)#已提交前缀校验新事件
    上下文对象.on('internal/dispatch',内部派发,{'global':True})#全局监听，不随作用域拆除

安装.inject=['sessions']#安装器还要 sessions

def 应用(上下文对象):#注册目标轮次驱动器的不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺

apply=应用#Cordis插件入口
