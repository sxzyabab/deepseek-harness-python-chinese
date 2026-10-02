'纯客户端安全的 token 投影词表'
from typing import NotRequired,TypedDict#可选字段与结构类型

__all__=['用量投影','压力投影','分解投影']#仅中文公开名

class 用量投影(TypedDict):#一份完整会话日志的持久累计提供方用量
    uncachedInputTokens:int#未缓存输入
    outputTokens:int#输出（含推理）
    cacheReadTokens:int#缓存读取
    cacheWriteTokens:int#缓存写入

class 压力投影(TypedDict):#供状态展示用的近似上下文占用
    pressureTokens:NotRequired[int]#最近请求提示词压力（未缓存输入加缓存读写）
    projectedTokens:NotRequired[int]#投影下一次提示词规模
    contextWindow:NotRequired[int]#最新记录的路由容量

class 分解投影(TypedDict):#下一次请求上下文的启发式构成
    systemTokens:int#表面顺序下末个非空幸存系统提示词
    toolsTokens:int#最新请求信封工具模式
    messageTokens:int#其余可见表面节点（含已被取代的系统）
