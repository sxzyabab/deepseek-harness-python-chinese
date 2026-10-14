'显式产品用量事件，经共享 otel 通道送出'
import threading
from urllib.parse import urlparse
from ...依赖.cordis import 服务
from ...依赖.schemastery import 字符串字段,数字字段,复合类型字段,常量字段
from .异常 import 产品遥测错误#产品遥测配置失败

__all__=['包名','名称','依赖','默认','配置','产品遥测']

包名='@deepseek-ai/dsh-host-product-telemetry-otel'
名称='product-telemetry-otel'
依赖=['otel']

配置={
    'endpoint':字符串字段(默认值='https://dsh-otel-collector.deepseeksvc.com/v1/logs'),
    'channel':字符串字段(最小长度=1,默认值='dsh_otel_report'),
    'serviceName':字符串字段(可空=False),
    'serviceVersion':字符串字段(可空=False),
    'compression':复合类型字段(常量字段('none'),常量字段('gzip')),
    'maxExportBatchSize':数字字段(最小=1,最大=2147483647,默认值=512),
    'maxQueueSize':数字字段(最小=1,最大=2147483647,默认值=2048),
    'scheduledDelayMillis':数字字段(最小=1,默认值=30000),
    'timeoutMillis':数字字段(最小=1,默认值=15000),
    'exportTimeoutMillis':数字字段(最小=1,默认值=20000),
    'shutdownTimeoutMillis':数字字段(最小=1,默认值=21000),
}

def 取配置(配置值,键,缺省):
    '缺席用缺省；显式给出的值原样保留'
    if not isinstance(配置值,dict) or 键 not in 配置值:
        return 缺省
    return 配置值[键]

def 头值合法(值):
    'HTTP 头值：制表符、可见 ASCII，以及 0x80–0xff'
    if not isinstance(值,str) or 值=='':
        return False
    for 字符 in 值:
        码=ord(字符)
        if 码==9 or 32<=码<=126 or 128<=码<=255:
            continue
        return False
    return True

class _关闭信号:
    '卸载截止用的中止信号；报告器只看 aborted'
    def __init__(自身):
        '尚未中止'
        自身.aborted=False

    def 中止(自身):
        '标成已中止'
        自身.aborted=True

class 产品遥测(服务):
    '显式产品用量事件。只挂载不发送；卸载时排空共享通道'
    def __init__(自身,上下文,配置值):
        '校验路由，交给 otel 建通道，并在卸载时按截止排空'
        端点=取配置(配置值,'endpoint','https://dsh-otel-collector.deepseeksvc.com/v1/logs')
        频道=取配置(配置值,'channel','dsh_otel_report')
        try:
            解析=urlparse(端点)
        except (ValueError,TypeError) as 原因:
            raise 产品遥测错误('product-telemetry-otel: endpoint 必须是合法 HTTP(S) URL') from 原因
        if not isinstance(端点,str) or 解析.netloc=='' or any(字符.isspace() for 字符 in 端点):
            raise 产品遥测错误('product-telemetry-otel: endpoint 必须是合法 HTTP(S) URL')
        if not 头值合法(频道):
            raise 产品遥测错误('product-telemetry-otel: channel 必须是合法 HTTP 头值')
        if 解析.scheme not in ('http','https'):
            raise 产品遥测错误('product-telemetry-otel: endpoint 必须使用 HTTP 或 HTTPS')
        批量=取配置(配置值,'maxExportBatchSize',512)
        队列上限=取配置(配置值,'maxQueueSize',2048)
        if 批量>队列上限:
            raise 产品遥测错误('product-telemetry-otel: maxExportBatchSize 不得超过 maxQueueSize')
        super().__init__(上下文,'productTelemetry')
        压缩=取配置(配置值,'compression',None)
        导出器={
            'url':端点,
            'headers':{'x-channel':频道},
            'timeoutMillis':取配置(配置值,'timeoutMillis',15000),
        }
        if 压缩 is not None:
            导出器['compression']='gzip' if 压缩=='gzip' else 'none'
        关闭毫秒=取配置(配置值,'shutdownTimeoutMillis',21000)
        报告器=上下文.otel.创建事件上报器({
            'exporter':导出器,
            'resourceAttributes':{
                'service.name':配置值['serviceName'],
                'service.version':配置值['serviceVersion'],
            },
            'scope':{'name':'@deepseek-ai/dsh-host-product-telemetry-otel'},
            'processor':{
                'maxExportBatchSize':批量,
                'maxQueueSize':队列上限,
                'scheduledDelayMillis':取配置(配置值,'scheduledDelayMillis',30000),
                'exportTimeoutMillis':取配置(配置值,'exportTimeoutMillis',20000),
            },
            'onFailure':lambda 消息,错误=None:上下文.日志.警告(消息,错误),
        })
        自身._报告器=报告器
        def 拆除效果():
            '卸载时按截止排空；超时则中止剩余导出'
            def 清理():
                '与关闭截止赛跑'
                信号=_关闭信号()
                def 到期():
                    '截止后中止剩余导出'
                    上下文.日志.警告('产品遥测关闭截止已过；未送出的事件可能丢失')
                    信号.中止()
                定时器=threading.Timer(关闭毫秒/1000.0,到期)
                定时器.daemon=True
                定时器.start()
                try:
                    报告器.关闭(信号)
                finally:
                    定时器.cancel()
            return 清理
        上下文.副作用(拆除效果)

    def 发出(自身,记录):
        '入队一条选定事件，不等待网络'
        自身._报告器.发出(记录)

默认=产品遥测
Config=配置
name=名称
inject=依赖
default=默认
产品遥测.inject=依赖
产品遥测.Config=配置
