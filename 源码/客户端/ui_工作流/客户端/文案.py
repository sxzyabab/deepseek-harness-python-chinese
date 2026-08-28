"""`workflowRun` 命名空间词典。

对齐上游 `ui-workflow-run/src/client/locales.ts`。公开面仅中文名；词典键与英文字面量保持上游。
"""

__all__=['命名空间','中文','英文','工作流运行文案键']#仅中文公开名

命名空间='workflowRun'#词典命名空间名

中文={#简体中文词条（键集合的权威源）
    'run.title':'{name}',#运行面板标题
    'run.members.one':'{count} 个成员',#单数成员计数
    'run.members.other':'{count} 个成员',#复数成员计数
    'run.empty':'没有启动成员',#无启动成员空态
    'phase.unassigned':'未分阶段',#未分阶段占位
    'phase.empty':'空阶段名',#空阶段名占位
    'statusCount.running':'运行中 {count}',#运行中计数
    'statusCount.completed':'已完成 {count}',#已完成计数
    'statusCount.failed':'失败 {count}',#失败计数
    'statusCount.cancelled':'已取消 {count}',#已取消计数
    'statusCount.interrupted':'已中断 {count}',#已中断计数
    'member.empty':'空成员名',#空成员名占位
    'member.open':'打开 {name}',#打开成员无障碍名
    'status.running':'运行中',#运行状态
    'status.completed':'已完成',#完成状态
    'status.failed':'失败',#失败状态
    'status.cancelled':'已取消',#取消状态
    'status.interrupted':'已中断',#中断状态
}#中文词典结束

英文={#英文词条，键与中文权威源一致
    'run.title':'{name}',#运行面板标题
    'run.members.one':'{count} member',#单数成员计数
    'run.members.other':'{count} members',#复数成员计数
    'run.empty':'No members started',#无启动成员空态
    'phase.unassigned':'Unphased',#未分阶段占位
    'phase.empty':'Empty phase name',#空阶段名占位
    'statusCount.running':'Running {count}',#运行中计数
    'statusCount.completed':'Completed {count}',#已完成计数
    'statusCount.failed':'Failed {count}',#失败计数
    'statusCount.cancelled':'Cancelled {count}',#已取消计数
    'statusCount.interrupted':'Interrupted {count}',#已中断计数
    'member.empty':'Empty member name',#空成员名占位
    'member.open':'Open {name}',#打开成员无障碍名
    'status.running':'Running',#运行状态
    'status.completed':'Completed',#完成状态
    'status.failed':'Failed',#失败状态
    'status.cancelled':'Cancelled',#取消状态
    'status.interrupted':'Interrupted',#中断状态
}#英文词典结束

工作流运行文案键=tuple(中文.keys())#由中文词典键推导的键域
