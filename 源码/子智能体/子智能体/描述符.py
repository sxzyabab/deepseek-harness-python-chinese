"""耐久的子智能体子描述符：版本化、对模型隐藏的 subagent/descriptor 会话事件，标识每个有会话的子智能体，并记录它是一次性还是可续跑。可续跑描述符额外保存冷恢复所需的已声明组合。"""
from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型
from session import 快照json值#导入无损JSON快照

子智能体描述符版本=2#当前描述符版本
描述符公共键=('version','mode','provider','label')#描述符公共键
一次性描述符键=set(描述符公共键)#一次性允许键
可续跑描述符键=set(list(描述符公共键)+['agentProvider','agentModel','persona','toolFilter'])#可续跑允许键
工具过滤键=set(['allow','deny'])#工具过滤允许键

class 一次性子智能体描述符数据(TypedDict):#其跑结束后不能冷恢复的有会话子智能体
    version:int#描述符格式版本
    mode:Literal['one-shot']#固定为一次性
    provider:str#建立该子体的 ctx.subagents 提供方名
    label:NotRequired[str]#可选创建标签

class 可续跑子智能体描述符数据(TypedDict):#已声明组合支持冷恢复的有会话子智能体
    version:int#描述符格式版本
    mode:Literal['continuable']#固定为可续跑
    provider:str#建立该子体的 ctx.subagents 提供方名
    label:str#创建标签
    agentProvider:NotRequired[str]#已解析的子 agentOptions.provider
    agentModel:NotRequired[str]#已解析的子 agentOptions.model
    persona:NotRequired[str]#恢复时遮蔽部署人设的每子体人设
    toolFilter:NotRequired[object]#恢复时再应用的子工具作用域

子智能体描述符数据=一次性子智能体描述符数据|可续跑子智能体描述符数据#受支持的耐久子智能体身份与可选续跑组合

class 一次性子智能体描述符输入(TypedDict):#一次性子体耐久身份的输入
    mode:Literal['one-shot']#固定为一次性
    provider:str#将建立该子体的提供方名
    label:NotRequired[str]#可选创建标签

class 可续跑子智能体描述符输入(TypedDict):#可续跑子体耐久身份与可恢复组合的输入
    mode:Literal['continuable']#固定为可续跑
    provider:str#将建立该子体的提供方名
    label:str#创建标签
    agentProvider:NotRequired[str]#请求的子 agentOptions.provider
    agentModel:NotRequired[str]#请求的子 agentOptions.model
    persona:NotRequired[str]#请求的每子体人设
    toolFilter:NotRequired[object]#请求的子工具作用域

子智能体描述符输入=一次性子智能体描述符输入|可续跑子智能体描述符输入#snapshot 校验并分离的输入

def 是否记录(值):#对象记录守卫
    """持久化 JSON 值是否为对象记录。"""
    return isinstance(值,dict)#非空非数组对象在Python里就是dict

def 断言已知键(值,键集,路径):#断言无未知键
    """拒绝一份版本化记录已声明模式之外的字段。"""
    for 键 in 值.keys():#逐键
        if 键 not in 键集:#未知字段
            raise Exception('persisted subagent descriptor '+路径+' has unknown field "'+键+'"')#拒绝

def 可选字符串(值,键):#读可选字符串
    """从持久化描述符记录读一个可选字符串字段。"""
    if 键 not in 值:#缺席
        return None#缺席
    字段=值[键]#字段值
    if not isinstance(字段,str):#类型不对
        raise Exception('persisted subagent descriptor '+键+' must be a string')#拒绝
    return 字段#字符串

def 可选字符串数组(值,键):#读可选字符串数组
    """从持久化工具限制读一个可选字符串数组字段。"""
    if 键 not in 值:#缺席
        return None#缺席
    字段=值[键]#字段值
    if not isinstance(字段,list):#不是数组
        raise Exception('persisted subagent descriptor toolFilter.'+键+' must be an array of strings')#拒绝
    for 项 in 字段:#逐元素
        if not isinstance(项,str):#有非字符串
            raise Exception('persisted subagent descriptor toolFilter.'+键+' must be an array of strings')#拒绝
    return 字段#字符串数组

def 解析工具过滤(值):#解析工具过滤
    """校验并重建持久化的工具限制。"""
    if not 是否记录(值):#必须是对象
        raise Exception('persisted subagent descriptor toolFilter must be an object')#拒绝
    断言已知键(值,工具过滤键,'toolFilter')#只允许allow/deny
    允许=可选字符串数组(值,'allow')#可选允许表
    拒绝=可选字符串数组(值,'deny')#可选拒绝表
    if 允许 is None and 拒绝 is None:#两者都缺
        raise Exception('persisted subagent descriptor toolFilter must declare allow and/or deny')#必须声明其一
    结果={}#重建限制
    if 允许 is not None:#有allow
        结果['allow']=允许#展开
    if 拒绝 is not None:#有deny
        结果['deny']=拒绝#展开
    return 结果#工具限制

