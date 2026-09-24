"""循环、会话日志与插件共用的规范、提供方中立消息与流式词表。

公开面仅中文名；块 type／字段键为线协议原样保留。
"""
import threading#取消通道
from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型

__all__=(#仅中文公开名；无英文别名
    '中止信号',
    '语言模型失败',
    '文本块','推理块','图片块','文件块','工具调用块','工具追加块','工具移除块',
    '用户消息来源','模型消息来源','工具消息来源','系统提示词消息来源','消息来源',
    '消息','用户消息','助手消息','系统消息','开发者消息','工具结果消息','请求用户输入',
    '文本模态','图片模态','模型模态',
    '正常停止','工具调用停止','达到令牌上限',
    '令牌用量','图片请求价格','提供方简介','可配置提供方',
    '模型发现请求','发现到的模型','模型信息','模型上下文',
    '推理力度信息','模型推理信息','已解析模型信息',
    '系统提示词更新','图片请求预算','回放信封','工具模式','生成选项',
)#公开面结束

class 中止信号:
    """调用方取消通道；深冻结必须跳过，以免破坏中止。"""
    def __init__(自身,已中止标志=False):
        """创建一条取消通道。"""
        自身._事件=threading.Event()#中止旗标
        自身._异常=None#中止时抛出的异常
        if 已中止标志:#创建时已中止
            自身._事件.set()#置位

    def 触发(自身,原因=None):
        """标记中止。"""
        if 自身._事件.is_set():#只触发一次
            return#已触发
        if isinstance(原因,BaseException):#已是异常
            自身._异常=原因#承载
        自身._事件.set()#置位

class 语言模型失败(TypedDict):#可序列化提供方或传输失败事实
    """可序列化的提供方或传输失败事实；政策决定它们是否可重试。"""
    message:str#人类可读失败摘要
    code:str#稳定提供方中立机器路由码
    status:NotRequired[int]#提供方 HTTP 状态（若有）
    providerRetryAfterMs:NotRequired[float]#提供方请求的延迟毫秒
    requestId:NotRequired[str]#不透明提供方签发请求标识
    offloadImages:NotRequired[int]#还需卸载的最旧保留出现张数

class 文本块(TypedDict):#对最终用户可见的纯文本
    """对最终用户可见的纯文本。"""
    type:Literal['text']#文本标签
    text:str#文本内容

class 推理块(TypedDict):#推理/思考内容
    """推理/思考内容，与可见文本分开。"""
    type:Literal['reasoning']#推理标签
    text:str#推理文本

class 图片块(TypedDict):#持久栅格图片引用
    """持久的栅格图片引用，在用户或助手内容里都合法。"""
    type:Literal['image']#图片标签
    attachment:object#附件服务拥有的不可变字节与固有显示元数据
    offloaded:NotRequired[Literal[True]]#表面已卸载则走占位文本

class 文件块(TypedDict):#持久逐字文件引用
    """持久的逐字文件引用，在用户内容里合法；请求组装投影为句柄文本。"""
    type:Literal['file']#文件标签
    attachment:object#附件服务拥有的不可变逐字字节与显示元数据

class 工具调用块(TypedDict):#模型请求的一次工具调用
    """模型请求的一次工具调用。"""
    type:Literal['tool-call']#工具调用标签
    id:str#提供方签发的调用 id
    name:str#工具名
    arguments:str#模型产出的原始 JSON 字符串

class 工具追加块(TypedDict):#从历史请求头激活一条工具定义
    """从开发者事件所引用请求头里激活一条工具定义。"""
    type:Literal['tool-addition']#工具追加标签
    toolName:str#历史头里恰好一条工具名

class 工具移除块(TypedDict):#按会话本地名记录动态移除
    """按会话本地名记录一次工具的动态移除。"""
    type:Literal['tool-removal']#工具移除标签
    toolName:str#工具名

class 用户消息来源(TypedDict):#用户产出的消息来源
    """用户产出的消息来源。"""
    kind:Literal['user']#用户

