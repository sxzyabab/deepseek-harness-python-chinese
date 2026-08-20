"""技能能力缝的共享类型面：目录摘要/候选/定义、提供方约定、查找选项、用户显式调用的消息来源，以及 seam 的 Cordis 事件声明。仅类型——没有运行时代码；线协议字段名与上游 JS 对齐，公开类型名为中文。"""
from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型

技能调用来源种类='skill-invocation'#用户显式技能调用的 MessageSource 判别标签
技能调用形态='instructions'#注入正文是模型应遵循的指令

技能调用源字段=(#用户显式技能调用注入的上下文消息来源
    'kind',#固定为 skill-invocation
    'name',#在注入边界已校验为用户可调用的技能名
    'form',#固定为 instructions
)#技能调用源字段结束

class 技能调用来源(TypedDict):#用户显式技能调用注入的上下文消息来源；用户原话走普通用户消息，渲染后的技能正文作为带此来源的 instructions 形态跟在后面
    kind:Literal['skill-invocation']#来源判别标签
    name:str#被调用的技能名，在注入边界已校验为用户可调用
    form:Literal['instructions']#注入正文是模型应遵循的指令

# 技能贡献的来源桶。该值是提示词可见元数据，本身不决定优先级；可扩展为任意字符串。
技能来源已知=(#已知来源标签；开放字符串仍合法
    'project-dsh',#项目 .dsh/skills
    'project-agents',#项目 .agents/skills
    'runtime',#运行时嵌入
    'user-dsh',#用户 .dsh/skills
    'user-agents',#用户 .agents/skills
    'custom',#自定义根
    'bundled',#捆绑根
)#已知来源结束

技能资源基址种类=('directory','url','opaque')#相对资源基址的三种形态

class 技能资源基址目录(TypedDict):#本地目录基址
    kind:Literal['directory']#目录臂
    path:str#基目录绝对路径

class 技能资源基址网址(TypedDict):#URL 基址
    kind:Literal['url']#网址臂
    url:str#基 URL

class 技能资源基址不透明(TypedDict):#不透明描述基址
    kind:Literal['opaque']#不透明臂
    description:str#面向模型的资源描述

class 技能调用策略(TypedDict):#模型面/用户面是否可调用；提供方在每个候选与定义中返回已解析形状
    modelInvocable:bool#面向模型的目录与加载器是否包含此技能
    userInvocable:bool#面向人的命令目录与加载器是否包含此技能

class 技能摘要(TypedDict):#ctx.skills.列出()/快照() 返回的、与调用面无关的技能元数据
    name:str#kebab-case 标识符
    description:str#发现消费方展示的短路由描述
    whenToUse:NotRequired[str]#可选的额外路由指引
    invocation:技能调用策略#已解析的模型与用户调用控制
    source:str#产出此胜出技能的发现来源桶
    provider:str#拥有此技能正文的提供方名
    resourceBase:NotRequired[dict]#相对资源的提供方专用基址（三臂之一）

class 技能候选(技能摘要):#提供方目录条目，供注册表合并并随后加载
    rank:float#层内优先排名；较低先胜
    locator:object#不透明的提供方自有句柄，回传给 provider.get()
    path:NotRequired[str]#提供方有绝对路径时给出
    metadata:NotRequired[dict]#从提供方专用 frontmatter 解析出的可选元数据

class 技能定义(技能摘要):#完整解析后的技能定义，含 ctx.skills.获取() 加载的正文
    content:str#去掉提供方专用元数据后的 Markdown 指令正文
    path:NotRequired[str]#技能来自磁盘时的绝对路径
    metadata:NotRequired[dict]#从 frontmatter 解析出的可选元数据

class 技能注册输入(TypedDict):#ctx.skills.登记() 接受的运行时技能贡献；invocation/provider 可省略
    name:str#kebab-case 技能名
    description:str#路由描述
    content:str#指令正文
    source:str#来源桶
    whenToUse:NotRequired[str]#可选何时使用
    invocation:NotRequired[技能调用策略]#省略则模型面与用户面都允许
    provider:NotRequired[str]#省略则用注册表自有的 runtime 提供方
    resourceBase:NotRequired[dict]#可选资源基址
    path:NotRequired[str]#可选磁盘路径
    metadata:NotRequired[dict]#可选元数据

class 技能查找选项(TypedDict):#供对 cwd 敏感且可取消的提供方工作使用的调用方上下文
    cwd:NotRequired[str]#当前查找的工作区选择器
    signal:NotRequired[object]#中止当前调用方的发现或加载工作

class 技能视图选项(技能查找选项):#注册表读取选项：提供方查找上下文加上观察作用域
    scope:NotRequired[object]#观察作用域（调用方智能体）；省略则只读全局层

class 技能目录快照(TypedDict):#一次目录观察，以及发现是否在稳定的目录修订内完成
    skills:list#本次观察收集到的、已排序的、与调用面无关的摘要
    complete:bool#是否每个已注册提供方都在无并发目录修订的情况下完成

class 技能提供方观察(TypedDict):#提供方候选，以及当前发现是否具权威性
    candidates:list#当前提供方发现可用的候选
    complete:bool#发现是否完成，且这些候选可否缓存

class 技能提供方控制(TypedDict):#一个提供方借用的、绑定到此次注册的生命周期与失效能力
    signal:object#注册失败或恰好这次提供方注册被拆除时中止
    invalidate:object#仅在恰好这次注册仍活跃时，使已完成目录失效并通知消费方

class 技能配置(TypedDict):#技能注册表可配置项
    collectCacheMaxEntries:NotRequired[int]#内存中保留的已完成 cwd/提供方目录的最大数量

技能提供方字段=('name','list','get')#提供方约定字段；list/get 键名与上游 JS SkillProvider 对齐，经登记提供方同步注册

class 技能提供方:#一种技能来源的提供方接口，例如本地目录或远程注册表；字段由实例或映射赋值
    """具名提供方约定。线协议仍用 list/get 键；本类用中文方法名描述同一能力。"""
    name=None#在 ctx.skills 注册表中的唯一提供方名

    def 列出(自身,选项):#列出当前查找上下文可用的技能候选
        """列出候选；远程初始化与发现在本方法内等待。应在 options.signal 中止时尽快结束。"""
        raise NotImplementedError('SkillProvider.list')#由提供方实现

    def 获取(自身,候选,选项):#为先前列出的候选加载完整技能正文
        """加载完整正文；已不可加载则返回 None。"""
        raise NotImplementedError('SkillProvider.get')#由提供方实现

# 事件 skills/change() @mode emit：技能提供方、运行时贡献或提供方支持的目录可能已变化。这是未过滤的失效通知；消费方按自己的查找选项重新拉取目录（快照）。监听器失败（同步抛出与异步拒绝一样）被收容并记日志，不能否决注册表变更，也不能阻止后续监听器执行。无参数。
