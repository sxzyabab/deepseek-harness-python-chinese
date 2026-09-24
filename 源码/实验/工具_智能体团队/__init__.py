import json#紧凑JSON渲染
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 字符串字段#配置字段
from ...内核.工具 import 定义工具#定义面向模型的工具

__all__=[
    '名称','依赖','配置','应用','团队任务标识','工具团队错误',
]

名称='tool-agent-team'
依赖=['agents','agentTeams','tools','systemPrompt']
配置={#工具路由配置
    'freshProvider':字符串字段(默认值='spawn'),#新建 teammate 的可续跑 subagent provider
    'forkProvider':字符串字段(默认值='fork'),#fork teammate 的可续跑 subagent provider
}#配置模式结束

策略=(#Lead 与 teammate 共用的面向模型协作策略（字面量不译）
    'Agent Teams is available in this session, but create teammates only when the user explicitly asks to use Agent Teams or teammates.\n\n'
    +'The Team Lead and all teammates share the same working directory and filesystem. Edits are immediately visible to every member. Split write work into disjoint scopes, record expected write scopes on shared tasks, and use task dependencies when work must be ordered. Write-scope overlap is advisory, not a lock.\n\n'
    +'Prefer read/edit/write for file changes. If a file operation returns FS_STALE_VERSION, read the current file, rebase your intended change onto the new content, and retry. Bash, formatters, code generators, and scripts are not fully protected by the filesystem version guard; coordinate them explicitly and have the Lead review the final diff and run tests.\n\n'
    +'Use the target returned by spawn_teammate or list_agents for send_message and interrupt_agent, or as owner when assigning or filtering shared tasks. send_message steers a running target at its nearest step boundary and starts or resumes an inactive target. inactive means no turn is executing; it does not describe task completion, success, failure, or waiting for other agents. provisioning means member creation is in progress; failed means member creation failed. A delivered peer item starts with its stable message id and sender name. A successful send is already durable even when its result says queued; do not resend it. Shared-task workflow is list, get, claim with the current revision, perform the work, then complete. Task readiness never starts an owner. Before wait_agent, use list_agents and make sure another required member is running or provisioning; use send_message first when the required member is inactive. wait_agent observes only changes after that call starts, never wakes a member, and returns noProgress immediately when no other member can produce a change. Re-list after wakeup or timeout. The Lead must wait for required teammates before giving the final answer.'
)#策略结束
活跃等待状态=frozenset(['running','provisioning'])#可等待的活跃成员状态
无活跃同伴文案=(#无活跃同伴时 wait_agent 的提示（字面量不译）
    'No other Team member is running or provisioning. wait_agent cannot make progress or wake inactive teammates. '
    +'Re-list with list_agents and team_task_list, then use send_message to wake each required inactive teammate before waiting again.'
)#无活跃同伴文案结束

