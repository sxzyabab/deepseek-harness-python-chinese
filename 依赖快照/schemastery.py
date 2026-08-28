from __future__ import annotations
from abc import ABC as 抽象基类#字段基类不能直接用
from re import compile as 编译正则#字符串字段的格式约束
from urllib.parse import urlsplit as 拆分URL#URL字段拆协议与主机
from .工具 import 克隆,深入比较#可变默认每次新副本、常量与默认值的深等于

未定义=object()#和显式默认 None 区分
################################ 字段 ################################
class 校验错误(TypeError):
    """数据没通过字段校验。"""

def 检查区间(数值,最小,最大,描述):
    """按包含式上下限检查一个数，数值与长度都走这里。"""
    if 最小 is not None and 数值<最小:
        raise 校验错误(f'期望{描述}不小于 {最小}，实际是 {数值}')#低于下限
    if 最大 is not None and 数值>最大:
        raise 校验错误(f'期望{描述}不大于 {最大}，实际是 {数值}')#超过上限

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

class 字段(抽象基类):
    json类型=None#JSON Schema 的 type，任意与复合不写

    def __init__(自身,严格模式=True,可空=False,默认值=未定义,描述=None):#约束条件
        """收下共有约束，缺席默认值与显式给 None 不是一回事。"""
        自身.严格模式=bool(严格模式)#关掉就按各类型的宽松规则转换
        自身.可空=bool(可空)#空输入是否合法
        自身.默认值=默认值#缺席时是未定义
        自身.描述=描述#给人看的说明

    def __class_getitem__(类,内层):
        """容器写法：容器字段[内层字段]，多个内层用逗号分开。"""
        return 类(*内层) if isinstance(内层,tuple) else 类(内层)#内层照原样交给构造

    def __repr__(自身):
        """类型名加全部属性。"""
        属性={'json类型':自身.json类型,**自身.__dict__}#共有与本实例
        片段=','.join(f'"{键}":{值!r}' for 键,值 in 属性.items())#逐项
        return f'{自身.__class__.__name__.removesuffix("字段")}:{{{片段},}}'#类型:属性

    def 校验数据(自身,数据=None):
        """空输入按默认值与可空收尾，非空原样交出由子类收窄。"""
        if 数据 is None:
            if 自身.默认值 is None:
                return None#默认就是空
            if 自身.默认值 is not 未定义:
                数据=克隆(自身.默认值)#默认值每次都给一份新的
            elif 自身.可空:
                return None#允许空
            else:
                raise 校验错误(f'期望{自身!r}，实际什么都没给')#不可空又没有默认值
        return 数据#非空交给子类继续收窄

    def 转JSON模式(自身):
        """收成 JSON Schema，界面照着它渲染。"""
        节点={} if 自身.json类型 is None else {'type':[自身.json类型,'null'] if 自身.可空 else 自身.json类型}#类型；可空就多一个 null
        if 自身.描述 is not None:
            节点['description']=自身.描述#说明
        if 自身.默认值 is not 未定义:
            节点['default']=自身.默认值#空输入的回落值
        return 节点#JSON Schema

class 任意字段(字段):
    """任意值：不收窄类型，原样直通。"""

class 常量字段(字段):
    """常量：只收一个字面量，深等于才算。"""
    def __init__(自身,常量值,**约束条件):#约束条件
        """收下唯一合法取值。"""
        super().__init__(**约束条件)#共有约束
        自身.常量值=常量值#唯一合法取值

    def 校验数据(自身,数据=None):
        """深等于才通过。"""
        数据=super().校验数据(数据)#空输入
        if 数据 is None:
            return None#可空
        if not 深入比较(数据,自身.常量值):
            raise 校验错误(f'期望 {自身!r}，实际是 {数据!r}')#不是那个值
        return 自身.常量值#通过

    def 转JSON模式(自身):
        """收成 const。"""
        节点=super().转JSON模式()#共有项
        节点['const']=自身.常量值#唯一取值
        return 节点#JSON Schema

