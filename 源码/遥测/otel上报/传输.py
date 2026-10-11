'显式的 OTLP JSON 传输；不继承别的收集器的头或 TLS 身份'
import json,threading
from requests import Session as 请求会话
from ...基础设施.通用工具.序列化编码 import 紧凑json编码

__all__=['会话日志最大请求字节','级别文本','属性项','铺属性','日志传输选项','创建日志导出器']

会话日志最大请求字节=4000000

def 级别文本(号):
    'OTel 严重级别文本；缺省 INFO'
    名称=('TRACE','DEBUG','INFO','WARN','ERROR','FATAL')
    if not isinstance(号,int) or isinstance(号,bool) or 号<1 or 号>24:
        return 'INFO'
    组=(号-1)//4
    余=(号-1)%4
    return 名称[组] if 余==0 else 名称[组]+str(余+1)

def 属性项(键,值):
    '一条 OTLP 属性'
    if isinstance(值,bool):
        return {'key':键,'value':{'boolValue':值}}
    if isinstance(值,int) and not isinstance(值,bool):
        return {'key':键,'value':{'intValue':str(值)}}
    if isinstance(值,float):
        return {'key':键,'value':{'doubleValue':值}}
    return {'key':键,'value':{'stringValue':str(值)}}

def 铺属性(属性表):
    '标量或一层对象'
    if not isinstance(属性表,dict):
        return []
    结果=[]
    for 键,值 in 属性表.items():
        if isinstance(值,dict):
            子=[属性项(子键,子值) for 子键,子值 in 值.items()]
            结果.append({'key':键,'value':{'kvlistValue':{'values':子}}})
        else:
            结果.append(属性项(键,值))
    return 结果

def 日志传输选项(选项):
    '收集器地址、头、压缩和超时；头由调用方显式给出'
    def 头():
        '每次导出重新取头'
        给定=选项.get('headers') or {}
        if callable(给定):
            给定=给定()
        return {'Content-Type':'application/json',**给定}
    return {
        'url':选项['url'],
        'headers':头,
        'compression':选项.get('compression') or 'none',
        'timeoutMillis':选项.get('timeoutMillis') or 10000,
        'userAgent':选项.get('userAgent'),
    }

def 创建日志导出器(选项):
    '一条通道自己的 JSON 导出器；关闭时关掉自己的连接'
    配置=日志传输选项(选项)
    会话=请求会话()
    锁=threading.Lock()
    已关=False

    def 导出(记录,回调):
        'POST 一批日志'
        try:
            if 已关:
                raise RuntimeError('OTLP exporter is shut down')
            正文=紧凑json编码(记录体(记录,选项)).encode('utf-8')
            头=配置['headers']()
            数据=正文
            if 配置['compression']=='gzip':
                import gzip
                数据=gzip.compress(正文)
                头={**头,'Content-Encoding':'gzip'}
            if 配置['userAgent'] is not None:
                头={**头,'User-Agent':配置['userAgent']}
            响应=会话.post(配置['url'],data=数据,headers=头,timeout=配置['timeoutMillis']/1000.0,allow_redirects=False)
            if 响应.status_code>=300:
                raise RuntimeError('OTLP collector returned HTTP '+str(响应.status_code))
            if 回调 is not None:
                回调({'code':0})
        except Exception as 错误:
            if 回调 is not None:
                回调({'code':1,'error':错误 if isinstance(错误,Exception) else RuntimeError(str(错误))})

    def 强制刷出():
        '这一导出器没有单独的在途队列'
        return None

    def 关闭():
        '关掉连接'
        nonlocal 已关
        with 锁:
            if 已关:
                return
            已关=True
        会话.close()

    return {'export':导出,'forceFlush':强制刷出,'shutdown':关闭}

def 记录体(记录,选项):
    '把调用方记录收成一条 OTLP logs 请求'
    资源=[]
    for 键,值 in (选项.get('resourceAttributes') or {}).items():
        资源.append(属性项(键,值))
    范围=选项.get('scope') or {'name':'otel'}
    日志=[]
    for 条 in 记录:
        号=条.get('severityNumber') if isinstance(条,dict) else None
        if 号 is None:
            号=9
        日志.append({
            'timeUnixNano':str(int(条['timestamp'])*1000000),
            'observedTimeUnixNano':str(int(条.get('observedTimestamp') or 条['timestamp'])*1000000),
            'severityNumber':号,
            'severityText':条.get('severityText') or 级别文本(号),
            'body':{'stringValue':条.get('body') if isinstance(条.get('body'),str) else ''},
            'attributes':铺属性(条.get('attributes') or {}),
        })
    return {'resourceLogs':[{
        'resource':{'attributes':资源},
        'scopeLogs':[{'scope':{'name':范围.get('name'),'version':范围.get('version')},'logRecords':日志}],
    }]}

def 序列化请求字节(记录,选项):
    '未压缩 UTF-8 字节数，含 OTLP 信封'
    return len(json.dumps(记录体(记录,选项),ensure_ascii=False,separators=(',',':')).encode('utf-8'))
