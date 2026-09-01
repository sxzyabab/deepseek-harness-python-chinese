"""设置控制器投影与写入辅助。

对齐上游 settings-controller 私有辅助。公开面仅中文名。
"""
from .工具 import 取字段,远程错误,远程错误消息#基础

__all__=['命名空间视图','设置冲突','拒绝写入','消息']#仅中文公开名

def 命名空间视图(描述符):#红化描述符→视图
    """逐字段投影设置描述符，避免多余可枚举属性泄漏到线上。"""
    视图={#基础字段
        'ns':str(取字段(描述符,'ns')),#命名空间
        'schema':取字段(描述符,'schema'),#schema
        'value':取字段(描述符,'value'),#值
        'applies':取字段(描述符,'applies'),#适用性
        'secrets':[{'path':list(取字段(项,'path') or []),'set':取字段(项,'set')} for 项 in (取字段(描述符,'secrets') or [])],#秘密元数据
        'revision':取字段(描述符,'revision'),#修订
    }#视图
    if 取字段(描述符,'base') is not None:#有 base
        视图['base']=取字段(描述符,'base')#base
    if 取字段(描述符,'user') is not None:#有 user
        视图['user']=取字段(描述符,'user')#user
    return 视图#返回

def 设置冲突(错误):#解析 SETTINGS_CONFLICT
    """识别陈旧写入冲突。"""
    码=取字段(错误,'code')#码
    if 码!='SETTINGS_CONFLICT':#不是冲突
        return None#不是
    if not all(isinstance(取字段(错误,键),(int,str)) for 键 in ('message','expected','actual')):#形态
        return None#不是
    return 错误#冲突对象

def 拒绝写入(命名空间,错误):#分类写入拒绝
    """把 seam 拒绝映射为 settings/conflict 或 settings/rejected。"""
    冲突=设置冲突(错误)#冲突？
    if 冲突 is not None:#冲突
        return 远程错误('settings/conflict',str(取字段(冲突,'message')),{'ns':命名空间,'expected':取字段(冲突,'expected'),'actual':取字段(冲突,'actual')},cause=错误)#冲突
    return 远程错误('settings/rejected',远程错误消息(错误),{'ns':命名空间},cause=错误)#拒绝

def 消息(错误):#错误消息
    """取错误消息字符串。"""
    return 远程错误消息(错误)#委托
