'workflowRun 词表。页面上的字不读这张表'

__all__=['命名空间','中文','英文']

命名空间='workflowRun'#插件自己的词表命名空间

中文={
    'run.title':'{name}',#运行标题
    'run.members.one':'{count} 个成员',#一个成员
    'run.members.other':'{count} 个成员',#多个成员
    'run.empty':'没有启动成员',#还没有成员
    'phase.unassigned':'未分阶段',#没有阶段字段
    'phase.empty':'空阶段名',#阶段名是空字符串
    'statusCount.running':'运行中 {count}',#运行中的数量
    'statusCount.completed':'已完成 {count}',#已完成的数量
    'statusCount.failed':'失败 {count}',#失败的数量
    'statusCount.cancelled':'已取消 {count}',#已取消的数量
    'statusCount.interrupted':'已中断 {count}',#已中断的数量
    'member.empty':'空成员名',#成员名是空字符串
    'member.open':'打开 {name}',#可打开的成员
    'status.running':'运行中',#运行中
    'status.completed':'已完成',#已完成
    'status.failed':'失败',#失败
    'status.cancelled':'已取消',#已取消
    'status.interrupted':'已中断',#已中断
}

英文={
    'run.title':'{name}',#运行标题
    'run.members.one':'{count} member',#一个成员
    'run.members.other':'{count} members',#多个成员
    'run.empty':'No members started',#还没有成员
    'phase.unassigned':'Unphased',#没有阶段字段
    'phase.empty':'Empty phase name',#阶段名是空字符串
    'statusCount.running':'Running {count}',#运行中的数量
    'statusCount.completed':'Completed {count}',#已完成的数量
    'statusCount.failed':'Failed {count}',#失败的数量
    'statusCount.cancelled':'Cancelled {count}',#已取消的数量
    'statusCount.interrupted':'Interrupted {count}',#已中断的数量
    'member.empty':'Empty member name',#成员名是空字符串
    'member.open':'Open {name}',#可打开的成员
    'status.running':'Running',#运行中
    'status.completed':'Completed',#已完成
    'status.failed':'Failed',#失败
    'status.cancelled':'Cancelled',#已取消
    'status.interrupted':'Interrupted',#已中断
}
