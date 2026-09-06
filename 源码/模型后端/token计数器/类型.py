"""回放 token 计量的公开配置与测量词表。对齐上游 `token-meter/src/types.ts`。公开面仅中文名。"""
from typing import Literal,TypedDict#字面量与结构类型
from .投影 import 用量投影,压力投影,分解投影#再导出投影词表

__all__=[#仅中文公开名
    '计量错误','计量配置','测量基线','表面节点','令牌测量',
    '用量投影','压力投影','分解投影',
]#公开面结束

class 计量错误(Exception):
    """token 计量包的异常基类。"""

计量配置=dict#空配置；固定估算器没有设置项（对齐 TokenMeterConfig=Record<string,never>）

class 表面节点(TypedDict):#当前有序会话表面上一个已计价节点
    seq:int#该表面事件的持久序号
    tokens:int#本节点所投影精确消息的启发式 token

class 测量基线无(TypedDict):#尚无基线
    kind:Literal['none']#种类
    tokens:Literal[0]#固定为 0

class 测量基线估算(TypedDict):#启发式估算
    kind:Literal['estimated']#种类
    tokens:int#启发式 token

class 测量基线用量(TypedDict):#提供方用量
    kind:Literal['usage']#种类
    tokens:int#提供方合计
    usage:dict#提供方用量桶（线路键保持英文）

测量基线=测量基线无|测量基线估算|测量基线用量#带符号表面增量据此得到当前压力的基线

class 令牌测量(TypedDict):#在某一已消费日志修订处拆离的、不可变的请求压力与表面快照
    logRevision:int#已消费的持久事件数；等于下一条未读事件序号
    baseline:测量基线#本次测量所用的提供方或启发式锚点
    surfaceDeltaTokens:int#相对基线锚点对当前表面内容的带符号重新计价
    totalTokens:int#非负的当前请求与响应压力
    surfaceTokens:int#当前表面的启发式 token 合计
    nodes:list#当前表面节点，从头到尾的位置顺序（元素为表面节点）
