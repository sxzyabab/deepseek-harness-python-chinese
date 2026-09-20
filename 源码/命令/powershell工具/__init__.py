"""面向模型的 PowerShell 消费方。

用于 Windows 组合，由 PowerShell 执行器支撑外壳能力；工具约定是 PowerShell 方言：原生 C:\\... 路径与 $env:NAME 变量。行为与 bash 工具逐调用镜像。
"""
import json,math,os#JSON片段、有限数与路径
from ...依赖.schemastery import 布尔字段#配置字段
from ...内核.工具 import 定义工具,工具体后中止#定义工具与体后中止码
from ...模型后端.llm import 装备错误#Harness错误
from ..命令 import 解析退出状态#共用退出状态解析
from ...沙盒.沙盒 import (
    升级目标,#可广告的升级目标
    批准升级,#批准升级
    校验升级参数,#校验升级参数配对
)#沙箱升级面
from .后台 import 做成任务完成#后台done映射为任务结果
from .渲染 import 渲染Pwsh结果,渲染Pwsh进程读取#pwsh渲染

__all__=['名称','依赖','配置','应用']#仅中文公开名

名称='tool-pwsh'#插件名（字面量不译）
依赖=['tools','shell','systemPrompt','shellEnv']#依赖工具、shell、提示词与环境
配置={#pwsh工具配置模式
    'enableRunInBackground':布尔字段(默认值=True),#默认启用后台
}#配置模式结束
后台输出字段={#后台输出字段
    'kind':{'type':'string','required':True,'const':'background'},#种类为background
    'jobId':{'type':'string','required':True},#任务id
}#后台输出字段结束

class pwsh工具错误(Exception):#本包校验与组合失败
    """pwsh 工具入参或组合非法。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

def 已中止(信号):#读中止事实
    """信号按 Event 定死。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号.is_set()#事件已置位

def 校验Pwsh参数(参数):#校验参数值
    """已解析工具参数；校验 ParameterSchemaSpec 没有的值约束。"""
    if len(参数['command'].strip())==0:#命令为空
        raise pwsh工具错误('invalid command: expected a non-empty string')#拒绝空命令
    if len(参数['description'].strip())==0:#描述为空
        raise pwsh工具错误('invalid description: expected a non-empty string')#拒绝空描述
    超时=参数['timeoutMs'] if 'timeoutMs' in 参数 else None#可选超时
    if 超时 is not None and (isinstance(超时,bool) or not isinstance(超时,(int,float)) or not math.isfinite(超时) or 超时<=0):#超时非法
        raise pwsh工具错误('invalid timeoutMs: expected a positive number, got '+json.dumps(超时,ensure_ascii=False,separators=(',',':'),allow_nan=False))#拒绝非正超时
    校验升级参数(参数['sandbox_permissions'] if 'sandbox_permissions' in 参数 else None,参数['justification'] if 'justification' in 参数 else None)#校验升级配对

