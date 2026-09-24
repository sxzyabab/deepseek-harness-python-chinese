from ...依赖.schemastery import 字段,字典字段
from ...依赖.工具 import 是否表达式节点
from .脱敏 import 脱敏密钥

def 朴素配置(值):
    """从配置快照去掉运行时引用，得到可脱敏与填表的普通值。"""
    取=getattr(值,'get',None)
    if callable(取) and not isinstance(值,(dict,list,str,bytes,int,float,bool,type(None))):
        return 朴素配置(值.get())
    if isinstance(值,list):
        return [朴素配置(项) for 项 in 值]
    if isinstance(值,dict):
        return {键:朴素配置(孩子) for 键,孩子 in 值.items()}
    return 值

def 朴素模式(模式):
    """去掉易变标记，并对密钥缺省做脱敏。"""
    根=字段() if not isinstance(模式,字段) else 模式
    结果=type(模式)(模式.toJSON()) if hasattr(模式,'toJSON') else 模式
    def 行走(节点):
        """递归剥易变与密钥缺省。"""
        元=getattr(节点,'meta',None)
        if isinstance(元,dict):
            元.pop('volatile',None)
            if 元.get('role')=='secret':
                元.pop('default',None)
                元.pop('required',None)
            elif 元.get('default') is not None:
                元['default']=脱敏密钥(节点,元['default'])['value']
        字典=getattr(节点,'dict',None) or {}
        for 孩子 in 字典.values():
            行走(孩子)
        内层=getattr(节点,'inner',None)
        if 内层 is not None:
            行走(内层)
        for 孩子 in getattr(节点,'list',None) or []:
            行走(孩子)
    行走(结果)
    _=根
    return 结果

def 易变表单(模式):
    """选出最近易变祖先使其可不重挂即编辑的字段。"""
    元=getattr(模式,'meta',None) or {}
    if 元.get('volatile'):
        return 朴素模式(模式)
    if getattr(模式,'type',None)=='object':
        字典={}
        for 键,孩子 in (getattr(模式,'dict',None) or {}).items():
            字段模式=易变表单(孩子)
            if 字段模式 is not None:
                字典[键]=字段模式
        if len(字典)==0:
            return None
        return 字典字段(字典) if not isinstance(字典字段,type) else 模式
    return None

def 投影表单(模式,值):
    """只投影模式声明字段，排除普通配置。"""
    if getattr(模式,'type',None)=='object' and isinstance(值,dict) and not 是否表达式节点(值):
        结果={}
        for 键,孩子 in (getattr(模式,'dict',None) or {}).items():
            if 键 not in 值:
                continue
            结果[键]=投影表单(孩子,值[键])
        return 结果
    return 值

def 是否易变路径(模式,路径):
    """字段路径是否落在已声明易变节点之下。"""
    元=getattr(模式,'meta',None) or {}
    if 元.get('volatile'):
        return True
    if len(路径)==0:
        return False
    键=路径[0]
    其余=路径[1:]
    孩子=(getattr(模式,'dict',None) or {}).get(键)
    return 孩子 is not None and 是否易变路径(孩子,其余)

__all__=['朴素配置','易变表单','投影表单','是否易变路径']
