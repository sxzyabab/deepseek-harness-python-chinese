"""OpenTelemetry 会话遥测后端（对齐 upstream session-telemetry-otel）。"""
import threading,time#定时与并发
from ...依赖.schemastery import 字典字段,字符串字段,任意字段,数字字段#配置
from ...身份.匿名用户id import 获取或创建匿名用户id#用户 id
from ...模型后端.llm import 应用身份#产品身份
from ..会话遥测 import 会话遥测后端#基类
from ..会话遥测.协调器 import 会话遥测协调器#协调器
from ...内核.智能体循环.辅助 import 取 as 取字段#字段读取
名称='session-telemetry-otel'#Cordis 插件名
注入=['sessions']#依赖
默认关闭超时毫秒=3000#默认 shutdown 上限
最大定时器延迟毫秒=2147483647#Node 定时器上限
禁用反馈警告='session telemetry is DISABLED; nothing will be shared and this feedback remains local'#禁用提示
非规范反馈警告='session telemetry ignored a feedback event absent from the canonical session log'#非规范反馈
配置=字典字段({
    'mode':字符串字段(默认值='DISABLED'),#FULL/FEEDBACK_ONLY/DISABLED
    'exporter':任意字段(),#OTLP 导出器选项
    'processor':任意字段(),#批处理器选项
    'shutdownTimeoutMillis':数字字段(默认值=默认关闭超时毫秒),#关闭上限
})#配置模式
__all__=['名称','注入','配置','会话遥测模式','开放遥测会话后端','默认']#公开面

会话遥测模式=('FULL','FEEDBACK_ONLY','DISABLED')#模式枚举

def 取字段(对象,键,缺省=None):#读字段
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键,缺省)#键
    return getattr(对象,键,缺省)#属性

def 解析模式(模式):#校验模式
    已解析=模式 or 'DISABLED'#默认
    if 已解析 not in 会话遥测模式:#未知
        raise Exception('session-telemetry-otel: unsupported mode '+repr(模式))#拒绝
    return 已解析#返回

def 共享状态于(模式):#模式→sharing
    映射={'FULL':'full','FEEDBACK_ONLY':'feedback-only','DISABLED':'disabled'}#表
    return 映射[模式]#返回

严重度映射={#OTel 严重度
    'info':('INFO',9),'warn':('WARN',13),'error':('ERROR',17),
}#映射结束

