'浅层、带类型的运行时对象检查，不转 JSON，也不隐式调用 getter'

import datetime
import re
import weakref
from .原始json import 未定义

__all__=['检查器对象值']

class 集合属性:
    '数组或类型数组上、非索引字段的合成容器'
    def __init__(自身,值,长度):
        '记下原集合和索引长度'
        自身.值=值
        自身.长度=长度

类型数组名=('Uint8Array','Uint16Array','Uint32Array','Int8Array','Int16Array','Int32Array','Float32Array','Float64Array','BigInt64Array','BigUint64Array','Uint8ClampedArray')

def 是映射(值):
    'JS Map，不是普通 dict'
    return type(值).__name__ in ('Map','映射')

def 是集合(值):
    'JS Set 或 Python set'
    return isinstance(值,(set,frozenset)) or type(值).__name__ in ('Set','集合')

def 是类型数组(值):
    '带 length 的类型数组，不含 DataView'
    return isinstance(值,bytearray) or type(值).__name__ in 类型数组名

def 索引长度(值):
    '数组或类型数组的长度'
    if isinstance(值,(list,tuple)) or 是类型数组(值):
        return len(值)
    return None

def 是索引键(键,长度):
    '非负整数字符串，且落在长度内；前导零不算索引'
    if not isinstance(键,str) or 键=='' or not 键.isdigit():
        return False
    if len(键)>1 and 键[0]=='0':
        return False
    数=int(键)
    return 0<=数<长度

def 字段(值,键,序号):
    '一个自身字段；访问器不求值，缺槽与显式空值分开'
    名=str(键)
    键名=键 if isinstance(键,str) else f'symbol:{序号}'
    if isinstance(值,(list,tuple)) or 是类型数组(值):
        下标=int(键)
        if 0<=下标<len(值):
            return {'key':键名,'name':名,'value':值[下标]}
        return {'key':键名,'name':名,'value':None,'absent':True}
    if isinstance(值,dict):
        if 键 in 值:
            return {'key':键名,'name':名,'value':值[键]}
        return {'key':键名,'name':名,'value':None,'absent':True}
    自身表=getattr(值,'__dict__',None)
    if isinstance(自身表,dict) and 键 in 自身表:
        return {'key':键名,'name':名,'value':自身表[键]}
    描述=getattr(type(值),'__dict__',{}).get(键)
    if isinstance(描述,property):
        return {'key':键名,'name':名,'value':None,'accessor':True}
    return {'key':键名,'name':名,'value':None,'absent':True}

def 构造名(值):
    '实例构造函数名；普通 dict 记为 Object'
    if isinstance(值,dict):
        return 'Object'
    名=getattr(type(值),'__name__','')
    return 名 if 名 not in ('', 'object') else 'Object'

def json字符串(值):
    'JSON 字符串字面量'
    转义=值.replace('\\','\\\\').replace('"','\\"').replace('\n','\\n').replace('\r','\\r').replace('\t','\\t')
    return '"'+转义+'"'

def 日期文本(值):
    'ISO 时间；非法日期记为 Invalid'
    try:
        if isinstance(值,datetime.datetime):
            时刻=值.astimezone(datetime.timezone.utc)
            return 时刻.strftime('%Y-%m-%dT%H:%M:%S.')+f'{时刻.microsecond//1000:03d}Z'
        return 值.isoformat()
    except (ValueError,OSError):
        return 'Invalid'

class 检查器对象值:
    '一个值的展示；枚举子项时不递归进入子值'
    def __init__(自身,值):
        '原运行时值，包括 Map、Set 和类实例'
        自身._值=值
        if 值 is 未定义:
            自身.可展开=False
            自身.标签='undefined'
            return
        日期=isinstance(值,(datetime.datetime,datetime.date))
        正则=isinstance(值,re.Pattern) or type(值).__name__=='RegExp'
        弱图=isinstance(值,weakref.WeakKeyDictionary) or type(值).__name__=='WeakMap'
        弱集=isinstance(值,weakref.WeakSet) or type(值).__name__=='WeakSet'
        对象=值 is not None and not isinstance(值,(str,int,float,bool)) and not callable(值)
        自身.可展开=对象 and not 日期 and not 正则 and not 弱图 and not 弱集
        if 是映射(值):
            规模=值.size if hasattr(值,'size') else len(值)
            自身.标签=f'Map({规模})'
        elif 是集合(值):
            自身.标签=f'Set({len(值)})'
        elif isinstance(值,(list,tuple)):
            自身.标签=f'Array({len(值)})'
        elif 日期:
            自身.标签=f'Date({日期文本(值)})'
        elif 正则:
            自身.标签=str(值)
        elif 弱图:
            自身.标签='WeakMap'
        elif 弱集:
            自身.标签='WeakSet'
        elif isinstance(值,bytes) or type(值).__name__=='ArrayBuffer':
            自身.标签=f'ArrayBuffer({len(值)})'
        elif isinstance(值,集合属性):
            自身.标签='Object'
        elif 对象:
            自身.标签=构造名(值)
        elif isinstance(值,str):
            自身.标签=json字符串(值)
        elif type(值).__name__=='bigint':
            自身.标签=f'{值}n'
        elif callable(值):
            自身.标签=f'[Function {getattr(值,"__name__","")}]'
        elif isinstance(值,bool):
            自身.标签='true' if 值 else 'false'
        elif 值 is None:
            自身.标签='null'
        else:
            自身.标签=str(值)

    def 条目(自身):
        '枚举一层，不求值访问器，也不下降到子值'
        值=自身._值
        if 是映射(值):
            序号=0
            配对=值.items() if hasattr(值,'items') else 值
            for 键,项 in 配对:
                yield {'key':str(序号),'name':str(序号),'value':{'key':键,'value':项}}
                序号+=1
            return
        if 是集合(值):
            序号=0
            for 项 in 值:
                yield {'key':str(序号),'name':str(序号),'value':项}
                序号+=1
            return
        if isinstance(值,bytes) or type(值).__name__ in ('ArrayBuffer','DataView') or isinstance(值,memoryview):
            if isinstance(值,memoryview) or type(值).__name__=='DataView':
                if isinstance(值,memoryview):
                    字节=bytearray(值.tobytes())
                else:
                    缓冲=getattr(值,'buffer',b'')
                    起点=getattr(值,'byteOffset',0)
                    长度=getattr(值,'byteLength',len(缓冲))
                    字节=bytearray(缓冲[起点:起点+长度])
            else:
                字节=bytearray(值)
            yield {'key':'bytes','name':'bytes','value':字节}
            return
        if 值 is None or 值 is 未定义 or isinstance(值,(str,int,float,bool)) or callable(值):
            return
        长度=索引长度(值)
        if 长度 is not None:
            yield {'key':'properties','name':'','properties':True,'value':集合属性(值,长度)}
            序号=0
            while 序号<长度:
                yield 字段(值,str(序号),序号)
                序号+=1
            return
        目标=值.值 if isinstance(值,集合属性) else 值
        if isinstance(目标,dict):
            键表=list(目标.keys())
        elif hasattr(目标,'__dict__') and isinstance(目标.__dict__,dict):
            键表=list(目标.__dict__.keys())
        else:
            键表=[]
        for 序号,键 in enumerate(键表):
            if isinstance(值,集合属性) and isinstance(键,str):
                if 键=='length' and isinstance(目标,(list,tuple)):
                    continue
                if 是索引键(键,值.长度):
                    continue
            项=字段(目标,键,序号)
            if not 项.get('absent'):
                yield 项
