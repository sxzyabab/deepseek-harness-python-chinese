"""六种面向模型的持久终端工具。所有者身份来自精确的工具执行智能体；通用 `ctx.jobs` 负责后台 id 与收集。"""
import threading#后台结算线程
from ...依赖 import cordis,schemastery#外部依赖胶水
模式=schemastery.模式#配置校验库
承诺=cordis.工具.承诺#承诺
是否thenable=cordis.工具.是否thenable#可等待
已兑现=cordis.工具.已兑现#立刻兑现
from ..终端 import 终端会话标识#导入会话id品牌化
from ..工具 import 定义工具#导入工具定义
from .渲染 import (#导入渲染与截断
    封顶终端文本,#封顶完整确认
    渲染列表,#渲染会话列表
    渲染读取,#渲染读取结果
    渲染发送,#渲染发送结果
    渲染发送读取,#渲染发送增量
    渲染打开,#渲染打开结果
)#渲染模块结束

名称='tool-terminal'#Cordis插件名
注入=['terminals','tools','systemPrompt']#必需的能力、注册表与提示词服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
默认结果字节=256*1024#一次完整面向模型的终端结果的默认上限
最小结果字节=64#能在截断回执里保住全部计数器签发的 PTY 与任务 id 的最小上限
安全整数上限=2**53-1#对齐 Number.MAX_SAFE_INTEGER
配置=模式.对象({#终端工具消费方配置
    'enableRunInBackground':模式.布尔().默认(True),#是否暴露 run_in_background 并接受后台发送
    'maxResultBytes':模式.数字().步进(1).最小(最小结果字节).最大(安全整数上限).默认(默认结果字节),#结果字节上限
})#配置模式结束
Config=配置#Cordis配置模式

会话状态模式={#会话状态模式
    'oneOf':[#运行中或已退出
        {#运行中
            'type':'object',#对象
            'additionalProperties':False,#禁止多余字段
            'properties':{#字段
                'kind':{'type':'string','required':True,'const':'running'},#种类固定running
            },#properties结束
        },#运行中结束
        {#已退出
            'type':'object',#对象
            'additionalProperties':False,#禁止多余字段
            'properties':{#字段
                'kind':{'type':'string','required':True,'const':'exited'},#种类固定exited
                'exitCode':{'required':True,'oneOf':[{'type':'integer'},{'type':'null'}]},#退出码或null
                'signal':{'required':True,'oneOf':[{'type':'string'},{'type':'null'}]},#信号或null
            },#properties结束
        },#已退出结束
    ],#oneOf结束
}#SESSION_STATUS_SCHEMA结束

会话快照字段={#快照字段
    'sessionId':{'type':'string','required':True},#会话id
    'name':{'type':'string'},#可选显示名
    'type':{'type':'string','required':True},#后端类型
    'pid':{'type':'integer'},#可选进程号
    'status':{**会话状态模式,'required':True},#会话状态
}#SESSION_SNAPSHOT_PROPERTIES结束

会话快照模式={#快照对象模式
    'type':'object',#对象
    'additionalProperties':False,#禁止多余字段
    'properties':会话快照字段,#快照字段
}#SESSION_SNAPSHOT_SCHEMA结束

后台任务输出模式={#后台任务输出模式
    'type':'object',#对象
    'additionalProperties':False,#禁止多余字段
    'properties':{#字段
        'kind':{'type':'string','required':True,'const':'background'},#种类固定background
        'jobId':{'type':'string','required':True},#任务id
    },#properties结束
}#BACKGROUND_TASK_OUTPUT_SCHEMA结束

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

