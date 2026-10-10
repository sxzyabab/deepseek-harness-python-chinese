'OpenTelemetry 会话遥测后端'
import threading#定时与并发
from ...依赖.schemastery import 字典字段,字符串字段,任意字段,数字字段#配置
from ...身份.匿名用户id import 获取或创建匿名用户id#用户 id
from ...内核.会话 import 会话 as 会话类#从检查结果恢复脱离会话
from ...模型后端.llm import 应用身份,结构化克隆#产品身份与检查快照
from ..会话遥测 import 会话遥测后端#基类
from ..会话遥测.协调器 import 会话遥测协调器#协调器
from .异常 import 开放遥测错误#本包异常
包名='@deepseek-ai/dsh-session-telemetry-otel'
名称='session-telemetry-otel'
依赖=['sessions']#依赖
默认关闭超时毫秒=3000#默认 shutdown 上限
最大定时器延迟毫秒=2147483647#Node 定时器上限
禁用反馈警告='OpenTelemetry session upload is DISABLED; this feedback is not uploaded through OpenTelemetry'#禁用提示
非规范反馈警告='session telemetry ignored an event absent from the canonical session log'#非规范事件
配置=字典字段(字典结构={
    'mode':字符串字段(默认值='FEEDBACK_ONLY'),#FEEDBACK_ONLY/DISABLED
    'exporter':任意字段(),#OTLP 导出器选项
    'processor':任意字段(),#批处理器选项
    'shutdownTimeoutMillis':数字字段(默认值=默认关闭超时毫秒),#关闭上限
    'maxRequestBytes':数字字段(),#未压缩请求字节上限
})#配置模式
__all__=['包名','名称','依赖','应用','默认','配置','会话遥测模式','开放遥测会话后端','开放遥测错误']

会话遥测模式=('FEEDBACK_ONLY','DISABLED')#模式枚举

def 解析模式(模式):
    '校验模式；缺省为只在显式反馈时上传'
    已解析='FEEDBACK_ONLY' if 模式 is None else 模式#默认
    if 已解析 not in 会话遥测模式:#未知
        raise 开放遥测错误('session-telemetry-otel: unsupported mode '+repr(已解析))#拒绝
    return 已解析#返回

def 共享状态于(模式):
    '模式→sharing'
    if 模式=='FEEDBACK_ONLY':#只上传反馈
        return 'feedback-only'#共享状态
    if 模式=='DISABLED':#关闭
        return 'disabled'#共享状态
    raise 开放遥测错误('session-telemetry-otel: unsupported mode '+repr(模式))#拒绝

def 是反馈(会话对象,事件):
    '只有本会话自己的反馈授权重放，分叉种子不算'
    继承=会话对象.inheritedEventCount if hasattr(会话对象,'inheritedEventCount') else 0#继承切口
    if 事件['seq']<继承:#种子前缀
        return False#不算
    类型=事件['type']#类型
    if 类型=='feedback/record':#记录反馈
        return True#算
    if 类型=='feedback/message-put' or 类型=='feedback/message-delete':#消息反馈
        数据=事件['data'] if 'data' in 事件 else {}#载荷
        return 数据.get('sessionId')==会话对象.id#必须是本会话
    return False#其它不算

严重度映射={
    'info':('INFO',9),'warn':('WARN',13),'error':('ERROR',17),
}#OTel 严重度