def 解析子智能体描述符(值):#解析描述符
    """为当前运行时校验一份持久化描述符载荷。"""
    if not 是否记录(值):#必须是对象
        raise Exception('persisted subagent descriptor payload must be an object')#拒绝
    版本=值.get('version')#版本字段
    if not isinstance(版本,(int,float)) or isinstance(版本,bool):#必须是数字
        raise Exception('persisted subagent descriptor version must be a number')#拒绝
    if 版本!=子智能体描述符版本:#他版本无法分类
        return None#无法分类
    模式=值.get('mode')#模式字段
    if 模式!='one-shot' and 模式!='continuable':#必须是已知模式
        raise Exception('persisted subagent descriptor mode must be "one-shot" or "continuable"')#拒绝
    断言已知键(值,一次性描述符键 if 模式=='one-shot' else 可续跑描述符键,'payload')#按模式校验键
    提供方=值.get('provider')#提供方字段
    if not isinstance(提供方,str):#必须是字符串
        raise Exception('persisted subagent descriptor provider must be a string')#拒绝
    if 模式=='one-shot':#一次性载荷
        标签=可选字符串(值,'label')#可选标签
        结果={'version':子智能体描述符版本,'mode':模式,'provider':提供方}#一次性描述符
        if 标签 is not None:#有标签
            结果['label']=标签#展开
        return 结果#一次性
    标签=值.get('label')#可续跑标签必填
    if not isinstance(标签,str):#必须是字符串
        raise Exception('persisted subagent descriptor label must be a string')#拒绝
    智能体提供方=可选字符串(值,'agentProvider')#可选子提供方
    智能体模型=可选字符串(值,'agentModel')#可选子模型
    人设=可选字符串(值,'persona')#可选人设
    工具过滤=解析工具过滤(值['toolFilter']) if 'toolFilter' in 值 else None#是否带工具过滤
    结果={'version':子智能体描述符版本,'mode':模式,'provider':提供方,'label':标签}#可续跑描述符
    if 智能体提供方 is not None:#有子提供方
        结果['agentProvider']=智能体提供方#展开
    if 智能体模型 is not None:#有子模型
        结果['agentModel']=智能体模型#展开
    if 人设 is not None:#有人设
        结果['persona']=人设#展开
    if 工具过滤 is not None:#有过滤
        结果['toolFilter']=工具过滤#展开
    return 结果#可续跑

def 快照子智能体描述符(输入):#校验并分离描述符
    """在任何 Task 或提供方工作开始之前，把描述符输入校验并分离成耐久载荷——与会话日志自身强制的同一分离无损 JSON 边界。"""
    模式=输入['mode'] if isinstance(输入,dict) else 输入.mode#生命周期模式
    提供方=输入['provider'] if isinstance(输入,dict) else 输入.provider#提供方名
    if 模式=='one-shot':#一次性候选
        候选={'version':子智能体描述符版本,'mode':模式,'provider':提供方}#一次性候选
        标签=输入.get('label') if isinstance(输入,dict) else getattr(输入,'label',None)#可选标签
        if 标签 is not None:#有标签
            候选['label']=标签#展开
    else:#可续跑候选
        标签=输入['label'] if isinstance(输入,dict) else 输入.label#标签
        候选={'version':子智能体描述符版本,'mode':模式,'provider':提供方,'label':标签}#可续跑候选
        for 键 in ('agentProvider','agentModel','persona','toolFilter'):#可选组合字段
            值=输入.get(键) if isinstance(输入,dict) else getattr(输入,键,None)#读字段
            if 值 is not None:#有值
                候选[键]=值#展开
    快照=快照json值(候选)#经无损JSON边界分离
    if 快照 is None:#不能无损序列化
        raise Exception('subagent descriptor is not losslessly JSON-serializable')#拒绝
    return 快照#已分离载荷

def 折叠子智能体描述符(事件们):#折叠描述符
    """把持久化子日志折叠成其受支持的描述符。第一条 subagent/descriptor 事件是权威——建立提供方恰好追加一条，因此后来的同类型事件不能改写已声明组合。"""
    事件=None#第一条描述符
    for 候选 in 事件们:#找第一条描述符事件
        类型=候选['type'] if isinstance(候选,dict) else getattr(候选,'type',None)#类型
        if 类型=='subagent/descriptor':#命中
            事件=候选#记下
            break#第一条权威
    if 事件 is None:#没有描述符
        return None#无法分类
    数据=事件['data'] if isinstance(事件,dict) else getattr(事件,'data',None)#载荷
    return 解析子智能体描述符(数据)#解析载荷