class 枚举字段(字段):
    """枚举：收一串常量，命中一个就算通过。"""
    def __init__(自身,*取值表,**约束条件):#约束条件
        """收下各个常量，写成字面量的先包成常量字段。"""
        super().__init__(**约束条件)#共有约束
        自身.取值表=[项 if isinstance(项,常量字段) else 常量字段(项) for 项 in 取值表]#各个常量
        if not 自身.取值表:
            raise TypeError('枚举字段至少要有一个取值')#空枚举没有能命中的取值

    def 校验数据(自身,数据=None):
        """命中任何一个常量就通过。"""
        数据=super().校验数据(数据)#空输入
        if 数据 is None:
            return None#可空
        for 常量 in 自身.取值表:
            try:
                return 常量.校验数据(数据)#命中就交出
            except 校验错误:
                continue#这个常量不是，试下一个
        raise 校验错误(f'期望{自身!r}，实际是 {数据!r}')#都不命中

    def 转JSON模式(自身):
        """收成 enum。"""
        节点=super().转JSON模式()#共有项
        节点['enum']=[常量.常量值 for 常量 in 自身.取值表]#各个取值
        return 节点#JSON Schema

class 复合类型字段(字段):
    """复合类型：按顺序试各支，命中一支就算通过。"""
    def __init__(自身,*成员表,**约束条件):#约束条件
        """收下各支字段。"""
        super().__init__(**约束条件)#共有约束
        自身.成员表=[推断字段(成员) for 成员 in 成员表]#各支字段
        if not 自身.成员表:
            raise TypeError('复合类型字段至少要有一个成员')#空复合没有可命中的支

    def 校验数据(自身,数据=None):
        """一支支试，各支自己的默认值不参与。"""
        数据=super().校验数据(数据)#空输入
        if 数据 is None:
            return None#可空
        for 成员 in 自身.成员表:
            try:
                return 成员.校验数据(数据)#命中就交出
            except 校验错误:
                continue#这一支不匹配，试下一支
        raise 校验错误(f'期望{自身!r}，实际是 {数据!r}')#全都不匹配

    def 转JSON模式(自身):
        """各支收成 anyOf。"""
        节点=super().转JSON模式()#共有项
        节点['anyOf']=[成员.转JSON模式() for 成员 in 自身.成员表]#各支
        return 节点#JSON Schema

class 数字字段(字段):
    """数字：取值区间；严格模式只收整数与浮点，宽松还收布尔。"""
    json类型='number'#JSON Schema 类型

    def __init__(自身,最小=None,最大=None,**约束条件):#约束条件
        """收下取值区间。"""
        super().__init__(**约束条件)#共有约束
        自身.最小=最小#包含式下限
        自身.最大=最大#包含式上限

    def 校验数据(自身,数据=None):
        """先看类型再看区间。"""
        数据=super().校验数据(数据)#空输入
        if 数据 is None:
            return None#可空
        if isinstance(数据,bool):
            if 自身.严格模式:
                raise 校验错误(f'期望{自身!r}，实际是布尔 {数据!r}')#布尔不是数字
            数据=int(数据)#宽松就当 0 与 1
        if not isinstance(数据,(int,float)):
            raise 校验错误(f'期望{自身!r}，实际是 {数据!r}')#类型不符
        检查区间(数据,自身.最小,自身.最大,'数值')#取值区间
        return 数据#通过

    def 转JSON模式(自身):
        """区间收成 minimum 与 maximum。"""
        节点=super().转JSON模式()#共有项
        if 自身.最小 is not None:
            节点['minimum']=自身.最小#包含式下限
        if 自身.最大 is not None:
            节点['maximum']=自身.最大#包含式上限
        return 节点#JSON Schema

class 步进数字字段(数字字段):
    """带步进的数字，步进从区间下限起算，没有下限就从 0 起算。"""
    def __init__(自身,步进=None,**约束条件):#约束条件
        """收下步进。"""
        super().__init__(**约束条件)#区间与共有约束
        自身.步进=步进#步进

    def 校验数据(自身,数据=None):
        """区间之外还要落在步进的格子上。"""
        数据=super().校验数据(数据)#类型与区间
        if 数据 is None:
            return None#可空
        if 自身.步进 is not None and not 是否倍数(数据,自身.最小 or 0,自身.步进):
            raise 校验错误(f'期望是 {自身.步进} 的整数倍，实际是 {数据}')#不在格子上
        return 数据#通过

    def 转JSON模式(自身):
        """步进收成 multipleOf。"""
        节点=super().转JSON模式()#区间与共有项
        if 自身.步进 is not None:
            节点['multipleOf']=自身.步进#步进
        return 节点#JSON Schema

