"""非 CDP Inspector 查询帧的精确解码器。

对齐上游 `shared/bridge/messages/query/codec.ts`。公开面仅中文名。
"""
from ....cordis.模型 import 解析cordis运行时树#解析树
from ....json import 是否普通对象#普通对象
from ....校验 import 精确键,精确对象,线上标识#校验
from ...版本 import 检查器协议版本#协议版本
from .命令 import 查询错误码#错误码

__all__=[#仅中文公开名
    '检查器查询帧身份','是否检查器查询请求信封','是否检查器查询响应信封',
    '解析检查器查询请求帧','解析检查器查询帧身份','解析检查器查询响应帧',
]#公开面结束

查询错误码集合=set(查询错误码)#查询错误码集合

def 检查器查询帧身份(sourceId,generation,requestId):#查询帧身份
    """在接受查询体之前可恢复的关联字段。"""
    return {'sourceId':sourceId,'generation':generation,'requestId':requestId}#身份

def 是否检查器查询请求信封(值):#是否查询请求信封
    """测试解码后的载体值是否属于查询请求协议。"""
    return 是否普通对象(值) and 值.get('t')=='query/request'#类型匹配

def 是否检查器查询响应信封(值):#是否查询响应信封
    """测试解码后的载体值是否属于查询响应协议。"""
    return 是否普通对象(值) and 值.get('t')=='query/response'#类型匹配

def 解析查询(值):#解析查询
    """解析查询。"""
    记录=精确对象(值,['op'],'Inspector query')#精确对象
    if 记录['op']!='cordis-tree/get':#未知操作
        raise Exception(f'inspector protocol: unknown query operation {记录["op"]!r}')#英文诊断
    return {'op':'cordis-tree/get'}#取树查询

def 解析结果(值):#解析结果
    """解析结果。"""
    if not 是否普通对象(值) or not isinstance(值.get('op'),str):#须有op
        raise Exception('inspector protocol: query result must have an op')#英文诊断
    if 值['op']=='cordis-tree/get':#取树
        精确键(值,['op','tree'],'Cordis tree query result')#精确字段
        return {'op':'cordis-tree/get','tree':解析cordis运行时树(值['tree'])}#解析树
    raise Exception(f'inspector protocol: unknown query result {值["op"]!r}')#英文诊断

def 解析结果封装(值):#解析结果封装
    """解析结果封装。"""
    if not 是否普通对象(值) or not isinstance(值.get('ok'),bool):#须有ok
        raise Exception('inspector protocol: invalid query outcome')#英文诊断
    if 值['ok']:#成功
        精确键(值,['ok','result'],'successful query outcome')#精确字段
        return {'ok':True,'result':解析结果(值['result'])}#成功结果
    精确键(值,['ok','error'],'failed query outcome')#失败字段
    错误=精确对象(值['error'],['code','message'],'query error')#错误对象
    if 错误['code'] not in 查询错误码集合 or not isinstance(错误['message'],str):#错误非法
        raise Exception('inspector protocol: invalid query error')#英文诊断
    return {'ok':False,'error':{'code':错误['code'],'message':错误['message']}}#失败结果

def 解析检查器查询请求帧(值):#解析查询请求
    """解码一帧源-到-Worker 查询请求。"""
    记录=精确对象(值,['v','t','sourceId','generation','requestId','query'],'query request')#精确对象
    if 记录['v']!=检查器协议版本 or 记录['t']!='query/request':#信封非法
        raise Exception('inspector protocol: invalid query request envelope')#英文诊断
    return {#请求帧
        'v':检查器协议版本,#协议版本
        't':'query/request',#帧类型
        'sourceId':线上标识(记录['sourceId'],'sourceId'),#源标识
        'generation':线上标识(记录['generation'],'generation'),#世代
        'requestId':线上标识(记录['requestId'],'requestId'),#请求标识
        'query':解析查询(记录['query']),#查询体
    }#返回结束

def 解析检查器查询帧身份(值):#解析帧身份
    """解码用于拒绝畸形请求、且不让调用方超时的关联字段。"""
    if not 是否普通对象(值) or 值.get('v')!=检查器协议版本 or 值.get('t')!='query/request':#信封非法
        raise Exception('inspector protocol: invalid query request envelope')#英文诊断
    return {#身份
        'sourceId':线上标识(值['sourceId'],'sourceId'),#源标识
        'generation':线上标识(值['generation'],'generation'),#世代
        'requestId':线上标识(值['requestId'],'requestId'),#请求标识
    }#返回结束

def 解析检查器查询响应帧(值):#解析查询响应
    """解码一帧 Worker-到-源 查询响应。"""
    记录=精确对象(值,['v','t','sourceId','generation','requestId','outcome'],'query response')#精确对象
    if 记录['v']!=检查器协议版本 or 记录['t']!='query/response':#信封非法
        raise Exception('inspector protocol: invalid query response envelope')#英文诊断
    return {#响应帧
        'v':检查器协议版本,#协议版本
        't':'query/response',#帧类型
        'sourceId':线上标识(记录['sourceId'],'sourceId'),#源标识
        'generation':线上标识(记录['generation'],'generation'),#世代
        'requestId':线上标识(记录['requestId'],'requestId'),#请求标识
        'outcome':解析结果封装(记录['outcome']),#结果封装
    }#返回结束
