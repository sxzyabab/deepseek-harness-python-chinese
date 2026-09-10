"""DeepSeek 会话日志无损增量上传的线路类型约定。"""
from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型

class 深度求索会话日志线路头(TypedDict):#线路会话头
    version:int#头版本
    id:str#会话id
    createdAt:int#创建时刻
    cwd:NotRequired[str]#工作目录
    parentSession:NotRequired[str]#父会话
    seedLength:NotRequired[int]#精确继承前缀长度；未播种会话缺席
    origin:NotRequired[Literal['subagent']]#来源
    delegationDepth:NotRequired[int]#委托深度
    agentPreset:NotRequired[str]#agent预设

class 深度求索会话日志扩展(TypedDict):#会话日志扩展
    version:Literal[1]#扩展版本
    sessionFormatVersion:int#本后缀所代表的会话格式世代
    session:深度求索会话日志线路头#会话头
    afterSeq:int#本请求前已耐久记录为已接受的最高序号，或 -1
    throughSeq:int#events 所代表的最高序号
    events:list#从 afterSeq+1 到 throughSeq 的完整规范事件信封

__all__=['深度求索会话日志线路头','深度求索会话日志扩展']#公开面
