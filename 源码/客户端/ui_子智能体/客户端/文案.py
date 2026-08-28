"""`subagent` 命名空间词典。

对齐上游 `ui-subagent/src/client/locales.ts`。公开面仅中文名；词典键与英文字面量保持上游。
"""

__all__=['命名空间','中文','英文','子智能体文案键']#仅中文公开名

命名空间='subagent'#本插件拥有的词典命名空间名

中文={#简体中文词条（键集合的权威源）
    'diagnostic.corrupt':'会话记录损坏',#会话记录损坏诊断
    'diagnostic.unsupported':'子代理记录版本不受支持',#版本不受支持诊断
    'diagnostic.unavailable':'会话记录暂不可用',#记录暂不可用诊断
    'duration.seconds':'{seconds}秒',#秒级时长
    'duration.minutes':'{minutes}分{seconds}秒',#分秒时长
    'duration.hours':'{hours}小时{minutes}分{seconds}秒',#时分秒时长
    'duration.days':'{days}天',#天数时长
    'duration.daysHours':'{days}天{hours}小时',#天小时时长
    'duration.months':'约{months}个月',#约月数时长
    'duration.monthsDays':'约{months}个月{days}天',#约月天数时长
    'duration.years':'约{years}年',#约年数时长
    'duration.yearsMonths':'约{years}年{months}个月',#约年月时长
    'duration.exactDays':'{days}天{hours}小时{minutes}分{seconds}秒',#精确到秒的天数时长
    'duration.exactTitle':'总活跃耗时：{duration}',#总活跃耗时标题
    'loading.label':'正在加载子代理…',#加载中可见标签
    'loading.aria':'正在加载子代理',#加载中无障碍名
    'load.error':'无法加载子代理',#加载失败文案
    'retry':'重试',#重试按钮
    'mode.oneShot':'一次性',#一次性模式
    'mode.continuable':'可继续',#可继续模式
    'activity.running':'正在运行',#运行中状态
    'activity.inactive':'当前未运行',#未运行状态
    'branch.collapse':'收起 {label} 的下级子代理',#收起下级
    'branch.expand':'展开 {label} 的下级子代理',#展开下级
    'count.total.one':'{count} 个子代理',#总数单数
    'count.total.other':'{count} 个子代理',#总数复数
    'count.running.one':'{count} 个子代理，正在运行',#运行数单数
    'count.running.other':'{count} 个子代理，正在运行',#运行数复数
    'tree.aria':'子代理会话',#树无障碍名
    'readonly.oneShot.title':'一次性子代理记录',#一次性只读标题
    'readonly.title':'此子代理暂时只读',#只读标题
    'readonly.oneShot.body':'一次性任务不支持后续消息，可在这里查看完整执行记录。',#一次性只读说明
    'readonly.body':'父会话当前不在线，重新打开父会话后即可继续发送消息。',#父会话离线只读说明
}#中文词典结束

英文={#英文词条，键与中文权威源一致
    'diagnostic.corrupt':'corrupted session record',#会话记录损坏诊断
    'diagnostic.unsupported':'unsupported subagent record version',#版本不受支持诊断
    'diagnostic.unavailable':'session record temporarily unavailable',#记录暂不可用诊断
    'duration.seconds':'{seconds}s',#秒级时长
    'duration.minutes':'{minutes}m {seconds}s',#分秒时长
    'duration.hours':'{hours}h {minutes}m {seconds}s',#时分秒时长
    'duration.days':'{days}d',#天数时长
    'duration.daysHours':'{days}d {hours}h',#天小时时长
    'duration.months':'~{months}mo',#约月数时长
    'duration.monthsDays':'~{months}mo {days}d',#约月天数时长
    'duration.years':'~{years}y',#约年数时长
    'duration.yearsMonths':'~{years}y {months}mo',#约年月时长
    'duration.exactDays':'{days}d {hours}h {minutes}m {seconds}s',#精确到秒的天数时长
    'duration.exactTitle':'Total active duration: {duration}',#总活跃耗时标题
    'loading.label':'Loading subagents…',#加载中可见标签
    'loading.aria':'Loading subagents',#加载中无障碍名
    'load.error':'Unable to load subagents',#加载失败文案
    'retry':'Retry',#重试按钮
    'mode.oneShot':'one-shot',#一次性模式
    'mode.continuable':'continuable',#可继续模式
    'activity.running':'running',#运行中状态
    'activity.inactive':'not running',#未运行状态
    'branch.collapse':'Collapse {label} descendants',#收起下级
    'branch.expand':'Expand {label} descendants',#展开下级
    'count.total.one':'{count} subagent',#总数单数
    'count.total.other':'{count} subagents',#总数复数
    'count.running.one':'{count} subagent running',#运行数单数
    'count.running.other':'{count} subagents running',#运行数复数
    'tree.aria':'Subagent sessions',#树无障碍名
    'readonly.oneShot.title':'One-shot subagent record',#一次性只读标题
    'readonly.title':'This subagent is read-only for now',#只读标题
    'readonly.oneShot.body':'One-shot tasks do not accept follow-ups; review the full execution record here.',#一次性只读说明
    'readonly.body':'The parent session is offline; reopen it to continue sending messages.',#父会话离线只读说明
}#英文词典结束

子智能体文案键=tuple(中文.keys())#由中文词典键推导的键域
