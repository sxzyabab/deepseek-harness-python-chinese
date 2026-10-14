from .频率文案 import 频率中文,频率英文

__all__=['命名空间','中文','英文']

命名空间='schedule.catalog'

中文={
    **频率中文,
    'trigger.label':'提醒',
    'trigger.one':'{count} 个提醒',
    'trigger.other':'{count} 个提醒',
    'list.aria':'活动提醒',
    'list.loading':'正在加载提醒…',
    'list.error':'无法加载提醒。',
    'list.retry':'重试',
    'list.open':'打开提醒详情：{title}',
    'list.nextRun':'下次运行',
    'delete.action':'删除',
    'delete.pending':'正在删除…',
    'delete.label':'删除提醒：{title}',
    'status.scheduled':'等待中',
    'status.overdue':'已逾期',
    'frequency.once':'单次',
    'frequency.every':'{value}{unit}一次',
    'mark.aria':'{count} 个自动化任务',
    'hover.more':'另有 {count} 个任务',
}

英文={
    **频率英文,
    'trigger.label':'Reminders',
    'trigger.one':'{count} reminder',
    'trigger.other':'{count} reminders',
    'list.aria':'Active reminders',
    'list.loading':'Loading reminders…',
    'list.error':'Could not load reminders.',
    'list.retry':'Retry',
    'list.open':'Open reminder details: {title}',
    'list.nextRun':'Next run',
    'delete.action':'Delete',
    'delete.pending':'Deleting…',
    'delete.label':'Delete reminder: {title}',
    'status.scheduled':'Scheduled',
    'status.overdue':'Overdue',
    'frequency.once':'Once',
    'frequency.every':'Every {value} {unit}',
    'mark.aria':'{count} scheduled tasks',
    'hover.more':'{count} more',
}
