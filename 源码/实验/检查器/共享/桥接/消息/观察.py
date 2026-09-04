"""两种载体共用的、带版本的源生命周期、观测与扩展帧。

对齐上游 `shared/bridge/messages/observation.ts`。公开面仅中文名。
"""
from ...身份 import 检查器id#品牌化
from ...json import 是否json值,是否普通对象#JSON
from ...校验 import 精确键#精确键
from ..版本 import 检查器协议版本#协议版本
from .运行时 import (#Runtime解析
    解析客户端控制台能力,解析客户端控制台控制帧,解析客户端控制台事件帧,
    解析客户端运行时能力,解析客户端运行时取消帧,解析客户端运行时请求帧,
    解析客户端运行时响应确认帧,解析客户端运行时响应帧,解析客户端运行时会话关闭帧,
)
from .源 import (#源解析
    解析客户端源请求帧,解析客户端源响应帧,解析客户端源会话关闭帧,解析客户端源能力,
)

__all__=[#仅中文公开名
    '检查器协议版本','检查器源种类','检查器源能力','检查器源描述符','检查器记录输入',
    '源打开帧','源替换帧','源追加帧','源关闭帧','源到工作者帧',
    '源接纳帧','源追加确认帧','源重快照帧','源拒绝帧','工作者到源帧',
    '解析工作者源帧','解析源帧',
]#公开面结束

检查器源种类=('host','client')#源种类

def 源标识(值):#校验源标识
    """校验源标识。"""
    if not isinstance(值,str):#须字符串
        raise Exception('inspector protocol: sourceId must be a string')#英文诊断
    return 检查器id(值,'sourceId')#品牌化

def 世代(值):#校验世代
    """校验世代。"""
    if not isinstance(值,str):#须字符串
        raise Exception('inspector protocol: generation must be a string')#英文诊断
    return 检查器id(值,'generation')#品牌化

def 自然数(值,标签):#非负安全整数
    """非负安全整数。"""
    if not isinstance(值,int) or isinstance(值,bool) or 值<0:#越界
        raise Exception(f'inspector protocol: {标签} must be a non-negative safe integer')#英文诊断
    return 值#自然数

def 解析记录(值):#解析观测记录
    """解析观测记录。"""
    if (not 是否普通对象(值) or not isinstance(值.get('monotonicMs'),(int,float)) or isinstance(值.get('monotonicMs'),bool)
        or not (值['monotonicMs']==值['monotonicMs']) or not isinstance(值.get('topic'),str)
        or len(值['topic'])==0 or len(值['topic'])>128 or not 是否json值(值.get('payload'))):#非法
        raise Exception('inspector protocol: invalid observation record')#英文诊断
    精确键(值,['monotonicMs','topic','payload'],'observation record')#精确字段
    return {'monotonicMs':值['monotonicMs'],'topic':值['topic'],'payload':值['payload']}#记录

def 解析源能力(值):#解析源能力
    """解析源能力。"""
    if not 是否普通对象(值) or not isinstance(值.get('type'),str):#须有type
        raise Exception('inspector protocol: source capability must have a type')#英文诊断
    if 值['type']=='client-runtime':#Runtime能力
        return 解析客户端运行时能力(值)#Runtime能力
    if 值['type']=='client-console':#Console能力
        return 解析客户端控制台能力(值)#Console能力
    if 值['type']=='client-sources':#源目录能力
        return 解析客户端源能力(值)#源目录能力
    raise Exception(f'inspector protocol: unknown source capability {值["type"]!r}')#英文诊断

def 解析打开(值):#解析打开帧
    """解析打开帧。"""
    精确键(值,['v','t','source','topics'],'source/open frame')#精确字段
    if not 是否普通对象(值.get('source')) or not isinstance(值.get('topics'),list):#形状非法
        raise Exception('inspector protocol: source/open needs source and topics')#英文诊断
    源=值['source']#源对象
    精确键(源,['sourceId','generation','kind','label','timeOriginMs','capabilities'],'source descriptor')#精确字段
    种类=源['kind']#源种类
    if 种类 not in ('host','client'):#种类非法
        raise Exception('inspector protocol: invalid source kind')#英文诊断
    if not isinstance(源.get('label'),str) or len(源['label'])==0 or len(源['label'])>256:#标签非法
        raise Exception('inspector protocol: source label must contain 1 to 256 characters')#英文诊断
    if not isinstance(源.get('timeOriginMs'),(int,float)) or isinstance(源.get('timeOriginMs'),bool) or not (源['timeOriginMs']==源['timeOriginMs']):#时间原点非法
        raise Exception('inspector protocol: source timeOriginMs must be finite')#英文诊断
    if not isinstance(源.get('capabilities'),list):#能力须数组
        raise Exception('inspector protocol: source capabilities must be an array')#英文诊断
    能力们=[解析源能力(项) for 项 in 源['capabilities']]#解析能力
    能力类型=set()#已见能力类型
    for 能力 in 能力们:#逐能力
        if 能力['type'] in 能力类型:#重复类型
            raise Exception(f'inspector protocol: source declares {能力["type"]} more than once')#英文诊断
        能力类型.add(能力['type'])#记入
    if 种类!='client' and len(能力们)>0:#Host不得声明Client能力
        raise Exception('inspector protocol: Host sources cannot declare Client capabilities')#英文诊断
    主题们=[]#主题
    for 主题 in 值['topics']:#校验主题
        if not isinstance(主题,str) or len(主题)==0 or len(主题)>128:#主题非法
            raise Exception('inspector protocol: every source topic must contain 1 to 128 characters')#英文诊断
        主题们.append(主题)#合法主题
    return {'v':检查器协议版本,'t':'source/open','source':{'sourceId':源标识(源['sourceId']),'generation':世代(源['generation']),'kind':种类,'label':源['label'],'timeOriginMs':源['timeOriginMs'],'capabilities':能力们},'topics':主题们}#打开帧

