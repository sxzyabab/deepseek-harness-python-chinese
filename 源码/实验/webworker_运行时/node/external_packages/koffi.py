import json
from ..未实现失败 import 未实现失败,运行时错误

__all__=['pointer','struct','array','opaque','types','__esModule','default']

模块='koffi'

原始大小表={
    'void':0,'bool':1,'char':1,'uchar':1,'int8':1,'uint8':1,
    'short':2,'ushort':2,'int16':2,'uint16':2,
    'int':4,'uint':4,'int32':4,'uint32':4,'float':4,'float32':4,
    'long':8,'ulong':8,'longlong':8,'ulonglong':8,'int64':8,'uint64':8,
    'double':8,'float64':8,'str':8,'str16':8,
}

def 造令牌(标签,大小,对齐=None):
    """构造不透明类型描述符。"""
    if 对齐 is None: 对齐=min(大小,8) or 1
    return {'__dshKoffiType':标签,'size':大小,'alignment':对齐}

def 解析类型(目标):
    """按名或已有描述符解析类型。"""
    if isinstance(目标,str):
        if 目标 not in 原始大小表:
            raise 运行时错误(f'web-preview: koffi type "{目标}" is unknown to the stub')
        return 造令牌(目标,原始大小表[目标])
    if not isinstance(目标,dict) or '__dshKoffiType' not in 目标:
        raise 运行时错误('web-preview: koffi 类型 '+json.dumps(目标,ensure_ascii=False,separators=(',',':'),allow_nan=False)+' 不是桩描述符')
    return 目标

def 描述(目标):
    """取类型标签字符串。"""
    if isinstance(目标,str): return 目标
    if isinstance(目标,dict):
        return 目标['__dshKoffiType'] if '__dshKoffiType' in 目标 else 'anonymous'
    return 'anonymous'

def pointer(目标):
    """指针类型描述符。"""
    return 造令牌(f'pointer({描述(目标)})',8)

def struct(名称,字段表=None):
    """结构类型描述符；大小与对齐按 koffi x64 填充规则。"""
    源=字段表 if isinstance(名称,str) else 名称
    成员表={} if 源 is None else 源#??空表，空字典合法
    偏移=0
    对齐=1
    for 成员 in 成员表.values():
        类型=解析类型(成员)
        对齐=max(对齐,类型['alignment'])
        偏移=((偏移+类型['alignment']-1)//类型['alignment'])*类型['alignment']+类型['size']
    大小=((偏移+对齐-1)//对齐)*对齐
    结构名=名称 if isinstance(名称,str) else 'anonymous'
    return 造令牌(f'struct({结构名})',大小,对齐)

def array(目标,长度):
    """数组类型描述符。"""
    元素=解析类型(目标)
    return 造令牌(f'array({元素["__dshKoffiType"]}, {长度})',元素['size']*长度,元素['alignment'])

def opaque(名称=None):
    """不透明类型描述符。"""
    return 造令牌(f'opaque({名称 or "anonymous"})',0,1)

class _类型表:
    """原始类型表；成员携带其 x64 大小。"""

    def __getitem__(自身,属性):
        """按属性名解析原始类型。"""
        return 解析类型(str(属性))

    def __contains__(自身,属性):
        """是否为已知原始类型名。"""
        return isinstance(属性,str) and 属性 in 原始大小表

    def __getattr__(自身,属性):
        """点号取原始类型。"""
        return 解析类型(属性)

types=_类型表()

def 别名(名称,目标):
    """类型别名描述符。"""
    类型=解析类型(目标)
    return 造令牌(f'alias({名称})',类型['size'],类型['alignment'])

def 取大小(目标):
    """返回类型字节大小。"""
    return 解析类型(目标)['size']

def 取对齐(目标):
    """返回类型字节对齐。"""
    return 解析类型(目标)['alignment']

koffi={
    'pointer':pointer,'struct':struct,'array':array,'opaque':opaque,'types':types,
    'alias':别名,'sizeof':取大小,'alignof':取对齐,
    'load':未实现失败(模块,'load'),'alloc':未实现失败(模块,'alloc'),
    'free':未实现失败(模块,'free'),'decode':未实现失败(模块,'decode'),
    'encode':未实现失败(模块,'encode'),'address':未实现失败(模块,'address'),
    'register':未实现失败(模块,'register'),'unregister':未实现失败(模块,'unregister'),
    'call':未实现失败(模块,'call'),
}

__esModule=True
default=koffi
