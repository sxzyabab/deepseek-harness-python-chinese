"""循环、会话日志与插件共用的规范、提供方中立消息与流式词表。

对齐上游 `llm/src/types.ts`。公开面仅中文名；块 type／字段键保持上游 wire 名。
"""
import math#有限数判定
from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型

__all__=(#仅中文公开名；无英文别名
    '安全整数上限','是否整数','是否安全整数','是否有限','缺席',
    '中止信号','是否中止信号',
    '语言模型失败',
    '文本块','推理块','图片块','工具调用块','工具结果块',
    '文本模态','图片模态','模型模态',
    '正常停止','工具调用停止','达到令牌上限',
    '令牌用量','提供方信息','可配置提供方',
    '模型发现请求','发现到的模型','模型信息','模型上下文',
    '推理力度信息','模型推理信息','已解析模型信息',
    '工具模式','生成选项',
)#公开面结束

安全整数上限=9007199254740991#JS Number.MAX_SAFE_INTEGER

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

def 是否有限(值):#对齐 JS Number.isFinite
    """对齐 JS Number.isFinite，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是数字
    if isinstance(值,(int,float)):#数字
        return math.isfinite(值)#非 NaN 非无穷
    return False#其它类型

def 缺席(对象,键):#对齐字段 === undefined
    """对齐 JS 字段 === undefined：缺键或值为 None。"""
    if 对象 is None:#无对象
        return True#无对象
    if isinstance(对象,dict):#映射
        return 对象.get(键) is None#缺键或空
    return getattr(对象,键,None) is None#缺属性或空

class 中止信号:#调用方取消通道
    """调用方取消通道；深冻结必须跳过，以免破坏中止。"""
    def __init__(自身,已中止=False):#创建一条取消通道
        """创建一条取消通道。"""
        自身.aborted=已中止#英文旗标（上游 AbortSignal wire）
        自身.已中止=已中止#中文旗标
        自身.reason=None#英文中止原因
        自身.原因=None#中文中止原因

def 是否中止信号(值):#是否为活动取消通道
    """是否为请求的活动取消通道。"""
    if 值 is None:#空
        return False#空
    if isinstance(值,(str,bytes,int,float,bool,dict,list)):#原语与容器不是信号
        return False#原语与容器不是信号
    return hasattr(值,'aborted') or hasattr(值,'已中止')#有中止旗标

class 语言模型失败(TypedDict):#可序列化提供方或传输失败事实
    """可序列化的提供方或传输失败事实；政策决定它们是否可重试。"""
    message:str#人类可读失败摘要
    code:str#稳定提供方中立机器路由码
    status:NotRequired[int]#提供方 HTTP 状态（若有）
    providerRetryAfterMs:NotRequired[float]#提供方请求的延迟毫秒
    requestId:NotRequired[str]#不透明提供方签发请求标识

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

class 工具调用块(TypedDict):#模型请求的一次工具调用
    """模型请求的一次工具调用。"""
    type:Literal['tool-call']#工具调用标签
    id:str#提供方签发的调用 id
    name:str#工具名
    arguments:str#模型产出的原始 JSON 字符串

class 工具结果块(TypedDict):#一次工具调用的结果
    """一次工具调用的结果，送回模型。"""
    type:Literal['tool-result']#工具结果标签
    toolCallId:str#关联的调用 id
    content:list#结果内容块列表
    isError:NotRequired[bool]#是否失败

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
    cacheReadTokens:NotRequired[int]#缓存读取
    cacheWriteTokens:NotRequired[int]#缓存写入
    reasoningTokens:NotRequired[int]#推理

class 提供方信息(TypedDict):#已注册提供方路由的显示元数据
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

class 模型信息(TypedDict):#适配器发现的目录模型
    """适配器发现的一个模型；目录成员资格是建议性的。"""
    provider:str#提供方
    id:str#模型 id
    name:str#显示名
    description:NotRequired[str]#可选描述
    inputModalities:NotRequired[list]#可选输入模态

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

class 工具模式(TypedDict):#发给模型的工具 JSON Schema 描述
    """发给模型的工具 JSON Schema 描述。"""
    name:str#工具名
    description:str#描述
    parameters:dict#参数的 JSON Schema 对象

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
