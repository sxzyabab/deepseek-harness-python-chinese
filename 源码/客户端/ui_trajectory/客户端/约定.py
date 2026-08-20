"""Trajectory 目标的类型约定常量与空快照。

对齐上游 `ui-trajectory/src/client/trajectory-contract.ts`。公开面仅中文名。
Python 侧用字典信封承载贡献；类型注释不强制。
"""

__all__=['空轨迹快照']#仅中文公开名

空轨迹快照={#空轨迹快照
    'eventNodes':(),#尚无事件节点
    'eventLocations':{},#尚无事件位置
    'requests':(),#尚无请求
    'callSchemas':{},#尚无调用模式
    'partial':None,#无部分助手
    'runningCalls':(),#无进行中调用
}#空快照结束
