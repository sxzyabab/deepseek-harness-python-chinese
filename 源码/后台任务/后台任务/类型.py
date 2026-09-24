"""任务生产者、注册表与消费方共用的类型面。客户端安全投影在 视图，服务实现在包根。"""
from .标识构造 import 任务标识
from .视图 import (
    任务状态,任务通道,任务分块字段,任务视图字段,任务输出坐标字段,
)

任务结局字段=('status','detail','result')
任务源读取字段=('text','nextOffset','lossy','spillPath')
任务输出源字段=('channel','read')
任务追加选项字段=('channel','gapBefore')
任务句柄字段=('id','append','updateProgress')
任务钩子字段=('cancel','done')
任务规格字段=('kind','label','owner','outputLimitBytes','output','run')
任务读取字段=('chunks','lossy','result','job')
任务偏移读取字段=('chunks','next','lossy')
任务结算起因=('producer','kill','teardown')

__all__=[
    '任务标识',
    '任务状态','任务通道','任务分块字段','任务视图字段','任务输出坐标字段',
    '任务结局字段','任务源读取字段','任务输出源字段','任务追加选项字段',
    '任务句柄字段','任务钩子字段','任务规格字段','任务读取字段',
    '任务偏移读取字段','任务结算起因',
]
