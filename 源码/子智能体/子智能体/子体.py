from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型
from ...内核.系统提示词 import 人设段落名,人设顺序#遮蔽部署人设须同名同序
from .深度 import 委托深度于#导入委托深度读取
from .异常 import 子智能体深度错误,范围错误#本包异常

安全整数上限=2**53-1#对齐 Number.MAX_SAFE_INTEGER

class 子体组合(TypedDict):
    '子智能体创建窗口应用的作用域组合'
    persona:NotRequired[str]#遮蔽部署人设的每子体人设
    toolFilter:NotRequired[object]#每子体工具作用域

class 委托策略覆盖(TypedDict):
    '在委托边界播种到子会话日志的策略'
    sandboxMode:object#父会话的显式沙盒模式覆盖；没有则为 None
    approvalPolicy:NotRequired[Literal['never']]#组合了审批能力时为 never，否则缺席

def 解析子深度(父,最大深度=None):
    '从父解析子体委托深度并强制可选上限。持久父头是单调下限，因此恢复的父不能像顶层一样委托'
    子深度=委托深度于(父)+1#父深度加一
    if (not isinstance(子深度,int)) or isinstance(子深度,bool) or 子深度>安全整数上限:#超出安全整数
        raise 范围错误('子智能体子体深度超出安全整数范围')#拒绝
    if 最大深度 is not None and 子深度>最大深度:#超过可选上限
        raise 子智能体深度错误(子深度,最大深度)#深度超限
    return 子深度#已解析深度

def 父委托智能体选项(父):
    '委托用的父路由：请求头拥有提供方、模型与推理力度，其余仍用父选项'
    父选项=dict(父.options) if isinstance(父.options,dict) else {}#父选项拷贝
    请求头=父.session.请求头() if hasattr(父.session,'请求头') else None#当前请求头
    配置=请求头['config'] if isinstance(请求头,dict) and 'config' in 请求头 else None#请求配置
    if not isinstance(配置,dict):#没有请求头
        return 父选项#整份父选项
    结果={键:值 for 键,值 in 父选项.items() if 键 not in ('provider','model','reasoningEffort')}#去掉创建时路由
    结果['provider']=配置['provider']#请求头提供方
    结果['model']=配置['model']#请求头模型
    if 'reasoningEffort' in 配置 and 配置['reasoningEffort'] is not None:#请求头点了力度
        结果['reasoningEffort']=配置['reasoningEffort']#力度
    return 结果#委托路由

def 解析子智能体选项(父,请求,子深度):
    '解析子体的 AgentOptions：除非请求覆盖，否则继承父的提供方/模型/推理力度/maxTokens，并盖上子体自己的委托深度。换了路由又没点力度时清掉父的力度'
    父选项=父委托智能体选项(父)#委托路由
    结果={}#合并路由
    for 键 in ('provider','model','reasoningEffort','maxTokens'):#继承这些
        if 键 in 父选项 and 父选项[键] is not None:#有值
            结果[键]=父选项[键]#展开
    if isinstance(请求,dict):#有请求覆盖
        结果.update(请求)#覆盖
    结果['subagentDepth']=子深度#盖上子深度
    路由变了=结果.get('provider')!=父选项.get('provider') or 结果.get('model')!=父选项.get('model')#路由变了
    请求点了力度=isinstance(请求,dict) and 'reasoningEffort' in 请求 and 请求['reasoningEffort'] is not None#请求自己点了力度
    if 路由变了 and not 请求点了力度 and 'reasoningEffort' in 结果:#清掉父路由自己的力度
        del 结果['reasoningEffort']#让所选模型用自己的默认力度
    return 结果#已解析选项

