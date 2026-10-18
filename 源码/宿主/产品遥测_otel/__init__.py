'共享 Cordis otel 上的产品用量策略适配器'
from threading import Timer as 定时器#截止定时器
from urllib.parse import urlparse as 解析网址#拆开绝对网址
from ...依赖.cordis import 服务#服务基类
from . import 异常#配置失败。导入时执行顶层

__all__=['名称','依赖','配置','产品遥测','异常']#同目录模块与公开名

def 取正整数(数据,键,缺省):
    '缺席用缺省。写出的值必须是 1 到 2147483647 的整数，布尔不算'
    if 键 not in 数据:#没写
        值=缺省#缺省
    else:#写了
        值=数据[键]#原值
    if isinstance(值,bool) or not isinstance(值,int) or 值<1 or 值>2147483647:#不是范围内的整数
        raise ValueError(键+' 必须是 1 到 2147483647 的整数')#加载时失败
    return 值#整数

class 配置模式:
    '收集器地址、应用身份和内存批量上限'
    def 校验数据(自身,数据=None):
        '补默认值。serviceName 与 serviceVersion 必填。compression 不写就略过'
        if 数据 is None:#没传配置
            数据={}#空配置
        if not isinstance(数据,dict):#必须是对象
            raise ValueError('产品遥测配置必须是对象')#拒绝
        if 'endpoint' in 数据:#写了地址
            端点=数据['endpoint']#原值
            if not isinstance(端点,str):#必须是字符串
                raise ValueError('endpoint 必须是字符串')#拒绝
        else:#没写
            端点='https://dsh-otel-collector.deepseeksvc.com/v1/logs'#默认收集器
        if 'channel' in 数据:#写了频道
            频道=数据['channel']#原值
            if not isinstance(频道,str) or len(频道)<1:#至少 1 个字符
                raise ValueError('channel 必须是非空字符串')#拒绝
        else:#没写
            频道='dsh_otel_report'#默认频道
        if 'serviceName' not in 数据 or not isinstance(数据['serviceName'],str):#必填字符串
            raise ValueError('serviceName 必须是字符串')#拒绝
        if 'serviceVersion' not in 数据 or not isinstance(数据['serviceVersion'],str):#必填字符串
            raise ValueError('serviceVersion 必须是字符串')#拒绝
        if 'compression' in 数据:#写了压缩
            压缩=数据['compression']#原值
            if 压缩 not in ('none','gzip'):#只允许这两项
                raise ValueError('compression 只能是 none 或 gzip')#拒绝
        结果={#校验后的配置
            'endpoint':端点,#地址
            'channel':频道,#频道
            'serviceName':数据['serviceName'],#服务名
            'serviceVersion':数据['serviceVersion'],#服务版本
        }#身份结束
        if 'compression' in 数据:#显式压缩才留下
            结果['compression']=数据['compression']#省略时不写这个键
        结果['maxExportBatchSize']=取正整数(数据,'maxExportBatchSize',512)#每批条数
        结果['maxQueueSize']=取正整数(数据,'maxQueueSize',2048)#队列上限
        结果['scheduledDelayMillis']=取正整数(数据,'scheduledDelayMillis',30000)#不满批的等待
        结果['timeoutMillis']=取正整数(数据,'timeoutMillis',15000)#导出器期限
        结果['exportTimeoutMillis']=取正整数(数据,'exportTimeoutMillis',20000)#一批导出期限
        结果['shutdownTimeoutMillis']=取正整数(数据,'shutdownTimeoutMillis',21000)#排空期限
        return 结果#解析后的配置

    def __call__(自身,数据=None):
        '直接调用时同样解析'
        return 自身.校验数据(数据)#解析

配置=配置模式()#加载器与直接调用都走这份模式

