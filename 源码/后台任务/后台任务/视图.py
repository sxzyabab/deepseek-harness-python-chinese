"""客户端安全的任务词表：一份任务的只读投影，以及输出环交出的分块。本叶不触及宿主包。"""

任务状态=('running','stopping','completed','killed','failed')
任务通道=('stdout','stderr','log')
任务分块字段=('at','text','channel','gapBefore')
任务视图字段=(
    'id','kind','label','owner','outputLimitBytes','status',
    'progress','detail','startedAt','finishedAt','output',
)
任务输出坐标字段=('total','earliest','spillPaths')

__all__=[
    '任务状态','任务通道','任务分块字段','任务视图字段','任务输出坐标字段',
]
