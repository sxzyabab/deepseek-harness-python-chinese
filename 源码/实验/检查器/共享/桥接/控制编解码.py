"""Host、Worker 与注入 Client 生命周期值的精确解码器。

对齐上游 `shared/bridge/control-codec.ts`。公开面仅中文名。
"""
from urllib.parse import urlparse as 解析网址#解析URL
from ..json import 是否普通对象#普通对象
from ..校验 import 精确键,精确对象#精确校验

__all__=[#仅中文公开名
    '解析检查器工作者配置','解析检查器宿主控制','解析检查器工作者控制','解析检查器客户端引导',
]#公开面结束

def 解析检查器工作者配置(值):#解析Worker配置
    """解码结构化克隆的 Worker 配置。"""
    记录=精确对象(值,[#精确对象
        'host','startPort','targetId','clientToken','clientOrigins','maxSourceFrameBytes',#字段1
        'maxSourceRecordsPerFrame','maxRetainedRequests','maxJournalBytes','clientRuntimeTimeoutMs','maxCordisNodes',#字段2
        'maxDisconnectedCordisTrees','maxClientSourceBytes',#字段3
    ],'Worker config')#校验结束
    if 记录['host']!='127.0.0.1':#主机须回环
        raise Exception('inspector protocol: Worker host must be 127.0.0.1')#英文诊断
    if not isinstance(记录['targetId'],str) or len(记录['targetId'])==0:#目标标识非法
        raise Exception('inspector protocol: Worker targetId must be a non-empty string')#英文诊断
    if not isinstance(记录['clientToken'],str) or len(记录['clientToken'])==0:#令牌非法
        raise Exception('inspector protocol: Worker clientToken must be a non-empty string')#英文诊断
    if not isinstance(记录['clientOrigins'],list) or not all(isinstance(项,str) for 项 in 记录['clientOrigins']):#来源非法
        raise Exception('inspector protocol: Worker clientOrigins must be strings')#英文诊断
    起始端口=自然数(记录['startPort'],'startPort',True)#解析端口
    if 起始端口>65535:#端口上限
        raise Exception('inspector protocol: Worker startPort must not exceed 65535')#英文诊断
    return {#配置对象
        'host':记录['host'],#主机
        'startPort':起始端口,#端口
        'targetId':记录['targetId'],#目标
        'clientToken':记录['clientToken'],#令牌
        'clientOrigins':记录['clientOrigins'],#来源
        'maxSourceFrameBytes':自然数(记录['maxSourceFrameBytes'],'maxSourceFrameBytes'),#源帧字节
        'maxSourceRecordsPerFrame':自然数(记录['maxSourceRecordsPerFrame'],'maxSourceRecordsPerFrame'),#每帧记录
        'maxRetainedRequests':自然数(记录['maxRetainedRequests'],'maxRetainedRequests'),#保留请求
        'maxJournalBytes':自然数(记录['maxJournalBytes'],'maxJournalBytes'),#日志字节
        'clientRuntimeTimeoutMs':自然数(记录['clientRuntimeTimeoutMs'],'clientRuntimeTimeoutMs'),#Runtime超时
        'maxClientSourceBytes':自然数(记录['maxClientSourceBytes'],'maxClientSourceBytes'),#Client源字节
        'maxCordisNodes':自然数(记录['maxCordisNodes'],'maxCordisNodes'),#Cordis节点
        'maxDisconnectedCordisTrees':自然数(记录['maxDisconnectedCordisTrees'],'maxDisconnectedCordisTrees',True),#断开树上限
    }#返回结束

def 解析检查器宿主控制(值):#解析Host控制
    """解码一条 Host-到-Worker 生命周期命令。"""
    记录=精确对象(值,['type'],'Host control message')#精确对象
    if 记录['type']!='shutdown':#仅shutdown
        raise Exception('inspector protocol: unknown Host control message')#英文诊断
    return {'type':'shutdown'}#关闭命令

def 解析检查器工作者控制(值):#解析Worker控制
    """解码一条 Worker-到-Host 生命周期事件。"""
    记录=按类型取对象(值,'Worker control message')#按type取对象
    if 记录['type']=='ready':#就绪
        精确键(记录,['type','host','port','targetId'],'Worker ready message')#精确字段
        if not isinstance(记录['host'],str) or not isinstance(记录['targetId'],str):#身份非法
            raise Exception('inspector protocol: invalid Worker ready identity')#英文诊断
        return {'type':'ready','host':记录['host'],'port':自然数(记录['port'],'port',True),'targetId':记录['targetId']}#就绪事件
    if 记录['type']=='failure':#失败
        精确键(记录,['type','message'],'Worker failure message')#精确字段
        if not isinstance(记录['message'],str):#须字符串
            raise Exception('inspector protocol: invalid Worker failure')#英文诊断
        return {'type':'failure','message':记录['message']}#失败事件
    if 记录['type']=='stopped':#已停止
        精确键(记录,['type'],'Worker stopped message')#精确字段
        return {'type':'stopped'}#停止事件
    raise Exception('inspector protocol: unknown Worker control message')#英文诊断

