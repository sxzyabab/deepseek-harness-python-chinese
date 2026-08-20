"""共享的进程内子体组合：委托深度预算、耐久会话元数据、已解析的子 AgentOptions、委托策略种子，以及子智能体需要的作用域装配。一次性提供方驱动与续跑管理器都这样组合子体。"""
from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型
from .深度 import 委托深度于#导入委托深度读取

安全整数上限=2**53-1#对齐 Number.MAX_SAFE_INTEGER

class 子体组合(TypedDict):#子智能体创建窗口应用的作用域组合
    persona:NotRequired[str]#遮蔽部署人设的每子体人设
    toolFilter:NotRequired[object]#每子体工具作用域

class 委托策略覆盖(TypedDict):#在委托边界播种到子会话日志的策略
    sandboxMode:object#父会话的显式沙盒模式覆盖；没有则为 None
    approvalPolicy:NotRequired[Literal['never']]#组合了审批能力时为 never，否则缺席

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

class 子智能体深度错误(Exception):#深度超限错误
    """启动子体会超过所请求深度上限时抛出。"""
    def __init__(自身,尝试深度,最大深度):#记下尝试深度与上限
        """记下尝试深度与上限；消费方只读中文属性。"""
        Exception.__init__(自身,'subagent depth '+str(尝试深度)+' exceeds maxDepth '+str(最大深度))#文案含两个数
        自身.尝试深度=尝试深度#已算出的子深度
        自身.最大深度=最大深度#调用方给出的绝对上限

class 范围错误(Exception):#对齐 JS RangeError
    """子深度离开安全整数范围时抛出。"""
    pass#无附加字段

def 解析子深度(父,最大深度=None):#解析子深度
    """从父解析子体委托深度并强制可选上限。持久父头是单调下限，因此恢复的父不能像顶层一样委托。"""
    子深度=委托深度于(父)+1#父深度加一
    if not isinstance(子深度,int) or 子深度>安全整数上限:#超出安全整数
        raise 范围错误('subagent child depth exceeds the safe-integer range')#拒绝
    if 最大深度 is not None and 子深度>最大深度:#超过可选上限
        raise 子智能体深度错误(子深度,最大深度)#深度超限
    return 子深度#已解析深度

def 解析子智能体选项(父,请求,子深度):#解析子智能体选项
    """解析子体的 AgentOptions：除非请求覆盖，否则继承父的提供方/模型/maxTokens 路由，并盖上子体自己的委托深度。"""
    结果={}#合并路由
    父提供方=取字段(取字段(父,'options'),'provider')#父提供方
    父模型=取字段(取字段(父,'options'),'model')#父模型
    父令牌上限=取字段(取字段(父,'options'),'maxTokens')#父token上限
    if 父提供方 is not None:#有父提供方
        结果['provider']=父提供方#展开
    if 父模型 is not None:#有父模型
        结果['model']=父模型#展开
    if 父令牌上限 is not None:#有父token上限
        结果['maxTokens']=父令牌上限#展开
    if 请求 is not None:#有请求覆盖
        if isinstance(请求,dict):#映射
            结果.update(请求)#覆盖
        else:#对象
            for 键 in ('provider','model','maxTokens','subagentDepth'):#常见键
                值=getattr(请求,键,None)#读
                if 值 is not None:#有值
                    结果[键]=值#写入
    结果['subagentDepth']=子深度#盖上子深度
    return 结果#已解析选项

def 子会话元数据(父,子深度,谱系种子长度):#建造子会话元数据
    """建造子会话的耐久创建元数据：父的工作区、其直接谱系、粗产品来源、必须活过持久化的递归预算、分隔继承父历史与子工作的种子边界，以及子体运行所在的组合。"""
    父头=取字段(取字段(父,'session'),'header')#父会话头
    预设服务=None#活组合预设服务
    父上下文=取字段(父,'ctx')#父上下文
    if 父上下文 is not None and hasattr(父上下文,'get'):#可取服务
        预设服务=父上下文.get('agentPresets')#智能体预设
    智能体预设=None#活组合预设
    if 预设服务 is not None:#有预设服务
        组合自=getattr(预设服务,'composedPreset',None) or getattr(预设服务,'组合预设',None)#组合方法
        if 组合自 is not None:#有方法
            智能体预设=组合自(父上下文)#活组合预设
    结果={'parentSession':取字段(父头,'id'),'origin':'subagent','delegationDepth':子深度}#耐久元数据
    工作区=取字段(父头,'cwd')#工作区
    if 工作区 is not None:#有工作区
        结果['cwd']=工作区#展开
    if 智能体预设 is not None:#有预设
        结果['agentPreset']=智能体预设#展开
    if 谱系种子长度>0:#有父前缀
        结果['seedLength']=谱系种子长度#记下边界
    return 结果#创建元数据