class 开放遥测会话后端(会话遥测后端):
    '把逻辑记录映射到 OTel Logger.emit'
    def __init__(自身,上下文,配置值):
        '按模式安装后端'
        模式=解析模式(配置值['mode'] if 'mode' in 配置值 else None)#模式
        super().__init__(上下文)#基类
        自身._共享=共享状态于(模式)#sharing
        自身._直接发出=自身._丢弃记录#默认丢弃
        自身._提供者=None#LoggerProvider
        自身._关闭超时=默认关闭超时毫秒#上限
        if 模式=='DISABLED':#禁用
            上下文.监听('session/event',自身._监听禁用反馈)#挂
            return
        导出器配置=配置值['exporter'] if 'exporter' in 配置值 else {}#导出器
        网址=导出器配置['url'] if isinstance(导出器配置,dict) and 'url' in 导出器配置 else None#端点
        if 网址 is None or len(str(网址))==0:#缺 url
            raise 开放遥测错误('session-telemetry-otel: exporter.url is required (the full OTLP logs endpoint)')#拒绝
        协议=str(网址).split(':',1)[0]+':' if ':' in str(网址) else ''#协议
        if 协议!='http:' and 协议!='https:':#协议
            raise 开放遥测错误('session-telemetry-otel: exporter.url must be http(s), got '+协议)#拒绝
        请求字节=配置值['maxRequestBytes'] if 'maxRequestBytes' in 配置值 else None#请求上限
        if 请求字节 is not None and (isinstance(请求字节,bool) or not isinstance(请求字节,int) or 请求字节<1 or 请求字节>4000000):#非法
            raise 开放遥测错误('session-telemetry-otel: maxRequestBytes must be an integer from 1 to 4000000')#拒绝
        处理器配置=配置值['processor'] if 'processor' in 配置值 else None#批处理
        批大小=处理器配置['maxExportBatchSize'] if isinstance(处理器配置,dict) and 'maxExportBatchSize' in 处理器配置 else None#批大小
        if 批大小 is not None and (isinstance(批大小,bool) or not isinstance(批大小,int) or 批大小<1):#非法
            raise 开放遥测错误('session-telemetry-otel: processor.maxExportBatchSize must be a positive integer, got '+str(批大小))#拒绝
        关闭超时=配置值['shutdownTimeoutMillis'] if 'shutdownTimeoutMillis' in 配置值 else 默认关闭超时毫秒#读上限
        if isinstance(关闭超时,bool) or not isinstance(关闭超时,(int,float)) or 关闭超时!=关闭超时 or 关闭超时<=0 or 关闭超时>最大定时器延迟毫秒:#非法
            raise 开放遥测错误('session-telemetry-otel: shutdownTimeoutMillis must be a positive finite number no greater than '+str(最大定时器延迟毫秒)+', got '+str(关闭超时))#拒绝
        自身._关闭超时=关闭超时#记下
        try:#装 OTel；此 try 仅覆盖 SDK 导入，按配套约定保留
            from opentelemetry.sdk._logs import LoggerProvider#提供者
            from opentelemetry.sdk._logs.export import BatchLogRecordProcessor#处理器
            from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter#导出器
            from opentelemetry.sdk.resources import Resource#资源
        except ImportError as 错误:#缺依赖
            raise 开放遥测错误('session-telemetry-otel: OpenTelemetry Python SDK is required: '+str(错误))#阻塞
        资源=Resource.create({
            'service.name':应用身份['product'],'service.version':应用身份['version'],
            'user.id':获取或创建匿名用户id(),
        })#资源属性
        导出器=OTLPLogExporter(endpoint=str(网址))#HTTP 导出
        处理器选项={} if 处理器配置 is None else 处理器配置#批选项
        处理器=BatchLogRecordProcessor(导出器,**处理器选项)#批处理
        提供者=LoggerProvider(resource=资源)#提供者
        提供者.add_log_record_processor(处理器)#挂处理器
        自身._提供者=提供者#记下
        自身._账本=提供者.get_logger('@deepseek-ai/dsh-session-telemetry-otel')#账本 logger
        自身._运维=提供者.get_logger('@deepseek-ai/dsh-session-telemetry-otel/ops')#ops logger
        自身._直接发出=自身._入队#协调器仍走入队
        接收={'发出':自身._入队,'关闭':自身.关闭}#协调器后端
        自身._协调=会话遥测协调器(上下文,接收,{'capture':'on-demand','includeHistory':True})#按需并含历史
        上下文.监听('session/event',自身._反馈监听)#规范日志里的反馈
        上下文.监听('feedback/committed',自身._反馈已提交)#已提交检查

    def _丢弃记录(自身,记录):
        '禁用模式丢弃'
        return#丢弃

    def _监听禁用反馈(自身,会话对象,事件):
        '禁用时对反馈警告'
        if 是反馈(会话对象,事件):#本会话反馈
            自身.ctx.日志.警告(禁用反馈警告)#警告

    def _反馈监听(自身,会话对象,事件):
        '仅规范日志中的反馈授权捕获'
        if not 是反馈(会话对象,事件):#不是反馈
            return#跳过
        事件列表=会话对象.events#日志
        序号=事件['seq']#序号
        if 序号<0 or 序号>=len(事件列表) or 事件列表[序号] is not 事件:#不在规范日志
            自身.ctx.日志.警告(非规范反馈警告)#警告
            return#跳过
        自身._协调.捕获会话(会话对象,序号)#捕获

    def _反馈已提交(自身,检查):
        '用已提交检查里的最后一条事件授权捕获'
        快照=结构化克隆(检查)#拆离
        事件列表=快照['events'] if isinstance(快照,dict) and 'events' in 快照 else []#事件
        if len(事件列表)==0:#没有
            return#跳过
        已提交事件=事件列表[-1]#最后一条
        恢复=会话类.从恢复(快照['meta']['id'],快照['events'],快照['meta'],快照['inheritedEventCount'],'detached',自身.ctx.sessions.消息投影列表)#脱离会话
        if 是反馈(恢复,已提交事件):#仍是反馈
            自身._协调.捕获会话(恢复,已提交事件['seq'])#捕获

    def _入队(自身,记录):
        '映射到 OTel emit'
        记录器=自身._运维 if 记录['channel']=='ops' else 自身._账本#选 logger
        严重=严重度映射[记录['severity']] if 'severity' in 记录 and 记录['severity'] in 严重度映射 else ('INFO',9)#严重度
        记录器.emit({
            'timestamp':记录['time']*1000000,'observed_timestamp':记录['time']*1000000,
            'severity_text':严重[0],'severity_number':严重[1],
            'body':记录['body'],'attributes':记录['attributes'] if 'attributes' in 记录 else {},
        })#发出

    @property
    def 共享(自身):
        '共享策略'
        return 自身._共享#策略

    def 发出(自身,记录):
        '直接记录不上载'
        return#只有规范反馈能授权捕获

    def 关闭(自身):
        '同步关闭提供者'
        if 自身._提供者 is None:#禁用
            return#立即
        错误箱=[]#超时错误
        def 记下超时():
            '超时标记'
            错误箱.append(开放遥测错误('session-telemetry-otel: provider shutdown exceeded '+str(自身._关闭超时)+'ms'))#超时
        定时=threading.Timer(自身._关闭超时/1000.0,记下超时)#定时器
        定时.daemon=True#守护
        定时.start()
        try:#等待
            自身._提供者.shutdown()#同步关闭
        finally:#清定时器
            定时.cancel()#取消
        if len(错误箱)>0:#超时
            raise 错误箱[0]#抛出

def 应用(上下文,配置值):
    '加载 otel 后端'
    开放遥测会话后端(上下文,配置值)#注册

默认=开放遥测会话后端
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=默认#框架槽
