__all__=[#仅中文公开名
    '业务视图槽名','业务视图所有者字段','卡片面钩子','运行卡片面钩子','面板面钩子','面板面动词',
]

业务视图槽名='tool.view.cordis'
业务视图所有者字段=('pluginId','packageId','pluginRunId')

卡片面钩子=('inventory','loaded')
运行卡片面钩子=('inventory','loaded','runCards','activeRuns')#运行卡钩子
面板面钩子=('inventory','activeRuns','runErrors','renderFailures','loaded')
面板面动词=('onApprove','onDecline','onRun','onStop','onRemove','onRefresh')

def 业务视图键(插件标识,包标识):
    'self → pluginId.packageId'
    return f'{插件标识}.{包标识}'
