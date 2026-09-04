"""`koffi` 桩：Windows ACL 层与 Landlock 启动器使用的 FFI 桥。
类型构造器返回不透明令牌；任何真正跨入原生代码的入口都大声失败。

对齐上游 `webworker-runtime/src/node/external_packages/koffi.ts`。
"""
import json#诊断序列化
from ..未实现失败 import 未实现失败#未实现桩

__all__=['pointer','struct','array','opaque','types','__esModule','default']#Node面

模块='koffi'#模块名

原始大小们={#原始类型大小（x64 ABI）
    'void':0,'bool':1,'char':1,'uchar':1,'int8':1,'uint8':1,#1字节族
    'short':2,'ushort':2,'int16':2,'uint16':2,#2字节族
    'int':4,'uint':4,'int32':4,'uint32':4,'float':4,'float32':4,#4字节族
    'long':8,'ulong':8,'longlong':8,'ulonglong':8,'int64':8,'uint64':8,#8字节族
    'double':8,'float64':8,'str':8,'str16':8,#指针与浮点
}#原始大小们结束

def 造令牌(标签,大小,对齐=None):#造描述符
    """构造不透明类型描述符。"""
    if 对齐 is None: 对齐=min(大小,8) or 1#默认对齐
    return {'__dshKoffiType':标签,'size':大小,'alignment':对齐}#令牌字面量

def 解析类型(目标):#解析为描述符
    """按名或已有描述符解析类型。"""
    if isinstance(目标,str):#按名
        大小=原始大小们.get(目标)#查表
        if 大小 is None: raise Exception(f'web-preview: koffi type "{目标}" is unknown to the stub')#未知
        return 造令牌(目标,大小)#造令牌
    if not isinstance(目标,dict) or 目标.get('__dshKoffiType') is None:#非法
        raise Exception(f'web-preview: koffi type {json.dumps(目标)} is not a stub descriptor')#报错
    return 目标#交回

def 描述(目标):#取标签
    """取类型标签字符串。"""
    if isinstance(目标,str): return 目标#名
    if isinstance(目标,dict): return 目标.get('__dshKoffiType') or 'anonymous'#标签
    return 'anonymous'#兜底

def pointer(目标):#指针类型
    """指针类型描述符。"""
    return 造令牌(f'pointer({描述(目标)})',8)#8字节指针

def struct(名称,字段们=None):#结构类型
    """结构类型描述符；大小与对齐按 koffi x64 填充规则。"""
    成员们=(字段们 if isinstance(名称,str) else 名称) or {}#字段表
    偏移=0#当前偏移
    对齐=1#结构对齐
    for 成员 in 成员们.values():#遍历字段
        类型=解析类型(成员)#解析字段类型
        对齐=max(对齐,类型['alignment'])#抬齐对齐
        偏移=((偏移+类型['alignment']-1)//类型['alignment'])*类型['alignment']+类型['size']#填充后累加
    大小=((偏移+对齐-1)//对齐)*对齐#尾填充
    结构名=名称 if isinstance(名称,str) else 'anonymous'#结构名
    return 造令牌(f'struct({结构名})',大小,对齐)#结构令牌

def array(目标,长度):#数组类型
    """数组类型描述符。"""
    元素=解析类型(目标)#元素类型
    return 造令牌(f'array({元素["__dshKoffiType"]}, {长度})',元素['size']*长度,元素['alignment'])#数组令牌

def opaque(名称=None):#不透明类型
    """不透明类型描述符。"""
    return 造令牌(f'opaque({名称 or "anonymous"})',0,1)#零大小

class _类型表:#按名取类型的代理面
    """原始类型表；成员携带其 x64 大小。"""

    def __getitem__(自身,属性):#访问即解析
        """按属性名解析原始类型。"""
        return 解析类型(str(属性))#访问即解析

    def __contains__(自身,属性):#仅原始名
        """是否为已知原始类型名。"""
        return isinstance(属性,str) and 属性 in 原始大小们#仅原始名

    def __getattr__(自身,属性):#点号访问
        """点号取原始类型。"""
        return 解析类型(属性)#解析

types=_类型表()#原始类型表

def 别名(名称,目标):#别名
    """类型别名描述符。"""
    类型=解析类型(目标)#目标类型
    return 造令牌(f'alias({名称})',类型['size'],类型['alignment'])#别名令牌

def 取大小(目标):#取大小
    """返回类型字节大小。"""
    return 解析类型(目标)['size']#取大小

def 取对齐(目标):#取对齐
    """返回类型字节对齐。"""
    return 解析类型(目标)['alignment']#取对齐

koffi={#koffi外观
    'pointer':pointer,'struct':struct,'array':array,'opaque':opaque,'types':types,#类型构造
    'alias':别名,'sizeof':取大小,'alignof':取对齐,#度量
    'load':未实现失败(模块,'load'),'alloc':未实现失败(模块,'alloc'),#内存桩
    'free':未实现失败(模块,'free'),'decode':未实现失败(模块,'decode'),#编解码桩
    'encode':未实现失败(模块,'encode'),'address':未实现失败(模块,'address'),#地址桩
    'register':未实现失败(模块,'register'),'unregister':未实现失败(模块,'unregister'),#注册桩
    'call':未实现失败(模块,'call'),#call桩
}#koffi结束

__esModule=True#CJS互操作
default=koffi#默认导出
