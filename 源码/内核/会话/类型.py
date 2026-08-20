"""会话身份、磁盘格式版本与事件词汇的运行时常量。对齐上游 `session/src/types.ts`。公开面仅中文名。"""
from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型

安全整数上限=9007199254740991#JS Number.MAX_SAFE_INTEGER

__all__=[#仅中文公开名
    '会话标识','会话格式版本','是否安全整数','会话头字段','会话头',
    '创建会话选项','恢复会话选项','准备会话选项',
    '智能体取消原因','轮次结束取消原因','轮次结束原因映射','轮次结束原因',
    '待办状态','待办条目','纪元请求头','请求上下文','请求头原因',
    '核心会话事件类型','表面事件类型','表面操作','表面意图','会话事件信封字段',
]#公开面结束

def 会话标识(标识):#品牌会话 id
    """把字符串标成会话标识，不做校验。"""
    return 标识#编译期品牌在 Python 中无运行时成本

会话格式版本=0#磁盘格式版本，未发布期间钉在 0

def 是否整数(值):#对齐 JS Number.isInteger
    """对齐 JS Number.isInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是数字
    if isinstance(值,int):#整数
        return True#整数
    if isinstance(值,float):#浮点
        return 值.is_integer()#整值浮点
    return False#其它类型

def 是否安全整数(值):#对齐 JS Number.isSafeInteger
    """对齐 JS Number.isSafeInteger。"""
    if not 是否整数(值):#不是整数
        return False#不是整数
    return abs(值)<=安全整数上限#落在安全范围

#不可变的已校验存储元数据，放在对话事件日志之外（对齐上游 SessionHeader；本包拥有，持久化只再导出）。
会话头字段=(#会话头字段键表
    'version',#磁盘格式版本，创建时从会话格式版本盖上
    'id',#会话 id（镜像 Session.id）
    'createdAt',#创建时的非负安全整数 Unix 纪元毫秒
    'cwd',#可选：创建时所在绝对工作目录
    'parentSession',#可选：分叉自的父会话 id
    'seedLength',#可选：经种子继承的前导事件条数
    'origin',#可选：来源分类，仅允许 "subagent"
    'delegationDepth',#可选：委托深度（顶层缺省为零）
    'agentPreset',#可选：本会话 Agent 组合自的预设 id
)#会话头字段结束

class 会话头(TypedDict):#不可变已校验存储元数据
    version:int#磁盘格式版本
    id:str#会话 id（会话标识品牌）
    createdAt:int#创建时 Unix 纪元毫秒
    cwd:NotRequired[str]#可选绝对工作目录
    parentSession:NotRequired[str]#可选父会话 id
    seedLength:NotRequired[int]#可选种子边界条数
    origin:NotRequired[Literal['subagent']]#可选来源分类
    delegationDepth:NotRequired[int]#可选委托深度
    agentPreset:NotRequired[str]#可选 Agent 预设 id

class 创建会话选项(TypedDict):#经存储创建会话的选项
    seed:NotRequired[list]#可选初始回放或分叉历史
    meta:NotRequired[dict]#发表前读一次的存储元数据字段

class 恢复会话选项(TypedDict):#持久化移交的新鲜存储值，不再二次序列化拷贝
    seed:list#要就地校验并冻结的新鲜脱离事件
    meta:会话头#要就地校验并冻结的新鲜脱离元数据
    seedSource:Literal['persistence']#选择持久化所有权转移路径

准备会话选项=创建会话选项|恢复会话选项#构造尚未发表会话时接受的输入

智能体取消原因=Literal['user','parent','hook','disposed']#活动 Agent 驱动器为何被取消（hook 另带 reason 字符串）
轮次结束取消原因=智能体取消原因|Literal['legacy']#可持久化取消原因，含无原因的导入

轮次结束原因映射={#一轮为何结束；可合并扩展的和类型（键为 reason.kind）
    'completed':{'kind':'completed'},#正常完成
    'aborted':{'kind':'aborted'},#取消请求打断在线轮次；另带 reason
    'blocked':{'kind':'blocked'},#预步骤拒绝
    'error':{'kind':'error'},#轮次失败；另带结构化 error
    'max-tokens':{'kind':'max-tokens'},#至少一步到达输出 token 上限
    'interrupted':{'kind':'interrupted'},#持久化后端关闭崩溃孤儿轮次
}#轮次结束原因映射结束
轮次结束原因=Literal['completed','aborted','blocked','error','max-tokens','interrupted']#轮次结束原因联合

待办状态=('pending','in_progress','completed')#待办生命周期三态，无 id

def 待办条目(内容,状态):#构造一条待办
    """一条待办：短祈使内容和三态状态。整表替换所以不需要稳定身份。"""
    return {'content':内容,'status':状态}#一条待办快照

class 纪元请求头(TypedDict):#派生历史之外的已记下请求状态
    config:object#调用配置（提供方、模型、推理力度与采样标量）
    adapterDefaults:NotRequired[dict]#由精确适配器物化的有效配置字段旗标
    system:NotRequired[str]#渲染后的系统提示词；无则缺省
    tools:NotRequired[list]#组装后的工具模式；无则缺省

class 请求上下文(TypedDict):#一条已解析模型路由的注册绑定元数据
    provider:str#已注册提供方路由
    model:str#提供方拥有的模型 id
    contextWindow:NotRequired[int]#广告的最大请求加响应上下文 token 数

请求头原因=Literal['initial','resume','change']#为何追加 request/header：首条 / 恢复首请求 / 后续变更

核心会话事件类型=(#SessionEventMap 核心键；插件可合并扩展更多类型
    'turn/start',#打开轮次
    'turn/end',#以轮次结束原因关闭轮次
    'step/start',#打开步骤（一次模型调用及其工具）
    'step/end',#关闭步骤
    'user/message',#模型可见用户角色消息
    'assistant/chunk',#原始流块
    'assistant/message',#组装好的助手消息（派生历史用）
    'tool/call',#模型请求的工具调用
    'tool/result',#工具结果（可进表面）
    'todo/write',#整表待办快照
    'request/header',#完整请求头快照
    'request/context',#路由元数据
    'session/end-seed',#构造种子结束标记
)#核心会话事件类型结束

表面事件类型=('user/message','assistant/message','tool/result')#产出 LLM 消息、可进有序表面的子集
表面操作=Literal['append']|dict#追加，或 {op:'replace',start,end} 区间替换

class 表面意图(TypedDict):#追加时的表面放置与所引用源事件序号
    surfaceOp:object#表面操作（追加或替换）
    sourceEventSeqs:NotRequired[list]#已知源事件序号；助手消息允许空数组

会话事件信封字段=('type','seq','time','data','surfaceOp','sourceEventSeqs','ignorable')#固定事件信封键
