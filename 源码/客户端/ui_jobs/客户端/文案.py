"""`job` 命名空间词典。

对齐上游 `ui-jobs/src/client/locales.ts`。公开面仅中文名；词典键与英文字面量保持上游。
"""

__all__=['命名空间','中文','英文','任务文案键']#仅中文公开名

命名空间='job'#词典命名空间名

中文={#简体中文词条（键集合的权威源）
    'count.live.one':'{count} 个后台任务运行中',#单数运行中计数
    'count.live.other':'{count} 个后台任务运行中',#复数运行中计数
    'count.idle.one':'{count} 个后台任务',#单数空闲计数
    'count.idle.other':'{count} 个后台任务',#复数空闲计数
    'list.aria':'后台任务',#列表无障碍名
    'status.running':'运行中',#运行状态
    'status.stopping':'正在停止',#停止中状态
    'status.completed':'已完成',#完成状态
    'status.killed':'已取消',#取消状态
    'status.failed':'已失败',#失败状态
    'duration.seconds':'{seconds}秒',#仅秒时长
    'duration.minutes':'{minutes}分{seconds}秒',#分秒时长
    'duration.hours':'{hours}小时{minutes}分',#时分时长
    'duration.title.live':'已运行 {duration}',#进行中时长标题
    'duration.title.done':'耗时 {duration}',#已结束时长标题
}#中文词典结束

英文={#英文词条，键与中文权威源一致
    'count.live.one':'{count} background job running',#单数运行中计数
    'count.live.other':'{count} background jobs running',#复数运行中计数
    'count.idle.one':'{count} background job',#单数空闲计数
    'count.idle.other':'{count} background jobs',#复数空闲计数
    'list.aria':'Background jobs',#列表无障碍名
    'status.running':'running',#运行状态
    'status.stopping':'stopping',#停止中状态
    'status.completed':'completed',#完成状态
    'status.killed':'cancelled',#取消状态
    'status.failed':'failed',#失败状态
    'duration.seconds':'{seconds}s',#仅秒时长
    'duration.minutes':'{minutes}m {seconds}s',#分秒时长
    'duration.hours':'{hours}h {minutes}m',#时分时长
    'duration.title.live':'Running for {duration}',#进行中时长标题
    'duration.title.done':'Took {duration}',#已结束时长标题
}#英文词典结束

任务文案键=tuple(中文.keys())#由中文词典键推导的键域