成员视图模式={#一行 roster；Lead 伪行省略 teammate 专属供给字段
    'type':'object',#对象类型
    'additionalProperties':False,#禁止额外字段
    'properties':{#字段表
        'target':{'type':'string','required':True},#面向模型的目标名
        'role':{'type':'string','required':True,'enum':['lead','teammate']},#角色枚举
        'status':{'type':'string','required':True,'enum':['running','inactive','provisioning','failed']},#状态枚举
        'description':{'type':'string'},#职责描述
        'provider':{'type':'string'},#供应器名
        'context':{'type':'string','enum':['fresh','fork']},#上下文模式
        'model':{'type':'string'},#模型名
        'diagnostics':{'type':'array','required':True,'items':{'type':'string'}},#诊断列表
    },#properties结束
}#成员视图模式结束
任务视图模式={#一条共享任务，匹配公开 TeamTaskView
    'type':'object',#对象类型
    'additionalProperties':False,#禁止额外字段
    'properties':{#字段表
        'id':{'type':'string','required':True},#任务id
        'revision':{'type':'integer','required':True},#修订号
        'subject':{'type':'string','required':True},#标题
        'description':{'type':'string','required':True},#详情
        'status':{'type':'string','required':True,'enum':['pending','in_progress','completed','deleted']},#状态枚举
        'ownerName':{'type':'string'},#所有者名
        'blockedBy':{'type':'array','required':True,'items':{'type':'string'}},#阻塞依赖
        'writeScopes':{'type':'array','required':True,'items':{'type':'string'}},#写范围
        'ready':{'type':'boolean','required':True},#是否就绪
        'writeScopeWarnings':{'type':'array','required':True,'items':{'type':'string'}},#写范围警告
    },#properties结束
}#任务视图模式结束
创建成员值模式={#spawn 结果 schema
    'type':'object',#对象类型
    'additionalProperties':False,#禁止额外字段
    'properties':{#字段表
        'member':{**成员视图模式,'required':True},#新建成员视图
    },#properties结束
}#创建成员值模式结束
成员列表值模式={'type':'array','items':成员视图模式}#成员列表结果
发消息值模式={#发消息结果 schema
    'type':'object',#对象类型
    'additionalProperties':False,#禁止额外字段
    'properties':{#字段表
        'messageId':{'type':'string','required':True},#消息id
        'status':{'type':'string','required':True,'enum':['accepted','queued']},#投递状态
    },#properties结束
}#发消息值模式结束
等待值模式={#等待结果 schema；noProgress 仅出现在跳过等待的模型侧捷径上
    'type':'object',#对象类型
    'additionalProperties':False,#禁止额外字段
    'properties':{#字段表
        'timedOut':{'type':'boolean','required':True},#是否超时
        'noProgress':{#无进展捷径
            'type':'object',#对象类型
            'additionalProperties':False,#禁止额外字段
            'properties':{#字段表
                'reason':{'type':'string','required':True,'const':'no-active-peer'},#无进展原因
                'message':{'type':'string','required':True},#提示文案
            },#properties结束
        },#noProgress结束
    },#properties结束
}#等待值模式结束
中断值模式={#中断结果 schema
    'type':'object',#对象类型
    'additionalProperties':False,#禁止额外字段
    'properties':{#字段表
        'previousStatus':{'type':'string','required':True,'enum':['running','inactive']},#中断前状态
    },#properties结束
}#中断值模式结束
任务列表值模式={#任务列表结果 schema
    'type':'object',#对象类型
    'additionalProperties':False,#禁止额外字段
    'properties':{#字段表
        'tasks':{'type':'array','required':True,'items':任务视图模式},#任务页
        'nextCursor':{'type':'integer'},#下一页游标
    },#properties结束
}#任务列表值模式结束

def 团队任务标识(标识):#字符串→TeamTaskId 标识构造
    """同串标识构造。"""
    return 标识#同串标识构造

class 工具团队错误(Exception):#本包异常基类
    """面向模型的 Agent Teams 工具包错误。"""
    def __init__(自身,消息):#构造
        """记下英文诊断。"""
        super().__init__(消息)#基类
        自身.消息=消息#诊断

def 模型成员(成员):
    """把成员名暴露为面向模型的 target。"""
    细节=dict(成员)#拷贝
    名称=细节.pop('name')#成员名
    细节.pop('id',None)#内部 id 不出站
    return {'target':名称,**细节}#target 加其余字段

def 紧凑JSON输出(模式):#声明规范输出并以紧凑 JSON 渲染
    """声明一份规范输出 schema，并以紧凑面向模型的 JSON 渲染。"""
    def 渲染(_参数,值):#序列化为 JSON 文本块
        """把结构化结果渲染成紧凑 JSON 文本块。"""
        return [{'type':'text','text':json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)}]#紧凑 JSON
    return {'schema':模式,'render':渲染}#output 声明

def 调用方智能体(智能体,工具名):#取调用方 Agent
    """找回 Agent 作用域工具发现所保证的精确调用方。"""
    if 智能体 is None:#缺调用方
        raise 工具团队错误(工具名+' requires a calling Agent')#缺调用方则报错
    return 智能体#返回调用方

