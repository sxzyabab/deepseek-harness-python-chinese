'普通事件按条数聚合，走可取消的 HTTP 传输'
import threading
from ...基础设施.通用工具.时间工具 import 当前毫秒
from .传输 import 级别文本
from .事件传输 import 创建事件日志导出器

__all__=['事件日志上报器']

class 事件日志上报器:
    '调用方自己的一条普通事件队列，和会话日志队列互不相干'
    def __init__(自身,选项):
        '按显式的传输、资源和队列设置建通道'
        自身.选项=选项
        自身.取消=threading.Event()
        信号=type('信号',(),{})()
        信号.aborted=False
        信号.is_set=自身.取消.is_set
        def 看到取消():
            '关闭时标成已取消'
            信号.aborted=自身.取消.is_set()
        自身._同步取消=看到取消
        自身.导出器=创建事件日志导出器({
            **(选项.get('exporter') or {}),
            'resourceAttributes':选项.get('resourceAttributes') or {},
            'scope':选项.get('scope') or {'name':'otel'},
        },信号)
        处理=选项.get('processor') or {}
        自身.批量=处理.get('maxExportBatchSize') or 512
        自身.队列上限=处理.get('maxQueueSize') or 2048
        自身.延迟毫秒=处理.get('scheduledDelayMillis') or 1000
        自身.失败=选项.get('onFailure')
        自身.队列=[]
        自身.锁=threading.Lock()
        自身.定时器=None
        自身.已停=False

    def 发出(自身,记录):
        '入队调用方选定的字段，不等待送达'
        号=记录.get('severityNumber')
        if 号 is None:
            号=9
        条目={
            'eventName':记录['eventName'],
            'body':记录['body'],
            'timestamp':记录['timestamp'],
            'observedTimestamp':当前毫秒(),
            'severityNumber':号,
            'severityText':级别文本(号),
            'attributes':记录.get('attributes') or {},
        }
        with 自身.锁:
            if 自身.已停 or len(自身.队列)>=自身.队列上限:
                return
            自身.队列.append(条目)
            if len(自身.队列)>=自身.批量:
                批次=自身.队列
                自身.队列=[]
                自身._取消定时()
            else:
                自身._武装定时()
                return
        自身._导出(批次)

    def 关闭(自身,信号=None):
        '排空队列并放开传输；信号已中止则取消剩余导出'
        if 信号 is not None and getattr(信号,'aborted',False):
            自身.取消.set()
        自身._同步取消()
        with 自身.锁:
            自身.已停=True
            批次=自身.队列
            自身.队列=[]
            自身._取消定时()
        if len(批次)>0 and not 自身.取消.is_set():
            自身._导出(批次)
        自身.导出器['shutdown']()

    def _武装定时(自身):
        '不满一批时延迟送出'
        if 自身.定时器 is not None:
            return
        定时器=threading.Timer(自身.延迟毫秒/1000.0,自身._到期)
        定时器.daemon=True
        自身.定时器=定时器
        定时器.start()

    def _取消定时(自身):
        '拆掉未到期的定时器'
        定时器=自身.定时器
        自身.定时器=None
        if 定时器 is not None:
            定时器.cancel()

    def _到期(自身):
        '定时送出当前队列'
        with 自身.锁:
            自身.定时器=None
            批次=自身.队列
            自身.队列=[]
        if len(批次)>0:
            自身._导出(批次)

    def _导出(自身,批次):
        '失败时调用诊断，不抛回调用方'
        def 回调(结果):
            '非成功交给 onFailure'
            if 结果.get('code')!=0 and callable(自身.失败):
                自身.失败('Product telemetry export failed',结果.get('error'))
        自身.导出器['export'](批次,回调)
