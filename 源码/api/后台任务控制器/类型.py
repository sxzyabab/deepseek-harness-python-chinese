'job 远程命名空间的线路类型。帧和请求都是 dict，键保持上游原文'

任务列表请求字段=('sessionId',)#job.list 请求
任务列表帧类型='rows'#整表替换
任务列表帧字段=('type','jobs')#type 与整表
任务终止请求字段=('sessionId','jobId')#job.kill 请求
任务终止结果字段=('outcome',)#登记表的接纳
任务终止结局=('requested','already-finished')#outcome 的两个值
任务未找到码='job/not-found'#名册里没有可终止的那一行
任务未找到详情字段=('sessionId','jobId')#该码的详情
任务跟随请求字段=('jobId','sessionId','from')#job.follow；sessionId 与 from 可省略
任务跟随帧类型=('opened','output','status')#观察帧的三种 type
打开帧字段=('type','job','from')#opened：投影与续读偏移
输出帧字段=('type','chunks','next','lossy')#output；lossy 可省略
状态帧字段=('type','job')#status：已结算投影
人类终止原因='cancelled by the user'#登记表记下的原因，壳工具会读到

__all__=[
    '任务列表请求字段','任务列表帧类型','任务列表帧字段',
    '任务终止请求字段','任务终止结果字段','任务终止结局',
    '任务未找到码','任务未找到详情字段',
    '任务跟随请求字段','任务跟随帧类型',
    '打开帧字段','输出帧字段','状态帧字段','人类终止原因',
]
