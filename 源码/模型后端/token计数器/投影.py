"""纯客户端安全的 token 投影词表。对齐上游 `token-meter/src/projection.ts`。公开面仅中文名。

四个用量桶互不相交；推理已计入 `outputTokens`，不再另加一次。
压力字段在出现时不是一次原子请求观察：各自后写获胜，切换模型可能把新容量与上一路由压力配对。
分解三数是启发式构成近似，不会加总成提供方锚定的 `projectedTokens`。
"""
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
    systemTokens:int#系统提示词启发式 token
    toolsTokens:int#工具模式启发式 token
    messageTokens:int#消息表面启发式 token