def 安装(智能体,上下文,已解析配置):#在一个精确 Agent 作用域中注册完整 Team 工具集
    """在一个精确 Agent 作用域中注册完整 Team 工具集，返回拆除函数。"""
    作用域=智能体.ctx#成员作用域
    拆除器列表=[]#拆除回调
    def 登记(拆除器):#登记拆除
        """把拆除器追加到本作用域拆除表。"""
        拆除器列表.append(拆除器)#记下
    try:#注册工具与段落
        登记(作用域.systemPrompt.section({#注册策略系统提示段落
            'name':'team:policy',#段落名
            'order':作用域.systemPrompt.getSectionOrder('TEAM_POLICY'),#段落顺序
            'text':策略,#固定文案
        }))#策略段落

        def 执行创建队友(参数,执行):#执行 spawn_teammate
            """创建具名耐久 teammate；仅 Lead 可调（由服务侧校验）。"""
            调用方=调用方智能体(执行['agent'] if 'agent' in 执行 else None,'spawn_teammate')#调用方
            上下文模式=参数['context'] if 'context' in 参数 else None#上下文模式
            if 上下文模式 is None:#缺省 fresh
                上下文模式='fresh'#默认
            提供方=已解析配置['forkProvider'] if 上下文模式=='fork' else 已解析配置['freshProvider']#选 provider
            提醒=(#队友系统提醒
                '<system-reminder>\n'
                +'You are teammate "'+参数['name'].strip()+'".\n'
                +'Your Team Lead is named "lead".\n'
                +'Use list_agents({}) to find your teammates and their names.\n'
                +'To message your Team Lead, use send_message({ target: "lead", message: "..." }).\n'
                +'To message another teammate, use send_message({ target: "<teammate name>", message: "..." }).\n'
                +'</system-reminder>\n\n'
            )#提醒结束
            结果=上下文.agentTeams.spawnTeammate(调用方,{#调用团队服务创建
                'name':参数['name'],#成员名
                'description':参数['description'],#职责描述
                'prompt':[{'type':'text','text':提醒},{'type':'text','text':参数['prompt']}],#提醒加初始任务
                'context':上下文模式,#上下文模式
                'provider':提供方,#选中的 provider
                'signal':执行['signal'] if 'signal' in 执行 else None,#取消信号
            })#spawnTeammate结束
            return {'member':模型成员(结果['member'])}#面向模型的成员行
        登记(作用域.tools.register(定义工具({#注册 spawn_teammate
            'name':'spawn_teammate',#工具名
            'description':'Create one named, durable teammate. Only the Team Lead may call this tool.',#工具说明
            'parameters':{#参数 schema
                'name':{'type':'string','required':True,'description':'Unique lower-kebab-case teammate name.'},#成员名
                'description':{'type':'string','required':True,'description':'Short description of the delegated responsibility.'},#职责描述
                'prompt':{'type':'string','required':True,'description':'Complete initial task for the teammate.'},#初始任务
                'context':{#上下文模式
                    'type':'string',#字符串
                    'enum':['fresh','fork'],#fresh 或 fork
                    'description':'fresh starts without Lead history; fork inherits completed Lead turns. Defaults to fresh.',#模式说明
                },#context结束
            },#parameters结束
            'output':紧凑JSON输出(创建成员值模式),#输出声明
            'execute':执行创建队友,#执行创建队友
        })))#spawn_teammate

        def 执行发消息(参数,执行):#执行 send_message
            """向另一 Team 成员投递一条耐久消息。"""
            return 上下文.agentTeams.sendMessage(调用方智能体(执行['agent'] if 'agent' in 执行 else None,'send_message'),{#投递消息，已同步
                'target':参数['target'],#目标成员
                'content':[{'type':'text','text':参数['message']}],#消息内容块
                'signal':执行['signal'] if 'signal' in 执行 else None,#取消信号
            })#sendMessage结束
        登记(作用域.tools.register(定义工具({#注册 send_message
            'name':'send_message',#工具名
            'description':'Send one durable message to another Team member. A running target receives it at the nearest step boundary; an inactive target starts or resumes a turn.',#工具说明
            'parameters':{#参数 schema
                'target':{'type':'string','required':True,'description':'Member target returned by spawn_teammate or list_agents, including lead.'},#目标名
                'message':{'type':'string','required':True,'description':'Self-contained message for the target.'},#消息正文
            },#parameters结束
            'output':紧凑JSON输出(发消息值模式),#输出声明
            'execute':执行发消息,#执行发消息
        })))#send_message

        def 执行列成员(_参数,执行):#执行 list_agents
            """列出 Lead 与每个耐久 teammate 的当前运行时状态。"""
            return [模型成员(成员) for 成员 in 上下文.agentTeams.listMembers(调用方智能体(执行['agent'] if 'agent' in 执行 else None,'list_agents'))]#面向模型的成员行
        登记(作用域.tools.register(定义工具({#注册 list_agents
            'name':'list_agents',#工具名
            'description':'List the Lead and every durable teammate with an addressable target and current availability. inactive means no turn is executing, not a task result. provisioning and failed describe member creation.',#工具说明
            'parameters':{},#无参数
            'output':紧凑JSON输出(成员列表值模式),#输出声明
            'execute':执行列成员,#执行列成员
        })))#list_agents

        def 执行等待(参数,执行):#执行 wait_agent
            """等待本调用开始之后的下一次 teammate 状态、邮箱或共享任务变更。"""
            调用方=调用方智能体(执行['agent'] if 'agent' in 执行 else None,'wait_agent')#调用方
            超时毫秒=参数['timeout_ms'] if 'timeout_ms' in 参数 else None#等待毫秒
            if 超时毫秒 is None:#缺省 30s
                超时毫秒=30_000#默认
            信号=执行['signal'] if 'signal' in 执行 else None#取消信号
            if isinstance(超时毫秒,bool) or not isinstance(超时毫秒,int) or 超时毫秒<10_000 or 超时毫秒>3_600_000:#超时非法则交给服务
                return 上下文.agentTeams.waitForChange(调用方,超时毫秒,信号)#权威校验路径
            有活跃同伴=False#是否有其他活跃成员
            for 成员 in 上下文.agentTeams.listMembers(调用方):#扫描其他活跃成员
                if 成员['id']!=调用方.id and 成员['status'] in 活跃等待状态:#命中活跃同伴
                    有活跃同伴=True#有同伴
                    break#结束扫描
            if 有活跃同伴 is not True:#无活跃同伴则捷径返回
                return {#立即无进展载荷
                    'timedOut':False,#未超时
                    'noProgress':{#无进展说明
                        'reason':'no-active-peer',#固定原因码
                        'message':无活跃同伴文案,#提示文案
                    },#noProgress结束
                }#立即无进展
            return 上下文.agentTeams.waitForChange(调用方,超时毫秒,信号)#正常等待变更
        登记(作用域.tools.register(定义工具({#注册 wait_agent
            'name':'wait_agent',#工具名
            'description':'Wait for the next teammate status, mailbox, or shared-task change after this call starts. This never wakes inactive members and returns noProgress immediately when no other member is running or provisioning. Re-list after wakeup or timeout instead of polling.',#工具说明
            'parameters':{#参数 schema
                'timeout_ms':{#等待时长
                    'type':'integer',#整数毫秒
                    'description':'Wait duration in milliseconds, from 10000 through 3600000. Defaults to 30000.',#时长说明
                },#timeout_ms结束
            },#parameters结束
            'output':紧凑JSON输出(等待值模式),#输出声明
            'execute':执行等待,#执行等待
        })))#wait_agent

        def 执行中断(参数,执行):#执行 interrupt_agent
            """中断一名 teammate 的当前轮次并保留其待处理收件箱；仅 Lead。"""
            return 上下文.agentTeams.interrupt(#中断指定队友，已同步
                调用方智能体(执行['agent'] if 'agent' in 执行 else None,'interrupt_agent'),#调用方
                参数['target'],#目标名
            )#interrupt结束
        登记(作用域.tools.register(定义工具({#注册 interrupt_agent
            'name':'interrupt_agent',#工具名
            'description':"Interrupt one teammate's current turn while preserving its pending inbox. Team Lead only.",#工具说明
            'parameters':{#参数 schema
                'target':{'type':'string','required':True,'description':'Teammate target returned by spawn_teammate or list_agents.'},#目标队友名
            },#parameters结束
            'output':紧凑JSON输出(中断值模式),#输出声明
            'execute':执行中断,#执行中断
        })))#interrupt_agent

        def 执行创建任务(参数,执行):#执行 team_task_create
            """在共享 Team 任务板上创建一条无主 pending 任务。"""
            请求={#创建请求
                'subject':参数['subject'],#标题
                'description':参数['description'],#详情
            }#请求骨架
            if 'blocked_by' in 参数 and 参数['blocked_by'] is not None:#有依赖才展开
                请求['blockedBy']=[团队任务标识(项) for 项 in 参数['blocked_by']]#标识构造依赖
            if 'write_scopes' in 参数 and 参数['write_scopes'] is not None:#有写范围才展开
                请求['writeScopes']=参数['write_scopes']#写范围
            return 上下文.agentTeams.createTask(调用方智能体(执行['agent'] if 'agent' in 执行 else None,'team_task_create'),请求)#创建共享任务
        登记(作用域.tools.register(定义工具({#注册 team_task_create
            'name':'team_task_create',#工具名
            'description':'Create one unowned pending task on the shared Team task board.',#工具说明
            'parameters':{#参数 schema
                'subject':{'type':'string','required':True,'description':'Concise task title.'},#任务标题
                'description':{'type':'string','required':True,'description':'Complete task details and acceptance criteria.'},#任务详情
                'blocked_by':{'type':'array','items':{'type':'string'},'description':'Task ids that must complete first.'},#前置依赖
                'write_scopes':{#建议写范围
                    'type':'array',#字符串数组
                    'items':{'type':'string'},#路径前缀项
                    'description':'Advisory workspace-relative file or directory prefixes this task expects to modify.',#写范围说明
                },#write_scopes结束
            },#parameters结束
            'output':紧凑JSON输出(任务视图模式),#输出声明
            'execute':执行创建任务,#执行创建任务
        })))#team_task_create

        def 执行列任务(参数,执行):#执行 team_task_list
            """列出共享任务，含就绪、所有者、修订、阻塞与写范围警告。"""
            状态=参数['status'] if 'status' in 参数 else None#状态过滤
            所有者过滤=参数['owner'] if 'owner' in 参数 else None#所有者过滤
            就绪过滤=参数['ready'] if 'ready' in 参数 else None#就绪过滤
            已筛=[]#过滤后任务
            for 任务 in 上下文.agentTeams.listTasks(调用方智能体(执行['agent'] if 'agent' in 执行 else None,'team_task_list')):#按条件筛任务
                if 状态 is not None and 任务['status']!=状态:#状态不匹配
                    continue#跳过
                if 所有者过滤 is not None:#有所有者过滤
                    所有者名=任务['ownerName'] if 'ownerName' in 任务 else None#任务所有者
                    if 所有者过滤=='unowned':#无主过滤
                        if 所有者名 is not None:#有主则跳过
                            continue#跳过
                    elif 所有者名!=所有者过滤:#名字不匹配
                        continue#跳过
                if 就绪过滤 is not None and 任务['ready']!=就绪过滤:#就绪不匹配
                    continue#跳过
                已筛.append(任务)#收下
            游标=参数['cursor'] if 'cursor' in 参数 else None#偏移
            if 游标 is None:#缺省 0
                游标=0#默认
            页大小=参数['limit'] if 'limit' in 参数 else None#页大小
            if 页大小 is None:#缺省 50
                页大小=50#默认
            if isinstance(游标,bool) or not isinstance(游标,int) or 游标<0:#校验游标
                raise 工具团队错误('cursor must be a non-negative safe integer')#游标非法
            if isinstance(页大小,bool) or not isinstance(页大小,int) or 页大小<1 or 页大小>100:#校验页大小
                raise 工具团队错误('limit must be an integer from 1 through 100')#页大小非法
            结果={'tasks':已筛[游标:游标+页大小]}#当前页任务
            if 游标+页大小<len(已筛):#还有下一页
                结果['nextCursor']=游标+页大小#下一游标
            return 结果#分页结果
        登记(作用域.tools.register(定义工具({#注册 team_task_list
            'name':'team_task_list',#工具名
            'description':'List shared tasks, including readiness, owner, revision, blockers, and write-scope warnings.',#工具说明
            'parameters':{#参数 schema
                'status':{#状态过滤
                    'type':'string',#字符串
                    'enum':['pending','in_progress','completed'],#可选状态
                    'description':'Optional exact status filter.',#状态说明
                },#status结束
                'owner':{'type':'string','description':'Optional member target from spawn_teammate or list_agents, matching ownerName; use unowned for tasks without an owner.'},#所有者过滤
                'ready':{'type':'boolean','description':'Optional readiness filter.'},#就绪过滤
                'cursor':{'type':'integer','description':'Zero-based result offset. Defaults to 0.'},#偏移
                'limit':{'type':'integer','description':'Number of rows, 1 through 100. Defaults to 50.'},#页大小
            },#parameters结束
            'output':紧凑JSON输出(任务列表值模式),#输出声明
            'execute':执行列任务,#执行列任务
        })))#team_task_list

        def 执行取任务(参数,执行):#执行 team_task_get
            """读取一条共享任务的完整最新值。"""
            return 上下文.agentTeams.getTask(#取最新任务视图，已同步
                调用方智能体(执行['agent'] if 'agent' in 执行 else None,'team_task_get'),#调用方
                团队任务标识(参数['task_id']),#规范化任务id
            )#getTask结束
        登记(作用域.tools.register(定义工具({#注册 team_task_get
            'name':'team_task_get',#工具名
            'description':'Read the complete latest value of one shared task before changing or executing it.',#工具说明
            'parameters':{#参数 schema
                'task_id':{'type':'string','required':True,'description':'Shared task id.'},#任务id
            },#parameters结束
            'output':紧凑JSON输出(任务视图模式),#输出声明
            'execute':执行取任务,#执行取任务
        })))#team_task_get

        def 执行更新任务(参数,执行):#执行 team_task_update
            """用 team_task_get/list 拿到的最新修订做共享任务的比较交换动作。"""
            请求={#CAS 更新请求
                'taskId':团队任务标识(参数['task_id']),#任务id
                'expectedRevision':参数['expected_revision'],#期望修订号
                'action':参数['action'],#动作
            }#请求骨架
            if 'subject' in 参数 and 参数['subject'] is not None:#有标题才展开
                请求['subject']=参数['subject']#替换标题
            if 'description' in 参数 and 参数['description'] is not None:#有详情才展开
                请求['description']=参数['description']#替换详情
            if 'blocked_by' in 参数 and 参数['blocked_by'] is not None:#有依赖才展开
                请求['blockedBy']=[团队任务标识(项) for 项 in 参数['blocked_by']]#标识构造依赖
            if 'write_scopes' in 参数 and 参数['write_scopes'] is not None:#有写范围才展开
                请求['writeScopes']=参数['write_scopes']#写范围
            if 'owner' in 参数 and 参数['owner'] is not None:#有所有者才展开
                请求['owner']=参数['owner']#再指派
            return 上下文.agentTeams.updateTask(调用方智能体(执行['agent'] if 'agent' in 执行 else None,'team_task_update'),请求)#CAS更新
        登记(作用域.tools.register(定义工具({#注册 team_task_update
            'name':'team_task_update',#工具名
            'description':'Compare-and-set a shared task action using the latest revision from team_task_get or team_task_list.',#工具说明
            'parameters':{#参数 schema
                'task_id':{'type':'string','required':True,'description':'Shared task id.'},#任务id
                'expected_revision':{'type':'integer','required':True,'description':'Current task revision used as the CAS precondition.'},#期望修订号
                'action':{#任务动作
                    'type':'string',#字符串
                    'required':True,#必填
                    'enum':['claim','release','edit','set_dependencies','complete','reopen','reassign','delete'],#动作枚举
                    'description':'Task transition to apply.',#动作说明
                },#action结束
                'subject':{'type':'string','description':'Replacement title for edit.'},#编辑标题
                'description':{'type':'string','description':'Replacement details for edit.'},#编辑详情
                'blocked_by':{'type':'array','items':{'type':'string'},'description':'Complete blocker list for set_dependencies.'},#依赖列表
                'write_scopes':{'type':'array','items':{'type':'string'},'description':'Replacement advisory write scopes for edit.'},#写范围
                'owner':{'type':'string','description':'Member target from spawn_teammate or list_agents for Lead-only reassign; omit to unassign.'},#再指派所有者
            },#parameters结束
            'output':紧凑JSON输出(任务视图模式),#输出声明
            'execute':执行更新任务,#执行更新任务
        })))#team_task_update
    except Exception:#插件 install 中途可能抛 ImportError/配置错误，契约未定所以收不窄
        for 拆除 in reversed(拆除器列表):#安装失败则逆序拆除
            拆除()#拆除
        raise#继续抛出
    def 拆除作用域():#正常拆除
        """逆序拆除本作用域已登记的工具与段落。"""
        for 拆除 in reversed(拆除器列表):#逆序拆除
            拆除()#拆除
    return 拆除作用域#返回拆除函数

