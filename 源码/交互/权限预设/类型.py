"""权限域的纯类型：`permissions` 投影键声明及其载荷类型的唯一家园，不含本包宿主侧值导入（cordis、schemastery）。两个命名空间投影为它服务——给宿主消费方的包根再导出，以及给客户端聚合的 `./客户端`——内容零重复。"""

预设选项字段=('value','name','description')#展示层为一条可用预设或派生 custom 当前值的选择项字段：稳定值、展示标签、可选说明
"""展示层为一条可用预设或派生的 `custom` 当前值公布的选择项形态。value 为表键、在线 auto 或 custom；name 为展示标签；description 一句面向用户说明，未配置时省略。"""

权限目录字段=('options',)#进程级权限目录字段：当前可选项列表
"""进程级权限目录。它随在线贡献变化，有意与会话历史分开。options 为当前每一个可选项，按贡献顺序。"""

权限选择字段=('currentValue',)#整份 permissions 会话投影字段：只含当前持久选择
"""整份 `permissions` 会话投影：只含当前持久选择。currentValue 为表键、auto 或 custom。"""
