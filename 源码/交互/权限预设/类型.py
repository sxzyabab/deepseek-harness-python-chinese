"""权限域的纯类型：`permissions` 投影键声明及其载荷类型的唯一家园，不含本包宿主侧值导入（cordis、schemastery）。两个命名空间投影为它服务——给宿主消费方的包根再导出，以及给客户端聚合的 `./客户端`——内容零重复。"""

预设选项字段=('value','name','description')#展示层为一条预设（或派生的 custom 状态）公布的选择项字段：稳定值、展示标签、可选说明
"""展示层为一条预设（或派生的 `custom` 状态）公布的选择项形态。value 为表键或 custom；name 为展示标签；description 一句面向用户说明，未配置时省略。"""

权限选择字段=('options','currentValue')#完整 permissions 投影值字段：选项列表与生效当前值
"""完整 `permissions` 投影值：按表顺序的每个可切换预设（当旋钮与任何条目都不匹配时，外加仅当前派生的 `custom`）以及生效的当前值。options 可切换预设，仅当 custom 是当前值时才追加它；currentValue 为预设表键或 custom。"""
