"""`ctx.shell` 能力 seam 的面向模型消费方。对齐上游 `tool-bash/src/index.ts`。公开面仅中文名。

后台调用把进程句柄登记到 `ctx.jobs`；一旦返回 id，其工作使用任务取消而不是工具调用信号。
Cordis 槽 `name` / `inject` / `Config` / `apply` / `default` 可保留。
"""
import json,math,os,threading#JSON 片段、有限数、路径与后台结算线程
from ...依赖 import cordis,schemastery#外部依赖胶水
模式=schemastery.模式#配置模式
承诺=cordis.工具.承诺#承诺
是否thenable=cordis.工具.是否thenable#可等待判定
from ..工具 import 定义工具,工具体后中止,已中止#定义工具、体后中止码与中止判定
from ..llm import 装备错误#Harness 错误
from ..命令 import 托管环境前缀#DSH 环境前缀
from ..沙盒 import (
    升级目标,#可广告的升级目标
    批准升级,#批准升级
    规范路径,#规范路径
    校验升级参数,#校验升级参数配对
)#导入沙箱升级与路径辅助
from .后台 import 进程结果#后台结果映射
from .呈现 import 解析退出状态,渲染结果,渲染进程读取#退出解析与渲染

__all__=['名称','注入','配置','应用','默认']#仅中文公开名（Cordis 槽另挂）