子智能体委托上下文=(#委托作用域声明
    'You are a delegated subagent: your permission scope was fixed when you were started and cannot be '#权限已固定
    +'widened from inside this session — operations that require approval are rejected automatically. '#不可扩权
    +'When the task needs access beyond that scope, do not retry the denied operation; state the '#勿重试拒绝
    +'limitation in your reply so the delegating agent can handle it.'#上报限制收尾
)#声明结束

def 应用子体组合(子上下文,父,组合):#应用子体组合
    """在创建窗口内组合一个子体：加入其父的预设，登记固定的委托作用域声明，然后应用子体自己的遮蔽人设段落与工具限制。"""
    预设服务=子上下文.get('agentPresets') if hasattr(子上下文,'get') else None#智能体预设
    if 预设服务 is not None:#有预设服务
        组合自=getattr(预设服务,'composeFrom',None) or getattr(预设服务,'自组合',None)#加入方法
        if 组合自 is not None:#有方法
            组合自(子上下文,取字段(父,'ctx'))#加入父预设
    # 顺序 120：在 sandbox:policy（110）与 approval:policy（115）句子之后。
    子上下文.systemPrompt.context({'name':'subagent:delegation','order':120,'text':子智能体委托上下文})#登记委托声明
    人设=取字段(组合,'persona')#每子体人设
    if 人设 is not None:#有每子体人设
        子上下文.systemPrompt.section({'name':'deployment:persona','order':0,'text':人设})#遮蔽部署人设
    工具过滤=取字段(组合,'toolFilter')#工具过滤
    if 工具过滤 is not None:#有工具限制
        子上下文.tools.restrict(工具过滤)#应用工具限制

def 捕获委托策略覆盖(父):#捕获委托策略
    """捕获要播种进一次委托的策略。在子体 start 的第一次 await 之前同步调用：后来的父切换属于父的未来，不属于本子体。"""
    父上下文=取字段(父,'ctx')#父上下文
    沙盒模式=None#显式沙盒覆盖
    审批策略=None#审批钉
    if 父上下文 is not None and hasattr(父上下文,'get'):#可取服务
        沙盒政策=父上下文.get('sandboxPolicy')#沙盒策略服务
        if 沙盒政策 is not None:#有沙盒策略
            覆盖于=getattr(沙盒政策,'overrideOf',None) or getattr(沙盒政策,'覆盖于',None)#覆盖读取
            if 覆盖于 is not None:#有方法
                沙盒模式=覆盖于(取字段(父,'session'))#显式沙盒覆盖
        if 父上下文.get('approval') is not None:#有审批能力
            审批策略='never'#钉never
    return {'sandboxMode':沙盒模式,'approvalPolicy':审批策略}#当前父策略快照

def 追加委托策略覆盖(子会话,覆盖):#追加委托策略事件
    """把捕获的委托策略作为 source: 'delegation' 事件追加到子体自己的日志，位于未发布创建窗口内。"""
    沙盒模式=取字段(覆盖,'sandboxMode')#沙盒覆盖
    if 沙盒模式 is not None:#有沙盒覆盖
        if hasattr(子会话,'追加'):#会话追加入口（中文优先）
            子会话.追加('sandbox/mode',{'mode':沙盒模式,'source':'delegation'})#追加沙盒事件
        else:#英文 append
            子会话.append('sandbox/mode',{'mode':沙盒模式,'source':'delegation'})#追加沙盒事件
    审批策略=取字段(覆盖,'approvalPolicy')#审批钉
    if 审批策略 is not None:#有审批钉
        if hasattr(子会话,'追加'):#会话追加入口（中文优先）
            子会话.追加('approval/policy',{'policy':审批策略,'source':'delegation'})#追加审批事件
        else:#英文 append
            子会话.append('approval/policy',{'policy':审批策略,'source':'delegation'})#追加审批事件
