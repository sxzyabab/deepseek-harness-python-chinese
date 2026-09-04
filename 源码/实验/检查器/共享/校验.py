"""版本化检查器线上协议共用的精确对象读取器。

对齐上游 `shared/validation.ts`。公开面仅中文名。
"""
from .身份 import 检查器id#品牌化
from .json import 是否普通对象#普通对象

__all__=[#仅中文公开名
    '精确对象','精确键','线上标识','可选字符串','可选布尔','可选非负数',
]#公开面结束

def 精确对象(值,键们,标签):#要求精确字段对象
    """要求仅含所列字段的普通对象。"""
    if not 是否普通对象(值):#须为普通对象
        raise Exception(f'inspector protocol: {标签} must be an object')#英文诊断
    精确键(值,键们,标签)#拒绝未知字段
    return 值#已校验

def 精确键(值,键们,标签):#拒绝未知字段
    """拒绝版本化对象声明字段集之外的字段。"""
    允许=set(键们)#允许键集合
    for 键 in 值.keys():#逐自有键
        if not isinstance(键,str) or 键 not in 允许:#非字符串或不在白名单
            raise Exception(f'inspector protocol: {标签} has unknown field {键!r}')#英文诊断

def 线上标识(值,标签):#读取线上标识
    """读取一个非空不透明标识。"""
    if not isinstance(值,str):#须为字符串
        raise Exception(f'inspector protocol: {标签} must be a string')#英文诊断
    return 检查器id(值,标签)#品牌化

def 可选字符串(值,键):#读取可选字符串
    """读取一个可选字符串字段。"""
    if 键 not in 值:#缺席
        return {}#空
    项=值[键]#取字段
    if not isinstance(项,str):#须为字符串
        raise Exception(f'inspector protocol: {键} must be a string')#英文诊断
    return {键:项}#带回字段

def 可选布尔(值,键):#读取可选布尔
    """读取一个可选布尔字段。"""
    if 键 not in 值:#缺席
        return {}#空
    项=值[键]#取字段
    if not isinstance(项,bool):#须为布尔
        raise Exception(f'inspector protocol: {键} must be a boolean')#英文诊断
    return {键:项}#带回字段

def 可选非负数(值,键):#读取可选非负有限数
    """读取一个可选的非负有限数字段。"""
    if 键 not in 值:#缺席
        return {}#空
    项=值[键]#取字段
    if not isinstance(项,(int,float)) or isinstance(项,bool) or not (项==项) or 项<0:#非有限或负
        raise Exception(f'inspector protocol: {键} must be a non-negative finite number')#英文诊断
    return {键:项}#带回字段
