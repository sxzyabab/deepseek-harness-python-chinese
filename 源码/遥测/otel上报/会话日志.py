'独立的、按字节封顶的会话日志队列'
import json,threading
from .传输 import (
    会话日志最大请求字节,级别文本,创建日志导出器,序列化请求字节,
)

__all__=['会话日志最大请求字节','解析会话日志限制','会话日志上报器']

def 解析会话日志限制(选项):
    '建通道前校验字节和队列；返回收集器请求上限'
    上限=选项.get('maxRequestBytes')
    if 上限 is None:
        上限=会话日志最大请求字节
    if not isinstance(上限,int) or isinstance(上限,bool) or 上限<1 or 上限>会话日志最大请求字节:
        raise ValueError('session log maxRequestBytes must be an integer between 1 and '+str(会话日志最大请求字节))
    处理=选项.get('processor') or {}
    for 键 in ('maxQueueSize','maxExportBatchSize','scheduledDelayMillis','exportTimeoutMillis'):
        值=处理.get(键)
        if 值 is not None and (not isinstance(值,int) or isinstance(值,bool) or 值<1 or 值>2147483647):
            raise ValueError('session log processor.'+键+' must be a positive integer no greater than 2147483647')
    队列=处理.get('maxQueueSize') or 2048
    批量=处理.get('maxExportBatchSize') or 512
    if 批量>队列:
        raise ValueError('session log maxExportBatchSize must not exceed maxQueueSize')
    return 上限

class 会话日志处理器:
    '按字节和条数组包，同时只有一个传输请求'
    def __init__(自身,导出器,上限,配置,警告):
        '记下导出器、上限和诊断'
        自身.导出器=导出器
        自身.上限=上限
        自身.配置=配置
        自身.警告=警告
        自身.队列=[]
        自身.字节=0
        自身.定时器=None
        自身.在途=None
        自身.已停=False
        自身.锁=threading.Lock()

    def 入队(自身,记录):
        '超限或队列满则拒绝这一条，不截断'
        if 自身.已停:
            return
        if len(自身.队列)>=自身.配置['maxQueueSize']:
            自身.警告('Session log queue is full; record rejected')
            return
        try:
            字节=序列化请求字节([记录],{
                'resourceAttributes':自身.配置.get('resourceAttributes') or {},
                'scope':自身.配置.get('scope') or {'name':'session-log'},
            })
        except Exception as 错误:
            自身.警告('Session log serialization failed; record rejected',错误 if isinstance(错误,Exception) else RuntimeError(str(错误)))
            return
        if 字节>自身.上限:
            自身.警告('Session log record rejected; content was not truncated',RuntimeError('Session log record exceeds maxRequestBytes: '+str(字节)+' > '+str(自身.上限)))
            return
        自身.队列.append({'record':记录,'bytes':字节})
        自身.字节+=字节
        if 自身.在途 is not None:
            return
        if len(自身.队列)>=自身.配置['maxExportBatchSize'] or 自身.字节>=自身.上限:
            自身.强制刷出()
        elif 自身.定时器 is None:
            自身.定时器=threading.Timer(自身.配置['scheduledDelayMillis']/1000.0,自身.强制刷出)
            自身.定时器.daemon=True
            自身.定时器.start()

    def 强制刷出(自身):
        '送出当前能装进上限的一批'
        if 自身.定时器 is not None:
            自身.定时器.cancel()
            自身.定时器=None
        if 自身.在途 is not None:
            return 自身.在途
        if len(自身.队列)==0:
            return None
        自身.在途=True
        try:
            while not 自身.已停 and len(自身.队列)>0:
                字节=0
                条数=0
                for 项 in 自身.队列:
                    if 条数==自身.配置['maxExportBatchSize'] or 字节+项['bytes']>自身.上限:
                        break
                    字节+=项['bytes']
                    条数+=1
                批=自身.队列[:条数]
                del 自身.队列[:条数]
                自身.字节-=字节
                自身._发送([项['record'] for 项 in 批])
                自身.导出器['forceFlush']()
        finally:
            自身.在途=None

    def _发送(自身,记录):
        '等到这一请求结算；超时只警告，仍等传输结束'
        完成=threading.Event()
        盒子={'错误':None}
        def 到期():
            '超过导出超时仍在等'
            自身.警告('Session log request exceeded exportTimeoutMillis; waiting for transport settlement')
        定时=threading.Timer(自身.配置['exportTimeoutMillis']/1000.0,到期)
        定时.daemon=True
        定时.start()
        def 回调(结果):
            '记下失败并放行'
            if 结果.get('code')!=0:
                盒子['错误']=结果.get('error') or RuntimeError('Session log HTTP export failed')
            完成.set()
        try:
            自身.导出器['export'](记录,回调)
        except Exception as 错误:
            盒子['错误']=错误
            完成.set()
        完成.wait()
        定时.cancel()
        if 盒子['错误'] is not None:
            自身.警告('Session log export failed',盒子['错误'])

    def 停待发(自身):
        '丢掉还没送出的队列；正在送的可以继续结算'
        自身.已停=True
        自身.队列.clear()
        自身.字节=0
        if 自身.定时器 is not None:
            自身.定时器.cancel()
            自身.定时器=None

    def 关闭(自身):
        '先刷出再关导出器'
        自身.强制刷出()
        自身.导出器['shutdown']()

class 会话日志上报器:
    '持有已授权的会话日志；不挂普通事件队列'
    def __init__(自身,选项):
        '校验限制并建独立通道'
        上限=解析会话日志限制(选项)
        处理=选项.get('processor') or {}
        自身.导出器=创建日志导出器({
            **选项['exporter'],
            'resourceAttributes':选项.get('resourceAttributes') or {},
            'scope':选项['scope'],
        })
        自身.处理器=会话日志处理器(自身.导出器,上限,{
            'resourceAttributes':选项.get('resourceAttributes') or {},
            'scope':选项['scope'],
            'maxQueueSize':处理.get('maxQueueSize') or 2048,
            'maxExportBatchSize':处理.get('maxExportBatchSize') or 512,
            'scheduledDelayMillis':处理.get('scheduledDelayMillis') or 1000,
            'exportTimeoutMillis':处理.get('exportTimeoutMillis') or 30000,
        },选项['onFailure'])
        自身.范围=选项['scope']
        自身.资源=选项.get('resourceAttributes') or {}

    def 上报会话日志(自身,记录):
        '入队一条完整事件，不等待网络'
        号=记录.get('severityNumber')
        if 号 is None:
            号=9
        自身.处理器.入队({
            'eventName':'session-log',
            'body':'session-log',
            'timestamp':记录['event']['time'],
            'observedTimestamp':记录['event']['time'],
            'severityNumber':号,
            'severityText':级别文本(号),
            'attributes':{
                **(记录.get('attributes') or {}),
                'sessionId':记录['sessionId'],
                'content':json.dumps(记录['event'],ensure_ascii=False,separators=(',',':')),
            },
            'resourceAttributes':自身.资源,
            'scope':自身.范围,
        })

    def 停待发(自身):
        '拥有方的关闭期限到了就停掉还在排队的请求'
        自身.处理器.停待发()

    def 关闭(自身):
        '排空并放开传输'
        自身.处理器.关闭()
