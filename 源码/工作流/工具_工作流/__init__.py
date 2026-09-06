"""面向模型的 `workflow` 工具：运行一份向外扇出子智能体的 JavaScript 编排脚本，并返回脚本的最终值。它拥有面向模型的模式与运行生命周期；脚本解析、执行、上限与取消放在 `ctx.workflowEngine`（`@deepseek-ai/dsh-workflow`）后面，因此换上加固引擎不必改动模型所见。执行会等待运行结果并始终销毁运行；非 completed 原因变成工具错误，后台收集仍推迟。展示是仅依赖 args 的通用卡片，标题来自 `meta.name`。显式询问的用法指引登记为工具自己的提示词段落，而不是部署人设散文。"""
import json#结果 JSON 渲染
from ...依赖.schemastery import 字符串字段,自然数字段#配置字段
from ...内核.工具 import 定义工具#导入工具定义辅助

__all__=[#仅中文公开名；Cordis 英文槽不入表
    '名称','注入','配置','描述','渲染记录错误',
    '创建工作流记录器','呈现工作流调用','呈现工作流结果','停止原因错误',
    '渲染结果','解析配置','应用','工作流工具错误',
]#公开面结束

名称='tool-workflow'#Cordis 插件名
注入=['tools','workflowEngine','systemPrompt']#依赖工具、工作流引擎与系统提示词
配置={#插件配置：面向模型的工具名以及结果渲染上限
    'toolName':字符串字段(默认值='workflow'),#要登记的面向模型的工具名（默认 workflow）
    'maxResultChars':自然数字段(最小=1,默认值=50_000),#渲染结果的字符上限（默认 50000）
}#配置模式结束

