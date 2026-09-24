from ...依赖.schemastery import 字符串字段,布尔字段

__all__=['配置']

配置={
    'default':字符串字段(可空=False),
    'selectedDefault':字符串字段(),
    'modeSelectionEnabled':布尔字段(默认值=True),
}