class 整数字段(步进数字字段):
    """整数：严格模式只收整数，宽松还收浮点与布尔，但不许丢小数。"""
    json类型='integer'#JSON Schema 类型

    def __init__(自身,步进=1,**约束条件):#约束条件
        """整数天然按 1 步进。"""
        super().__init__(步进,**约束条件)#步进

    def 校验数据(自身,数据=None):
        """先收拢成整数，再交给数字看区间与步进。"""
        数据=字段.校验数据(自身,数据)#空输入
        if 数据 is None:
            return None#可空
        if not 自身.严格模式 and isinstance(数据,(bool,float)):
            if isinstance(数据,float) and int(数据)!=数据:
                raise 校验错误(f'期望{自身!r}，{数据} 转整数会丢小数')#不许悄悄丢小数
            数据=int(数据)#宽松就转过来
        if isinstance(数据,bool) or not isinstance(数据,int):
            raise 校验错误(f'期望{自身!r}，实际是 {数据!r}')#类型不符
        return super().校验数据(数据)#区间与步进

class 自然数字段(整数字段):
    """自然数：不小于 0 的整数。"""
    下限=0#默认的包含式下限

    def __init__(自身,**约束条件):#约束条件
        """下限压到本类的下限，调用方给的最小优先。"""
        super().__init__(**({'最小':自身.下限}|约束条件))#下限

class 正整数字段(自然数字段):
    """正整数：不小于 1 的整数。"""
    下限=1#默认的包含式下限

class 浮点数字段(步进数字字段):
    """浮点数：严格模式只收浮点，宽松还收整数与布尔。"""
    def 校验数据(自身,数据=None):
        """先收拢成浮点，再交给数字看区间与步进。"""
        数据=字段.校验数据(自身,数据)#空输入
        if 数据 is None:
            return None#可空
        if not 自身.严格模式 and isinstance(数据,(bool,int)):
            数据=float(数据)#宽松就转过来
        if not isinstance(数据,float):
            raise 校验错误(f'期望{自身!r}，实际是 {数据!r}')#类型不符
        return super().校验数据(数据)#区间与步进

class 布尔字段(字段):
    """布尔：严格模式不接受 0 与 1 冒充。"""
    json类型='boolean'#JSON Schema 类型

    def 校验数据(自身,数据=None):
        """只认真布尔，宽松时 0 与 1 也算。"""
        数据=super().校验数据(数据)#空输入
        if 数据 is None:
            return None#可空
        if not 自身.严格模式 and 数据 in (0,1):
            数据=bool(数据)#宽松就转过来
        if not isinstance(数据,bool):
            raise 校验错误(f'期望{自身!r}，实际是 {数据!r}')#类型不符
        return 数据#通过

class 字节字段(字段):
    """字节：严格模式只收 bytes，宽松还收 bytearray 与按 UTF-8 编码的字符串。"""
    json类型='string'#JSON Schema 里字节走字符串

    def 校验数据(自身,数据=None):
        """先收拢成 bytes。"""
        数据=super().校验数据(数据)#空输入
        if 数据 is None:
            return None#可空
        if not 自身.严格模式 and isinstance(数据,bytearray):
            数据=bytes(数据)#宽松就转过来
        if not 自身.严格模式 and isinstance(数据,str):
            数据=数据.encode('utf-8')#宽松就按 UTF-8 编码
        if not isinstance(数据,bytes):
            raise 校验错误(f'期望{自身!r}，实际是 {数据!r}')#类型不符
        return 数据#通过

    def 转JSON模式(自身):
        """收成 base64 编码的字符串。"""
        节点=super().转JSON模式()#共有项
        节点['contentEncoding']='base64'#字节按 base64 写进 JSON
        return 节点#JSON Schema

class 字符串字段(字段):
    """字符串：长度区间与格式正则；严格模式只收 str，宽松拿 str() 转。"""
    json类型='string'#JSON Schema 类型

    def __init__(自身,最小=None,最大=None,格式=None,**约束条件):#约束条件
        """收下长度区间与格式，格式给字符串就先编译。"""
        super().__init__(**约束条件)#共有约束
        自身.最小=最小#长度下限
        自身.最大=最大#长度上限
        自身.格式=编译正则(格式) if isinstance(格式,str) else 格式#整串要匹配的正则

    def 校验数据(自身,数据=None):
        """类型、长度与格式。"""
        数据=super().校验数据(数据)#空输入
        if 数据 is None:
            return None#可空
        if not 自身.严格模式 and not isinstance(数据,str):
            数据=str(数据)#宽松就转过来
        if not isinstance(数据,str):
            raise 校验错误(f'期望{自身!r}，实际是 {数据!r}')#类型不符
        检查区间(len(数据),自身.最小,自身.最大,'字符串长度')#长度区间
        if 自身.格式 is not None and not 自身.格式.search(数据):
            raise 校验错误(f'期望匹配 {自身.格式.pattern}，实际是 {数据!r}')#格式不匹配
        return 数据#通过

    def 转JSON模式(自身):
        """长度收成 minLength 与 maxLength，格式收成 pattern。"""
        节点=super().转JSON模式()#共有项
        if 自身.最小 is not None:
            节点['minLength']=自身.最小#长度下限
        if 自身.最大 is not None:
            节点['maxLength']=自身.最大#长度上限
        if 自身.格式 is not None:
            节点['pattern']=自身.格式.pattern#正则原文
        return 节点#JSON Schema