def 子会话元数据(父,子深度,已播种):
    '建造子会话的耐久创建元数据：父的工作区、其直接谱系、粗产品来源、必须活过持久化的递归预算、是否继承父日志前缀（含显式空前缀），以及子体运行所在的组合'
    父头=父.session.header#父会话头
    预设服务=None#活组合预设服务
    父上下文=父.ctx#父上下文
    if 父上下文 is not None:#可取服务
        预设服务=父上下文.获取服务('agentPresets')#智能体预设
    智能体预设=None#活组合预设
    if 预设服务 is not None:#有预设服务
        智能体预设=预设服务.composedPreset(父上下文)#活组合预设
    结果={'parentSession':父头['id'] if isinstance(父头,dict) and 'id' in 父头 else None,'origin':'subagent','delegationDepth':子深度,'isSeeded':bool(已播种)}#耐久元数据
    工作区=父头['cwd'] if isinstance(父头,dict) and 'cwd' in 父头 else None#工作区
    if 工作区 is not None:#有工作区
        结果['cwd']=工作区#展开
    if 智能体预设 is not None:#有预设
        结果['agentPreset']=智能体预设#展开
    return 结果#创建元数据

子智能体委托上下文=(#委托作用域声明
    'You are a delegated subagent: your permission scope was fixed when you were started and cannot be '#权限已固定
    +'widened from inside this session — operations that require approval are rejected automatically. '#不可扩权
    +'When the task needs access beyond that scope, do not retry the denied operation; state the '#勿重试拒绝
    +'limitation in your reply so the delegating agent can handle it.'#上报限制收尾
)#声明结束

def 应用子体组合(子上下文,父,组合):
    '在创建窗口内组合一个子体：加入其父的预设，登记固定的委托作用域声明，然后应用子体自己的遮蔽人设段落与工具限制。组合为 dict'
    预设服务=子上下文.获取服务('agentPresets')#智能体预设
    if 预设服务 is not None:#有预设服务
        预设服务.composeFrom(子上下文,父.ctx)#加入父预设
    子上下文.systemPrompt.context({'name':'subagent:delegation','order':120,'text':子智能体委托上下文})#登记委托声明
    人设=组合['persona'] if isinstance(组合,dict) and 'persona' in 组合 else None#每子体人设
    if 人设 is not None:#有每子体人设
        子上下文.systemPrompt.section({'name':人设段落名,'order':人设顺序,'text':人设})#遮蔽部署人设
    工具过滤=组合['toolFilter'] if isinstance(组合,dict) and 'toolFilter' in 组合 else None#工具过滤
    if 工具过滤 is not None:#有工具限制
        子上下文.tools.restrict(工具过滤)#应用工具限制

def 捕获委托策略覆盖(父):
    '捕获要播种进一次委托的策略。在子体 start 的第一次等待之前同步调用：后来的父切换属于父的未来，不属于本子体'
    父上下文=父.ctx#父上下文
    沙盒模式=None#显式沙盒覆盖
    审批策略=None#审批钉
    if 父上下文 is not None:#可取服务
        沙盒政策=父上下文.获取服务('sandboxPolicy')#沙盒策略服务
        if 沙盒政策 is not None:#有沙盒策略
            沙盒模式=沙盒政策.覆盖于(父.session)#显式沙盒覆盖
        if 父上下文.获取服务('approval') is not None:#有审批能力
            审批策略='never'#钉never
    结果={'sandboxMode':沙盒模式}#当前父策略快照
    if 审批策略 is not None:#有审批钉才写入
        结果['approvalPolicy']=审批策略#展开
    return 结果#快照

def 追加委托策略覆盖(子会话,覆盖):
    '把捕获的委托策略作为 source: \'delegation\' 事件追加到子体自己的日志，位于未发布创建窗口内。覆盖为 dict'
    沙盒模式=覆盖['sandboxMode'] if 'sandboxMode' in 覆盖 else None#沙盒覆盖
    if 沙盒模式 is not None:#有沙盒覆盖
        子会话.追加('sandbox/mode',{'mode':沙盒模式,'source':'delegation'})#追加沙盒事件
    审批策略=覆盖['approvalPolicy'] if 'approvalPolicy' in 覆盖 else None#审批钉
    if 审批策略 is not None:#有审批钉
        子会话.追加('approval/policy',{'policy':审批策略,'source':'delegation'})#追加审批事件