class 模型消息来源(TypedDict):#模型产出的消息来源
    """模型产出的消息来源。"""
    kind:Literal['model']#模型
    provider:str#提供方
    model:str#模型
    replayState:NotRequired[object]#可选回放状态

class 工具消息来源(TypedDict):#工具产出的消息来源
    """工具产出的消息来源。"""
    kind:Literal['tool']#工具
    callId:str#调用 id

class 系统提示词消息来源(TypedDict):#系统提示词插件产出的来源
    """系统角色消息的必需来源。"""
    kind:Literal['system-prompt']#系统提示词

消息来源=用户消息来源|模型消息来源|工具消息来源|系统提示词消息来源#任一已知消息来源

class 消息(TypedDict):#共用消息表示
    """提供方中立的对话消息。"""
    id:str#稳定身份
    role:Literal['system','user','assistant']#角色
    content:list#内容块
    source:消息来源#来源

class 用户消息(消息):#用户角色特化
    """共用消息表示的用户角色特化。"""
    role:Literal['user']#用户角色

class 助手消息(消息):#助手角色特化
    """共用消息表示的模型产出助手特化。"""
    role:Literal['assistant']#助手角色
    source:模型消息来源#必须是模型来源

class 系统消息(消息):#系统角色特化
    """已渲染系统提示词，归属于系统提示词生产者；空 content 表示无系统提示词。"""
    role:Literal['system']#系统角色
    source:系统提示词消息来源#必须是系统提示词来源

class 开发者消息(消息):#开发者角色特化
    """按对话顺序的增量会话变更，目前是工具追加与移除。"""
    role:Literal['developer']#开发者角色

class 工具结果消息(TypedDict):#工具角色特化
    """一等工具角色消息，承载一次工具调用的结果。"""
    id:str#稳定身份
    role:Literal['tool']#工具角色
    content:list#结果内容块
    source:工具消息来源#必须是工具来源
    toolCallId:str#所回答的工具调用 id
    isError:NotRequired[bool]#是否失败

class 请求用户输入(TypedDict):#仅用于一次请求的用户输入
    """一次请求的用户输入；没有持久会话身份或来源。"""
    role:Literal['user']#用户角色
    content:list#内容块

文本模态='text'#文本模态字面量
图片模态='image'#图片模态字面量
模型模态=(文本模态,图片模态)#已声明提供方模型模态

正常停止={'kind':'stop'}#正常停止结束原因
工具调用停止={'kind':'tool-calls'}#因工具调用停止
达到令牌上限={'kind':'max-tokens'}#达到 token 上限

class 令牌用量(TypedDict):#一次模型调用的 token 记账
    """一次模型调用的 token 记账（缓存字段可选）；计数互斥。"""
    inputTokens:int#未缓存输入
    outputTokens:int#输出
    totalTokens:NotRequired[int]#可选精确合计
    cacheReadTokens:NotRequired[int]#缓存读取
    cacheWriteTokens:NotRequired[int]#缓存写入
    reasoningTokens:NotRequired[int]#推理

class 图片请求价格(TypedDict):#一次有序图片出现的请求价格
    """一条精确模型路由请求投影下，一次有序图片出现的请求价格。"""
    visualTokens:int#保留请求图的提供方视觉 token；仅文本代表本次出现时为 0
    text:str#为本出现发送的模型可见文本

class 提供方简介(TypedDict):#已注册提供方路由的显示元数据
    """一条已注册提供方路由的显示元数据。"""
    id:str#路由键
    name:str#显示名

class 可配置提供方(TypedDict):#可通过配置激活的提供方路由
    """适配器插件可通过配置激活的一条提供方路由。"""
    provider:str#路由键
    displayName:str#显示名
    settingsNs:str#设置命名空间
    settingsPath:list#从命名空间根到配置对象的路径
    declared:NotRequired[bool]#是否仅因配置而认识
    error:NotRequired[str]#可选配置诊断

