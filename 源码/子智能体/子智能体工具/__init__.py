from ...基础设施.js特性 import PromiseEX as 期约#期约封装
from ...依赖.schemastery import 字符串字段,布尔字段,整数字段,列表字段,复合类型字段,常量字段,字典字段,自然数字段#配置字段
from ...内核.工具 import 定义工具#导入工具定义
from ..子智能体 import 断言子智能体最大深度#深度断言
from ..子智能体.异常 import 子智能体错误#缝内失败

名称='tool-subagent'#Cordis插件名
依赖=['tools','subagents','systemPrompt','sessionProjections']#依赖工具、子智能体、提示词与投影
委托工具集合=set()#可见委托工具定义，指引只列当前作用域看得到的
配置入口上限=2**53-1#外来 JSON 配置的深度上限校验
配置={#部署配置：委托到哪个提供方以及子体默认值
    'provider':字符串字段(可空=False),#必填提供方名
    'toolName':字符串字段(默认值='subagent'),#默认工具名
    'modelSelectionSettings':布尔字段(默认值=False),#默认关闭模型选择设置
    'agentOptions':字典字段(字典结构={#智能体选项模式
        'provider':字符串字段(),#模型提供方
        'model':字符串字段(),#模型名
        'reasoningEffort':字符串字段(),#推理力度
        'maxTokens':整数字段(默认值=1),#正整数token上限
    },默认值=None),#省略时保持未定义
    'persona':字符串字段(),#可选人格字符串
    'toolFilter':字典字段(字典结构={#工具过滤模式
        'allow':列表字段(字符串字段(),默认值=None),#省略allow时不物化空数组
        'deny':列表字段(字符串字段(),默认值=None),#省略deny时不物化空数组
    },默认值=None),#省略整个过滤
    'maxDepth':复合类型字段(自然数字段(最大=配置入口上限),常量字段('provider-managed')),#无默认；省略读 Host 设置
}#配置模式结束

__all__=['名称','依赖','配置','应用']#仅中文公开名

def 提供方措辞(继承会话):
    '由提供方的会话历史描述符得到面向模型的措辞'
    if 继承会话:#分叉/继承会话
        return {#继承会话措辞
            'description':(#工具描述
                'Delegate a task to a subagent that inherits this conversation: a child agent seeded with all '
                +'completed turns so far (it does not see the current in-flight turn). Use this when the subtask '
                +"builds on this conversation's context — a follow-up analysis, "
                +'a review, a continuation — without consuming this conversation\'s context for the work itself. '
                +'You receive its result, not its intermediate steps.'
            ),#描述结束
            'promptDescription':(#prompt参数说明
                "The task for the subagent. It already sees this conversation's completed turns, so build on them "
                +'freely and state only what is new.'
            ),#说明结束
        }#继承分支结束
    return {#全新会话措辞
        'description':(#工具描述
            'Delegate a self-contained task to a subagent (a separate agent that works in its own context) '
            +'to offload focused, independent work — research, a scoped '
            +'implementation, an analysis — so it does not consume this conversation\'s context. The subagent '
            +'returns its result, not its intermediate steps.'
        ),#描述结束
        'promptDescription':(#prompt参数说明
            'The complete, self-contained task for the subagent. It does not share this '
            +"conversation's context, so include everything it needs."
        ),#说明结束
    }#全新分支结束

def 应用(上下文,配置值,会话=None):
    '安装委托工具。每次委托都启动一次受管理激活并立刻返回子 id'
    _=会话#直接装配签名保留；模型选择模块不在本次同步范围
    if 配置值.get('modelSelectionSettings') is True:#打开了模型选择
        raise 子智能体错误(
            'tool-subagent: `modelSelectionSettings` requires '
            +'@deepseek-ai/dsh-tool-subagent/model-selection-settings in the Host scope',
            'MODEL_SELECTION_UNAVAILABLE',
        )#本树没有该宿主模块，大声失败
    _安装委托(上下文,配置值)#关闭模型选择的路径

