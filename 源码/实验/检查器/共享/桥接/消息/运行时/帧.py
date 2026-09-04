"""Worker-到-Client Runtime 操作的带版本信封。

对齐上游 `shared/bridge/messages/runtime/frames.ts`。公开面仅中文名。
"""
from ....json import 是否普通对象#普通对象
from ....校验 import 精确键,精确对象,线上标识#校验
from ...版本 import 检查器协议版本#协议版本
from .命令编解码 import 解析客户端运行时命令#命令
from .值编解码 import 解析客户端运行时结果#结果
from .命令 import 客户端运行时错误码#错误码

__all__=[#仅中文公开名
    '客户端运行时能力','客户端运行时请求帧','客户端运行时取消帧',
    '客户端运行时响应确认帧','客户端运行时响应帧','客户端运行时会话关闭帧',
    '解析客户端运行时能力','解析客户端运行时请求帧','解析客户端运行时取消帧',
    '解析客户端运行时响应确认帧','解析客户端运行时响应帧','解析客户端运行时会话关闭帧',
]#公开面结束

错误码集合=set(客户端运行时错误码)#Runtime错误码

def 解析结果封装(值):#解析结果封装
    """解析结果封装。"""
    if not 是否普通对象(值) or not isinstance(值.get('ok'),bool):#须有ok
        raise Exception('inspector protocol: invalid Client Runtime outcome')#英文诊断
    if 值['ok']:#成功
        精确键(值,['ok','result'],'successful Client Runtime outcome')#精确字段
        return {'ok':True,'result':解析客户端运行时结果(值['result'])}#成功结果
    精确键(值,['ok','error'],'failed Client Runtime outcome')#失败字段
    错误=精确对象(值['error'],['code','message'],'Client Runtime error')#错误对象
    if 错误['code'] not in 错误码集合 or not isinstance(错误['message'],str):#错误非法
        raise Exception('inspector protocol: invalid Client Runtime error')#英文诊断
    return {'ok':False,'error':{'code':错误['code'],'message':错误['message']}}#失败结果

def 解析客户端运行时能力(值):#解析Runtime能力
    """解析并重建一个 Client Runtime 能力。"""
    记录=精确对象(值,['type','origin'],'Client Runtime capability')#精确对象
    if 记录['type']!='client-runtime' or not isinstance(记录.get('origin'),str) or len(记录['origin'])>2048:#形状非法
        raise Exception('inspector protocol: invalid Client Runtime capability')#英文诊断
    return {'type':'client-runtime','origin':记录['origin']}#能力

def 解析客户端运行时请求帧(值):#解析Runtime请求
    """解析并重建一帧 Worker-到-Client Runtime 请求。"""
    精确键(值,['v','t','sourceId','generation','sessionId','requestId','command'],'Client Runtime request')#精确字段
    if 值.get('v')!=检查器协议版本 or 值.get('t')!='client-runtime/request':#信封非法
        raise Exception('inspector protocol: invalid Client Runtime request envelope')#英文诊断
    return {'v':检查器协议版本,'t':'client-runtime/request','sourceId':线上标识(值['sourceId'],'sourceId'),'generation':线上标识(值['generation'],'generation'),'sessionId':线上标识(值['sessionId'],'sessionId'),'requestId':线上标识(值['requestId'],'requestId'),'command':解析客户端运行时命令(值['command'])}#请求帧

def 解析客户端运行时取消帧(值):#解析取消帧
    """解析并重建一帧 Worker-到-Client Runtime 取消。"""
    精确键(值,['v','t','sourceId','generation','sessionId','requestId'],'Client Runtime cancellation')#精确字段
    if 值.get('v')!=检查器协议版本 or 值.get('t')!='client-runtime/cancel':#信封非法
        raise Exception('inspector protocol: invalid Client Runtime cancellation envelope')#英文诊断
    return {'v':检查器协议版本,'t':'client-runtime/cancel','sourceId':线上标识(值['sourceId'],'sourceId'),'generation':线上标识(值['generation'],'generation'),'sessionId':线上标识(值['sessionId'],'sessionId'),'requestId':线上标识(值['requestId'],'requestId')}#取消帧

def 解析客户端运行时响应确认帧(值):#解析响应确认
    """解析并重建一帧 Worker 对 Client Runtime 响应的确认。"""
    精确键(值,['v','t','sourceId','generation','sessionId','requestId'],'Client Runtime response acknowledgement')#精确字段
    if 值.get('v')!=检查器协议版本 or 值.get('t')!='client-runtime/response-acknowledged':#信封非法
        raise Exception('inspector protocol: invalid Client Runtime response acknowledgement envelope')#英文诊断
    return {'v':检查器协议版本,'t':'client-runtime/response-acknowledged','sourceId':线上标识(值['sourceId'],'sourceId'),'generation':线上标识(值['generation'],'generation'),'sessionId':线上标识(值['sessionId'],'sessionId'),'requestId':线上标识(值['requestId'],'requestId')}#确认帧

def 解析客户端运行时响应帧(值):#解析Runtime响应
    """解析并重建一帧 Client-到-Worker Runtime 响应。"""
    精确键(值,['v','t','sourceId','generation','sessionId','requestId','outcome'],'Client Runtime response')#精确字段
    if 值.get('v')!=检查器协议版本 or 值.get('t')!='client-runtime/response':#信封非法
        raise Exception('inspector protocol: invalid Client Runtime response envelope')#英文诊断
    return {'v':检查器协议版本,'t':'client-runtime/response','sourceId':线上标识(值['sourceId'],'sourceId'),'generation':线上标识(值['generation'],'generation'),'sessionId':线上标识(值['sessionId'],'sessionId'),'requestId':线上标识(值['requestId'],'requestId'),'outcome':解析结果封装(值['outcome'])}#响应帧

def 解析客户端运行时会话关闭帧(值):#解析会话关闭
    """解析并重建一帧 Runtime 会话清理通知。"""
    精确键(值,['v','t','sourceId','generation','sessionId'],'Client Runtime session close')#精确字段
    if 值.get('v')!=检查器协议版本 or 值.get('t')!='client-runtime/session-closed':#信封非法
        raise Exception('inspector protocol: invalid Client Runtime session close envelope')#英文诊断
    return {'v':检查器协议版本,'t':'client-runtime/session-closed','sourceId':线上标识(值['sourceId'],'sourceId'),'generation':线上标识(值['generation'],'generation'),'sessionId':线上标识(值['sessionId'],'sessionId')}#关闭帧
