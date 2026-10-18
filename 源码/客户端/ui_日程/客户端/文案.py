'schedule.catalog 的中英文案。界面显示只用中文表原文'
from .频率文案 import 频率中文,频率英文

__all__=['命名空间','目录中文','目录英文','套用']

命名空间='schedule.catalog'

def 套用(模板,参数=None):
    '把模板里的 {键} 换成这次的值。模板是中文表原文'
    if not isinstance(参数,dict):
        return 模板
    文=模板
    for 键,值 in 参数.items():
        文=文.replace('{'+str(键)+'}','' if 值 is None else str(值))
    return 文

目录中文={
    'trigger.label':'提醒',
    'list.loading':'正在加载提醒…',
    'list.error':'无法加载提醒。',
    'list.retry':'重试',
    'delete.action':'删除',
    'delete.pending':'正在删除…',
    'delete.label':'删除提醒：{title}',
    'list.open':'打开提醒详情：{title}',
    'trigger.one':'{count} 个提醒',
    'trigger.other':'{count} 个提醒',
    'list.aria':'活动提醒',
    'list.nextRun':'下次运行',
    'frequency.once':'单次',
    'frequency.every':'{value}{unit}一次',
    **频率中文,
    'mark.aria':'{count} 个自动化任务',
    'hover.more':'另有 {count} 个任务',
}

目录英文={
    'trigger.label':'Reminders',
    'list.loading':'Loading reminders…',
    'list.error':'Could not load reminders.',
    'list.retry':'Retry',
    'delete.action':'Delete',
    'delete.pending':'Deleting…',
    'delete.label':'Delete reminder: {title}',
    'list.open':'Open reminder details: {title}',
    'trigger.one':'{count} reminder',
    'trigger.other':'{count} reminders',
    'list.aria':'Active reminders',
    'list.nextRun':'Next run',
    'frequency.once':'Once',
    'frequency.every':'Every {value} {unit}',
    **频率英文,
    'mark.aria':'{count} scheduled tasks',
    'hover.more':'{count} more',
}