def 应用(上下文,配置值=None):#在每个已有或随后发布的 Team 成员作用域中安装 Team 工具
    """在每个已有或随后发布的 Team 成员作用域中安装 Team 工具。"""
    if 配置值 is None:#缺省配置
        配置值={}#空映射
    新建提供方=配置值['freshProvider'] if 'freshProvider' in 配置值 else None#新建 provider
    if 新建提供方 is None:#缺省 spawn
        新建提供方='spawn'#默认
    分叉提供方=配置值['forkProvider'] if 'forkProvider' in 配置值 else None#fork provider
    if 分叉提供方 is None:#缺省 fork
        分叉提供方='fork'#默认
    已解析={'freshProvider':新建提供方,'forkProvider':分叉提供方}#补全默认配置
    已安装={}#id(智能体)→拆除，身份表不用对象当键
    def 或许安装(智能体):#尝试为成员安装
        """已安装或非 Team 成员则跳过。"""
        键=id(智能体)#对象身份
        if 键 in 已安装:#已安装
            return#跳过
        if 上下文.agentTeams.tryMembership(智能体) is None:#非成员
            return#跳过
        已安装[键]=安装(智能体,上下文,已解析)#安装并记录
    for 智能体 in 上下文.agents.list():#现有 Agent
        或许安装(智能体)#尝试安装
    def 智能体已创建(事件):#新建时安装
        """agent/created 时尝试安装。"""
        或许安装(事件['agent'])#安装
    def 智能体已销毁(事件):#Agent 销毁时拆除
        """agent/disposed 时拆除作用域工具。"""
        智能体=事件['agent']#取出 Agent
        键=id(智能体)#对象身份
        if 键 not in 已安装:#无拆除器
            return#跳过
        已安装[键]()#拆除
        del 已安装[键]#从表移除
    上下文.监听('agent/created',智能体已创建)#新建时安装
    上下文.监听('agent/disposed',智能体已销毁)#销毁时拆除
    def 作用域工具副作用():#插件卸载副作用
        """插件卸载时拆除全部已安装作用域工具。"""
        def 拆除全部():#拆除全部
            """拆除全部并清空表。"""
            for 拆除 in list(已安装.values()):#逐个拆除
                拆除()#拆除
            已安装.clear()#清空表
        return 拆除全部#拆除器
    上下文.副作用(作用域工具副作用,'tool-team.scopedTools()')#effect 标签

name=名称
inject=依赖
apply=应用
Config=配置
default=应用