class 开放遥测会话后端(会话遥测后端):#OTel 后端
    """把逻辑记录映射到 OTel Logger.emit。"""
    def __init__(自身,上下文,配置值):#构造
        模式=解析模式(配置值.get('mode'))#模式
        super().__init__(上下文)#基类
        自身._共享=共享状态于(模式)#sharing
        自身._直接发出=lambda 记录:None#默认丢弃
        自身._提供者=None#LoggerProvider
        自身._关闭超时=默认关闭超时毫秒#上限
        if 模式=='DISABLED':#禁用
            def 监听反馈(会话,事件):#反馈警告
                if 取字段(事件,'type')=='feedback/record':#反馈
                    上下文.logger.warn(禁用反馈警告)#警告
            上下文.on('session/event',监听反馈)#挂
            return#结束
        网址=取字段(取字段(配置值,'exporter',{}),'url')#端点
        if 网址 is None or len(str(网址))==0:#缺 url
            raise Exception('session-telemetry-otel: exporter.url is required')#拒绝
        if not str(网址).startswith('http://') and not str(网址).startswith('https://'):#协议
            raise Exception('session-telemetry-otel: exporter.url must be http(s)')#拒绝
        批大小=取字段(取字段(配置值,'processor',{}),'maxExportBatchSize')#批大小
        if 批大小 is not None and (not isinstance(批大小,int) or 批大小<1):#非法
            raise Exception('session-telemetry-otel: processor.maxExportBatchSize must be a positive integer')#拒绝
        关闭超时=配置值.get('shutdownTimeoutMillis',默认关闭超时毫秒)#读上限
        if (not isinstance(关闭超时,(int,float))) or 关闭超时<=0 or 关闭超时>最大定时器延迟毫秒:#非法
            raise Exception('session-telemetry-otel: shutdownTimeoutMillis out of range')#拒绝
        自身._关闭超时=关闭超时#记下
        try:#装 OTel
            from opentelemetry.sdk._logs import LoggerProvider#提供者
            from opentelemetry.sdk._logs.export import BatchLogRecordProcessor#处理器
            from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter#导出器
            from opentelemetry.sdk.resources import Resource#资源
        except ImportError as 错误:#缺依赖
            raise Exception('session-telemetry-otel: OpenTelemetry Python SDK is required: '+str(错误))#阻塞
        资源=Resource.create({#资源属性
            'service.name':应用身份['product'],'service.version':应用身份['version'],
            'user.id':获取或创建匿名用户id(),
        })#资源结束
        导出器=OTLPLogExporter(endpoint=str(网址))#HTTP 导出
        处理器=BatchLogRecordProcessor(导出器,**({} if 配置值.get('processor') is None else 配置值['processor']))#批处理
        提供者=LoggerProvider(resource=资源)#提供者
        提供者.add_log_record_processor(处理器)#挂处理器
        自身._提供者=提供者#记下
        账本=提供者.get_logger('@deepseek-ai/dsh-session-telemetry-otel')#账本 logger
        运维=提供者.get_logger('@deepseek-ai/dsh-session-telemetry-otel/ops')#ops logger
        def 入队(记录):#emit
            记录器=运维 if 取字段(记录,'channel')=='ops' else 账本#选 logger
            严重=严重度映射.get(取字段(记录,'severity'),('INFO',9))#严重度
            记录器.emit({
                'timestamp':取字段(记录,'time')*1000000,'observed_timestamp':取字段(记录,'time')*1000000,
                'severity_text':严重[0],'severity_number':严重[1],
                'body':取字段(记录,'body'),'attributes':取字段(记录,'attributes',{}),
            })#发出
        自身._直接发出=入队#记下
        if 模式=='FULL':#全量
            会话遥测协调器(上下文,{'emit':入队,'shutdown':lambda:自身.关闭()},'live')#实时
            return#结束
        协调=会话遥测协调器(上下文,{'emit':入队,'shutdown':lambda:自身.关闭()},'on-demand')#按需
        def 反馈监听(会话,事件):#仅反馈
            if 取字段(事件,'type')!='feedback/record':#非反馈
                return#跳过
            事件们=取字段(会话,'events',[])#日志
            序号=取字段(事件,'seq')#序号
            if 序号<0 or 序号>=len(事件们) or 事件们[序号] is not 事件:#非规范
                上下文.logger.warn(非规范反馈警告)#警告
                return#跳过
            协调.捕获会话(会话,序号)#捕获
        上下文.on('session/event',反馈监听)#挂

    @property#sharing
    def 共享(自身):#sharing
        return 自身._共享#策略
    sharing=共享#Cordis 槽

    def 发出(自身,记录):#emit
        自身._直接发出(记录)#转发
    emit=发出#Cordis 槽

    async def 关闭(自身):#shutdown
        if 自身._提供者 is None:#禁用
            return#立即
        完成=自身._提供者.shutdown()#SDK 关闭
        错误箱=[]#超时错误
        def 超时():错误箱.append(Exception('session-telemetry-otel: provider shutdown exceeded '+str(自身._关闭超时)+'ms'))#超时
        定时=threading.Timer(自身._关闭超时/1000.0,超时)#定时器
        定时.daemon=True#守护
        定时.start()#启动
        try:#等待
            if hasattr(完成,'__await__'):#协程
                await 完成#等待
            else:#同步
                完成#假定已完成
        finally:#清定时器
            定时.cancel()#取消
        if len(错误箱)>0:#超时
            raise 错误箱[0]#抛出

def 应用(上下文,配置值):#加载
    开放遥测会话后端(上下文,配置值)#注册

apply=应用#Cordis 插件入口
default=开放遥测会话后端#默认类
默认=开放遥测会话后端#中文默认
