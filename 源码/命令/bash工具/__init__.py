import json,math,os,threading#JSON片段、有限数、路径与后台结算线程
from concurrent.futures import Future as 原生Future#单次操作结果
from ...依赖.schemastery import 布尔字段#配置字段
from ...内核.工具 import 定义工具,工具体后中止#定义工具与体后中止码
from ...模型后端.llm import 装备错误#Harness错误
from ..命令 import 托管环境前缀#DSH环境前缀
from ...沙盒.沙盒 import (
    升级目标,#可广告的升级目标
    批准升级,#批准升级
    规范路径,#规范路径
    校验升级参数,#校验升级参数配对
)#导入沙箱升级与路径辅助
from .后台 import 进程结果#后台结果映射
from .呈现 import 解析退出状态,渲染结果,渲染进程读取#退出解析与渲染

__all__=['名称','注入','配置','应用']#仅中文公开名

名称='tool-bash'#Cordis插件名
注入=['tools','shell','systemPrompt','shellEnv']#依赖工具、shell、提示词与环境
配置={#bash工具部署配置
    'enableRunInBackground':布尔字段(默认值=True),#默认启用后台
}#配置模式结束
后台输出字段={#后台输出字段
    'kind':{'type':'string','required':True,'const':'background'},#种类为background
    'jobId':{'type':'string','required':True},#任务id
}#后台输出字段结束

class bash工具错误(Exception):#本包校验与组合失败
    """bash工具入参或组合非法。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

class 操作任务:#单次操作结果
    """任务对象只留等待。"""
    def __init__(自身):#构造未决任务
        """构造未决任务。"""
        自身.未来=原生Future()#底层Future
    def 兑现(自身,值=None):#成功结算
        """成功结算。"""
        if not 自身.未来.done():#尚未结算
            自身.未来.set_result(值)#写入结果
        return 值#返回兑现值
    def 拒绝(自身,错误):#失败结算
        """失败结算。"""
        if not 自身.未来.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身.未来.set_exception(错误)#原样拒绝
            else:#非异常
                自身.未来.set_exception(bash工具错误(错误))#包装拒绝
    def 等待(自身,超时=None):#阻塞等待
        """阻塞到结算。"""
        return 自身.未来.result(timeout=超时)#取结果或抛错

def 已中止(信号):#读中止事实
    """信号按Event定死。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号.is_set()#事件已置位

def 校验Bash参数(参数):#校验参数值
    """已解析工具参数；execute校验ParameterSchemaSpec没有的值约束。"""
    if len(参数['command'].strip())==0:#命令为空
        raise bash工具错误('非法 command：需要非空字符串')#拒绝空命令
    if len(参数['description'].strip())==0:#描述为空
        raise bash工具错误('非法 description：需要非空字符串')#拒绝空描述
    超时=参数['timeoutMs'] if 'timeoutMs' in 参数 else None#可选超时
    if 超时 is not None and (isinstance(超时,bool) or not isinstance(超时,(int,float)) or not math.isfinite(超时) or 超时<=0):#超时非法
        raise bash工具错误('非法 timeoutMs：需要正数，实际为 '+json.dumps(超时,ensure_ascii=False,separators=(',',':'),allow_nan=False))#拒绝非正超时
    校验升级参数(参数['sandbox_permissions'] if 'sandbox_permissions' in 参数 else None,参数['justification'] if 'justification' in 参数 else None)#校验升级配对

def 拼Bash描述(后台启用,升级模式):#拼工具描述
    """按组合拼面向模型的bash工具描述。"""
    if 后台启用 is True:#启用后台
        后台句='Set `run_in_background: true` for long-running commands: the call returns a job id immediately; read its output with `job_output` and stop it with `job_kill`.'#后台说明
    else:#无后台
        后台句='Background execution is not available; long-running commands must finish within the timeout.'#无后台说明
    基础=('Execute a bash command (`bash -c`) and return its stdout/stderr. '#基础描述
        +'Each call runs in a fresh shell: no state (cwd, variables, functions) persists between calls — '#新鲜shell
        +'pass `workdir` instead of using `cd`. Non-zero exits are reported as `[exit code: N]`. '#workdir与退出码
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
    """前台调用展示为终端，后台启动展示为通用卡片。两条路径标题都是命令；前台cwd传给桥去解析，后台描述留在卡片内容里。"""
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
    }#前台卡片骨架
    if 'workdir' in 参数 and 参数['workdir'] is not None:#有workdir
        卡片['cwd']=参数['workdir']#带上
    return 卡片#前台卡片