class URL字段(字符串字段):
    """URL：得是带协议与主机的绝对地址。"""
    def 校验数据(自身,数据=None):
        """先按字符串收拢，再看协议与主机。"""
        数据=super().校验数据(数据)#字符串、长度与格式
        if 数据 is None:
            return None#可空
        拆开=拆分URL(数据)#协议、主机与其余部分
        if not 拆开.scheme or not 拆开.netloc:
            raise 校验错误(f'期望{自身!r}，实际是 {数据!r}')#不是绝对地址
        return 数据#通过

    def 转JSON模式(自身):
        """收成 format: uri。"""
        节点=super().转JSON模式()#字符串约束
        节点['format']='uri'#URI 格式
        return 节点#JSON Schema

class 元组字段(字段):
    """元组：定长，每一位各有自己的字段；严格模式只收 tuple，宽松还收 list。"""
    json类型='array'#JSON Schema 类型

    def __init__(自身,*各位字段,**约束条件):#约束条件
        """收下每一位的字段。"""
        super().__init__(**约束条件)#共有约束
        自身.各位字段=[推断字段(每位) for 每位 in 各位字段]#每一位一个字段
        if not 自身.各位字段:
            raise TypeError('元组字段至少要有一位')#空元组只能是空的，没必要

    def 校验数据(自身,数据=None):
        """位数要对上，再逐位校验。"""
        数据=super().校验数据(数据)#空输入
        if 数据 is None:
            return None#可空
        if not 自身.严格模式 and isinstance(数据,list):
            数据=tuple(数据)#宽松就转过来
        if not isinstance(数据,tuple):
            raise 校验错误(f'期望{自身!r}，实际是 {数据!r}')#类型不符
        if len(数据)!=len(自身.各位字段):
            raise 校验错误(f'期望{自身!r} 的 {len(自身.各位字段)} 位，实际是 {len(数据)} 位')#位数不符
        return tuple(每位.校验数据(数据[下标]) for 下标,每位 in enumerate(自身.各位字段))#逐位校验

    def 转JSON模式(自身):
        """逐位收成 prefixItems，位数收成定长。"""
        节点=super().转JSON模式()#共有项
        节点['prefixItems']=[每位.转JSON模式() for 每位 in 自身.各位字段]#逐位
        节点['minItems']=len(自身.各位字段)#定长
        节点['maxItems']=len(自身.各位字段)#定长
        return 节点#JSON Schema

class 容器字段(字段):
    """装别的字段的字段：数量有上下限，具体类型由子类收拢。"""
    数量键=('minItems','maxItems')#JSON Schema 的数量约束键

    def __init__(自身,最小数量=None,最大数量=None,**约束条件):#约束条件
        """收下数量区间。"""
        super().__init__(**约束条件)#共有约束
        自身.最小数量=最小数量#数量下限
        自身.最大数量=最大数量#数量上限

    def 校验数据(自身,数据=None):
        """子类先把类型收拢，这里管空输入与数量。"""
        数据=super().校验数据(数据)#空输入
        if 数据 is None:
            return None#可空
        检查区间(len(数据),自身.最小数量,自身.最大数量,'数量')#数量区间
        return 数据#数量没问题

    def 转JSON模式(自身):
        """数量收成各自的上下限键。"""
        节点=super().转JSON模式()#共有项
        下限键,上限键=自身.数量键#该容器用哪对键
        if 自身.最小数量 is not None:
            节点[下限键]=自身.最小数量#数量下限
        if 自身.最大数量 is not None:
            节点[上限键]=自身.最大数量#数量上限
        return 节点#JSON Schema