def 解析记录帧(值,最大记录,替换):#解析记录帧
    """解析记录帧。"""
    白名单=['v','t','sourceId','generation','nextSequence','records'] if 替换 else ['v','t','sourceId','generation','firstSequence','droppedBefore','records']#白名单
    精确键(值,白名单,'source/replace frame' if 替换 else 'source/append frame')#精确字段
    if not isinstance(值.get('records'),list) or len(值['records'])>最大记录:#记录超限
        raise Exception(f'inspector protocol: source batch exceeds {最大记录} records')#英文诊断
    记录们=[解析记录(项) for 项 in 值['records']]#解析记录
    公共={'v':检查器协议版本,'sourceId':源标识(值['sourceId']),'generation':世代(值['generation']),'records':记录们}#公共字段
    if 替换:#替换
        return {**公共,'t':'source/replace','nextSequence':自然数(值['nextSequence'],'nextSequence')}#替换帧
    return {**公共,'t':'source/append','firstSequence':自然数(值['firstSequence'],'firstSequence'),'droppedBefore':自然数(值['droppedBefore'],'droppedBefore')}#追加帧

def 解析工作者源帧(值):#解析Worker到源帧
    """解析并重建源收到的一帧 Worker 控制。"""
    if not 是否json值(值) or not 是否普通对象(值) or 值.get('v')!=检查器协议版本 or not isinstance(值.get('t'),str):#信封非法
        raise Exception('inspector protocol: invalid Worker source frame')#英文诊断
    if 值['t']=='source/rejected':#拒绝帧
        精确键(值,['v','t','code','message'],'source/rejected frame')#精确字段
        if 值.get('code') not in ('invalid-frame','version-mismatch','unauthorized') or not isinstance(值.get('message'),str):#码非法
            raise Exception('inspector protocol: invalid source/rejected frame')#英文诊断
        return {'v':检查器协议版本,'t':'source/rejected','code':值['code'],'message':值['message']}#拒绝帧
    if 值['t']=='client-runtime/request':#Runtime请求
        return 解析客户端运行时请求帧(值)#Runtime请求
    if 值['t']=='client-runtime/cancel':#Runtime取消
        return 解析客户端运行时取消帧(值)#Runtime取消
    if 值['t']=='client-runtime/response-acknowledged':#Runtime响应确认
        return 解析客户端运行时响应确认帧(值)#解析确认
    if 值['t']=='client-runtime/session-closed':#Runtime会话关闭
        return 解析客户端运行时会话关闭帧(值)#Runtime会话关闭
    if 值['t']=='client-sources/request':#源请求
        return 解析客户端源请求帧(值)#源请求
    if 值['t']=='client-sources/session-closed':#源会话关闭
        return 解析客户端源会话关闭帧(值)#源会话关闭
    if 值['t'] in ('client-console/enable','client-console/disable'):#Console控制
        return 解析客户端控制台控制帧(值)#解析控制
    公共={'v':检查器协议版本,'sourceId':源标识(值.get('sourceId')),'generation':世代(值.get('generation'))}#公共字段
    if 值['t']=='source/accepted':#接纳
        精确键(值,['v','t','sourceId','generation'],'source/accepted frame')#精确字段
        return {**公共,'t':'source/accepted'}#接纳帧
    if 值['t']=='source/append-acknowledged':#追加确认
        精确键(值,['v','t','sourceId','generation','nextSequence'],'source append acknowledgement')#精确字段
        return {**公共,'t':'source/append-acknowledged','nextSequence':自然数(值['nextSequence'],'nextSequence')}#确认帧
    if 值['t']=='source/resnapshot' and isinstance(值.get('reason'),str):#重快照
        精确键(值,['v','t','sourceId','generation','expectedSequence','reason'],'source/resnapshot frame')#精确字段
        return {**公共,'t':'source/resnapshot','expectedSequence':自然数(值['expectedSequence'],'expectedSequence'),'reason':值['reason']}#重快照帧
    raise Exception(f'inspector protocol: unknown Worker source frame {值["t"]!r}')#英文诊断

def 解析源帧(值,最大记录):#解析源到Worker帧
    """解析并重建在进程或网络边界收到的一帧源帧。"""
    if not 是否json值(值) or not 是否普通对象(值):#须JSON对象
        raise Exception('inspector protocol: source frame must be a lossless JSON object')#英文诊断
    if 值.get('v')!=检查器协议版本:#版本不支持
        raise Exception(f'inspector protocol: unsupported version {值.get("v")!r}')#英文诊断
    类型=值.get('t')#类型
    if 类型=='source/open':#打开
        return 解析打开(值)#解析打开
    if 类型=='source/replace':#替换
        return 解析记录帧(值,最大记录,True)#解析替换
    if 类型=='source/append':#追加
        return 解析记录帧(值,最大记录,False)#解析追加
    if 类型=='source/close':#关闭
        精确键(值,['v','t','sourceId','generation'],'source/close frame')#精确字段
        return {'v':检查器协议版本,'t':'source/close','sourceId':源标识(值['sourceId']),'generation':世代(值['generation'])}#关闭帧
    if 类型=='client-runtime/response':#Runtime响应
        return 解析客户端运行时响应帧(值)#解析响应
    if 类型=='client-console/event':#Console事件
        return 解析客户端控制台事件帧(值)#解析事件
    if 类型=='client-sources/response':#源响应
        return 解析客户端源响应帧(值)#解析响应
    raise Exception(f'inspector protocol: unknown source frame {类型!r}')#英文诊断
