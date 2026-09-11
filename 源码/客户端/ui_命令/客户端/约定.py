"""客户端命令面的冻结约定。仅类型形。

对齐上游 `ui-commands/src/client/contract.ts`。公开面仅中文名。
CommandUiRuntime（`ctx.commandUi`）实现此面；业务包只消费 register。
跨包值为 dict；AbortSignal 在调用处译为可中止信号。
"""

__all__=[#仅中文公开名
    '命令错误',
    '选定确认','选定选项','弹出选定规格','动作规格','命令UI规格',
    '命令贡献','命令装饰','命令UI约定',
]#公开面结束

class 命令错误(Exception):
    """ui-commands 包异常基类。消息原样英文。"""

#选定确认：title / description / acknowledgeLabel / cancelLabel / confirmLabel
选定确认=dict#选定前确认文案形

#选定选项：id / label / detail? / active? / confirmation?
选定选项=dict#弹出选择一行形

#弹出选定规格：kind='popupSelect' / options(session, signal) / onSelect(option, session)
弹出选定规格=dict#popupSelect 业务规格形

#动作规格：kind='action' / run(session)——裸调用消费令牌并跑回调，不提交，带附件草稿不拒
动作规格=dict#action 业务规格形

#命令UI规格：弹出选定规格 | 动作规格
命令UI规格=dict#UI 规格联合形

#命令贡献：name / label?() / description?() / icon? / available(session) / ui
命令贡献=dict#客户端自有命令贡献形

#命令装饰：name / available(session) / ui——挂在宿主命令上的裸调用 UI
命令装饰=dict#宿主命令装饰形

#命令UI约定：register / decorate / popupFor
命令UI约定=dict#ctx.commandUi 服务面形
