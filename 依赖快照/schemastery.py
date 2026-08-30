from __future__ import annotations
from abc import ABC as 抽象基类,abstractmethod as 抽象方法#字段基类不能直接用
from re import compile as 编译正则,Pattern as 正则模式#字符串字段的格式约束
from urllib.parse import urlsplit as 拆分URL#URL字段拆协议与主机
from .工具 import 深入比较,未传参#可变默认每次新副本、常量与默认值的深等于
from typing import Any

class 数据校验错误(TypeError):
    "数据没通过字段校验"

无数据=object() #此处没有数据(不包括传None)

宽松整数=宽松浮点=int|float|bool

def 在区间内(数值,最小,最大):
    if 最小 is not None and 数值<最小:
        return False
    if 最大 is not None and 数值>最大:
        return False
    return True

def 是自然数(数:int):
    if not isinstance(数,int):
        return False
    return 数>=0

def 十进制移位(数据,位数):
    文本=str(数据)#数字的十进制文本
    if '.' not in 文本 or 'e' in 文本 or 'E' in 文本:
        return 数据*10**位数#整数与科学计数法拆不出小数部分
    整数,小数=文本.split('.')#拆成两段
    if len(小数)<=位数:
        return float(整数+小数.ljust(位数,'0'))#右边补零
    return float(整数+小数[:位数]+'.'+小数[位数:])#在新位置插回小数点

def 是否倍数(数据,起点,步长):
    "通过字符串解决浮点数精度问题"
    步长=abs(步长)#只看大小
    文本=str(步长)#步长的十进制文本
    if '.' not in 文本:
        return (数据-起点)%步长==0#整数步长直接取模
    位数=len(文本.split('.')[1])#小数位数
    return abs(十进制移位(数据,位数)-十进制移位(起点,位数))%十进制移位(步长,位数)==0#整数化后取模

################################ 字段 ################################

class 字段(抽象基类):
    json类型=None
    def __init__(自身,*,
        严格模式:bool=True,可空:bool=False,
        默认值:Any=未传参,描述:str=None
        ):
        if not isinstance(严格模式,bool):
            raise TypeError('严格模式必须是布尔值')
        if not isinstance(可空,bool):
            raise TypeError('可空必须是布尔值')
        if 描述 is not None and not isinstance(描述,str):
            raise TypeError('描述必须是未传参或None')
        自身.严格模式=bool(严格模式)#非严格模式下部分字段会对接收的数据尝试转换
        自身.可空=bool(可空)
        自身.默认值=默认值
        自身.描述=描述

    def __repr__(自身):
        属性=dict(自身.__dict__)#实例上的约束
        片段=','.join(f'"{键}":{值!r}' for 键,值 in 属性.items())#逐项
        return f'<{自身.__class__.__name__}:{{{片段},}}>'#<类名:{属性}>

    def toJsonSchema(自身):
        节点={} if 自身.json类型 is None else {
            'type':[自身.json类型,'null'] if 自身.可空 else 自身.json类型
            }#类型；可空就多一个 null
        if 自身.描述 is not None:
            节点['description']=自身.描述#说明
        if 自身.默认值 is not 未传参:
            节点['default']=自身.默认值#空输入的回落值
        return 节点#JSON Schema

    def 校验数据(自身,数据=未传参):
        '字段只有可空这一个性质需要判断'
        if 数据 is 未传参:
            raise ValueError('未传入需要检查的数据')
        if 数据 is 无数据 and not 自身.可空:
            raise 数据校验错误(f'期望 {自身!r} 实际不存在该数据')

class 任意字段(字段):
    '不限制数据类型'

class 常量字段(字段):
    '需要完全匹配(包括内部值)'
    def __init__(自身,常量值,**约束条件):#约束条件
        super().__init__(**约束条件)#共有约束
        自身.常量值=常量值#唯一合法取值

    def 校验数据(自身,数据=未传参):
        数据=super().校验数据(数据)
        if not 深入比较(数据,自身.常量值):
            raise 数据校验错误(f'期望 {自身!r} 实际是 {数据!r}')#不是那个值

    def toJsonSchema(自身):
        节点=super().toJsonSchema()#共有项
        节点['const']=自身.常量值
        return 节点