def 呈现Bash结果(参数,结果):#结果卡片
    """已完成前台输出展示为终端；后台确认与执行错误用通用围栏输出，没有退出状态药丸。"""
    if 'content' not in 结果:#无内容
        return None#不展示
    内容=结果['content']#内容块
    if 内容 is None:#无内容
        return None#不展示
    块=内容[0] if len(内容)==1 else None#唯一内容块
    if 块 is None or 块['type']!='text':#不是单文本块
        return None#不展示
    原文=块['text']#正文
    是后台='run_in_background' in 参数 and 参数['run_in_background'] is True#是否后台
    if 是后台 is True or ('isError' in 结果 and 结果['isError'] is True):#后台或错误
        return {'card':'generic','content':[{'type':'text','text':'```console\n'+原文.rstrip('\n')+'\n```'}]}#通用围栏
    解析=解析退出状态(原文)#拆正文与退出
    卡片={'card':'terminal','output':解析['body']}#终端输出
    if 'exitCode' in 解析:#有退出码键
        卡片['exitCode']=解析['exitCode']#退出药丸
    if 'signal' in 解析:#有信号键
        卡片['signal']=解析['signal']#信号药丸
    return 卡片#终端加药丸

def 解析工作目录(模型工作目录,执行上下文,政策工作区根=None):#解析工作目录
    """先解析显式workdir，相对路径相对会话工作区；否则用会话cwd的文件系统身份，并把执行器默认当作回退。已解析的沙箱政策根赢，因此workdir与隔离使用完全相同的按次身份。"""
    头=执行上下文['agent'].session.header#会话头；执行上下文是dict，智能体是对象
    头cwd=头['cwd'] if 'cwd' in 头 else None#会话头cwd
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
    """把执行器DTO从只读Service Definition类型拆成普通JSON数据。"""
    def 一路输出(流):#一路输出
        """投影一路收集输出。"""
        出={'text':流['text'],'truncated':流['truncated']}#文本与截断
        if 'spillPath' in 流 and 流['spillPath'] is not None:#有溢出路径
            出['spillPath']=流['spillPath']#带上
        return 出#一路输出
    收成={#规范结果
        'kind':'foreground',#种类为foreground
        'exitCode':结果['exitCode'],#退出码
        'signal':结果['signal'],#信号
        'timedOut':结果['timedOut'],#是否超时
        'aborted':结果['aborted'],#是否中止
        'timeoutMs':结果['timeoutMs'],#超时毫秒
        'stdout':一路输出(结果['stdout']),#标准输出
        'stderr':一路输出(结果['stderr']),#标准错误
    }#骨架结束
    if 'sandbox' in 结果 and 结果['sandbox'] is not None:#有沙箱事实
        沙箱=结果['sandbox']#沙箱事实
        沙箱出={#沙箱
            'mode':沙箱['mode'],#模式
            'denied':沙箱['denied'],#是否拒绝
        }#沙箱骨架
        if 'enforcement' in 沙箱 and 沙箱['enforcement'] is not None:#有强制程度
            沙箱出['enforcement']=沙箱['enforcement']#带上
        if 'runnerFailed' in 沙箱 and 沙箱['runnerFailed'] is not None:#有运行器失败
            沙箱出['runnerFailed']=沙箱['runnerFailed']#带上
        收成['sandbox']=沙箱出#写入
    return 收成#规范结果

def 抛中止():#抛出工具调用中止
    """抛出带AbortError名的体后中止。"""
    错误=装备错误('工具调用已中止',工具体后中止)#中止错误
    错误.name='AbortError'#名字
    raise 错误#抛出

