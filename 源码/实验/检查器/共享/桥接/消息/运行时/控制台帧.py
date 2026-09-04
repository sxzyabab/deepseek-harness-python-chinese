"""Client Console 会话与事件的类型化传输。

对齐上游 `shared/bridge/messages/runtime/console-frames.ts`。公开面仅中文名。
"""
from ....json import 是否普通对象#普通对象
from ....校验 import 精确键,精确对象,线上标识#校验
from ....cdp.控制台 import 运行时控制台类型#Console类别
from ...版本 import 检查器协议版本#协议版本
from .值编解码 import 解析客户端运行时异常详情,解析客户端运行时远程对象,解析客户端运行时栈跟踪#值编解码

__all__=[#仅中文公开名
    '客户端控制台能力','客户端控制台启用帧','客户端控制台禁用帧','客户端控制台事件帧',
    '解析客户端控制台能力','解析客户端控制台控制帧','解析客户端控制台事件帧',
]#公开面结束

控制台类型集合=set(运行时控制台类型)#Console类别集合

def 整数(值,标签):#整数校验
    """整数校验。"""
    if not isinstance(值,int) or isinstance(值,bool):#须安全整数
        raise Exception(f'inspector protocol: {标签} must be an integer')#英文诊断
    return 值#整数

def 解析事件(值):#解析事件
    """解析事件。"""
    if not 是否普通对象(值) or 值.get('type') not in ('console-api','exception'):#种类非法
        raise Exception('inspector protocol: invalid Client Console event')#英文诊断
    if 值['type']=='console-api':#Console API
        精确键(值,['type','event'],'Client Console API event')#精确字段
        事件=精确对象(值['event'],['type','arguments','timestamp','contextId','stackTrace'],'Console API event')#事件体
        if 事件.get('type') not in 控制台类型集合 or not isinstance(事件.get('arguments'),list) or not isinstance(事件.get('timestamp'),(int,float)) or isinstance(事件.get('timestamp'),bool) or not (事件['timestamp']==事件['timestamp']):#非法
            raise Exception('inspector protocol: invalid Console API event')#英文诊断
        载荷={'type':事件['type'],'arguments':[解析客户端运行时远程对象(项) for 项 in 事件['arguments']],'timestamp':事件['timestamp']}#事件载荷
        if 事件.get('contextId') is not None:#可选上下文
            载荷['contextId']=整数(事件['contextId'],'contextId')#上下文
        if 事件.get('stackTrace') is not None:#可选栈
            载荷['stackTrace']=解析客户端运行时栈跟踪(事件['stackTrace'])#栈
        return {'type':'console-api','event':载荷}#API事件
    精确键(值,['type','event'],'Client exception event')#异常事件字段
    事件=精确对象(值['event'],['timestamp','contextId','details'],'Client exception event payload')#异常载荷
    if not isinstance(事件.get('timestamp'),(int,float)) or isinstance(事件.get('timestamp'),bool) or not (事件['timestamp']==事件['timestamp']):#时间戳非法
        raise Exception('inspector protocol: invalid Client exception timestamp')#英文诊断
    载荷={'timestamp':事件['timestamp'],'details':解析客户端运行时异常详情(事件['details'])}#事件载荷
    if 事件.get('contextId') is not None:#可选上下文
        载荷['contextId']=整数(事件['contextId'],'contextId')#上下文
    return {'type':'exception','event':载荷}#异常事件

def 解析客户端控制台能力(值):#解析Console能力
    """解析 Client Console 转发的标记能力。"""
    记录=精确对象(值,['type'],'Client Console capability')#精确对象
    if 记录['type']!='client-console':#类型须匹配
        raise Exception('inspector protocol: invalid Client Console capability')#英文诊断
    return {'type':'client-console'}#标记能力

def 解析客户端控制台控制帧(值):#解析Console控制帧
    """解析一帧 Worker-到-Client Console 生命周期帧。"""
    精确键(值,['v','t','sourceId','generation','sessionId'],'Client Console control frame')#精确字段
    if 值.get('v')!=检查器协议版本 or 值.get('t') not in ('client-console/enable','client-console/disable'):#信封非法
        raise Exception('inspector protocol: invalid Client Console control frame')#英文诊断
    return {'v':检查器协议版本,'t':值['t'],'sourceId':线上标识(值['sourceId'],'sourceId'),'generation':线上标识(值['generation'],'generation'),'sessionId':线上标识(值['sessionId'],'sessionId')}#控制帧

def 解析客户端控制台事件帧(值):#解析Console事件
    """解析一帧 Client-到-Worker Console 事件。"""
    精确键(值,['v','t','sourceId','generation','sessionId','event'],'Client Console event frame')#精确字段
    if 值.get('v')!=检查器协议版本 or 值.get('t')!='client-console/event':#信封非法
        raise Exception('inspector protocol: invalid Client Console event envelope')#英文诊断
    return {'v':检查器协议版本,'t':'client-console/event','sourceId':线上标识(值['sourceId'],'sourceId'),'generation':线上标识(值['generation'],'generation'),'sessionId':线上标识(值['sessionId'],'sessionId'),'event':解析事件(值['event'])}#事件帧
