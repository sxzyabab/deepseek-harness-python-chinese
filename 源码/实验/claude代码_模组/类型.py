'模组面向的结构。字段名保持 Claude Code 原文，好让未改过的模组对得上'
from typing import Literal,NotRequired,TypedDict#结构类型

__all__=[
    '钩子来源','钩子失败','钩子预算','模组定义',
    '序列化元素','表面快照',
    '界面绘制输入','会话开始输入','会话开始结果','会话结束输入','会话结束结果',
    '提示提交输入','提示提交结果','回合开始输入','回合开始结果','回合用量','回合完成输入','回合完成结果',
    '工具调用输入','工具调用结果','命令运行输入','命令运行结果',
    '命令规格','命令信息','工具规格','工具信息','会话消息','工具使用摘要','会话用量','会话版本',
    '询问选项','界面日志选项','提示条选项','窗格打开参数','窗格打开结果','状态引用',
    '文件项','文件状态','进程运行初始','进程运行结果','请求初始','请求响应','提示提交参数',
]

class 钩子来源(TypedDict):
    '谁引发了事件'
    plugin:str
    tier:Literal['prepend','user','append','builtin','core']

class 钩子失败(TypedDict):
    '失败钩子在 next.error 上的样子'
    kind:Literal['throw','timeout']
    message:str

class 钩子预算(TypedDict):
    '钩子自己的运行时间上限'
    ms:int
    remainingMs:float

class 模组定义(TypedDict):
    '交给桥的一份模组'
    name:str
    register:object
    version:NotRequired[str]
    root:NotRequired[str]
    options:NotRequired[dict]

class 序列化元素(TypedDict):
    '回调已换成动作编号的元素'
    type:Literal['Box','Text','Button']
    props:dict
    children:list
    actionId:NotRequired[str]

class 表面快照(TypedDict):
    '提示上方一条带的一代画面'
    generation:int
    tree:list|None

class 界面绘制输入(TypedDict):
    'ui.render 的入参'
    component:Literal['AbovePrompt','Pane']
    surface:str
    props:dict
    viewport:dict
    requestId:NotRequired[str]

class 会话开始输入(TypedDict):
    'session.start'
    cwd:str
    surface:str|None
    isInteractive:bool

class 会话开始结果(TypedDict):
    'session.start 的结果'
    cwd:str

class 会话结束输入(TypedDict):
    'session.end'
    reason:Literal['clear','logout','prompt_input_exit','resume','other']
    sessionId:str

class 会话结束结果(TypedDict):
    'session.end 的结果'
    sessionId:str

class 提示提交输入(TypedDict):
    'prompt.submit'
    text:str
    wait:bool
    origin:dict
    context:NotRequired[list]
    turnId:NotRequired[str]

class 提示提交结果(TypedDict,total=False):
    'prompt.submit 的结果：改写文本，或丢掉并给出原因'
    text:str
    context:list
    drop:str

class 回合开始输入(TypedDict):
    'turn.start'
    text:str
    turnId:str
    agentId:NotRequired[str]

class 回合开始结果(TypedDict):
    'turn.start 的结果'
    turnId:str

class 回合用量(TypedDict):
    '一轮的 token 合计，字段用 Claude Code 的接口词'
    input_tokens:int
    output_tokens:int
    cache_read_input_tokens:int
    cache_creation_input_tokens:int
    model:str

class 回合完成输入(TypedDict):
    'turn.complete'
    turnId:str
    answer:str
    durationMs:int
    isAborted:bool
    reason:Literal['answer','aborted','error']
    agentId:NotRequired[str]
    usage:NotRequired[dict]

class 回合完成结果(TypedDict):
    'turn.complete 的结果。text 显示在回答下面'
    text:str

class 工具调用输入(TypedDict):
    'tool.call。参数字段和 tool 放在同一层'
    tool:str
    tool_use_id:str
    agentId:NotRequired[str]

class 工具调用结果(TypedDict,total=False):
    'tool.call 的结果：拒绝，或工具结果'
    deny:str
    result:object
    isError:bool

class 命令运行输入(TypedDict):
    'command.run'
    command:str
    args:str
    origin:dict

class 命令运行结果(TypedDict,total=False):
    'command.run 的结果'
    text:str

class 命令规格(TypedDict):
    '模组登记的命令'
    name:str
    description:str
    argumentHint:NotRequired[str]

class 命令信息(TypedDict):
    '命令列表里的一条'
    name:str
    description:str
    source:Literal['builtin','plugin','user','mcp']

class 工具规格(TypedDict):
    '模组登记的工具'
    name:str
    description:str
    inputSchema:NotRequired[dict]

class 工具信息(TypedDict):
    '工具列表里的一条'
    name:str
    description:str

class 工具使用摘要(TypedDict):
    '一条消息里的一次工具调用'
    tool_use_id:str
    tool:str
    input:dict

class 会话消息(TypedDict):
    '$.session.messages 的一条'
    role:Literal['user','assistant']
    text:str
    toolUses:list

class 会话用量(TypedDict):
    '上下文占用'
    startedAt:int
    context:dict
    rateLimits:list

class 会话版本(TypedDict):
    '$.session.version 报告的接口版本'
    version:str
    engine:Literal['deepseek-harness']

class 询问选项(TypedDict,total=False):
    '$.ui.ask 的选项'
    options:list
    header:str
    multiSelect:bool

class 界面日志选项(TypedDict,total=False):
    '$.ui.log 写到哪里'
    to:Literal['transcript','debug']

class 提示条选项(TypedDict,total=False):
    '$.ui.toast 的选项'
    timeoutMs:int

class 窗格打开参数(TypedDict):
    '$.ui.open'
    id:str

class 窗格打开结果(TypedDict):
    '这个宿主不放窗格'
    id:str
    isPlaced:bool
    reason:NotRequired[str]

class 状态引用(TypedDict):
    '$.state 的一条'
    plugin:str
    key:str

class 文件项(TypedDict):
    '$.fs.list 的一条'
    name:str
    kind:Literal['file','dir','other']
    size:int
    isLink:bool

class 文件状态(TypedDict):
    '$.fs.stat'
    kind:Literal['file','dir','other']
    size:int
    mtimeMs:int
    isLink:bool

class 进程运行初始(TypedDict,total=False):
    '$.process.run 的选项'
    cwd:str
    env:dict
    timeoutMs:int

class 进程运行结果(TypedDict):
    '$.process.run 的结果'
    exitCode:int
    stdout:str
    stderr:str

class 请求初始(TypedDict,total=False):
    '$.http.fetch 的选项'
    method:str
    headers:dict
    body:str
    timeoutMs:int

class 请求响应(TypedDict):
    '$.http.fetch 读完正文后的结果'
    status:int
    ok:bool
    headers:dict
    text:str

class 提示提交参数(TypedDict):
    '$.prompt.submit'
    text:str
    asUser:NotRequired[bool]
