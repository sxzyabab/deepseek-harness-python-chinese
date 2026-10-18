'模组条带周围的界面文案；模组自己的内容仍归模组'

__all__=['命名空间','中文','英文']

命名空间='claude-code-mods'#文案命名空间，槽位和事件仍用这个英文名

中文={
    'band':'Claude Code 模组',#条带的无障碍名
    'pressing':'正在处理…',#词典里有，界面这次不取
    'press.failed':'按钮操作失败：{message}',#按下失败
    'press.stale':'该按钮属于更早的绘制，面板已刷新',#词典里有，界面这次不取
}

英文={
    'band':'Claude Code mods',#英文对照，显示不走这张表
    'pressing':'Working…',
    'press.failed':'The button failed: {message}',
    'press.stale':'That button belonged to an earlier drawing; the band has refreshed',
}