def 应用(上下文,配置值=None):#加载bash工具插件
    """在ctx.tools上登记bash；有隔离执行器时要求ctx.sandboxPolicy。"""
    if 配置值 is None:#缺省空配置
        配置值={}#空配置
    后台启用=配置值['enableRunInBackground'] if 'enableRunInBackground' in 配置值 else True#是否启用后台
    默认模式=上下文.shell.沙箱模式#执行器默认沙箱模式
    升级模式=[] if 默认模式 is None else list(升级目标)#有隔离才暴露升级
    沙箱政策=None if 默认模式 is None else 上下文.获取服务('sandboxPolicy',False)#政策服务
    if 默认模式 is not None and 沙箱政策 is None:#隔离却缺政策
        raise bash工具错误('tool-bash: 已挂载的 bash 执行器会隔离，但缺少 ctx.sandboxPolicy')#加载时失败
    def 解析沙箱政策(执行上下文):#解析常驻政策
        """挂上隔离执行器时，解析本次调用的完整常驻政策。"""
        if 沙箱政策 is None:#无政策服务
            return None#无
        请求={}#常驻政策请求
        智能体=执行上下文['agent'] if 'agent' in 执行上下文 else None#调用方智能体
        if 智能体 is not None:#有智能体
            请求['session']=智能体.session#带上会话
        return 沙箱政策.resolve(请求)#按会话解析
    def 审批Bash升级(模式,理由,执行上下文,常驻政策):#审批bash升级
        """在任何东西执行之前，经ctx.approval解析沙箱升级请求。"""
        if len(升级模式)==0:#本组合没有升级
            raise bash工具错误('本组合没有可升级的沙箱执行器，不能使用 sandbox_permissions')#拒绝
        return 批准升级(#共用审批
            {'requestedMode':模式,'justification':理由,'effectiveMode':常驻政策['mode'],'subject':'command'},#升级请求
            {#审批上下文
                'approver':上下文.获取服务('approval',False),#审批服务
                'agent':执行上下文['agent'] if 'agent' in 执行上下文 else None,#智能体
                'callId':执行上下文['callId'],#调用id
                'toolName':'bash',#工具名
                'signal':执行上下文['signal'] if 'signal' in 执行上下文 else None,#取消
            },#上下文结束
        )#批准升级结束
    上下文.systemPrompt.段落({#写入系统提示词段落
        'name':'tool:bash',#段落名
        'order':105,#排序
        'text':'Check the [exit code: N] marker on every bash result; investigate failures before moving on.',#面向模型的用法
    })#段落结束
    def 渲染(参数,值):#按种类渲染
        """把结构化结果渲染成模型可见文本。"""
        if 值['kind']=='background':#后台
            文本='started background job '+str(值['jobId'])#只报任务号
        else:#前台
            文本=渲染结果(值,升级模式)#前台渲染运行结果
        return [{'type':'text','text':文本}]#单个文本块
    def 执行(参数,执行上下文):#执行bash
        """校验后前台run或后台jobs。"""
        校验Bash参数(参数)#先校验参数
        常驻政策=解析沙箱政策(执行上下文)#常驻政策
        if ('sandbox_permissions' in 参数 and 参数['sandbox_permissions'] is not None and
                'justification' in 参数 and 参数['justification'] is not None):#请求升级
            批准模式=审批Bash升级(参数['sandbox_permissions'],参数['justification'],执行上下文,常驻政策)#先审批
        else:#未请求升级
            批准模式=None#无
        if 批准模式 is None:#没有批准的更宽模式
            政策=常驻政策#用常驻
        else:#盖上已批准模式
            政策=dict(常驻政策)#拷贝常驻
            政策['mode']=批准模式#覆盖模式
        工作目录=解析工作目录(参数['workdir'] if 'workdir' in 参数 else None,执行上下文,None if 常驻政策 is None else (常驻政策['workspaceRoot'] if 'workspaceRoot' in 常驻政策 else None))#解析工作目录
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
            if 后台启用 is not True:#配置关闭
                raise bash工具错误('run_in_background 已对本部署关闭（enableRunInBackground: false）')#拒绝
            任务服务=上下文.获取服务('jobs',False)#读取任务服务
            if 任务服务 is None:#缺少任务服务
                raise bash工具错误('后台任务不可用：请加载 @deepseek-ai/dsh-jobs 与 @deepseek-ai/dsh-tool-jobs')#拒绝
            if 已中止(执行上下文['signal'] if 'signal' in 执行上下文 else None):#已取消
                抛中止()#抛出中止
            def 任务体():#任务体
                """在ctx.jobs下拉起后台bash进程。"""
                进程=上下文.shell.启动(上下文.shell.解析(请求))#解析并后台启动
                结算=操作任务()#任务done
                def 监视结算():#等到进程关闭再映射结果
                    """把进程done映射成任务结果。"""
                    try:#正常结算
                        进程.done.等待()#等到关闭
                        结算.兑现(进程结果(进程))#映射并兑现
                    except BaseException as 错误:#失败
                        结算.拒绝(错误)#拒绝
                工作=threading.Thread(target=监视结算)#后台结算线程
                工作.daemon=True#不挡住退出
                工作.start()#启动
                def 取消():#取消则杀进程
                    """请求杀掉后台进程。"""
                    进程.杀死()#杀进程
                def 读输出():#增量渲染
                    """增量渲染后台输出。"""
                    return 渲染进程读取(进程.读取输出(),进程.sandbox,升级模式)#增量渲染
                return {'cancel':取消,'done':结算,'readOutput':读输出}#交给任务收集器
            启动参数={#启动后台任务
                'kind':'bash',#任务种类
                'label':参数['command'],#标签是命令
                'run':任务体,#任务体
            }#启动参数骨架
            智能体=执行上下文['agent'] if 'agent' in 执行上下文 else None#调用方智能体
            if 智能体 is not None:#有智能体
                启动参数['owner']=智能体#带所有者
            编号=任务服务.start(启动参数)#启动
            return {'kind':'background','jobId':编号}#立刻返回任务号
        前台请求=dict(请求)#拷贝请求
        前台请求['signal']=执行上下文['signal'] if 'signal' in 执行上下文 else None#跟取消信号
        结果=上下文.shell.运行(上下文.shell.解析(前台请求))#前台跑
        if 结果['aborted'] is True:#被中止
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
    if 后台启用 is True:#启用后台时暴露
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

name=名称#Cordis插件名
inject=注入#Cordis依赖声明
Config=配置#Cordis配置模式
apply=应用#Cordis插件入口
default=应用#Cordis默认导出
