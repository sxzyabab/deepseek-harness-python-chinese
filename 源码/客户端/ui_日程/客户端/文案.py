"""`schedule.catalog` 命名空间词典。

对齐上游 `ui-schedule/src/client/locales.ts`。公开面仅中文名。
"""
__all__=['命名空间','中文','英文','NS','zh','en']#仅中文公开名

命名空间='schedule.catalog'#locale 命名空间
NS=命名空间#上游名

中文={#简体中文词典（键集合真源）
    'trigger.one':'{count} 个提醒',#单数触发标签
    'trigger.other':'{count} 个提醒',#复数触发标签
    'list.aria':'活动提醒',#目录无障碍标签
    'status.scheduled':'等待中',#未逾期状态
    'status.overdue':'已逾期',#逾期状态
    'frequency.once':'单次',#一次性频率
    'frequency.every':'{value}{unit}一次',#重复频率
    'unit.day.one':'天',#天单数
    'unit.day.other':'天',#天复数
    'unit.hour.one':'小时',#小时单数
    'unit.hour.other':'小时',#小时复数
    'unit.minute.one':'分钟',#分钟单数
    'unit.minute.other':'分钟',#分钟复数
    'unit.second.one':'秒',#秒单数
    'unit.second.other':'秒',#秒复数
    'relative.now':'现在到期',#恰到期
    'relative.future':'{value}{unit}后',#未来相对
    'relative.overdue':'已逾期 {value}{unit}',#逾期相对
}#中文结束

英文={#英文词典，键与中文真源一致
    'trigger.one':'{count} reminder',#单数触发标签
    'trigger.other':'{count} reminders',#复数触发标签
    'list.aria':'Active reminders',#目录无障碍标签
    'status.scheduled':'Scheduled',#未逾期状态
    'status.overdue':'Overdue',#逾期状态
    'frequency.once':'Once',#一次性频率
    'frequency.every':'Every {value} {unit}',#重复频率
    'unit.day.one':'day',#天单数
    'unit.day.other':'days',#天复数
    'unit.hour.one':'hour',#小时单数
    'unit.hour.other':'hours',#小时复数
    'unit.minute.one':'minute',#分钟单数
    'unit.minute.other':'minutes',#分钟复数
    'unit.second.one':'second',#秒单数
    'unit.second.other':'seconds',#秒复数
    'relative.now':'Due now',#恰到期
    'relative.future':'in {value} {unit}',#未来相对
    'relative.overdue':'{value} {unit} overdue',#逾期相对
}#英文结束

zh=中文#上游名
en=英文#上游名