名称='tool-bash'#Cordis 插件名
注入=['tools','shell','systemPrompt','shellEnv']#依赖工具、shell、提示词与环境
name=名称#Cordis插件名（协议槽）
inject=注入#Cordis依赖声明（协议槽）
配置=模式.对象({#bash 工具部署配置
    'enableRunInBackground':模式.布尔().默认(True),#默认启用后台
})#配置模式结束
Config=配置#Cordis配置模式（协议槽）
后台输出字段={#后台输出字段
    'kind':{'type':'string','required':True,'const':'background'},#种类为 background
    'jobId':{'type':'string','required':True},#任务 id
}#后台输出字段结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 是否有限数(值):#对齐JS Number.isFinite
    """对齐 JS Number.isFinite，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是有限数
    if isinstance(值,(int,float)):#整数或浮点
        return math.isfinite(值)#有限
    return False#其它类型

def 校验Bash参数(参数):#校验参数值
    """已解析工具参数；execute 校验 ParameterSchemaSpec 没有的值约束。"""
    if len(取字段(参数,'command').strip())==0:#命令为空
        raise Exception('invalid command: expected a non-empty string')#拒绝空命令
    if len(取字段(参数,'description').strip())==0:#描述为空
        raise Exception('invalid description: expected a non-empty string')#拒绝空描述
    超时=取字段(参数,'timeoutMs')#可选超时
    if 超时 is not None and ((not 是否有限数(超时)) or 超时<=0):#超时非法
        raise Exception('invalid timeoutMs: expected a positive number, got '+json.dumps(超时,ensure_ascii=False))#拒绝非正超时
    校验升级参数(取字段(参数,'sandbox_permissions'),取字段(参数,'justification'))#校验升级配对

def 拼Bash描述(后台启用,升级模式):#拼工具描述
    """按组合拼面向模型的 bash 工具描述。"""
    if 后台启用:#启用后台
        后台句='Set `run_in_background: true` for long-running commands: the call returns a job id immediately; read its output with `job_output` and stop it with `job_kill`.'#后台说明
    else:#无后台
        后台句='Background execution is not available; long-running commands must finish within the timeout.'#无后台说明
    基础=('Execute a bash command (`bash -c`) and return its stdout/stderr. '#基础描述
        +'Each call runs in a fresh shell: no state (cwd, variables, functions) persists between calls — '#新鲜 shell
        +'pass `workdir` instead of using `cd`. Non-zero exits are reported as `[exit code: N]`. '#workdir 与退出码
        +'Current harness environment facts are exposed through managed `$'+托管环境前缀+'*` variables; inspect them when needed. '#托管环境
        +'Commands may run under a file sandbox; a blocked file operation is reported as `[sandbox: file access denied under <mode> mode]` — a policy denial, not a bug in the command; do not retry another way. '#沙箱拒绝
        +'Long output is truncated to its tail; the full output is saved to a file whose path is reported when available. '#截断
        +后台句)#后台段
    if len(升级模式)==0:#无升级
        return 基础#到此
    return (基础+' Attempting a command the sandbox may deny is safe and expected: run it and read the '#升级指引
        +'marker rather than assuming the denial. When a command is denied and a wider mode would let it '#读标记
        +'succeed, escalate immediately in the same turn — the one sanctioned exception to a denial: retry '#同轮升级
        +'the exact same command once with `sandbox_permissions` (the narrowest wider mode that suffices) '#精确重试
        +'plus a one-sentence `justification`. Do not detour through chat to ask permission first — the '#不要先聊天
        +'approval prompt raised by that retry is how the user consents. If the session states approval '#审批提示
        +'prompts are disabled, there is no exception: a denial is final — do not set `sandbox_permissions`. '#禁用审批
        +'Never escalate speculatively: ground the request in a real denial — normally the one this command '#禁止投机
        +'just hit; escalating up front is fine only when this session already denied the same access. '#已有拒绝
        +'A rejected escalation is final for that command — stop and explain, never work around '#拒绝升级
        +'it — but it does not forbid attempting or escalating other commands later.')#不影响其他命令

def 呈现Bash调用(参数):#调用卡片
    """前台调用展示为终端，后台启动展示为通用卡片。两条路径标题都是命令；前台 cwd 传给桥去解析，后台描述留在卡片内容里。"""
    if 取字段(参数,'run_in_background') is True:#后台
        return {#通用执行卡片
            'card':'generic',#通用卡
            'title':取字段(参数,'command'),#标题是命令
            'kind':'execute',#执行
            'rawInput':取字段(参数,'command'),#原始输入
            'content':[{'type':'text','text':取字段(参数,'description')}],#描述正文
        }#后台卡片结束
    卡片={#终端卡片
        'card':'terminal',#终端卡
        'title':取字段(参数,'command'),#标题是命令
        'description':取字段(参数,'description'),#描述
    }#前台卡片骨架
    if 取字段(参数,'workdir') is not None:#有workdir
        卡片['cwd']=取字段(参数,'workdir')#带上
    return 卡片#前台卡片

def 呈现Bash结果(参数,结果):#结果卡片
    """已完成前台输出展示为终端；后台确认与执行错误用通用围栏输出，没有退出状态药丸。"""
    内容=取字段(结果,'content')#内容块
    if 内容 is None:#无内容
        return None#不展示
    块=内容[0] if len(内容)==1 else None#唯一内容块
    if 块 is None or 取字段(块,'type')!='text':#不是单文本块
        return None#不展示
    原文=取字段(块,'text')#正文
    是后台=isinstance(参数,dict) and 取字段(参数,'run_in_background') is True#是否后台
    if (not 是后台) and (not isinstance(参数,dict)) and 参数 is not None:#对象参数
        是后台=取字段(参数,'run_in_background') is True#读属性
    if 是后台 or 取字段(结果,'isError'):#后台或错误
        return {'card':'generic','content':[{'type':'text','text':'```console\n'+原文.rstrip('\n')+'\n```'}]}#通用围栏
    解析=解析退出状态(原文)#拆正文与退出
    卡片={'card':'terminal','output':取字段(解析,'body')}#终端输出
    if isinstance(解析,dict) and 'exitCode' in 解析:#有退出码键
        卡片['exitCode']=解析['exitCode']#退出药丸
    if isinstance(解析,dict) and 'signal' in 解析:#有信号键
        卡片['signal']=解析['signal']#信号药丸
    return 卡片#终端加药丸

def 解析工作目录(模型工作目录,执行上下文,政策工作区根=None):#解析工作目录
    """先解析显式 workdir，相对路径相对会话工作区；否则用会话 cwd 的文件系统身份，并把执行器默认当作回退。已解析的沙箱政策根赢，因此 workdir 与隔离使用完全相同的按次身份。"""
    头cwd=取字段(取字段(取字段(执行上下文,'agent'),'session'),'header')#会话头
    头cwd=取字段(头cwd,'cwd')#会话头cwd
    if 政策工作区根 is not None:#政策根优先
        会话cwd=政策工作区根#政策根
    elif 头cwd is None:#无会话cwd
        会话cwd=None#空
    else:#规范会话cwd
        会话cwd=规范路径(头cwd)#规范化
    if 模型工作目录 is None:#未给
        return 会话cwd#用会话
    if 会话cwd is not None and (not os.path.isabs(模型工作目录)):#相对路径
        return os.path.normpath(os.path.join(会话cwd,模型工作目录))#相对会话解析
    return 模型工作目录#绝对或无会话则原样

def 规范Bash结果(结果):#规范化前台结果
    """把执行器 DTO 从只读 Service Definition 类型拆成普通 JSON 数据。"""
    def 一路输出(流):#一路输出
        """投影一路收集输出。"""
        出={'text':取字段(流,'text'),'truncated':取字段(流,'truncated')}#文本与截断
        溢出=取字段(流,'spillPath')#溢出路径
        if 溢出 is not None:#有溢出路径
            出['spillPath']=溢出#带上
        return 出#一路输出
    收成={#规范结果
        'kind':'foreground',#种类为foreground
        'exitCode':取字段(结果,'exitCode'),#退出码
        'signal':取字段(结果,'signal'),#信号
        'timedOut':取字段(结果,'timedOut'),#是否超时
        'aborted':取字段(结果,'aborted'),#是否中止
        'timeoutMs':取字段(结果,'timeoutMs'),#超时毫秒
        'stdout':一路输出(取字段(结果,'stdout')),#标准输出
        'stderr':一路输出(取字段(结果,'stderr')),#标准错误
    }#骨架结束
    沙箱=取字段(结果,'sandbox')#沙箱事实
    if 沙箱 is not None:#有沙箱事实
        沙箱出={#沙箱
            'mode':取字段(沙箱,'mode'),#模式
            'denied':取字段(沙箱,'denied'),#是否拒绝
        }#沙箱骨架
        强制=取字段(沙箱,'enforcement')#强制程度
        if 强制 is not None:#有强制程度
            沙箱出['enforcement']=强制#带上
        运行器失败=取字段(沙箱,'runnerFailed')#运行器失败
        if 运行器失败 is not None:#有运行器失败
            沙箱出['runnerFailed']=运行器失败#带上
        收成['sandbox']=沙箱出#写入
    return 收成#规范结果

def 抛中止():#抛出工具调用中止
    """抛出带 AbortError 名的体后中止。"""
    错误=装备错误('tool call aborted',工具体后中止)#中止错误
    错误.name='AbortError'#名字
    raise 错误#抛出

def 应用(上下文,配置值=None):#加载bash工具插件
    """在 ctx.tools 上登记 bash；有隔离执行器时要求 ctx.sandboxPolicy。"""
    if 配置值 is None:#缺省空配置
        配置值={}#空配置
    后台启用=取字段(配置值,'enableRunInBackground')#是否启用后台
    if 后台启用 is None:#未给出
        后台启用=True#默认启用
    默认模式=上下文.shell.沙箱模式#执行器默认沙箱模式
    升级模式=[] if 默认模式 is None else list(升级目标)#有隔离才暴露升级
    沙箱政策=None if 默认模式 is None else 上下文.get('sandboxPolicy')#政策服务
    if 默认模式 is not None and 沙箱政策 is None:#隔离却缺政策
        raise Exception('tool-bash: the mounted bash executor confines but ctx.sandboxPolicy is missing')#加载时失败
    def 解析沙箱政策(执行上下文):#解析常驻政策
        """挂上隔离执行器时，解析本次调用的完整常驻政策。"""
        if 沙箱政策 is None:#无政策服务
            return None#无
        请求={}#常驻政策请求
        智能体=取字段(执行上下文,'agent')#调用方智能体
        if 智能体 is not None:#有智能体
            请求['session']=取字段(智能体,'session')#带上会话
        return 沙箱政策.resolve(请求)#按会话解析
    def 审批Bash升级(模式,理由,执行上下文,常驻政策):#审批bash升级
        """在任何东西执行之前，经 ctx.approval 解析沙箱升级请求。"""
        if len(升级模式)==0:#本组合没有升级
            raise Exception('sandbox_permissions is not available in this composition (no sandboxing executor to escalate)')#拒绝
        return 解开(批准升级(#共用审批
            {'requestedMode':模式,'justification':理由,'effectiveMode':取字段(常驻政策,'mode'),'subject':'command'},#升级请求
            {#审批上下文
                'approver':上下文.get('approval'),#审批服务
                'agent':取字段(执行上下文,'agent'),#智能体
                'callId':取字段(执行上下文,'callId'),#调用id
                'toolName':'bash',#工具名
                'signal':取字段(执行上下文,'signal'),#取消
            },#上下文结束
        ))#批准升级结束
    上下文.systemPrompt.段落({#写入系统提示词段落
        'name':'tool:bash',#段落名
        'order':105,#排序
        'text':'Check the [exit code: N] marker on every bash result; investigate failures before moving on.',#面向模型的用法
    })#段落结束
    def 渲染(参数,值):#按种类渲染
        """把结构化结果渲染成模型可见文本。"""
        if 取字段(值,'kind')=='background':#后台
            文本='started background job '+str(取字段(值,'jobId'))#只报任务号
        else:#前台
            文本=渲染结果(值,升级模式)#前台渲染运行结果
        return [{'type':'text','text':文本}]#单个文本块
    def 执行(参数,执行上下文):#执行bash
        """校验后前台 run 或后台 jobs。"""
        校验Bash参数(参数)#先校验参数
        常驻政策=解析沙箱政策(执行上下文)#常驻政策
        if 取字段(参数,'sandbox_permissions') is not None and 取字段(参数,'justification') is not None:#请求升级
            批准模式=审批Bash升级(取字段(参数,'sandbox_permissions'),取字段(参数,'justification'),执行上下文,常驻政策)#先审批
        else:#未请求升级
            批准模式=None#无
        if 批准模式 is None:#没有批准的更宽模式
            政策=常驻政策#用常驻
        else:#盖上已批准模式
            政策=dict(常驻政策)#拷贝常驻
            政策['mode']=批准模式#覆盖模式
        工作目录=解析工作目录(取字段(参数,'workdir'),执行上下文,取字段(常驻政策,'workspaceRoot'))#解析工作目录
        请求={#执行请求
            'command':取字段(参数,'command'),#命令
            'dshEnv':上下文.shellEnv.收集(执行上下文),#托管环境
        }#请求骨架
        if 工作目录 is not None:#有workdir
            请求['workdir']=工作目录#带上
        超时=取字段(参数,'timeoutMs')#超时
        if 超时 is not None:#有超时
            请求['timeoutMs']=超时#带上
        if 政策 is not None:#有政策
            请求['sandboxPolicy']=政策#带上
        if 取字段(参数,'run_in_background') is True:#走后台
            if not 后台启用:#配置关闭
                raise Exception('run_in_background is disabled for this deployment (enableRunInBackground: false)')#拒绝
            任务们=上下文.get('jobs')#读取任务服务
            if 任务们 is None:#缺少任务服务
                raise Exception('background jobs unavailable: load @deepseek-ai/dsh-jobs and @deepseek-ai/dsh-tool-jobs')#拒绝
            if 已中止(取字段(执行上下文,'signal')):#已取消
                抛中止()#抛出中止
            def 任务体():#任务体
                """在 ctx.jobs 下拉起后台 bash 进程。"""
                进程=上下文.shell.启动(上下文.shell.解析(请求))#解析并后台启动
                结算=承诺()#任务done
                def 盯结算():#等到进程关闭再映射结果
                    """把进程 done 映射成任务结果。"""
                    try:#正常结算
                        解开(取字段(进程,'done'))#等到关闭
                        结算.兑现(进程结果(进程))#映射并兑现
                    except BaseException as 错误:#失败
                        结算.拒绝(错误)#拒绝
                工作=threading.Thread(target=盯结算)#后台结算线程
                工作.daemon=True#不挡住退出
                工作.start()#启动
                def 取消():#取消则杀进程
                    """请求杀掉后台进程。"""
                    杀=取字段(进程,'kill')#终止方法
                    if callable(杀):#可调用
                        杀()#杀进程
                def 读输出():#增量渲染
                    """增量渲染后台输出。"""
                    读=取字段(进程,'readOutput')#读取方法
                    if callable(读):#可调用
                        读取=读()#读一次
                    else:#已是值
                        读取=读#原样
                    return 渲染进程读取(读取,取字段(进程,'sandbox'),升级模式)#增量渲染
                return {'cancel':取消,'done':结算,'readOutput':读输出}#交给任务收集器
            启动参数={#启动后台任务
                'kind':'bash',#任务种类
                'label':取字段(参数,'command'),#标签是命令
                'run':任务体,#任务体
            }#启动参数骨架
            智能体=取字段(执行上下文,'agent')#调用方智能体
            if 智能体 is not None:#有智能体
                启动参数['owner']=智能体#带所有者
            编号=任务们.start(启动参数)#启动
            return {'kind':'background','jobId':编号}#立刻返回任务号
        前台请求=dict(请求)#拷贝请求
        前台请求['signal']=取字段(执行上下文,'signal')#跟取消信号
        结果=解开(上下文.shell.运行(上下文.shell.解析(前台请求)))#前台跑
        if 取字段(结果,'aborted') is True:#被中止
            抛中止()#抛出中止
        return 规范Bash结果(结果)#返回规范前台结果
    参数表={#参数模式
        'command':{'type':'string','required':True,'description':'The bash command to execute.'},#命令
        'description':{#描述
            'type':'string',#字符串
            'required':True,#必填
            'description':('Clear, concise description of what this command does in active voice, '#UI描述
                +'5-10 words (shown in the UI). Examples: "ls" → "List files in current directory"; '#示例
                +'"git status" → "Show working tree status"; "npm install" → "Install package dependencies".'),#更多示例
        },#description结束
        'timeoutMs':{'type':'number','description':'Timeout in milliseconds. The executor applies its configured default and cap, and kills the command on expiry.'},#超时
        'workdir':{'type':'string','description':'Working directory for this command. Defaults to the session workspace; a relative path is resolved against it.'},#工作目录
    }#参数骨架
    if 后台启用:#启用后台时暴露
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
    上下文.tools.登记(定义工具({#注册bash工具
        'name':'bash',#工具名
        'description':拼Bash描述(后台启用,升级模式),#按组合拼描述
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
        'execute':执行,#执行bash
        'presentCall':呈现Bash调用,#调用卡片
        'presentResult':呈现Bash结果,#结果卡片
    }))#bash工具结束

apply=应用#Cordis插件入口（协议槽）
default=应用#Cordis默认导出（协议槽）
默认=应用#中文默认导出