class 枚举字段(字段):
    '一组常量'
    def __init__(自身,*常量表,**约束条件):#约束条件
        super().__init__(**约束条件)
        自身.常量表=[项 if isinstance(项,常量字段) else 常量字段(项) for 项 in 常量表]
        if not 自身.常量表:
            raise ValueError('枚举字段至少要有一个常量')

    def 校验数据(自身,数据=未传参):
        数据=super().校验数据(数据)
        if 数据 is 未传参:
            raise ValueError('未传入需要检查的数据')
        for 常量 in 自身.常量表:
            try:
                常量.校验数据(数据)
            except 数据校验错误:
                continue#这个常量不是，试下一个
        raise 数据校验错误(f'期望 {自身!r} 实际是 {数据!r}')

    def toJsonSchema(自身):
        节点=super().toJsonSchema()
        节点['enum']=[常量.常量值 for 常量 in 自身.常量表]
        return 节点

class 复合类型字段(字段):
    '多种字段类型'
    def __class_getitem__(类,内层):
        "复合写法：复合类型字段[支A,支B]"
        return 类(*内层) if isinstance(内层,tuple) else 类(内层)#内层照原样交给构造

    def __init__(自身,*字段表,**约束条件):
        super().__init__(**约束条件)
        自身.字段表=[推断字段(字段) for 字段 in 字段表]
        if not 自身.字段表:
            raise ValueError('复合类型字段至少要有一个字段')

    def 校验数据(自身,数据=未传参):
        数据=super().校验数据(数据)
        if 数据 is 未传参:
            raise ValueError('未传入需要检查的数据')
        for 字段 in 自身.字段表:
            try:
                字段.校验数据(数据)
            except 数据校验错误:
                continue#这一支不匹配，试下一支
        raise 数据校验错误(f'期望 {自身!r} 实际是 {数据!r}')

    def toJsonSchema(自身):
        节点=super().toJsonSchema()
        节点['anyOf']=[字段.toJsonSchema() for 字段 in 自身.字段表]
        return 节点

class 数字字段(字段):
    '非严格模式时,允许 字符串形式的数字 布尔'
    json类型='number'

    def __init__(自身,*,最小=None,最大=None,**约束条件):
        super().__init__(**约束条件)
        if 最小 is not None and 最大 is not None and 最小>最大:
            raise ValueError('最小不能大于最大')
        自身.最小=最小
        自身.最大=最大

    def 校验数据(自身,数据=未传参):
        数据=super().校验数据(数据)
        if isinstance(数据,bool):
            if 自身.严格模式:
                raise 数据校验错误(f'期望 {自身!r} 实际是 {数据!r}')
            数据=int(数据)
        elif isinstance(数据,str):
            if not 数据:
                raise 数据校验错误(f'期望 {自身!r} 实际是空字符串')
            if not 数据.replace('.','').isdigit():
                raise 数据校验错误(f'期望 {自身!r} 实际是 {数据!r}')
            if '.' in 数据:
                数据=float(数据)
            else:
                数据=int(数据)

        if isinstance(数据,(int,float)):
            if not 在区间内(数据,自身.最小,自身.最大):
                raise 数据校验错误(f'期望 {自身!r} 实际是 {数据!r}')
        else:
            raise 数据校验错误(f'期望 {自身!r} 实际是 {数据!r}')            

    def toJsonSchema(自身):
        节点=super().toJsonSchema()
        if 自身.最小 is not None:
            节点['minimum']=自身.最小
        if 自身.最大 is not None:
            节点['maximum']=自身.最大
        return 节点

class 步进数字字段(数字字段):
    '固定间隔的数列'
    def __init__(自身,基准值,步长,**约束条件):
        super().__init__(**约束条件)
        自身.基准值=基准值
        自身.步长=步长

    def 校验数据(自身,数据=未传参):
        数据=super().校验数据(数据)
        if not 是否倍数(数据,自身.基准值,自身.步长):
            raise 数据校验错误(f'期望是 {自身.步长} 的整数倍，实际是 {数据}')
        return 数据

    def toJsonSchema(自身):
        节点=super().toJsonSchema()
        if 自身.步长 is not None:
            节点['multipleOf']=自身.步长
        return 节点

class 整数字段(步进数字字段):
    '非严格模式接收: 浮点 布尔 字符串形式的整数'
    json类型='integer'

    def __init__(自身,**约束条件):
        super().__init__(基准值=0,步长=1,**约束条件)

    def 校验数据(自身,数据=未传参):
        if 自身.严格模式 and not isinstance(数据,int):
            raise 数据校验错误(f'期望 {自身!r} 实际是 {数据!r}')
        super().校验数据(数据)

