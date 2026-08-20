"""客户端命令面的冻结约定。仅类型形。

对齐上游 `ui-commands/src/client/contract.ts`。公开面仅中文名。
CommandUiRuntime（ctx.commandUi）实现此面；业务包只消费 register。
"""

__all__=[#仅中文公开名
    '选定确认','选择选项','命令界面规格','命令贡献','命令装饰','命令界面约定',
]#公开面结束

#选定确认：onSelect 能跑之前必须先确认的文案
#字段 title / description / acknowledgeLabel / cancelLabel / confirmLabel
选定确认=dict#选定前确认文案形

#选择选项：popupSelect 外壳的一行选项
#字段 id / label / detail? / active? / confirmation?
选择选项=dict#弹出选择的一行选项形

#命令界面规格：popupSelect 种类的业务注册
#字段 kind='popupSelect' / options(session,signal) / onSelect(option,session)
命令界面规格=dict#popupSelect 业务规格形

#命令贡献：客户端自有斜杠菜单项，行为完全住在客户端
#字段 name / description / available(session) / ui
命令贡献=dict#客户端自有命令贡献形

#命令装饰：挂在一条宿主命令上的裸调用 UI 装饰
#字段 name / available(session) / ui
命令装饰=dict#宿主命令裸调用装饰形

#命令界面约定：业务包可见的 ctx.commandUi 服务面
#方法 register(contribution) / decorate(decoration) / popupFor(actx)
命令界面约定=dict#命令 UI 服务面形
