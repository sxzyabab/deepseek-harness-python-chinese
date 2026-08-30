"""斜杠管线的冻结服务约定。仅类型形。

对齐上游 `ui-input-trigger/src/client/contract.ts`。公开面仅中文名。
InputTriggerService 实现把此面发布为 ctx.inputTriggers；
源只看见 registerSource，会话接线层经 sessionOf 解析其每会话控制器。
"""

__all__=['输入触发服务约定']#仅中文公开名

#输入触发服务约定：ctx.inputTriggers 服务面
#方法 registerSource(src) -> 拆除器
#方法 sessionOf(actx) -> 触发控制器
输入触发服务约定=dict#输入触发服务面形