class 自然数字段(整数字段):
    '非0整数'
    def __init__(自身,**约束条件):
        最小=约束条件.pop('最小',0)
        if 最小<0:
            最小=0
        super().__init__(**约束条件,最小=最小)

class 正整数字段(自然数字段):
    '大于0的整数'
    def __init__(自身,**约束条件):
        最小=约束条件.pop('最小',1)
        if not isinstance(最小,int):
            raise TypeError('最小必须是整数')
        if 最小<1:
            最小=1
        super().__init__(**约束条件,最小=最小)

    def 校验数据(自身,数据=未传参):
        if isinstance(数据,int) and 数据>0:
            return
        super().校验数据(数据)

class 浮点数字段(数字字段):
    '非严格模式接收: 整数 布尔 字符串形式的浮点数'
    def 校验数据(自身,数据=未传参):
        super().校验数据(数据)
        if 自身.严格模式 and not isinstance(数据,float):
            raise 数据校验错误(f'期望 {自身!r} 实际是 {数据!r}')

class 布尔字段(整数字段):
    '非严格模式允许 0与1 "0"与"1" "True"与"False" None'
    json类型='boolean'#JSON Schema 类型

    def 校验数据(自身,数据=未传参):
        if not 自身.严格模式:
            if 数据 in ('True','False','0','1'):
                return
            elif 数据 is None:
                return
        else:
            if not isinstance(数据,bool):
                raise 数据校验错误(f'期望 {自身!r} 实际是 {数据!r}')
        super().校验数据(数据)

class 字节字段(字段):
    '非严格模式允许 bytearray memoryview hex'
    json类型='string'#?

    def 校验数据(自身,数据=未传参):
        super().校验数据(数据)
        if 自身.严格模式 and not isinstance(数据,bytes):
            raise 数据校验错误(f'期望 {自身!r} 实际是 {数据!r}')
        elif isinstance(数据,bytearray):
            return
        elif isinstance(数据,memoryview):
            return
        elif isinstance(数据,str):
            try:
                bytes.fromhex(数据)
            except:
                raise 数据校验错误(f'期望 {自身!r} 实际是 {数据!r}')
            return
        else:
            raise 数据校验错误(f'期望 {自身!r} 实际是 {数据!r}')

    def toJsonSchema(自身):
        "收成 base64 编码的字符串"
        节点=super().toJsonSchema()#共有项
        节点['contentEncoding']='base64'#字节按 base64 写进 JSON
        return 节点#JSON Schema

class 字符串字段(字段):
    '字符串暂不支持非严格模式'
    json类型='string'

    def __init__(自身,最小长度=None,最大长度=None,格式=None,**约束条件):#约束条件
        super().__init__(**约束条件)
        if 最小长度 is not None and not 是自然数(最小长度):
            raise TypeError('最小长度必须是自然数')
        if 最大长度 is not None and not 是自然数(最大长度):
            raise TypeError('最大长度必须是自然数')    
        if 最小长度 is not None and 最大长度 is not None and 最小长度>最大长度:
            raise ValueError('最小长度不能大于最大长度')
        自身.最小长度=最小长度
        自身.最大长度=最大长度
        if isinstance(格式,str):
            格式=编译正则(格式)
        elif 格式 is None or isinstance(格式,正则模式):
            pass
        else:
            raise TypeError('格式必须是字符串或正则模式')
        自身.格式=格式

    def 校验数据(自身,数据=未传参):
        数据=super().校验数据(数据)
        if not isinstance(数据,str):
            raise 数据校验错误(f'期望 {自身!r} 实际是 {数据!r}')
        #长度区间
        if not 在区间内(len(数据),自身.最小长度,自身.最大长度):
            raise 数据校验错误(f'期望 {自身!r} 实际是 {数据!r}')
        #格式
        if 自身.格式 is not None and not 自身.格式.fullmatch(数据):
            raise 数据校验错误(f'期望匹配 {自身.格式.pattern}，实际是 {数据!r}')#格式不匹配

    def toJsonSchema(自身):
        "长度收成 minLength 与 maxLength，格式收成 pattern"
        节点=super().toJsonSchema()#共有项
        if 自身.最小 is not None:
            节点['minLength']=自身.最小#长度下限
        if 自身.最大 is not None:
            节点['maxLength']=自身.最大#长度上限
        if 自身.格式 is not None:
            节点['pattern']=自身.格式.pattern#正则原文
        return 节点#JSON Schema