def _安装委托(上下文,配置值):
    '登记面向模型的委托工具与多工具指引'
    最大深度=配置值['maxDepth'] if 'maxDepth' in 配置值 else None#读深度配置
    if 最大深度!='provider-managed':#数字上限当场校验
        断言子智能体最大深度(最大深度)#校验形态
    工具过滤=配置值['toolFilter'] if 'toolFilter' in 配置值 else None#读过滤
    if 工具过滤 is not None and ('allow' not in 工具过滤 or 工具过滤['allow'] is None) and ('deny' not in 工具过滤 or 工具过滤['deny'] is None):#空过滤
        raise 子智能体错误('tool-subagent: `toolFilter` is configured but names neither `allow` nor `deny` — remove the key or fill the filter','EMPTY_TOOL_FILTER')#空过滤失败
    工具名=配置值['toolName'] if 'toolName' in 配置值 and 配置值['toolName'] is not None else 'subagent'#工具名
    提供方名=配置值['provider']#提供方名
    拆除工具=[None]#已登记工具的拆除
    def 挂载(提供方):
        '提供方出现时登记面向模型的委托工具。提供方为对象'
        能力=提供方.能力 if 提供方.能力 is not None else {}#提供方能力
        解析深度=上下文.subagents.解析最大深度(配置值['maxDepth'] if 'maxDepth' in 配置值 else None)#按设置解析
        if 解析深度 is not None and ('depthLimit' not in 能力 or not 能力['depthLimit']):#解析后需强制但无能力
            raise 子智能体错误(#挂载失败
                'tool-subagent: provider "'+提供方.名称+'" cannot enforce maxDepth (no depthLimit capability) — '
                +"set maxDepth: 'provider-managed' to leave the recursion budget to the provider",#文案
                'UNSUPPORTED_CAPABILITY',
            )#结束
        if 'agentOptions' in 配置值 and 配置值['agentOptions'] is not None and not 能力.get('agentOptions'):#配置了选项但提供方不支持
            raise 子智能体错误(
                'tool-subagent: provider "'+提供方.名称+'" does not support child agentOptions',
                'UNSUPPORTED_CAPABILITY',
            )#挂载失败
        措辞=提供方措辞(bool(提供方.继承父上下文))#按是否继承会话选措辞
        可续跑=callable(getattr(提供方,'准备可续跑',None))#本地后端才能收后续
        if 可续跑:#可续跑后缀
            描述后缀=' This tool starts an independently managed subagent and immediately returns its id. The runtime notifies you when it finishes. The child reports results with `send_message`; use `send_message` to steer it while running or continue its conversation after it finishes.'
        else:#外部后端
            描述后缀=' This tool starts an independently managed subagent and immediately returns its id. The runtime notifies you when it finishes. The completion notice includes its final answer. This backend does not accept follow-up messages.'
        参数表={#参数模式
            'cwd':{#初始目录
                'type':'string',#字符串
                'description':'Initial child working directory. Relative paths use your current directory; omitted inherits it. Later directory changes in either agent are independent.',
            },#cwd结束
            'description':{#短描述
                'type':'string',#字符串
                'required':True,#必填
                'description':'A short (3-5 word) description of the delegated task, for display.',#参数说明
            },#description结束
            'prompt':{#任务提示
                'type':'string',#字符串
                'required':True,#必填
                'description':措辞['promptDescription'],#随提供方变化的说明
            },#prompt结束
        }#参数骨架
        def 渲染(_参数,值):
            '渲染已启动的子 id'
            return [{'type':'text','text':'started subagent '+str(值['subagentId'])}]#单个文本块
        def 可并行():
            '子体从不改父会话'
            return True#可并行
        def 执行(参数,执行元数据):
            '启动一次受管理激活并返回子 id'
            if 'agent' not in 执行元数据 or 执行元数据['agent'] is None:#没有调用方
                raise 子智能体错误('subagent tool requires a calling agent (exec.agent was undefined)','NO_AGENT')#缺父失败
            信号=执行元数据['signal'] if 'signal' in 执行元数据 else None#调用方取消
            if 信号 is not None and hasattr(信号,'throwIfAborted'):#发布前再查一次
                信号.throwIfAborted()#已取消则抛
            父=执行元数据['agent']#调用方智能体
            解析深度=上下文.subagents.解析最大深度(配置值['maxDepth'] if 'maxDepth' in 配置值 else None)#按设置解析
            请求={'prompt':[{'type':'text','text':参数['prompt']}],'parent':父}#任务
            if 'cwd' in 参数 and 参数['cwd'] is not None:#显式目录
                请求['cwd']=参数['cwd']#写入
            if 解析深度 is not None:#有数字上限才写入
                请求['maxDepth']=解析深度#写入
            if 'agentOptions' in 配置值 and 配置值['agentOptions'] is not None:#有选项才展开
                请求['agentOptions']=配置值['agentOptions']#写入
            if 'persona' in 配置值 and 配置值['persona'] is not None:#有人格才展开
                请求['persona']=配置值['persona']#写入
            if 工具过滤 is not None:#有过滤才展开
                请求['toolFilter']=工具过滤#写入
            规格={'provider':提供方名,'label':参数['description'],'request':请求,'delivery':'parent'}#激活规格
            if 信号 is not None:#有信号
                规格['signal']=信号#写入
            结果=期约()#工具结果
            def 已启动(激活):
                '返回激活身份'
                结果.解决({'kind':'activation','subagentId':激活['childId']})#子 id
            上下文.subagents.启动激活(规格).然后(已启动,结果.拒绝)#启动
            return 结果#期约
        定义=定义工具({#面向模型的委托工具
            'name':工具名,#工具名
            'description':措辞['description']+描述后缀,#基础描述加上运行时通知
            'parameters':参数表,#参数模式
            'output':{#返回值
                'schema':{#激活身份
                    'type':'object',#对象
                    'additionalProperties':False,#禁止多余键
                    'properties':{#字段
                        'kind':{'type':'string','required':True,'const':'activation'},#种类
                        'subagentId':{'type':'string','required':True},#子 id
                    },#properties结束
                },#schema结束
                'render':渲染,#渲染给模型的文本
            },#output结束
            'isConcurrencySafe':可并行,#可并行
            'execute':执行,#执行委托
        })#定义结束
        登记拆除=上下文.tools.登记(定义)#登记
        委托工具集合.add(定义)#记入可见集合
        def 拆除本工具():
            '卸工具并移出可见集合'
            委托工具集合.discard(定义)#移出
            登记拆除()#卸登记
        拆除工具[0]=拆除本工具#记下拆除
    def 提供方出现(提供方):
        '本提供方且尚未挂载则挂载。提供方为对象'
        if 提供方.名称==提供方名 and 拆除工具[0] is None:#本提供方且尚未挂载
            挂载(提供方)#挂载
    def 提供方消失(名):
        '不是本提供方或未挂载则忽略'
        if 名!=提供方名 or 拆除工具[0] is None:#不是本提供方或未挂载
            return#忽略
        拆除工具[0]()#拆除工具
        拆除工具[0]=None#清空拆除器
    上下文.监听('subagent/provider-added',提供方出现)#provider-added结束
    上下文.监听('subagent/provider-removed',提供方消失)#provider-removed结束
    现存=上下文.subagents.取提供方(提供方名)#当前是否已有该提供方
    if 现存 is not None:#已经在
        挂载(现存)#立刻挂载
    else:#还没有
        上下文.日志.信息('subagent provider "'+提供方名+'" not registered yet; the "'+工具名+'" tool will register when it appears')#等待提供方
    def 段落文本(上下文元):
        '只有本工具是当前作用域里排序后的第一个可见委托工具时才写指引'
        if 拆除工具[0] is None:#工具未挂
            return ''#空
        作用域=上下文元['scope'] if 'scope' in 上下文元 else None#作用域
        可见=[]#看得到的工具名
        for 工具 in 委托工具集合:#逐个已登记定义
            if 上下文.tools.获取(工具['name'],作用域) is 工具:#同一份定义
                可见.append(工具['name'])#收下
        可见.sort()#稳定顺序
        if len(可见)==0 or 可见[0]!=工具名:#不是第一份
            return ''#别的实例写
        名字=' or '.join('`'+名+'`' for 名 in 可见)#模型可见名字
        return 'Start independent delegations with '+名字+' together in one assistant message and continue useful work while they run.'
    上下文.systemPrompt.段落({#登记委托用法指引
        'name':'tool:'+工具名,#按工具名分段
        'order':上下文.systemPrompt.获取段落顺序('TOOL_SUBAGENT'),#段落顺序
        'text':段落文本,#动态文本
    })#段落结束

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=应用#框架槽