def 解析检查器客户端引导(值):#解析Client引导
    """解码注入到浏览器全局的引导数据。"""
    记录=精确对象(值,[#精确对象
        'endpoint','protocol','maxQueuedRecords','maxQueuedBytes','maxRecordsPerFrame','maxFrameBytes',#字段1
        'reconnectBaseMs','reconnectMaxMs','queryTimeoutMs','maxRuntimeObjectsPerSession',#字段2
        'maxRuntimePropertiesPerResult','maxCordisNodes','maxClientSourceBytes',#字段3
    ],'Client bootstrap')#校验结束
    if not isinstance(记录['endpoint'],str) or not isinstance(记录['protocol'],str):#端点协议非法
        raise Exception('inspector protocol: Client bootstrap endpoint and protocol must be strings')#英文诊断
    try:#解析端点
        端点=解析网址(记录['endpoint'])#绝对URL
    except Exception:#解析失败
        raise Exception('inspector protocol: Client bootstrap endpoint must be an absolute URL')#英文诊断
    if 端点.scheme!='ws' or 端点.hostname!='127.0.0.1':#须本机ws
        raise Exception('inspector protocol: Client bootstrap endpoint must use ws on 127.0.0.1')#英文诊断
    if len(记录['protocol'])==0 or len(记录['protocol'])>256:#协议名长度
        raise Exception('inspector protocol: Client bootstrap protocol must contain 1 to 256 characters')#英文诊断
    引导={#引导对象
        'endpoint':记录['endpoint'],#端点
        'protocol':记录['protocol'],#协议
        'maxQueuedRecords':自然数(记录['maxQueuedRecords'],'maxQueuedRecords'),#排队记录
        'maxQueuedBytes':自然数(记录['maxQueuedBytes'],'maxQueuedBytes'),#排队字节
        'maxRecordsPerFrame':自然数(记录['maxRecordsPerFrame'],'maxRecordsPerFrame'),#每帧记录
        'maxFrameBytes':自然数(记录['maxFrameBytes'],'maxFrameBytes'),#每帧字节
        'reconnectBaseMs':自然数(记录['reconnectBaseMs'],'reconnectBaseMs'),#重连基础
        'reconnectMaxMs':自然数(记录['reconnectMaxMs'],'reconnectMaxMs'),#重连最大
        'queryTimeoutMs':自然数(记录['queryTimeoutMs'],'queryTimeoutMs'),#查询超时
        'maxRuntimeObjectsPerSession':自然数(记录['maxRuntimeObjectsPerSession'],'maxRuntimeObjectsPerSession'),#会话对象
        'maxRuntimePropertiesPerResult':自然数(记录['maxRuntimePropertiesPerResult'],'maxRuntimePropertiesPerResult'),#结果属性
        'maxClientSourceBytes':自然数(记录['maxClientSourceBytes'],'maxClientSourceBytes'),#源字节
        'maxCordisNodes':自然数(记录['maxCordisNodes'],'maxCordisNodes'),#Cordis节点
    }#bootstrap结束
    if 引导['reconnectMaxMs']<引导['reconnectBaseMs']:#重连区间非法
        raise Exception('inspector protocol: reconnectMaxMs must be at least reconnectBaseMs')#英文诊断
    return 引导#引导

def 按类型取对象(值,标签):#按type取对象
    """要求带 type 字符串的普通对象。"""
    if not 是否普通对象(值) or not isinstance(值.get('type'),str):#须有type
        raise Exception(f'inspector protocol: {标签} must have a type')#英文诊断
    return 值#普通对象

def 自然数(值,标签,允许零=False):#自然数校验
    """安全整数自然数校验。"""
    下限=0 if 允许零 else 1#下限
    if not isinstance(值,int) or isinstance(值,bool) or 值<下限 or 值>9007199254740991:#非安全整数或越界
        raise Exception(f'inspector protocol: {标签} must be {"a non-negative" if 允许零 else "a positive"} safe integer')#英文诊断
    return 值#自然数
