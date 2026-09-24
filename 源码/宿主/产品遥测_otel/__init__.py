import gzip,json,threading,time
from urllib.parse import urlparse
from requests import request as 发请求
from ...依赖.cordis import 服务
from ...依赖.schemastery import 字符串字段,数字字段,复合类型字段,常量字段

__all__=['包名','名称','依赖','默认','配置','产品遥测']

包名='@deepseek-ai/dsh-host-product-telemetry-otel'
名称='product-telemetry-otel'
依赖=[]

信息级=9
严重级别文本={
    1:'TRACE',2:'TRACE2',3:'TRACE3',4:'TRACE4',
    5:'DEBUG',6:'DEBUG2',7:'DEBUG3',8:'DEBUG4',
    9:'INFO',10:'INFO2',11:'INFO3',12:'INFO4',
    13:'WARN',14:'WARN2',15:'WARN3',16:'WARN4',
    17:'ERROR',18:'ERROR2',19:'ERROR3',20:'ERROR4',
    21:'FATAL',22:'FATAL2',23:'FATAL3',24:'FATAL4',
}

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

class 产品遥测错误(Exception):
    """产品遥测配置或导出失败。"""

def 属性项(键,值):
    """OTLP 属性。"""
    if isinstance(值,bool):
        return {'key':键,'value':{'boolValue':值}}
    if isinstance(值,int) and not isinstance(值,bool):
        return {'key':键,'value':{'intValue':str(值)}}
    if isinstance(值,float):
        return {'key':键,'value':{'doubleValue':值}}
    return {'key':键,'value':{'stringValue':str(值)}}

def 铺属性(属性表):
    """标量或一层对象。"""
    if 属性表 is None:
        return []
    结果=[]
    for 键,值 in 属性表.items():
        if isinstance(值,dict):
            子=[]
            for 子键,子值 in 值.items():
                子.append(属性项(子键,子值))
            结果.append({'key':键,'value':{'kvlistValue':{'values':子}}})
        else:
            结果.append(属性项(键,值))
    return 结果

