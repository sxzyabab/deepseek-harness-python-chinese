"""Client 源目录操作的带版本信封。

对齐上游 `shared/bridge/messages/sources/frames.ts`。公开面仅中文名。
"""
from ....json import 是否普通对象#普通对象
from ....校验 import 精确键,精确对象,线上标识#校验
from ...版本 import 检查器协议版本#协议版本
from .编解码 import 解析客户端源命令,解析客户端源结果#编解码
from .命令 import 客户端源错误码#错误码

__all__=[#仅中文公开名
    '客户端源能力','客户端源请求帧','客户端源响应帧','客户端源会话关闭帧',
    '解析客户端源能力','解析客户端源请求帧','解析客户端源响应帧','解析客户端源会话关闭帧',
]#公开面结束

错误码集合=set(客户端源错误码)#源错误码

def 解析结果封装(值):#解析结果
    """解析结果。"""
    if not 是否普通对象(值) or not isinstance(值.get('ok'),bool):#须有ok
        raise Exception('inspector protocol: invalid Client source outcome')#英文诊断
    if 值['ok']:#成功
        精确键(值,['ok','result'],'successful Client source outcome')#精确字段
        return {'ok':True,'result':解析客户端源结果(值['result'])}#成功结果
    精确键(值,['ok','error'],'failed Client source outcome')#失败字段
    错误=精确对象(值['error'],['code','message'],'Client source error')#错误对象
    if 错误['code'] not in 错误码集合 or not isinstance(错误['message'],str):#错误非法
        raise Exception('inspector protocol: invalid Client source error')#英文诊断
    return {'ok':False,'error':{'code':错误['code'],'message':错误['message']}}#失败结果

def 解析客户端源能力(值):#解析源能力
    """解析 Client 源目录的标记能力。"""
    记录=精确对象(值,['type'],'Client Sources capability')#精确对象
    if 记录['type']!='client-sources':#类型须匹配
        raise Exception('inspector protocol: invalid Client Sources capability')#英文诊断
    return {'type':'client-sources'}#标记能力

def 解析客户端源请求帧(值):#解析源请求
    """解析一帧 Worker-到-Client 源请求。"""
    精确键(值,['v','t','sourceId','generation','sessionId','requestId','command'],'Client source request')#精确字段
    if 值.get('v')!=检查器协议版本 or 值.get('t')!='client-sources/request':#信封非法
        raise Exception('inspector protocol: invalid Client source request envelope')#英文诊断
    return {'v':检查器协议版本,'t':'client-sources/request','sourceId':线上标识(值['sourceId'],'sourceId'),'generation':线上标识(值['generation'],'generation'),'sessionId':线上标识(值['sessionId'],'sessionId'),'requestId':线上标识(值['requestId'],'requestId'),'command':解析客户端源命令(值['command'])}#请求帧

def 解析客户端源响应帧(值):#解析源响应
    """解析一帧 Client-到-Worker 源响应。"""
    精确键(值,['v','t','sourceId','generation','sessionId','requestId','outcome'],'Client source response')#精确字段
    if 值.get('v')!=检查器协议版本 or 值.get('t')!='client-sources/response':#信封非法
        raise Exception('inspector protocol: invalid Client source response envelope')#英文诊断
    return {'v':检查器协议版本,'t':'client-sources/response','sourceId':线上标识(值['sourceId'],'sourceId'),'generation':线上标识(值['generation'],'generation'),'sessionId':线上标识(值['sessionId'],'sessionId'),'requestId':线上标识(值['requestId'],'requestId'),'outcome':解析结果封装(值['outcome'])}#响应帧

def 解析客户端源会话关闭帧(值):#解析会话关闭
    """解析一帧 Client 源会话清理通知。"""
    精确键(值,['v','t','sourceId','generation','sessionId'],'Client source session close')#精确字段
    if 值.get('v')!=检查器协议版本 or 值.get('t')!='client-sources/session-closed':#信封非法
        raise Exception('inspector protocol: invalid Client source session close envelope')#英文诊断
    return {'v':检查器协议版本,'t':'client-sources/session-closed','sourceId':线上标识(值['sourceId'],'sourceId'),'generation':线上标识(值['generation'],'generation'),'sessionId':线上标识(值['sessionId'],'sessionId')}#关闭帧