class 模型发现请求(TypedDict):#对尚未存储端点的一次询问
    """对配置尚未存储的提供方端点的一次询问。"""
    provider:NotRequired[str]#可选已有路由
    baseURL:NotRequired[str]#可选端点
    api:NotRequired[str]#可选协议
    apiKey:NotRequired[str]#一次性凭证
    signal:NotRequired[object]#取消信号

class 发现到的模型(TypedDict):#端点报告的一个模型
    """端点关于自身报告的一个模型。"""
    id:str#模型 id
    name:NotRequired[str]#可选显示名
    contextWindow:NotRequired[int]#可选上下文窗口
    maxTokens:NotRequired[int]#可选最大输出
    inputModalities:NotRequired[list]#可选输入模态

class 模型信息(TypedDict):#适配器发现的目录模型
    """适配器发现的一个模型；目录成员资格是建议性的。"""
    provider:str#提供方
    id:str#模型 id
    name:str#显示名
    description:NotRequired[str]#可选描述
    inputModalities:NotRequired[list]#可选输入模态

class 图片请求预算(TypedDict):#一条视觉路由对保留出现的字节预算
    """一条精确视觉路由按请求版本字节执行的请求图预算。"""
    representation:Literal['raw','base64']#原始文件字节或内联 base64 长度
    maxBytes:NotRequired[int]#可选累计表示字节上限
    maxImages:NotRequired[int]#可选出现张数上限
    byteQuantum:NotRequired[int]#可选字节移除量子
    countQuantum:NotRequired[int]#可选张数移除量子

class 回放信封(TypedDict):#适配器私有无损回放状态
    """成功响应的适配器私有回放状态，随终止 finish 块保存。"""
    response:object#响应级私有元数据
    blocks:NotRequired[list]#按发出块顺序的逐块私有元数据

class 模型上下文(TypedDict):#精确路由的上下文容量
    """一条精确提供方/模型路由的提供方拥有上下文容量。"""
    contextWindow:int#上下文窗口

class 推理力度信息(TypedDict):#一档推理力度的显示元数据
    """适配器拥有的一档推理力度的显示元数据。"""
    id:str#力度 id
    name:str#显示名
    description:NotRequired[str]#可选描述

class 模型推理信息(TypedDict):#可选推理力度
    """一条精确提供方/模型路由的可选推理力度。"""
    efforts:list#受支持力度列表
    defaultEffort:NotRequired[str]#可选默认力度

系统提示词更新=Literal['in-history']#系统提示词更新模式

class 已解析模型信息(TypedDict):#由其拥有适配器解析的精确元数据
    """由其拥有适配器解析的精确路由模型元数据。"""
    provider:str#提供方
    id:str#模型 id
    name:str#显示名
    description:NotRequired[str]#可选描述
    inputModalities:NotRequired[list]#可选输入模态
    context:NotRequired[模型上下文]#可选上下文
    defaultMaxTokens:NotRequired[int]#可选默认最大输出
    reasoning:NotRequired[模型推理信息]#可选推理
    systemPromptUpdate:NotRequired[系统提示词更新]#可选系统提示词更新模式

class 工具模式(TypedDict):#发给模型的工具 JSON Schema 描述
    """发给模型的工具 JSON Schema 描述。"""
    name:str#工具名
    description:str#描述
    parameters:dict#参数的 JSON Schema 对象
    deferLoading:NotRequired[Literal[True]]#请求把工具定义推迟载入模型上下文

class 生成选项(TypedDict):#一次已完全组装的模型请求
    """一次已完全组装的模型请求。"""
    provider:str#提供方
    model:str#模型
    messages:list#对话消息
    reasoningEffort:NotRequired[str]#可选推理力度
    system:NotRequired[str]#可选系统提示
    tools:NotRequired[list]#可选工具模式
    temperature:NotRequired[float]#可选温度
    maxTokens:NotRequired[int]#可选最大 token
    stop:NotRequired[list]#可选停止序列
    signal:NotRequired[object]#可选取消信号
    sessionId:NotRequired[str]#可选会话 id
    purpose:NotRequired[Literal['compaction','session-title']]#可选辅助用途