class 列表字段(容器字段):
    """列表：元素同一个字段；严格模式只收 list，宽松还收元组与集合。"""
    json类型='array'#JSON Schema 类型

    def __init__(自身,元素字段=None,**约束条件):#约束条件
        """收下元素字段。"""
        super().__init__(**约束条件)#数量与共有约束
        自身.元素字段=推断字段(元素字段)#元素字段

    def 校验数据(自身,数据=None):
        """类型、数量与逐项。"""
        if 数据 is not None:
            if not 自身.严格模式 and isinstance(数据,(tuple,set)):
                数据=list(数据)#宽松就转过来
            if not isinstance(数据,list):
                raise 校验错误(f'期望{自身!r}，实际是 {数据!r}')#类型不符
        数据=super().校验数据(数据)#空输入与数量
        if 数据 is None:
            return None#可空
        return [自身.元素字段.校验数据(项) for 项 in 数据]#逐项校验

    def 转JSON模式(自身):
        """元素收成 items。"""
        节点=super().转JSON模式()#类型与数量
        节点['items']=自身.元素字段.转JSON模式()#元素
        return 节点#JSON Schema

class 集合字段(容器字段):
    """集合：元素同一个字段且不重复；严格模式只收 set，宽松还收列表与元组。"""
    json类型='array'#JSON Schema 里集合走数组

    def __init__(自身,元素字段=None,**约束条件):#约束条件
        """收下元素字段。"""
        super().__init__(**约束条件)#数量与共有约束
        自身.元素字段=推断字段(元素字段)#元素字段

    def 校验数据(自身,数据=None):
        """类型、数量与逐项。"""
        if 数据 is not None:
            if not 自身.严格模式 and isinstance(数据,(list,tuple)):
                数据=set(数据)#宽松就转过来
            if not isinstance(数据,set):
                raise 校验错误(f'期望{自身!r}，实际是 {数据!r}')#类型不符
        数据=super().校验数据(数据)#空输入与数量
        if 数据 is None:
            return None#可空
        return {自身.元素字段.校验数据(项) for 项 in 数据}#逐项校验

    def 转JSON模式(自身):
        """元素收成 items，去重收成 uniqueItems。"""
        节点=super().转JSON模式()#类型与数量
        节点['items']=自身.元素字段.转JSON模式()#元素
        节点['uniqueItems']=True#不重复
        return 节点#JSON Schema

class 字典字段(容器字段):
    """字典：键与值各一个字段；只收 dict。"""
    json类型='object'#JSON Schema 类型
    数量键=('minProperties','maxProperties')#对象的数量约束键

    def __init__(自身,键字段=None,值字段=None,**约束条件):#约束条件
        """收下键字段与值字段，键缺席就是字符串。"""
        super().__init__(**约束条件)#数量与共有约束
        自身.键字段=推断字段(键字段) if 键字段 is not None else 字符串字段()#键字段
        自身.值字段=推断字段(值字段)#值字段

    def 校验数据(自身,数据=None):
        """类型、数量、每个键与每个值。"""
        if 数据 is not None and not isinstance(数据,dict):
            raise 校验错误(f'期望{自身!r}，实际是 {数据!r}')#类型不符
        数据=super().校验数据(数据)#空输入与数量
        if 数据 is None:
            return None#可空
        结果={}#归一化输出
        for 键,值 in 数据.items():
            规范键=自身.键字段.校验数据(键)#键也要过校验
            结果[规范键]=自身.值字段.校验数据(值)#值校验
        return 结果#通过

    def 转JSON模式(自身):
        """键收成 propertyNames，值收成 additionalProperties。"""
        节点=super().转JSON模式()#类型与数量
        节点['propertyNames']=自身.键字段.转JSON模式()#键
        节点['additionalProperties']=自身.值字段.转JSON模式()#值
        return 节点#JSON Schema

def 推断字段(源=None):
    "从字段、内建类型或字面量推出字段，容器的内层就靠它收下简写"
    if 源 is None:
        return 任意字段()#没给就当任意
    if isinstance(源,字段):
        return 源#已经是字段
    if 源 is str:
        return 字符串字段()#字符串
    if 源 is bool:
        return 布尔字段()#布尔
    if 源 is int:
        return 整数字段()#整数
    if 源 is float:
        return 浮点数字段()#浮点数
    if 源 is bytes:
        return 字节字段()#字节
    if isinstance(源,(bool,str,int,float,bytes)):
        return 常量字段(源)#字面量当常量
    raise TypeError(f'无法从 {源} 推断出字段')#不认识的形态
