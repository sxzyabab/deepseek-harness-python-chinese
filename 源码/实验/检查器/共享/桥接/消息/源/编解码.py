"""Client 源目录操作与值的精确解码器。

对齐上游 `shared/bridge/messages/sources/codec.ts`。公开面仅中文名。
"""
import re#Base64校验
from ....json import 是否普通对象#普通对象
from ....校验 import 精确键,精确对象,可选布尔,可选字符串,线上标识#校验

__all__=['解析客户端源命令','解析客户端源结果']#仅中文公开名

基64规则=re.compile(r'^(?:[A-Za-z\d+/]{4})*(?:[A-Za-z\d+/]{2}==|[A-Za-z\d+/]{3}=)?$')#Base64校验

def 自然数(值,标签,允许零):#自然数
    """自然数校验。"""
    if not isinstance(值,int) or isinstance(值,bool) or 值<(0 if 允许零 else 1):#越界
        raise Exception(f'inspector protocol: {标签} must be {"a non-negative" if 允许零 else "a positive"} integer')#英文诊断
    return 值#自然数

def 内容种类(值):#内容种类
    """内容种类。"""
    if 值 not in ('source','source-map'):#非法种类
        raise Exception('inspector protocol: invalid Client source content kind')#英文诊断
    return 值#种类

def 解析脚本(值):#解析脚本描述
    """解析脚本描述。"""
    记录=精确对象(值,['scriptKey','url','hash','buildId','sourceMapUrl','startLine','startColumn','endLine','endColumn','isModule','length'],'Client script descriptor')#精确对象
    if not isinstance(记录.get('url'),str) or len(记录['url'])>8192 or not isinstance(记录.get('hash'),str):#身份非法
        raise Exception('inspector protocol: invalid Client script identity')#英文诊断
    结果={'scriptKey':线上标识(记录['scriptKey'],'scriptKey'),'url':记录['url'],'hash':记录['hash']}#脚本描述
    结果.update(可选字符串(记录,'buildId'))#构建标识
    结果.update(可选字符串(记录,'sourceMapUrl'))#source map
    结果['startLine']=自然数(记录['startLine'],'startLine',True)#起始行
    结果['startColumn']=自然数(记录['startColumn'],'startColumn',True)#起始列
    结果['endLine']=自然数(记录['endLine'],'endLine',True)#结束行
    结果['endColumn']=自然数(记录['endColumn'],'endColumn',True)#结束列
    结果.update(可选布尔(记录,'isModule'))#是否模块
    if 记录.get('length') is not None:#长度
        结果['length']=自然数(记录['length'],'length',True)#长度
    return 结果#脚本描述

def 解析客户端源命令(值):#解析源命令
    """解析一条 Worker-到-Client 源命令。"""
    if not 是否普通对象(值) or not isinstance(值.get('op'),str):#须有op
        raise Exception('inspector protocol: Client source command must have an op')#英文诊断
    if 值['op']=='list-scripts':#列脚本
        精确键(值,['op'],'Client source list command')#精确字段
        return {'op':'list-scripts'}#列表命令
    if 值['op']!='get-content-chunk':#未知操作
        raise Exception(f'inspector protocol: unknown Client source command {值["op"]!r}')#英文诊断
    精确键(值,['op','scriptKey','content','offset','maxBytes'],'Client source chunk command')#精确字段
    return {'op':'get-content-chunk','scriptKey':线上标识(值['scriptKey'],'scriptKey'),'content':内容种类(值['content']),'offset':自然数(值['offset'],'offset',True),'maxBytes':自然数(值['maxBytes'],'maxBytes',False)}#分片命令

def 解析客户端源结果(值):#解析源结果
    """解析一次成功的 Client 源结果。"""
    if not 是否普通对象(值) or not isinstance(值.get('op'),str):#须有op
        raise Exception('inspector protocol: Client source result must have an op')#英文诊断
    if 值['op']=='list-scripts':#列表结果
        精确键(值,['op','scripts'],'Client source list result')#精确字段
        if not isinstance(值.get('scripts'),list):#须数组
            raise Exception('inspector protocol: Client source scripts must be an array')#英文诊断
        return {'op':'list-scripts','scripts':[解析脚本(项) for 项 in 值['scripts']]}#解析脚本
    if 值['op']!='get-content-chunk':#未知结果
        raise Exception(f'inspector protocol: unknown Client source result {值["op"]!r}')#英文诊断
    if 值.get('available') is False:#不可用
        精确键(值,['op','scriptKey','content','available'],'unavailable Client source chunk')#精确字段
        return {'op':'get-content-chunk','scriptKey':线上标识(值['scriptKey'],'scriptKey'),'content':内容种类(值['content']),'available':False}#不可用结果
    精确键(值,['op','scriptKey','content','available','offset','nextOffset','data','eof'],'Client source chunk result')#精确字段
    if 值.get('available') is not True or not isinstance(值.get('data'),str) or not isinstance(值.get('eof'),bool):#形状非法
        raise Exception('inspector protocol: invalid Client source chunk result')#英文诊断
    偏移=自然数(值['offset'],'offset',True)#起始偏移
    下一偏移=自然数(值['nextOffset'],'nextOffset',True)#下一偏移
    if 下一偏移<偏移 or not 基64规则.fullmatch(值['data']):#数据非法
        raise Exception('inspector protocol: invalid Client source chunk data')#英文诊断
    return {'op':'get-content-chunk','scriptKey':线上标识(值['scriptKey'],'scriptKey'),'content':内容种类(值['content']),'available':True,'offset':偏移,'nextOffset':下一偏移,'data':值['data'],'eof':值['eof']}#可用结果
