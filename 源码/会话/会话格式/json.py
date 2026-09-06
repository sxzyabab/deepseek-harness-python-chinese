"""耐久会话格式 JSON 边界校验与快照。"""
import math#负零与有限数
from ...工具.值 import 快照json值,深冻结#JSON快照与深冻结
from .错误 import 会话格式错误#导入格式错误

安全整数上限=9007199254740991#外来JSON Number.MAX_SAFE_INTEGER

def 是否负零(值):#IEEE 负零
    """值为 IEEE 负零时为真。"""
    if not isinstance(值,float):#非浮点
        return False#不是负零
    return 值==0.0 and math.copysign(1.0,值)<0#符号为负的零

def 是否会话格式json对象(值):#是否JSON对象
    """测试值是否为非 null、非数组对象。"""
    return isinstance(值,dict)#对象判定

def 会话格式计数(值,标签):#格式计数
    """要求非负外来安全整数且排除 JSON 不稳定的负零。"""
    if isinstance(值,bool):#布尔不是整数
        raise 会话格式错误(标签+' must be a non-negative safe integer')#错误
    if isinstance(值,int):#整数
        合法=abs(值)<=安全整数上限#安全范围
    elif isinstance(值,float) and math.isfinite(值) and 值==int(值):#整值浮点
        合法=abs(值)<=安全整数上限#安全范围
    else:#其它类型
        合法=False#非法
    if (not 合法) or 值<0 or 是否负零(值):#非法
        raise 会话格式错误(标签+' must be a non-negative safe integer')#错误
    return int(值)#返回

def 会话格式安全整数(值,标签):#安全整数
    """要求外来安全整数且排除 JSON 不稳定的负零。"""
    if isinstance(值,bool):#布尔不是整数
        raise 会话格式错误(标签+' must be a safe integer')#错误
    if isinstance(值,int):#整数
        合法=abs(值)<=安全整数上限#安全范围
    elif isinstance(值,float) and math.isfinite(值) and 值==int(值):#整值浮点
        合法=abs(值)<=安全整数上限#安全范围
    else:#其它类型
        合法=False#非法
    if (not 合法) or 是否负零(值):#非法
        raise 会话格式错误(标签+' must be a safe integer')#错误
    return int(值)#返回

def 会话格式版本(值,标签='Session format version'):#格式版本
    """要求非负整数格式版本。"""
    return 会话格式计数(值,标签)#委托计数

def 检查会话格式版本(头值):#检查格式版本
    """仅读取方向分发所需的版本。"""
    if not 是否会话格式json对象(头值):#非对象
        raise 会话格式错误('Session header must be a JSON object')#错误
    return 会话格式版本(头值['version'])#取版本

def 快照会话格式json(值,标签='Session value'):#快照JSON
    """分离并深冻结调用方提供的无损 JSON 值。"""
    快照=快照json值(值)#深快照
    if 快照 is None:#非无损
        raise 会话格式错误(标签+' is not lossless JSON')#错误
    return 深冻结(快照)#深冻结

def 快照会话格式产物(产物,标签='Session artifact'):#快照产物
    """快照一份完整产物并校验其共享坐标。"""
    快照=快照会话格式json(产物,标签)#快照对象
    if not 是否会话格式json对象(快照):#非对象
        raise 会话格式错误(标签+' must be a JSON object')#错误
    头=快照['header']#头
    继承事件数=快照['inheritedEventCount']#继承数
    事件列表=快照['events']#事件
    if not 是否会话格式json对象(头):#头非法
        raise 会话格式错误(标签+' header must be a JSON object')#头非法
    检查会话格式版本(头)#检查版本
    会话格式计数(继承事件数,标签+' inheritedEventCount')#校验继承
    if not isinstance(事件列表,list):#事件非数组
        raise 会话格式错误(标签+' events must be an array')#事件非数组
    for 下标 in range(len(事件列表)):#遍历事件
        事件=事件列表[下标]#当前事件
        if not 是否会话格式json对象(事件):#非对象
            raise 会话格式错误(标签+' event '+str(下标)+' must be a JSON object')#非对象
        if 事件['seq']!=下标:#seq非稠密
            序号=事件['seq'] if 'seq' in 事件 else None#诊断序号
            raise 会话格式错误(标签+' event '+str(下标)+' has non-dense seq '+str(序号))#seq错误
        if 'type' not in 事件:#缺类型
            raise 会话格式错误(标签+' event '+str(下标)+' type must be a non-empty string')#类型错误
        类型=事件['type']#类型
        if not isinstance(类型,str) or len(类型)==0:#类型非法
            raise 会话格式错误(标签+' event '+str(下标)+' type must be a non-empty string')#类型错误
        会话格式安全整数(事件['time'],标签+' event '+str(下标)+' time')#校验时间
        if 'data' not in 事件:#缺data
            raise 会话格式错误(标签+' event '+str(下标)+' lacks data')#缺data
    if int(继承事件数)>len(事件列表):#继承超事件数
        raise 会话格式错误(标签+' inheritedEventCount exceeds its event count')#错误
    return 快照#返回产物

def 快照会话格式头(头,标签='Session header'):#快照头
    """快照一个逻辑头且不检查事件体。"""
    快照=快照会话格式json(头,标签)#快照
    if not 是否会话格式json对象(快照):#非对象
        raise 会话格式错误(标签+' must be a JSON object')#非对象
    检查会话格式版本(快照)#检查版本
    if 'id' not in 快照 or not isinstance(快照['id'],str):#id非法
        raise 会话格式错误(标签+' id must be a string')#id非法
    会话格式计数(快照['createdAt'],标签+' createdAt')#校验创建时间
    if 'isSeeded' not in 快照 or not isinstance(快照['isSeeded'],bool):#isSeeded非法
        raise 会话格式错误(标签+' isSeeded must be a boolean')#isSeeded非法
    会话格式计数(快照['delegationDepth'],标签+' delegationDepth')#校验委派深度
    return 快照#返回头