class 工作流工具错误(Exception):#面向模型的工作流工具失败
    """面向模型的工作流工具失败。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        Exception.__init__(自身,消息)#英文消息

# 脚本编写约定，嵌在工具描述里。这就是面向模型的规格：meta 块、钩子及其精确语义、以及受支持的模式子集。字面量保持原文。
描述=(#面向模型的工具描述
    'Run a JavaScript workflow script that orchestrates subagents at scale. Use this for work that fans out across many independent pieces — an audit over many files, a migration, multi-angle research, adversarial verification of findings — where you write the orchestration as a script instead of delegating turn by turn.\n\n'#用脚本编排大规模扇出子智能体
    +"The workflow's identity rides the `meta` parameter as JSON: required `name` (short kebab-case) and `description` strings, optional `whenToUse` string and `phases` array (`{title, detail?, provider?, model?}`). The `script` parameter is the plain JavaScript body ONLY (NOT TypeScript, and NO `export const meta` statement — meta is a parameter, not code), running with top-level await; end with `return <value>` — the value must be JSON-serializable and is this tool's result.\n\n"#meta 参数与纯 JS 脚本体约定
    +'Script-body hooks:\n'#脚本体内可用钩子列表
    +'- `agent(prompt, opts?): Promise<any>` — run one subagent to completion. Without `opts.schema` it resolves to the child\'s final text; with `opts.schema` (an object-rooted JSON Schema using ONLY type/properties/required/additionalProperties/items/enum/const/oneOf — no pattern/format/numeric bounds) it resolves to the validated object. Resolves `null` when the child fails (filter with `.filter(Boolean)`). Other opts: `label` (display), `phase` (progress group), and independent `provider`/`model` LLM target overrides (either may be provided alone). Anything else (`effort`/`isolation`/`agentType`) is rejected loudly.\n'#agent 钩子：跑完一个子智能体
    +'- `pipeline(items, ...stages): Promise<any[]>` — run each item through the stages independently with NO barrier between stages (prefer this for multi-stage work). Each stage receives `(prev, item, index)`. An ordinary stage throw drops that ITEM to `null` and skips its remaining stages.\n'#pipeline 钩子：无屏障多阶段
    +'- `parallel(thunks): Promise<any[]>` — run zero-argument functions concurrently and await ALL of them (a barrier; use only when a stage genuinely needs every prior result together). A throwing thunk resolves to `null`.\n'#parallel 钩子：并发屏障
    +'- `phase(title)` — start a progress phase; `log(message)` — narrate progress; `args` — the tool call\'s `args` input, verbatim.\n\n'#phase/log/args 辅助钩子
    +'Misused hooks (bad arguments, unknown options, unsupported schemas, tripped caps) throw errors that ALWAYS kill the script — they never dissolve into a per-item `null`.\n\n'#误用钩子一律杀死脚本
    +'Constraints: concurrency and total-agent caps apply; no filesystem, network, timers, or Node.js APIs are provided — the agents do the work, the script only coordinates them. The run executes in the foreground: this call returns when the whole script finishes.'#上限、无宿主 API、前台等待整脚本结束
)#描述结束

def 按utf8字节截断(文本,最大字节):#按 UTF-8 字节截断且切在字符边界
    """按 UTF-8 字节上限截断，切点落在字符边界。返回截断后的文本与被丢掉的字节数。"""
    数据=文本.encode('utf-8')#UTF-8 字节
    if len(数据)<=最大字节:#未超预算；判 length
        return 文本,0#原样
    切片=数据[:最大字节]#先按字节切开
    while len(切片)>0 and (切片[-1] & 0xC0)==0x80:#去掉不完整字符的续字节
        切片=切片[:-1]#回退
    if len(切片)>0 and (切片[-1] & 0xC0)==0xC0:#去掉不完整的首字节
        切片=切片[:-1]#回退
    return 切片.decode('utf-8'),len(数据)-len(切片)#截断文本与丢掉的字节数

def 渲染记录错误(错误):#把记录失败渲染成可记录字符串
    """渲染被收容的记录失败，不信任抛出值。"""
    try:#尝试强制转为字符串
        return str(错误)#返回字符串形式
    except Exception:#str() 对任意抛出值没有收窄契约
        return '[unrenderable thrown value]'#转换失败时返回固定标签

def 创建工作流记录器(上下文):#创建会话记录器
    """把活跃的顶层工作流运行投影进其父 Session，且不让记录失败影响工具执行。"""
    活跃={}#运行 id 到父会话

    def 追加(会话,类型,数据):#向会话追加一条本包记录事件
        """成功追加返回真。会话是对象，数据是 dict。"""
        try:#尝试写入会话日志
            会话.追加(类型,数据)#追加记录事件
            return True#写入成功
        except Exception as 错误:#追加可抛会话错误
            上下文.日志.警告('tool-workflow: disabled durable record after '+类型+' append failed: '+渲染记录错误(错误))#记录失败后关掉该运行的持久记录
            return False#写入失败

    def 智能体开始(信息,智能体,*其余):#把智能体开始投影为会话记录
        """投影 workflow/agent-start。信息与智能体都是 dict。"""
        _=其余#额外参数不用
        会话=活跃[信息['id']] if 信息['id'] in 活跃 else None#查找该运行的父会话
        if 会话 is None:#未在记录的运行直接跳过
            return#跳过
        数据={#组装成员开始载荷
            'runId':信息['id'],#运行标识
            'seq':智能体['seq'],#成员序号
            'label':智能体['label'],#展示标签
            'childId':智能体['childId'],#子会话标识
        }#结束基础载荷
        if 'phase' in 智能体 and 智能体['phase'] is not None:#有阶段才写入 phase
            数据['phase']=智能体['phase']#阶段
        if 追加(会话,'tool-workflow/agent-start',数据) is False:#追加失败
            活跃.pop(信息['id'],None)#停止跟踪该运行

    def 智能体结束(信息,智能体,*其余):#把智能体结束投影为会话记录
        """投影 workflow/agent-end。信息与智能体都是 dict。"""
        _=其余#额外参数不用
        会话=活跃[信息['id']] if 信息['id'] in 活跃 else None#查找该运行的父会话
        if 会话 is None:#未在记录的运行直接跳过
            return#跳过
        数据={#组装成员结束载荷
            'runId':信息['id'],#运行标识
            'seq':智能体['seq'],#成员序号
            'outcome':智能体['outcome'],#成员结局
        }#结束成员结束载荷
        if 追加(会话,'tool-workflow/agent-end',数据) is False:#追加失败
            活跃.pop(信息['id'],None)#停止跟踪该运行

    上下文.监听('workflow/agent-start',智能体开始)#把智能体开始投影为会话记录
    上下文.监听('workflow/agent-end',智能体结束)#把智能体结束投影为会话记录

    def 开始(会话,运行):#开始跟踪一次运行
        """开始跟踪一次运行。运行是对象。"""
        if 追加(会话,'tool-workflow/run-start',{'runId':运行.id,'name':运行.meta['name']}):#先写运行开始记录
            活跃[运行.id]=会话#成功后登记父会话

    def 完成(运行号,停止原因):#写运行结束并停止跟踪
        """写运行结束并停止跟踪。"""
        会话=活跃[运行号] if 运行号 in 活跃 else None#查找父会话
        if 会话 is not None:#仍在跟踪
            追加(会话,'tool-workflow/run-end',{'runId':运行号,'stopReason':停止原因})#写结束记录
        活跃.pop(运行号,None)#无论是否写入都停止跟踪

    def 放弃(运行号):#丢弃跟踪，不再写结束
        """丢弃跟踪，不再写结束。"""
        活跃.pop(运行号,None)#丢掉跟踪

    return {#返回记录器三方法
        '开始':开始,#开始
        '完成':完成,#结束
        '放弃':放弃,#放弃
    }#结束记录器对象

def 呈现工作流调用(参数):#渲染调用中卡片
    """进行中卡片：按工作流 meta 名标题的通用卡片。参数是 dict。"""
    return {#返回通用卡片视图
        'card':'generic',#通用卡片
        'title':'workflow: '+str(参数['meta']['name']),#标题带工作流名
        'rawInput':参数['script'],#原始脚本作为输入展示
    }#结束调用视图

def 呈现工作流结果(参数,结果):#渲染完成后卡片
    """完成态卡片：保留进行中标题；结果内容原样渲染。"""
    _=参数#展示不依赖参数
    _=结果#展示不依赖结果内容
    return {'card':'generic'}#只声明仍用通用卡片

def 停止原因错误(结果):#把停止原因映射为工具错误文案
    """非 `completed` 的停止原因表示脚本没有干净结束。结果是 dict。"""
    停止原因=结果['stopReason']#取出停止原因
    if 停止原因=='completed':#干净完成
        return None#不报错
    if 停止原因=='cancelled':#被取消
        错误=结果['error'] if 'error' in 结果 else None#可选错误文案
        return 'workflow run was cancelled'+(' ('+str(错误)+')' if 错误 is not None else '')#取消文案
    if 停止原因=='error':#脚本或引擎失败
        错误=结果['error'] if 'error' in 结果 else None#可选错误文案
        return 'workflow run failed: '+(str(错误) if 错误 is not None else 'unknown error')#失败文案
    return 'workflow run ended abnormally ('+str(停止原因)+')'#未知停止原因

def 渲染结果(名称值,已启动智能体数,返回值,最大字节):#把结果格式化成模型可见文本
    """渲染运行结局文本：meta 名、智能体计数、以及（有上限的）JSON 值。上限按 UTF-8 字节。"""
    已渲=json.dumps(返回值,ensure_ascii=False,separators=(',',':'),allow_nan=False,indent=2)#把返回值格式化成缩进 JSON
    已渲,丢掉=按utf8字节截断(已渲,最大字节)#按字节截断
    if 丢掉>0:#超限
        已渲=已渲+'\n… [truncated: '+str(丢掉)+' more bytes]'#附剩余字节数
    复数='' if 已启动智能体数==1 else 's'#英文复数
    return 'workflow "'+名称值+'" completed ('+str(已启动智能体数)+' agent'+复数+').\nReturn value:\n'+已渲#拼出完成摘要

def 解析配置(配置值):#取出已解析配置
    """schemastery 已填好带默认值的字段；此步骤记录该解析，不是隐藏回退。配置值是 dict。"""
    工具名=配置值['toolName'] if 'toolName' in 配置值 else 'workflow'#工具名
    最大字节=配置值['maxResultChars'] if 'maxResultChars' in 配置值 else 50000#结果字节上限（字段名沿用上游）
    return {'toolName':工具名,'maxResultChars':最大字节}#已解析

def 应用(上下文,配置值=None):#登记工作流工具与用法段落
    """登记面向模型的工作流工具与用法段落。配置值是 dict。"""
    if 配置值 is None:#无配置
        配置值={}#空配置
    已解析=解析配置(配置值)#取出已解析配置
    工具名=已解析['toolName']#工具名
    最大字节=已解析['maxResultChars']#结果字节上限
    记录器=创建工作流记录器(上下文)#创建会话记录器
    上下文.systemPrompt.段落({#登记工具用法段落
        'name':'tool:'+工具名,#段落名跟工具名
        'order':115,#段落顺序
        'text':'Use the '+工具名+' tool ONLY when the user explicitly asks for a workflow or for large multi-agent orchestration: you write a JavaScript script (the tool description documents the exact format) that fans work out across many subagents with phases and structured results. For one or two delegations, prefer plain subagent calls.',#仅在用户明确要求时使用
    })#结束段落登记

    def 渲染输出(参数,值):#把结构化结果渲成文本块
        """把结构化结果渲成文本块。参数与值都是 dict。"""
        return [{#文本块数组
            'type':'text',#文本块
            'text':渲染结果(参数['meta']['name'],值['agentsStarted'],值['result'],最大字节),#按上限渲染
        }]#结束文本块数组

    def 执行(参数,执行上下文):#执行一次工作流工具调用
        """启动工作流运行并等待结算。参数与执行上下文都是 dict。"""
        if 'agent' not in 执行上下文 or 执行上下文['agent'] is None:#没有调用方智能体
            raise 工作流工具错误('workflow tool requires a calling agent (exec.agent was undefined)')#缺少父智能体则失败
        父智能体=执行上下文['agent']#取出调用方智能体
        信号=执行上下文['signal'] if 'signal' in 执行上下文 else None#工具取消信号
        启动请求={#启动工作流运行请求
            'script':参数['script'],#脚本正文
            'meta':参数['meta'],#身份块
            'parent':父智能体,#父智能体
            'signal':信号,#工具取消信号
        }#结束基础请求
        if 'args' in 参数 and 参数['args'] is not None:#有 args 才传入
            启动请求['args']=参数['args']#脚本输入
        运行=上下文.workflowEngine.启动(启动请求)#启动工作流运行
        写记录=('parent' not in 执行上下文) or (执行上下文['parent'] is None)#仅顶层调用才写持久记录
        if 写记录:#顶层调用开始记录
            记录器['开始'](父智能体.session,运行)#开始记录
        结果=None#结算结果，finally 里再读
        try:#等待运行结算
            结果=运行.结果.等待()#等待脚本结算
            错误文案=停止原因错误(结果)#非干净结束则得到错误文案
            if 错误文案 is not None:#需要报成工具错误
                raise 工作流工具错误(错误文案)#抛出停止原因
            return {#返回结构化成功结果
                'runId':运行.id,#运行标识
                'agentsStarted':结果['agentsStarted'],#智能体计数
                'result':结果['value'],#脚本返回值
            }#结束成功结果
        finally:#无论成败都清理
            try:#等待销毁并写结束记录
                运行.销毁()#等待脚本与子运行静止
                if 写记录:#顶层调用需要写结束记录
                    if 结果 is None:#约定上结果必已赋值
                        raise 工作流工具错误('workflow run settled without a result')#缺少结果
                    记录器['完成'](运行.id,结果['stopReason'])#写入运行结束
            finally:#销毁后再丢掉跟踪
                if 写记录:#确保不再向已结束运行写事件
                    记录器['放弃'](运行.id)#放弃跟踪

    上下文.tools.register(定义工具({#登记面向模型的工作流工具
        'name':工具名,#工具名
        'description':描述,#工具描述
        'parameters':{#参数模式
            'script':{#脚本参数
                'type':'string',#字符串
                'required':True,#必填
                'description':'The plain-JS workflow script body (top-level await allowed; NO `export const meta` statement; end with `return <json-value>`).',#脚本说明
            },#结束脚本参数
            'meta':{#身份参数
                'type':'object',#对象
                'additionalProperties':True,#允许额外字段
                'required':True,#必填
                'description':'The workflow identity block (plain JSON — never code).',#身份块说明
                'properties':{#身份字段
                    'name':{'type':'string','required':True,'description':'Short kebab-case workflow name.'},#名称
                    'description':{'type':'string','required':True,'description':'One-line description of what the workflow does.'},#描述
                    'whenToUse':{'type':'string','description':'Optional guidance on when this workflow applies.'},#适用场景
                    'phases':{#阶段列表
                        'type':'array',#数组
                        'description':'Optional phase declarations matched by phase() calls.',#阶段说明
                        'items':{#阶段项
                            'type':'object',#对象
                            'additionalProperties':True,#允许额外字段
                            'properties':{#阶段字段
                                'title':{'type':'string','required':True,'description':'The phase title phase() calls match by exact string.'},#标题
                                'detail':{'type':'string','description':'Optional one-line description of the phase.'},#细节
                                'provider':{'type':'string','description':'Optional provider override this phase is expected to use.'},#提供方
                                'model':{'type':'string','description':'Optional model override this phase is expected to use.'},#模型
                            },#结束阶段字段
                        },#结束阶段项
                    },#结束阶段列表
                },#结束身份字段
            },#结束身份参数
            'args':{#脚本输入
                'type':'object',#对象
                'additionalProperties':True,#允许额外字段
                'description':'Optional JSON input exposed to the script as the `args` global (wrap a bare list as a field, e.g. {"files": [...]}).',#args 说明
            },#结束脚本输入
        },#结束参数模式
        'output':{#输出模式
            'schema':{#结果 JSON 模式
                'type':'object',#对象
                'additionalProperties':False,#禁止额外字段
                'properties':{#结果字段
                    'runId':{'type':'string','required':True},#运行标识
                    'agentsStarted':{'type':'integer','required':True},#智能体计数
                    'result':{'type':'json','required':True},#脚本返回值
                },#结束结果字段
            },#结束结果模式
            'render':渲染输出,#把结构化结果渲成文本块
        },#结束输出模式
        'execute':执行,#执行一次工作流工具调用
        'presentCall':呈现工作流调用,#调用中展示
        'presentResult':呈现工作流结果,#完成后展示
    }))#结束工具登记

name=名称#Cordis 插件名槽
inject=注入#Cordis 依赖槽
Config=配置#Cordis 配置槽
apply=应用#Cordis 入口槽
