"""注入面以及包所拥有的 `tool.view.cordis` 槽声明。

对齐上游 `ui-cordis/src/client/slots.ts`。公开面仅中文名。
完整 keyed 槽 DOM 绑定需浏览器。
"""

__all__=[#仅中文公开名
    '业务视图槽名','业务视图所有者字段','卡片面钩子','运行卡片面钩子','面板面钩子','面板面动词',
]#公开面结束

业务视图槽名='tool.view.cordis'#包业务视图槽
业务视图所有者字段=('pluginId','packageId','pluginRunId')#所有者通货

卡片面钩子=('inventory','loaded')#定义卡钩子
运行卡片面钩子=('inventory','loaded','runCards','activeRuns')#运行卡钩子
面板面钩子=('inventory','activeRuns','runErrors','renderFailures','loaded')#面板钩子
面板面动词=('onApprove','onDecline','onRun','onStop','onRemove','onRefresh')#面板动词

def 业务视图键(插件标识,包标识):#守卫钉死的键
    """对齐 Guard：self → pluginId.packageId。"""
    return f'{插件标识}.{包标识}'#绑到本包