def 是否安全整数(值):#对齐 JS Number.isSafeInteger
    """对齐 JS Number.isSafeInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是安全整数
    if isinstance(值,int):#整数
        return -(2**53)<值<(2**53)#安全整数范围
    if isinstance(值,float):#浮点
        if not 值.is_integer():#非整值
            return False#不是整数
        return abs(值)<=(2**53-1)#有限且在安全范围
    return False#其它类型

def 是否已中止(信号):#读中止旗标
    """对齐 signal.aborted。"""
    if 信号 is None:#无信号
        return False#未中止
    if getattr(信号,'aborted',False):#英文字段
        return True#已中止
    return bool(getattr(信号,'已中止',False))#中文字段

def 要求智能体(智能体):#工具执行必须有智能体
    """终端工具要求发起智能体。"""
    if 智能体 is None:#缺智能体
        raise Exception('terminal tools require an initiating agent')#拒绝缺智能体
    return 智能体#已确认

def 会话标识(参数):#品牌化会话id
    """把参数里的 sessionId 打成 TerminalSessionId。"""
    标识=取字段(参数,'sessionId')#取出会话id
    if not isinstance(标识,str) or len(标识)==0:#空字符串或非字符串
        raise Exception('sessionId must be a non-empty string')#拒绝空id
    return 终端会话标识(标识)#打上品牌

def 文本结果(文本,最大字节):#封顶后做成文本块
    """封顶后做成单块文本 ContentBlock。"""
    return [{'type':'text','text':封顶终端文本(文本,最大字节)}]#单块文本

def 原文单文本(内容):#取出唯一文本块
    """从权威 JSON 块数组取出唯一文本块正文。"""
    if 内容 is None or len(内容)!=1:#不是单块则放弃
        return None#放弃
    块=内容[0]#第一块
    if 取字段(块,'type')=='text':#仅文本块
        return 取字段(块,'text')#正文
    return None#非文本

def 发送详情(结果):#后台任务详情
    """把发送结算映射成任务 detail 字符串。"""
    会话状态=取字段(结果,'sessionStatus')#会话状态
    if 取字段(会话状态,'kind')=='running':#仍在运行
        return 'wait: '+str(取字段(结果,'waitReason'))#等待原因
    退出码=取字段(会话状态,'exitCode')#退出码
    信号=取字段(会话状态,'signal')#信号
    原因=退出码 if 退出码 is not None else (信号 if 信号 is not None else 'unknown')#退出信息
    return 'session exited: '+str(原因)#退出信息

def 应用(上下文,配置值=None):#登记全部终端工具与最少用法说明
    """登记全部终端工具与最少用法说明。"""
    if 配置值 is None:#缺省空配置
        配置值={}#空配置
    后台启用=取字段(配置值,'enableRunInBackground')#是否启用后台
    if 后台启用 is None:#缺省真
        后台启用=True#默认启用
    结果字节=取字段(配置值,'maxResultBytes')#结果字节上限
    if 结果字节 is None:#缺省默认
        结果字节=默认结果字节#默认上限
    if not 是否安全整数(结果字节) or 结果字节<最小结果字节:#非法上限
        raise Exception('tool-terminal: maxResultBytes must be a safe integer of at least '+str(最小结果字节))#拒绝
    def 收口内容(_执行,结果):#执行后封顶文本
        """执行后封顶文本内容。"""
        原文=原文单文本(取字段(结果,'content'))#取出原文
        if 原文 is None:#不能封顶
            return None#透传
        return 文本结果(原文,结果字节)#能封顶则替换
    上下文.systemPrompt.section({#写入系统提示
        'name':'tool:pty',#段落名
        'order':106,#顺序
        'text':'Use a terminal session only when work needs persistent terminal state or interactive stdin; prefer shell/read/write/edit for bounded one-shot operations. Track every terminal session id and close sessions that no longer matter. An inferred_idle or timeout result does not prove the foreground command exited.',#用法说明
    })#系统提示结束

    def 执行打开(参数,执行元数据):#执行打开
        """创建持久、所有者隔离的终端会话。"""
        类型=取字段(参数,'type')#后端类型
        if not isinstance(类型,str) or len(类型)==0:#拒绝空类型
            raise Exception('type must be a non-empty string')#拒绝空类型
        请求={'type':类型}#搭建请求
        显示名=取字段(参数,'name')#可选显示名
        if 显示名 is not None:#有名则带上
            请求['name']=显示名#显示名
        工作目录=取字段(参数,'cwd')#可选工作目录
        if 工作目录 is not None:#有cwd则带上
            请求['cwd']=工作目录#工作目录
        return 已兑现(解开(上下文.terminals.spawn(#搭建会话
            要求智能体(取字段(执行元数据,'agent')),#所有者
            请求,#搭建请求
            取字段(执行元数据,'signal'),#工具取消
        )))#带上工具取消
    def 呈现打开(参数):#调用卡片
        """打开终端的通用卡片。"""
        显示名=取字段(参数,'name')#可选显示名
        标题后缀=显示名 if 显示名 is not None else 取字段(参数,'type')#名或类型
        return {'card':'generic','title':'Open terminal '+str(标题后缀),'kind':'execute'}#通用卡片
    def 渲染打开结果(_参数,值):#渲染打开结果
        """渲染打开结果文本块。"""
        return [{'type':'text','text':渲染打开(值,结果字节)}]#渲染打开结果
    上下文.tools.register(定义工具({#登记打开工具
        'name':'terminal_open',#工具名
        'description':'Create a persistent, owner-isolated terminal session from a registered backend type. Use this for shell or REPL state that must survive across tool calls.',#描述
        'parameters':{#参数
            'type':{'type':'string','required':True,'description':'Registered terminal backend type, usually "shell".'},#后端类型
            'name':{'type':'string','description':'Optional owner-local display name such as "main" or "gdb".'},#显示名
            'cwd':{'type':'string','description':'Initial working directory. Defaults to the deployment workspace root.'},#工作目录
        },#parameters结束
        'finalizeContent':收口内容,#封顶
        'output':{#输出
            'schema':{#模式
                'type':'object',#对象
                'additionalProperties':False,#禁止多余字段
                'properties':{#字段
                    **会话快照字段,#快照字段
                    'motd':{'type':'string','required':True},#开机信息
                },#properties结束
            },#schema结束
            'render':渲染打开结果,#渲染打开结果
        },#output结束
        'execute':执行打开,#执行打开
        'presentCall':呈现打开,#调用卡片
    }))#terminal_open结束

    def 执行发送(参数,执行元数据):#执行发送
        """前台等待结算，或后台立刻返回任务 id。"""
        所有者=要求智能体(取字段(执行元数据,'agent'))#所有者
        标识=会话标识(参数)#会话id
        请求={'text':取字段(参数,'text'),'submit':True if 取字段(参数,'submit') is None else 取字段(参数,'submit')}#写入请求
        if 取字段(参数,'run_in_background') is True:#后台发送
            if not 后台启用:#配置禁止
                raise Exception('background terminal sends are disabled by tool-terminal configuration')#配置禁止
            任务们=上下文.get('jobs')#任务服务
            if 任务们 is None:#缺任务服务
                raise Exception('background terminal sends require @deepseek-ai/dsh-jobs and @deepseek-ai/dsh-tool-jobs')#缺任务服务
            取消请求=[False]#是否已请求取消
            文本=取字段(参数,'text') or ''#写入文本
            def 任务体():#任务体
                """在 ctx.jobs 下拉起后台终端发送。"""
                操作=上下文.terminals.startSend(所有者,标识,请求)#开始发送
                结算=承诺()#任务done
                def 盯结算():#把发送结算映射成任务结局
                    """把操作 done 映射成任务结果。"""
                    try:#正常结算
                        结果=解开(取字段(操作,'done'))#等到结算
                        状态='killed' if 取消请求[0] else 'completed'#成功或被杀
                        结算.兑现({'status':状态,'detail':发送详情(结果)})#兑现结局
                    except BaseException as 错误:#失败
                        结算.兑现({'status':'failed','detail':str(错误)})#失败结局
                工作=threading.Thread(target=盯结算)#后台结算线程
                工作.daemon=True#不挡住退出
                工作.start()#启动
                def 取消():#取消
                    """请求打断后台发送。"""
                    取消请求[0]=True#记下取消
                    取消入口=取字段(操作,'cancel')#取消方法
                    if callable(取消入口):#可调用
                        取消入口()#打断发送
                def 读输出():#增量输出
                    """增量渲染后台发送输出。"""
                    读=取字段(操作,'readOutput')#读取方法
                    if callable(读):#可调用
                        增量=读()#读一次
                    else:#已是值
                        增量=读#原样
                    return 渲染发送读取(增量)#增量输出
                return {'cancel':取消,'done':结算,'readOutput':读输出}#交给任务收集器
            编号=任务们.start({#启动后台任务
                'kind':'pty-send',#任务种类
                'label':str(标识)+': '+(文本 if len(文本)>0 else '(input)'),#标签
                'owner':所有者,#所有者
                'outputLimitBytes':结果字节,#输出上限
                'run':任务体,#任务体
            })#jobs.start结束
            return {'kind':'background','jobId':编号}#立刻返回任务id
        前台请求=dict(请求)#拷贝请求
        前台请求['signal']=取字段(执行元数据,'signal')#前台发送带取消
        操作=上下文.terminals.startSend(所有者,标识,前台请求)#前台发送
        结果=解开(取字段(操作,'done'))#等待结算
        if 是否已中止(取字段(执行元数据,'signal')):#工具已取消
            raise Exception('terminal send aborted')#工具已取消
        return {'kind':'foreground',**结果}#前台结果
    def 渲染发送结果(_参数,值):#渲染发送结果
        """后台报任务 id，前台渲染视口。"""
        if 取字段(值,'kind')=='background':#后台
            文本='started background job '+str(取字段(值,'jobId'))#任务id
        else:#前台
            文本=渲染发送(值,结果字节)#前台视口
        return [{'type':'text','text':文本}]#文本块
    def 发送展示元(_参数,值):#前台才给元数据
        """前台才给元数据；后台为 null。"""
        if 取字段(值,'kind')!='foreground':#后台无元数据
            return None#无元数据
        return {#前台元数据
            'viewport':取字段(值,'viewport'),#视口
            'waitReason':取字段(值,'waitReason'),#等待原因
            'sessionStatus':取字段(值,'sessionStatus'),#会话状态
            'truncated':取字段(值,'truncated'),#是否截断
        }#元数据结束
    def 呈现发送(参数):#调用卡片
        """后台用通用卡，前台用终端卡。"""
        if 取字段(参数,'run_in_background') is True:#后台
            return {#通用卡片
                'card':'generic',#通用
                'title':'Send to terminal '+str(取字段(参数,'sessionId'))+' in background',#标题
                'kind':'execute',#执行
                'rawInput':取字段(参数,'text'),#原文
            }#后台卡片结束
        return {#终端卡片
            'card':'terminal',#终端
            'title':取字段(参数,'text') or '(send input)',#标题
            'description':'Terminal '+str(取字段(参数,'sessionId')),#描述
        }#前台卡片结束
    def 呈现发送结果(参数,结果):#结果卡片
        """后台或错误不渲染；否则终端输出卡。"""
        if 取字段(参数,'run_in_background') is True or 取字段(结果,'isError'):#后台或错误
            return None#不渲染
        原文=原文单文本(取字段(结果,'content'))#取出文本
        if 原文 is None:#无文本
            return None#不渲染
        return {'card':'terminal','output':原文}#终端输出卡
    发送参数={#发送参数
        'sessionId':{'type':'string','required':True,'description':'Terminal session id returned by terminal_open or terminal_list.'},#会话id
        'text':{'type':'string','required':True,'description':'UTF-8 text to write to the terminal.'},#写入文本
        'submit':{'type':'boolean','description':'Submit Enter after text (default true). Set false for control characters or incomplete REPL input.'},#是否回车
    }#parameters骨架
    if 后台启用:#启用后台时
        发送参数['run_in_background']={#后台参数
            'type':'boolean',#布尔
            'description':'Return a job id immediately; collect with job_output or stop with job_kill.',#后台说明
        }#后台参数结束
    发送描述=('Send text to a persistent terminal. By default Enter is submitted and the call waits for a prompt, stdin wait, output silence, timeout, or session exit.'#前台发送说明
        +(' Background mode returns a job id for job_output/job_kill.' if 后台启用 else ''))#后台开启时补一句
    上下文.tools.register(定义工具({#登记发送工具
        'name':'terminal_send',#工具名
        'description':发送描述,#描述
        'parameters':发送参数,#参数
        'finalizeContent':收口内容,#封顶
        'output':{#输出
            'schema':{#模式
                'oneOf':[#后台或前台
                    后台任务输出模式,#后台
                    {#前台
                        'type':'object',#对象
                        'additionalProperties':False,#禁止多余字段
                        'properties':{#字段
                            'kind':{'type':'string','required':True,'const':'foreground'},#种类固定foreground
                            'viewport':{'type':'string','required':True},#视口
                            'waitReason':{#等待原因
                                'type':'string',#字符串
                                'required':True,#必填
                                'enum':['stdin_read','inferred_idle','timeout','session_exit'],#允许值
                            },#waitReason结束
                            'sessionStatus':{**会话状态模式,'required':True},#会话状态
                            'truncated':{'type':'boolean','required':True},#是否截断
                        },#properties结束
                    },#前台结束
                ],#oneOf结束
            },#schema结束
            'render':渲染发送结果,#渲染发送结果
            'presentationMeta':发送展示元,#展示元数据
        },#output结束
        'execute':执行发送,#执行发送
        'presentCall':呈现发送,#调用卡片
        'presentResult':呈现发送结果,#结果卡片
    }))#terminal_send结束

    def 执行读取(参数,执行元数据):#执行读取
        """读回滚页，不发送输入。"""
        请求={}#回滚请求
        偏移=取字段(参数,'offset')#相对最新偏移
        if 偏移 is not None:#有偏移则带上
            请求['offset']=偏移#偏移
        行数=取字段(参数,'count')#行数
        if 行数 is not None:#有行数则带上
            请求['count']=行数#行数
        return 已兑现(上下文.terminals.read(#读回滚
            要求智能体(取字段(执行元数据,'agent')),#所有者
            会话标识(参数),#会话id
            请求,#回滚请求
        ))#read结束
    def 渲染读取结果(_参数,值):#渲染读取结果
        """渲染读取结果文本块。"""
        return [{'type':'text','text':渲染读取(值,结果字节)}]#渲染读取结果
    def 呈现读取(参数):#调用卡片
        """读取终端的通用卡片。"""
        return {'card':'generic','title':'Read terminal '+str(取字段(参数,'sessionId')),'kind':'read','rawInput':参数}#调用卡片
    上下文.tools.register(定义工具({#登记读取工具
        'name':'terminal_read',#工具名
        'description':'Read a bounded page of retained output from a persistent terminal without sending input.',#描述
        'parameters':{#参数
            'sessionId':{'type':'string','required':True,'description':'Terminal session id.'},#会话id
            'offset':{'type':'number','description':'Newest-relative line offset (default 0).'},#偏移
            'count':{'type':'number','description':'Requested line count (default 500; backend caps apply).'},#行数
        },#parameters结束
        'finalizeContent':收口内容,#封顶
        'output':{#输出
            'schema':{#模式
                'type':'object',#对象
                'additionalProperties':False,#禁止多余字段
                'properties':{#字段
                    'text':{'type':'string','required':True},#页文本
                    'totalLines':{'type':'integer','required':True},#总行数
                    'lineBegin':{'type':'integer','required':True},#起始行
                    'lineEnd':{'type':'integer','required':True},#结束行
                    'truncated':{'type':'boolean','required':True},#是否截断
                },#properties结束
            },#schema结束
            'render':渲染读取结果,#渲染读取结果
        },#output结束
        'execute':执行读取,#执行读取
        'presentCall':呈现读取,#调用卡片
    }))#terminal_read结束

    def 执行信号(参数,执行元数据):#执行发信号
        """投递允许的信号到前台进程组。"""
        return 已兑现(解开(上下文.terminals.signal(#交给注册表
            要求智能体(取字段(执行元数据,'agent')),#所有者
            会话标识(参数),#会话id
            取字段(参数,'signal'),#信号名
        )))#signal结束
    def 渲染信号结果(参数,值):#渲染投递结果
        """渲染信号投递结果。"""
        return [{'type':'text','text':'delivered '+str(取字段(参数,'signal'))+' to foreground process group '+str(取字段(值,'targetPgid'))}]#渲染投递结果
    def 呈现信号(参数):#调用卡片
        """发信号的通用卡片。"""
        return {'card':'generic','title':'Signal terminal '+str(取字段(参数,'sessionId')),'kind':'execute','rawInput':参数}#调用卡片
    上下文.tools.register(定义工具({#登记信号工具
        'name':'terminal_signal',#工具名
        'description':'Send an allowed signal to the current foreground process group of a persistent terminal.',#描述
        'parameters':{#参数
            'sessionId':{'type':'string','required':True,'description':'Terminal session id.'},#会话id
            'signal':{'type':'string','required':True,'enum':['SIGINT','SIGTERM','SIGKILL','SIGTSTP','SIGHUP'],'description':'Signal to deliver. Shell-targeted SIGKILL is rejected; use terminal_close.'},#信号
        },#parameters结束
        'finalizeContent':收口内容,#封顶
        'output':{#输出
            'schema':{#模式
                'type':'object',#对象
                'additionalProperties':False,#禁止多余字段
                'properties':{#字段
                    'delivered':{'type':'boolean','required':True,'const':True},#已投递
                    'targetPgid':{'type':'integer','required':True},#目标进程组
                },#properties结束
            },#schema结束
            'render':渲染信号结果,#渲染投递结果
        },#output结束
        'execute':执行信号,#执行发信号
        'presentCall':呈现信号,#调用卡片
    }))#terminal_signal结束

    def 执行关闭(参数,执行元数据):#执行关闭
        """关闭一次已拥有会话并等待进程树消失。"""
        标识=会话标识(参数)#会话id
        已关闭=解开(上下文.terminals.kill(#关闭
            要求智能体(取字段(执行元数据,'agent')),#所有者
            标识,#会话id
        ))#kill结束
        return 已兑现({#结局
            'sessionId':标识,#会话id
            'outcome':'closed' if 已关闭 else 'already-closing',#关闭结局
        })#返回结局
    def 渲染关闭结果(_参数,值):#渲染关闭结果
        """渲染关闭结果文本块。"""
        if 取字段(值,'outcome')=='closed':#新关闭
            文本='closed terminal session '+str(取字段(值,'sessionId'))#已关闭
        else:#已在关闭
            文本='terminal session '+str(取字段(值,'sessionId'))+' was already closing'#已在关闭
        return [{'type':'text','text':文本}]#文本块
    def 呈现关闭(参数):#调用卡片
        """关闭终端的通用卡片。"""
        return {'card':'generic','title':'Close terminal '+str(取字段(参数,'sessionId')),'kind':'delete'}#调用卡片
    上下文.tools.register(定义工具({#登记关闭工具
        'name':'terminal_close',#工具名
        'description':'Close one persistent terminal and wait until its captured owned process tree is gone.',#描述
        'parameters':{#参数
            'sessionId':{'type':'string','required':True,'description':'Terminal session id.'},#会话id
        },#parameters结束
        'finalizeContent':收口内容,#封顶
        'output':{#输出
            'schema':{#模式
                'type':'object',#对象
                'additionalProperties':False,#禁止多余字段
                'properties':{#字段
                    'sessionId':{'type':'string','required':True},#会话id
                    'outcome':{'type':'string','required':True,'enum':['closed','already-closing']},#关闭结局
                },#properties结束
            },#schema结束
            'render':渲染关闭结果,#渲染关闭结果
        },#output结束
        'execute':执行关闭,#执行关闭
        'presentCall':呈现关闭,#调用卡片
    }))#terminal_close结束

    def 执行列表(_参数,执行元数据):#执行列出
        """列出本所有者快照。"""
        return 已兑现(上下文.terminals.list(#本所有者快照
            要求智能体(取字段(执行元数据,'agent')),#所有者
        ))#list结束
    def 渲染列表结果(_参数,值):#渲染列表
        """渲染会话列表文本块。"""
        return [{'type':'text','text':渲染列表(值,结果字节)}]#渲染列表
    def 呈现列表():#调用卡片
        """列出会话的通用卡片。"""
        return {'card':'generic','title':'List terminal sessions','kind':'read'}#调用卡片
    上下文.tools.register(定义工具({#登记列表工具
        'name':'terminal_list',#工具名
        'description':'List persistent terminal sessions owned by the current agent.',#描述
        'parameters':{},#无参数
        'finalizeContent':收口内容,#封顶
        'output':{#输出
            'schema':{'type':'array','items':会话快照模式},#快照数组
            'render':渲染列表结果,#渲染列表
        },#output结束
        'execute':执行列表,#执行列出
        'presentCall':呈现列表,#调用卡片
    }))#terminal_list结束

apply=应用#Cordis插件入口

__all__=['名称','注入','应用','配置','Config','name','inject','apply']#公开面