class URL字段(字符串字段):
    "URL：得是带协议与主机的绝对地址"
    def 校验数据(自身,数据=None):
        "先按字符串收拢，再看协议与主机"
        数据=super().校验数据(数据)#字符串、长度与格式
        if 数据 is None:
            return None#可空
        拆开=拆分URL(数据)#协议、主机与其余部分
        if not 拆开.scheme or not 拆开.netloc:
            raise 数据校验错误(f'期望{自身!r}，实际是 {数据!r}')#不是绝对地址
        return 数据#通过

    def toJsonSchema(自身):
        "收成 format: uri"
        节点=super().toJsonSchema()#字符串约束
        节点['format']='uri'#URI 格式
        return 节点#JSON Schema

class 容器字段(字段):
    "装别的字段的字段：数量有上下限，具体类型由子类收拢"
    数量键=('minItems','maxItems')#JSON Schema 的数量约束键

    def __class_getitem__(类,内层):
        "容器写法：列表字段[内层字段]，内层只能有一个"
        if isinstance(内层,tuple):
            if len(内层)!=1:
                raise TypeError(f'{类.__name__} 的内层只能有一个字段')#列表字典集合不能写多个
            内层=内层[0]#方括号里单个也会包成 tuple
        return 类(内层)#交给构造

    def __init__(自身,最小数量=None,最大数量=None,**约束条件):#约束条件
        "收下数量区间"
        super().__init__(**约束条件)#共有约束
        自身.最小数量=最小数量#数量下限
        自身.最大数量=最大数量#数量上限

    def 校验数据(自身,数据=None):
        super().校验数据(数据)
        if 数据 is None:
            return None
        if not 在区间内(len(数据),自身.最小数量,自身.最大数量):
            raise 数据校验错误(f'期望 {自身!r} 的 {自身.最小数量} 到 {自身.最大数量} 个，实际是 {len(数据)} 个')
        return 数据

    def toJsonSchema(自身):
        "数量收成各自的上下限键"
        节点=super().toJsonSchema()#共有项
        下限键,上限键=自身.数量键#该容器用哪对键
        if 自身.最小数量 is not None:
            节点[下限键]=自身.最小数量#数量下限
        if 自身.最大数量 is not None:
            节点[上限键]=自身.最大数量#数量上限
        return 节点#JSON Schema

class 列表字段(容器字段):
    "列表：元素同一个字段；严格模式只收 list，宽松还收元组与集合"
    json类型='array'#JSON Schema 类型

    def __init__(自身,元素字段=None,**约束条件):#约束条件
        "收下元素字段"
        super().__init__(**约束条件)#数量与共有约束
        自身.元素字段=推断字段(元素字段)#元素字段

    def 校验数据(自身,数据=未传参):
        "类型、数量与逐项"
        if not 自身.严格模式 and not isinstance(数据,list):
            数据=list(数据)
        super().校验数据(数据)
        return [自身.元素字段.校验数据(项) for 项 in 数据]

    def toJsonSchema(自身):
        "元素收成 items"
        节点=super().toJsonSchema()#类型与数量
        节点['items']=自身.元素字段.toJsonSchema()#元素
        return 节点#JSON Schema

class 元组字段(字段):
    "元组：定长，每一位各有自己的字段；严格模式只收 tuple，宽松还收 list"
    json类型='array'#JSON Schema 类型

    def __class_getitem__(类,内层):
        "元组写法：元组字段[字段A,字段B]"
        return 类(*内层) if isinstance(内层,tuple) else 类(内层)#内层照原样交给构造

    def __init__(自身,*各位字段,**约束条件):#约束条件
        "收下每一位的字段"
        super().__init__(**约束条件)#共有约束
        自身.各位字段=[推断字段(每位) for 每位 in 各位字段]#每一位一个字段
        if not 自身.各位字段:
            raise TypeError('元组字段至少要有一位')#空元组只能是空的，没必要

    def 校验数据(自身,数据=None):
        "位数要对上，再逐位校验"
        数据=super().校验数据(数据)#空输入
        if 数据 is None:
            return None#可空
        if not 自身.严格模式 and isinstance(数据,list):
            数据=tuple(数据)#宽松就转过来
        if not isinstance(数据,tuple):
            raise 数据校验错误(f'期望{自身!r}，实际是 {数据!r}')#类型不符
        if len(数据)!=len(自身.各位字段):
            raise 数据校验错误(f'期望{自身!r} 的 {len(自身.各位字段)} 位，实际是 {len(数据)} 位')#位数不符
        return tuple(每位.校验数据(数据[下标]) for 下标,每位 in enumerate(自身.各位字段))#逐位校验

    def toJsonSchema(自身):
        "逐位收成 prefixItems，位数收成定长"
        节点=super().toJsonSchema()#共有项
        节点['prefixItems']=[每位.toJsonSchema() for 每位 in 自身.各位字段]#逐位
        节点['minItems']=len(自身.各位字段)#定长
        节点['maxItems']=len(自身.各位字段)#定长
        return 节点#JSON Schema