def pwsh描述(启用后台,升级模式):#拼工具描述
    """按组合拼面向模型的 pwsh 工具描述；升级目标非空时追加 Windows 沙箱语言模式与同轮升级指引。"""
    if 启用后台 is True:#启用后台
        后台段='Set `run_in_background: true` for long-running commands: the call returns a job id immediately; read its output with `job_output` and stop it with `job_kill`.'#后台说明
    else:#无后台
        后台段='Background execution is not available; long-running commands must finish within the timeout.'#无后台说明
    基础=('Execute a PowerShell command (`pwsh -Command`) and return its stdout/stderr. '#基础描述
        +'Each call runs in a fresh pwsh process: no state (cwd, variables, functions) persists between calls — '#新鲜进程
        +'pass `workdir` instead of using `cd`. Paths use native Windows form (`C:\\...`); read environment '#Windows路径
        +'variables with `$env:NAME`. Non-zero exits are reported as `[exit code: N]`. '#环境变量与退出码
        +'Current harness environment facts are exposed through managed `$env:DSH_*` variables; inspect them when needed. '#托管环境
        +'Commands may run under a file sandbox; a blocked file operation is reported as `[sandbox: file access denied under <mode> mode]` — a policy denial, not a bug in the command; do not retry another way. '#沙箱拒绝
        +'Long output is truncated to its tail; the full output is saved to a file whose path is reported when available. '#截断
        +'On Windows a force-killed command settles as `[exit code: 1]` without a signal marker — treat it as an interruption, not a command failure. '#Windows强杀
        +后台段)#加上后台段
    if len(升级模式)==0:#无升级
        return 基础#到此
    return (基础#续拼升级说明
        +' Under the Windows sandbox, read-only pwsh runs in PowerShell ConstrainedLanguage mode, while '#Windows沙箱语言模式
        +'workspace-write stays in FullLanguage unless host policy says otherwise. In read-only, prefer cmdlets and core types (`[string]`, `[datetime]`, `[regex]`, `[guid]`); '#只读偏好
        +'.NET static calls (`[System.IO.*]::`, `[math]::`), `Add-Type`, COM objects, and reflection fail '#受限失败
        +'with "only core types" errors. `-f` formatting, property access, and core cmdlets work. '#仍可用的
        +"In both confined modes, programs cannot open named pipes, so a command that captures another "#命名管道
        +"program's output through piped stdio (Node.js `child_process.spawn`/`exec` with the default "#管道stdio
        +"`stdio: 'pipe'`) fails with EPERM, while `stdio: 'inherit'` and `stdio: 'ignore'` spawns "#EPERM
        +"work and PowerShell's own pipelines are unaffected. That EPERM is the documented boundary: "#边界
        +'do not retry the command another way — escalate the exact command once or restructure it to '#不要换路
        +'avoid capturing output. '#避免捕获
        +'Attempting a command the sandbox may deny is safe and expected: run it and read the '#读标记
        +'marker rather than assuming the denial. When a command is denied and a wider mode would let it '#同轮升级
        +'succeed, escalate immediately in the same turn — the one sanctioned exception to a denial: retry '#精确重试
        +'the exact same command once with `sandbox_permissions` (the narrowest wider mode that suffices) '#更宽模式
        +'plus a one-sentence `justification`. Do not detour through chat to ask permission first — the '#不要先聊天
        +'approval prompt raised by that retry is how the user consents. If the session states approval '#审批提示
        +'prompts are disabled, there is no exception: a denial is final — do not set `sandbox_permissions`. '#禁用审批
        +'Never escalate speculatively: ground the request in a real denial — normally the one this command '#禁止投机
        +'just hit; escalating up front is fine only when this session already denied the same access. '#已有拒绝
        +'A rejected escalation is final for that command — stop and explain, never work around '#拒绝升级
        +'it — but it does not forbid attempting or escalating other commands later.')#不影响其他命令

def 解析工作目录(模型工作目录,执行):#解析工作目录
    """先解析显式 workdir，相对路径相对会话工作区；否则用会话头 cwd，并把执行器默认当作回退。"""
    智能体=执行['agent'] if 'agent' in 执行 else None#调用智能体；执行是dict
    会话=智能体.session if 智能体 is not None else None#所属会话
    头=会话.header if 会话 is not None else None#会话头
    会话头工作目录=头['cwd'] if 头 is not None and 'cwd' in 头 else None#会话头cwd
    if 模型工作目录 is None:#未给
        return 会话头工作目录#用会话
    if 会话头工作目录 is not None and (not os.path.isabs(模型工作目录)):#相对路径
        return os.path.normpath(os.path.join(会话头工作目录,模型工作目录))#相对会话解析
    return 模型工作目录#绝对或无会话则原样

def 规范Pwsh结果(结果):#规范化前台结果
    """把执行器 DTO 从只读 Service Definition 类型拆成普通 JSON 数据。"""
    def 一路输出(流):#一路输出
        """投影一路收集输出。"""
        输出={'text':流['text'],'truncated':流['truncated']}#文本与截断
        if 'spillPath' in 流 and 流['spillPath'] is not None:#有溢出路径
            输出['spillPath']=流['spillPath']#带上
        return 输出#一路输出
    规范={#规范结果
        'kind':'foreground',#种类
        'exitCode':结果['exitCode'],#退出码
        'signal':结果['signal'],#信号
        'timedOut':结果['timedOut'],#是否超时
        'aborted':结果['aborted'],#是否中止
        'timeoutMs':结果['timeoutMs'],#超时毫秒
        'stdout':一路输出(结果['stdout']),#标准输出
        'stderr':一路输出(结果['stderr']),#标准错误
    }#规范骨架
    if 'sandbox' in 结果 and 结果['sandbox'] is not None:#有沙箱事实
        沙箱=结果['sandbox']#沙箱事实
        沙箱投影={#沙箱
            'mode':沙箱['mode'],#模式
            'denied':沙箱['denied'],#是否拒绝
        }#沙箱骨架
        if 'enforcement' in 沙箱 and 沙箱['enforcement'] is not None:#有强制程度
            沙箱投影['enforcement']=沙箱['enforcement']#带上
        if 'runnerFailed' in 沙箱 and 沙箱['runnerFailed'] is not None:#有运行器失败旗标
            沙箱投影['runnerFailed']=沙箱['runnerFailed']#带上
        规范['sandbox']=沙箱投影#写入规范
    return 规范#规范前台结果