class 产品遥测(服务):
    '显式产品用量事件。只挂载不发送；拥有它的纤程卸载时排空'
    inject=['otel']#等 otel
    name='product-telemetry-otel'#插件名
    Config=配置#配置模式
    def __init__(自身,上下文,配置值):
        '校验路由，交给 otel 建通道，并在卸载时按截止排空'
        #绝对网址。失败包成端点错误，此时还没登记服务
        端点文本=配置值['endpoint']#收集器地址
        try:#必须能拆出协议
            非法=not isinstance(端点文本,str) or 端点文本==''#空或不是字符串
            if not 非法:#再看字符
                for 字符 in 端点文本:#逐个
                    if ord(字符)<=32 or ord(字符)==127:#空白或 DEL
                        非法=True#拒绝
                        break#停
            if 非法:#不是绝对网址
                raise ValueError('invalid url')#交给下面包装
            解析=解析网址(端点文本)#协议与其余部分
            if 解析.scheme=='':#没有协议
                raise ValueError('invalid url')#相对地址
        except (ValueError,TypeError) as 原因:#解析失败
            raise 异常.产品遥测错误('product-telemetry-otel: endpoint must be a valid HTTP(S) URL') from 原因#包装成因
        #HTTP 头值。制表符、可见 ASCII，以及 0x80–0xff
        频道=配置值['channel']#路由头
        try:#非法字符包成频道错误
            if 频道 is None:#空值
                raise ValueError('header')#拒绝
            头文本=频道 if isinstance(频道,str) else str(频道)#非字符串转成文本
            for 字符 in 头文本:#逐个
                码=ord(字符)#码位
                if 码==9 or 32<=码<=126 or 128<=码<=255:#合法
                    continue#下一个
                raise ValueError('header')#非法字符
        except (ValueError,TypeError) as 原因:#头值非法
            raise 异常.产品遥测错误('product-telemetry-otel: channel must be a valid HTTP header value') from 原因#包装成因
        #协议与批量。这两项没有内层成因
        if 解析.scheme not in ('http','https'):#只要 http 与 https
            raise 异常.产品遥测错误('product-telemetry-otel: endpoint must use HTTP or HTTPS')#协议不对
        if 配置值['maxExportBatchSize']>配置值['maxQueueSize']:#批量不能大于队列
            raise 异常.产品遥测错误('product-telemetry-otel: maxExportBatchSize must not exceed maxQueueSize')#拒绝
        super().__init__(上下文,'productTelemetry')#登记服务
        #交给 otel。压缩没写就不传这个键
        导出器={#传输
            'url':配置值['endpoint'],#收集器地址
            'headers':{'x-channel':配置值['channel']},#路由头
            'timeoutMillis':配置值['timeoutMillis'],#HTTP 期限
        }#导出器
        if 'compression' in 配置值:#显式压缩
            if 配置值['compression']=='gzip':#gzip
                导出器['compression']='gzip'#压缩
            else:#none
                导出器['compression']='none'#不压缩
        def 失败时(消息,错误=None):
            '导出失败只记警告，不抛回发出方'
            上下文.日志.警告(消息,错误)#原文消息和错误
        报告器=上下文.otel.创建事件上报器({#普通事件通道
            'exporter':导出器,#传输
            'resourceAttributes':{#资源
                'service.name':配置值['serviceName'],#服务名
                'service.version':配置值['serviceVersion'],#版本
            },#资源结束
            'scope':{'name':'@deepseek-ai/dsh-host-product-telemetry-otel'},#作用域
            'processor':{#批量
                'maxExportBatchSize':配置值['maxExportBatchSize'],#每批
                'maxQueueSize':配置值['maxQueueSize'],#队列
                'scheduledDelayMillis':配置值['scheduledDelayMillis'],#不满批等待
                'exportTimeoutMillis':配置值['exportTimeoutMillis'],#一批期限
            },#批量结束
            'onFailure':失败时,#失败诊断
        })#通道
        自身.报告器=报告器#留下
        def 拆除效果():
            '卸载时按关闭截止排空'
            def 清理():
                '与关闭截止赛跑。到期则中止剩余导出'
                信号=type('信号',(),{})()#中止标记
                信号.aborted=False#尚未中止
                信号.reason=None#中止原因
                def 到期():
                    '截止后警告，并中止还在排队的导出'
                    上下文.日志.警告('Product telemetry shutdown deadline exceeded; pending events may be lost')#原文警告
                    信号.reason=Exception('Product telemetry shutdown deadline exceeded')#中止原因
                    信号.aborted=True#标成已中止
                定时=定时器(配置值['shutdownTimeoutMillis']/1000.0,到期)#毫秒转秒
                定时.start()#开始计时
                try:#排空
                    报告器.关闭(信号)#同步关闭
                finally:#无论成败都停表
                    定时.cancel()#拆掉未到期的定时器
            return 清理#拆除器
        上下文.副作用(拆除效果)#随纤程拆除

    def 发出(自身,记录):
        '入队一条选定事件，不等待网络送达。入队和关闭完成都不是收集器回执'
        自身.报告器.发出(记录)#入队

名称=产品遥测.name#插件名
依赖=产品遥测.inject#模块依赖
name=名称#框架槽
inject=依赖#框架槽
Config=配置#框架槽
default=产品遥测#默认导出是宿主服务类