class 集合字段(容器字段):
    "集合：元素同一个字段且不重复；严格模式只收 set，宽松还收列表与元组"
    json类型='array'#JSON Schema 里集合走数组

    def __init__(自身,元素字段=None,**约束条件):#约束条件
        "收下元素字段"
        super().__init__(**约束条件)#数量与共有约束
        自身.元素字段=推断字段(元素字段)#元素字段

    def 校验数据(自身,数据=None):
        "类型、数量与逐项"
        if 数据 is not None:
            if not 自身.严格模式 and isinstance(数据,(list,tuple)):
                数据=set(数据)#宽松就转过来
            if not isinstance(数据,set):
                raise 数据校验错误(f'期望{自身!r}，实际是 {数据!r}')#类型不符
        数据=super().校验数据(数据)#空输入与数量
        if 数据 is None:
            return None#可空
        return {自身.元素字段.校验数据(项) for 项 in 数据}#逐项校验

    def toJsonSchema(自身):
        "元素收成 items，去重收成 uniqueItems"
        节点=super().toJsonSchema()#类型与数量
        节点['items']=自身.元素字段.toJsonSchema()#元素
        节点['uniqueItems']=True#不重复
        return 节点#JSON Schema

class 字典字段(容器字段):#映射,与普通容器不同
    '对应js的object'
    json类型='object'
    数量键=('minProperties','maxProperties')#对象的数量约束键

    def __init__(自身,字典结构=None,**约束条件):#约束条件
        super().__init__(**约束条件)#数量与共有约束
        自身.字典结构=推断字段(字典结构)#值字段

    def 校验数据(自身,数据=None):
        "类型、数量、键是字符串与逐项"
        if 数据 is not None and not isinstance(数据,dict):
            raise 数据校验错误(f'期望{自身!r}，实际是 {数据!r}')#类型不符
        数据=super().校验数据(数据)#空输入与数量
        if 数据 is None:
            return None#可空
        结果={}#逐项校验的输出
        for 键,值 in 数据.items():
            if not isinstance(键,str):
                raise 数据校验错误(f'期望{自身!r} 的键是字符串，实际是 {键!r}')#键不是字符串
            结果[键]=自身.值字段.校验数据(值)#值校验
        return 结果#通过

    def toJsonSchema(自身):
        "值收成 additionalProperties"
        节点=super().toJsonSchema()#类型与数量
        节点['additionalProperties']=自身.值字段.toJsonSchema()#值
        return 节点#JSON Schema

def 推断字段(源=None):
    '传递的内容非字段实例时,自动判断是哪个字段'
    if 源 is None:
        return 任意字段()#没给就当任意字段
    elif isinstance(源,字段):
        return 源#已经是字段
    elif isinstance(源,(bool,str,int,float,bytes)):
        return 常量字段(源)#字面量当常量
    #
    elif 源 is str:
        return 字符串字段()#字符串
    elif 源 is bool:
        return 布尔字段()#布尔
    elif 源 is int:
        return 整数字段()#整数
    elif 源 is float:
        return 浮点数字段()#浮点数
    elif 源 is bytes:
        return 字节字段()#字节
    elif isinstance(源,list):
        return 列表字段()#列表
    elif isinstance(源,tuple):
        return 元组字段()#元组
    elif isinstance(源,set):
        return 集合字段()#集合
    elif isinstance(源,dict):
        return 字典字段()#字典
    #
    else:
        raise TypeError(f'无法从 {源} 推断出字段')#不认识的形态