def 抛中止():#抛出工具调用中止
    """抛出体后中止的 AbortError。"""
    错误=装备错误('tool call aborted',工具体后中止)#中止错误
    错误.name='AbortError'#名字
    raise 错误#抛出

def 应用(上下文,配置值=None):#加载pwsh工具插件
    """注册面向模型的 pwsh 工具、系统提示词段落，以及按组合广告的后台/升级参数面。"""
    if 配置值 is None:#未传配置
        配置值={}#空配置
    启用后台=配置值['enableRunInBackground'] if 'enableRunInBackground' in 配置值 else True#是否启用后台
    默认模式=上下文.shell.沙箱模式#执行器默认沙箱模式
    升级模式=[] if 默认模式 is None else list(升级目标)#有隔离才暴露升级
    沙箱政策服务=None if 默认模式 is None else 上下文.获取服务('sandboxPolicy',False)#政策服务
    if 默认模式 is not None and 沙箱政策服务 is None:#隔离却缺政策
        raise pwsh工具错误('tool-pwsh: the mounted bash executor confines but ctx.sandboxPolicy is missing')#加载时失败
    def 解析沙箱政策(执行):#解析常驻政策
        """挂上隔离执行器时，解析本次调用的完整常驻政策。"""
        if 沙箱政策服务 is None:#无政策服务
            return None#无政策
        请求={}#常驻政策请求
        智能体=执行['agent'] if 'agent' in 执行 else None#调用智能体
        if 智能体 is not None:#有智能体
            请求['session']=智能体.session#按会话
        return 沙箱政策服务.resolve(请求)#解析常驻政策
    def 批准Pwsh升级(模式,理由,执行,常驻政策):#审批pwsh升级
        """在任何东西执行之前，经审批层解析沙箱升级请求。"""
        if len(升级模式)==0:#本组合没有升级
            raise pwsh工具错误('sandbox_permissions is not available in this composition (no sandboxing executor to escalate)')#拒绝
        return 批准升级(#共用审批
            {'requestedMode':模式,'justification':理由,'effectiveMode':常驻政策['mode'],'subject':'command'},#升级请求
            {#审批上下文
                'approver':上下文.获取服务('approval',False),#审批服务
                'agent':执行['agent'] if 'agent' in 执行 else None,#智能体
                'callId':执行['callId'],#调用id
                'toolName':'pwsh',#工具名
                'signal':执行['signal'] if 'signal' in 执行 else None,#取消
            },#上下文结束
        )#批准升级结束
    上下文.systemPrompt.段落({#写入系统提示词段落
        'name':'tool:pwsh',#段落名
        'order':105,#排序
        'text':('Non-zero exits are reported as `[exit code: N]` markers; investigate failures before moving on. '#面向模型的用法
            +'On Windows a killed process settles as `[exit code: 1]` without a signal marker; treat a bare exit 1 after an interruption as a termination, not a command failure.'),#Windows强杀说明
    })#段落结束
    参数表={#参数模式
        'command':{'type':'string','required':True,'description':'The PowerShell command to execute.'},#命令
        'description':{#描述
            'type':'string',#字符串
            'required':True,#必填
            'description':('Clear, concise description of what this command does in active voice, '#UI描述
                +'5-10 words (shown in the UI). Examples: "ls" → "List files in current directory"; '#示例
                +'"git status" → "Show working tree status"; "Get-Process" → "List running processes".'),#更多示例
        },#description结束
        'timeoutMs':{'type':'number','description':'Timeout in milliseconds. The executor applies its configured default and cap, and kills the command on expiry.'},#超时
        'workdir':{'type':'string','description':'Working directory for this command. Defaults to the session workspace; a relative path is resolved against it.'},#工作目录
    }#基础参数
    if 启用后台 is True:#启用后台时暴露
        参数表['run_in_background']={'type':'boolean','description':'Run in the background and return a job id immediately (collect with job_output, stop with job_kill). No timeout applies.'}#后台开关
    if len(升级模式)>0:#有升级目标时暴露
        参数表['sandbox_permissions']={#升级模式
            'type':'string',#字符串
            'enum':list(升级模式),#允许的更宽模式
            'description':'The wider sandbox mode this command needs. Only valid as a one-shot retry of a command the sandbox just denied; requires justification and user approval.',#升级说明
        }#sandbox_permissions结束
        参数表['justification']={#升级理由
            'type':'string',#字符串
            'description':'Required with sandbox_permissions: one sentence for the user explaining why this exact command needs the wider access.',#理由说明
        }#justification结束
    def 渲染(参数,值):#按种类渲染
        """后台只报任务号；前台渲染运行结果。"""
        if 值['kind']=='background':#后台
            文本='started background job '+str(值['jobId'])#只报任务号
        else:#前台
            文本=渲染Pwsh结果(值,升级模式)#前台渲染
        return [{'type':'text','text':文本}]#单个文本块
    def 执行(参数,执行上下文):#执行pwsh
        """校验后前台运行或登记后台任务。"""
        校验Pwsh参数(参数)#先校验参数
        常驻政策=解析沙箱政策(执行上下文)#常驻政策
        if ('sandbox_permissions' in 参数 and 参数['sandbox_permissions'] is not None and
                'justification' in 参数 and 参数['justification'] is not None):#请求升级
            批准模式=批准Pwsh升级(参数['sandbox_permissions'],参数['justification'],执行上下文,常驻政策)#先审批
        else:#未请求升级
            批准模式=None#无批准模式
        if 批准模式 is None:#没有批准的更宽模式
            政策=常驻政策#用常驻
        else:#盖上已批准模式
            政策=dict(常驻政策)#拷贝常驻
            政策['mode']=批准模式#覆盖模式
        工作目录=解析工作目录(参数['workdir'] if 'workdir' in 参数 else None,执行上下文)#解析工作目录
        请求={#执行请求
            'command':参数['command'],#命令
            'dshEnv':上下文.shellEnv.收集(执行上下文),#托管环境
        }#请求骨架
        if 工作目录 is not None:#有workdir
            请求['workdir']=工作目录#带上
        if 'timeoutMs' in 参数 and 参数['timeoutMs'] is not None:#有超时
            请求['timeoutMs']=参数['timeoutMs']#带上
        if 政策 is not None:#有政策
            请求['sandboxPolicy']=政策#带上
        if 'run_in_background' in 参数 and 参数['run_in_background'] is True:#走后台
            if 启用后台 is not True:#配置关闭
                raise pwsh工具错误('run_in_background is disabled for this deployment (enableRunInBackground: false)')#拒绝
            任务服务=上下文.获取服务('jobs',False)#读取任务服务
            if 任务服务 is None:#缺少任务服务
                raise pwsh工具错误('background jobs unavailable: load @deepseek-ai/dsh-jobs and @deepseek-ai/dsh-tool-jobs')#拒绝
            if 已中止(执行上下文['signal'] if 'signal' in 执行上下文 else None):#已取消
                抛中止()#抛出中止
            def 任务体():#任务体
                """在通用任务层下拉起后台 pwsh 进程。"""
                进程=上下文.shell.启动(上下文.shell.解析(请求))#解析并后台启动
                def 取消():#取消则杀进程
                    """请求杀掉后台进程。"""
                    进程.杀死()#杀进程
                def 读输出():#增量渲染
                    """增量渲染后台输出。"""
                    return 渲染Pwsh进程读取(进程.读取输出(),进程.sandbox,升级模式)#增量渲染
                return {'cancel':取消,'done':做成任务完成(进程),'readOutput':读输出}#交给任务收集器
            启动参数={#启动参数
                'kind':'pwsh',#任务种类
                'label':参数['command'],#标签是命令
                'run':任务体,#任务体
            }#启动骨架
            智能体=执行上下文['agent'] if 'agent' in 执行上下文 else None#智能体
            if 智能体 is not None:#有智能体
                启动参数['owner']=智能体#带所有者
            编号=任务服务.start(启动参数)#启动后台任务
            return {'kind':'background','jobId':编号}#立刻返回任务号
        前台请求=dict(请求)#拷贝请求
        前台请求['signal']=执行上下文['signal'] if 'signal' in 执行上下文 else None#跟取消信号
        结果=上下文.shell.运行(上下文.shell.解析(前台请求))#前台跑
        if 结果['aborted'] is True:#被中止
            抛中止()#抛出中止
        return 规范Pwsh结果(结果)#返回规范前台结果
    def 呈现调用(参数):#调用卡片
        """后台确认不带终端退出状态；通用卡片镜像 bash 工具的后台呈现。"""
        if 'run_in_background' in 参数 and 参数['run_in_background'] is True:#后台
            return {#通用执行卡片
                'card':'generic',#通用卡
                'title':参数['command'],#标题是命令
                'kind':'execute',#执行
                'rawInput':参数['command'],#原始输入
                'content':[{'type':'text','text':参数['description']}],#描述正文
            }#后台卡片结束
        卡片={#终端卡片
            'card':'terminal',#终端卡
            'title':参数['command'],#标题是命令
            'description':参数['description'],#描述
        }#前台骨架
        if 'workdir' in 参数 and 参数['workdir'] is not None:#有workdir
            卡片['cwd']=参数['workdir']#带上
        return 卡片#前台卡片
    def 呈现结果(参数,结果):#结果卡片
        """已完成前台输出呈现为终端；后台确认与执行错误用通用围栏输出。"""
        if 'content' not in 结果:#无内容
            return None#不认
        内容=结果['content']#内容块列表
        if 内容 is None or len(内容)!=1:#不是恰好一块
            return None#不认
        块=内容[0]#唯一内容块
        if 块['type']!='text':#不是文本块
            return None#不认
        原文=块['text']#正文
        是后台='run_in_background' in 参数 and 参数['run_in_background'] is True#是否后台
        if 是后台 is True or ('isError' in 结果 and 结果['isError'] is True):#后台或错误
            去尾=原文.rstrip('\n') if isinstance(原文,str) else ''#去掉尾部换行
            return {'card':'generic','content':[{'type':'text','text':'```console\n'+去尾+'\n```'}]}#通用围栏
        解析=解析退出状态(原文)#拆正文与退出
        卡片={'card':'terminal','output':解析['body']}#终端输出
        if 'exitCode' in 解析:#有退出码
            卡片['exitCode']=解析['exitCode']#退出药丸
        if 'signal' in 解析:#有信号
            卡片['signal']=解析['signal']#信号药丸
        return 卡片#终端输出加药丸
    上下文.tools.登记(定义工具({#注册pwsh工具
        'name':'pwsh',#工具名
        'description':pwsh描述(启用后台,升级模式),#按组合拼描述
        'parameters':参数表,#参数模式
        'output':{#输出约定
            'schema':{#输出模式
                'oneOf':[#后台或前台
                    {#后台
                        'type':'object',#对象
                        'additionalProperties':False,#禁止额外字段
                        'properties':后台输出字段,#任务号
                    },#后台分支结束
                    {#前台
                        'type':'object',#对象
                        'additionalProperties':False,#禁止额外字段
                        'properties':{#字段
                            'kind':{'type':'string','required':True,'const':'foreground'},#种类为foreground
                            'exitCode':{'required':True,'oneOf':[{'type':'integer'},{'type':'null'}]},#退出码
                            'signal':{'required':True,'oneOf':[{'type':'string'},{'type':'null'}]},#信号
                            'timedOut':{'type':'boolean','required':True},#是否超时
                            'aborted':{'type':'boolean','required':True},#是否中止
                            'timeoutMs':{'type':'number','required':True},#超时毫秒
                            'stdout':{#标准输出
                                'type':'object',#对象
                                'additionalProperties':False,#禁止额外字段
                                'required':True,#必填
                                'properties':{#字段
                                    'text':{'type':'string','required':True},#文本
                                    'truncated':{'type':'boolean','required':True},#是否截断
                                    'spillPath':{'type':'string'},#溢出路径
                                },#stdout properties结束
                            },#stdout结束
                            'stderr':{#标准错误
                                'type':'object',#对象
                                'additionalProperties':False,#禁止额外字段
                                'required':True,#必填
                                'properties':{#字段
                                    'text':{'type':'string','required':True},#文本
                                    'truncated':{'type':'boolean','required':True},#是否截断
                                    'spillPath':{'type':'string'},#溢出路径
                                },#stderr properties结束
                            },#stderr结束
                            'sandbox':{#沙箱事实
                                'type':'object',#对象
                                'additionalProperties':False,#禁止额外字段
                                'properties':{#字段
                                    'mode':{'type':'string','required':True},#模式
                                    'denied':{'type':'boolean','required':True},#是否拒绝
                                    'enforcement':{'type':'string'},#强制程度
                                    'runnerFailed':{'type':'boolean'},#运行器失败
                                },#sandbox properties结束
                            },#sandbox结束
                        },#前台properties结束
                    },#前台分支结束
                ],#oneOf结束
            },#schema结束
            'render':渲染,#按种类渲染
        },#output结束
        'execute':执行,#执行
        'presentCall':呈现调用,#调用卡片
        'presentResult':呈现结果,#结果卡片
    }))#pwsh工具结束

name=名称#Cordis插件名
inject=依赖#Cordis依赖声明
Config=配置#Cordis配置模式
apply=应用#Cordis插件入口
default=应用#框架槽