class 产品遥测(服务):
    """显式产品用量事件，经 OTLP/HTTP JSON 送出。"""
    def __init__(自身,上下文,配置值):
        """校验路由并挂卸载刷出。"""
        端点=配置值['endpoint'] if 'endpoint' in 配置值 else 'https://dsh-otel-collector.deepseeksvc.com/v1/logs'
        频道=配置值['channel'] if 'channel' in 配置值 else 'dsh_otel_report'
        try:
            解析=urlparse(端点)
        except ValueError as 原因:
            raise 产品遥测错误('product-telemetry-otel: endpoint 必须是合法 HTTP(S) URL') from 原因
        if '\r' in 频道 or '\n' in 频道 or 频道=='':
            raise 产品遥测错误('product-telemetry-otel: channel 必须是合法 HTTP 头值')
        if 解析.scheme not in ('http','https'):
            raise 产品遥测错误('product-telemetry-otel: endpoint 必须使用 HTTP 或 HTTPS')
        批量=配置值['maxExportBatchSize'] if 'maxExportBatchSize' in 配置值 else 512
        队列上限=配置值['maxQueueSize'] if 'maxQueueSize' in 配置值 else 2048
        if 批量>队列上限:
            raise 产品遥测错误('product-telemetry-otel: maxExportBatchSize 不得超过 maxQueueSize')
        super().__init__(上下文,'productTelemetry')
        自身._上下文=上下文
        自身._端点=端点
        自身._频道=频道
        自身._服务名=配置值['serviceName']
        自身._服务版本=配置值['serviceVersion']
        自身._压缩=配置值['compression'] if 'compression' in 配置值 else 'none'
        自身._批量=批量
        自身._队列上限=队列上限
        自身._调度毫秒=配置值['scheduledDelayMillis'] if 'scheduledDelayMillis' in 配置值 else 30000
        自身._超时毫秒=配置值['timeoutMillis'] if 'timeoutMillis' in 配置值 else 15000
        自身._关闭毫秒=配置值['shutdownTimeoutMillis'] if 'shutdownTimeoutMillis' in 配置值 else 21000
        自身._队列=[]
        自身._锁=threading.Lock()
        自身._关闭=False
        自身._定时器=None
        def 拆除效果():
            """卸载时刷出队列。"""
            def 清理():
                """与关闭截止赛跑。"""
                自身._关闭=True
                完成=threading.Event()
                def 刷出():
                    """尽量送出剩余。"""
                    自身._刷出全部()
                    完成.set()
                线=threading.Thread(target=刷出,daemon=True)
                线.start()
                if not 完成.wait(自身._关闭毫秒/1000.0):
                    上下文.日志.警告('产品遥测关闭截止已过；未送出的事件可能丢失')
            return 清理
        上下文.副作用(拆除效果)

    def 发出(自身,记录):
        """入队一条选定事件，不等待网络。"""
        级别=记录['severityNumber'] if 'severityNumber' in 记录 else 信息级
        条目={
            'eventName':记录['eventName'],
            'body':记录['body'],
            'timestamp':记录['timestamp'],
            'observedTimestamp':int(time.time()*1000),
            'severityNumber':级别,
            'severityText':严重级别文本[级别] if 级别 in 严重级别文本 else 'INFO',
            'attributes':记录['attributes'] if 'attributes' in 记录 else {},
        }
        with 自身._锁:
            if 自身._关闭 or len(自身._队列)>=自身._队列上限:
                return
            自身._队列.append(条目)
            if len(自身._队列)>=自身._批量:
                批次=自身._队列
                自身._队列=[]
                自身._取消定时()
            else:
                自身._武装定时()
                return
        自身._导出(批次)

    def _武装定时(自身):
        """部分批次延迟送出。"""
        if 自身._定时器 is not None:
            return
        定时器=threading.Timer(自身._调度毫秒/1000.0,自身._到期)
        定时器.daemon=True
        自身._定时器=定时器
        定时器.start()

    def _取消定时(自身):
        """拆掉未到期定时器。"""
        定时器=自身._定时器
        自身._定时器=None
        if 定时器 is not None:
            定时器.cancel()

    def _到期(自身):
        """定时送出当前队列。"""
        with 自身._锁:
            自身._定时器=None
            批次=自身._队列
            自身._队列=[]
        if len(批次)>0:
            自身._导出(批次)

    def _刷出全部(自身):
        """同步送出队列剩余。"""
        自身._取消定时()
        with 自身._锁:
            批次=自身._队列
            自身._队列=[]
        if len(批次)>0:
            自身._导出(批次)

    def _导出(自身,批次):
        """POST 一批日志。"""
        记录=[]
        for 条目 in 批次:
            记录.append({
                'timeUnixNano':str(int(条目['timestamp'])*1000000),
                'observedTimeUnixNano':str(int(条目['observedTimestamp'])*1000000),
                'severityNumber':条目['severityNumber'],
                'severityText':条目['severityText'],
                'body':{'stringValue':条目['body']},
                'attributes':[属性项('event.name',条目['eventName'])]+铺属性(条目['attributes']),
            })
        载荷={
            'resourceLogs':[{
                'resource':{'attributes':[
                    属性项('service.name',自身._服务名),
                    属性项('service.version',自身._服务版本),
                ]},
                'scopeLogs':[{
                    'scope':{'name':'@deepseek-ai/dsh-host-product-telemetry-otel'},
                    'logRecords':记录,
                }],
            }],
        }
        正文=json.dumps(载荷,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
        头={'Content-Type':'application/json','x-channel':自身._频道}
        if 自身._压缩=='gzip':
            正文=gzip.compress(正文)
            头['Content-Encoding']='gzip'
        try:
            发请求('POST',自身._端点,headers=头,data=正文,timeout=自身._超时毫秒/1000.0)
        except Exception as 错误:
            自身._上下文.日志.警告('产品遥测导出失败',错误)

默认=产品遥测
Config=配置
name=名称
inject=依赖
default=默认
产品遥测.inject=依赖
产品遥测.Config=配置
