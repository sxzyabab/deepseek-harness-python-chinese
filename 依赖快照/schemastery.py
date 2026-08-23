"""配置模式：声明式校验并归一化配置对象。

模式树是可序列化的纯数据（`转JSON`/`从JSON`），校验交给 pydantic：每个节点惰性编译成一份注解与适配器，标量约束、默认值填充与未声明键的保留都由 pydantic 执行，本模块只负责树结构、中文诊断，以及写回配置文件用的 `简化`。

严格性：字符串、布尔与数字都走 pydantic 的 strict 判定，所以布尔不算数字、数字也不会被转成字符串。联合按书写顺序取第一个命中，与配置文件里的写法一致。
"""
import json
from typing import (
    Annotated,
    Any,
    Literal,
    Optional,
    Union,
)
from pydantic import (
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    TypeAdapter,
    ValidationError,
    create_model,
)
from .cosmokit import 克隆,深入比较#深克隆与深比较

标注=Annotated#给基础类型挂约束
任意类型=Any#任意值直通
字面量=Literal#常量节点的注解
可选=Optional#可选字段的注解
联合类型=Union#联合与数字节点的注解
模型配置=ConfigDict#动态模型的配置
字段=Field#字段约束与默认值
严格布尔=StrictBool#拒绝 0/1 的布尔
严格浮点=StrictFloat#拒绝布尔与字符串的浮点
严格整数=StrictInt#拒绝布尔与字符串的整数
类型适配器=TypeAdapter#按注解校验
pydantic校验错误=ValidationError#pydantic 的校验失败
建模型=create_model#按字段表建动态模型

_类型期望={#pydantic 的类型失败到中文类型名
    'string_type':'字符串',
    'bool_type':'布尔值',
    'int_type':'数字',
    'float_type':'数字',
    'list_type':'数组',
    'dict_type':'对象',
    'model_type':'对象',
    'model_attributes_type':'对象',
}#类型名表结束

class 校验错误(TypeError):
    """配置没通过模式校验。"""
    def __init__(自身,消息,路径=None):
        """把出错位置的路径拼到消息前面。"""
        前缀=拼路径(路径 or [])#出错位置
        super().__init__(f'{前缀} {消息}' if 前缀 else 消息)#带位置的消息
        自身.路径=list(路径 or [])#出错位置，供界面定位字段

def 拼路径(路径):
    """把路径片段拼成 a.b[0].c 形式。"""
    结果=''#位置文本
    for 片段 in 路径:
        结果+=f'[{片段}]' if isinstance(片段,int) else ('.'+str(片段) if 结果 else str(片段))#下标或键
    return 结果#位置文本

def _写值(值):
    """把值写成诊断消息里显示的紧凑文本。"""
    return json.dumps(值,default=str,ensure_ascii=False)#紧凑字面量

#============================== 编译成 pydantic 注解 ==============================
def _加约束(基类型,约束):
    """有约束才包一层标注，没有就用裸类型。"""
    if not 约束:
        return 基类型#无约束
    return 标注[基类型,字段(**约束)]#挂上约束

def _常量注解(值):
    """常量编译成严格字面量。Literal 装不下的取值在建模时就失败。"""
    if not isinstance(值,(str,bool,int,type(None))):
        raise 校验错误(f'常量 {_写值(值)} 不能做模式：只支持字符串、布尔、整数与 None')#大声失败
    return 标注[字面量[值],字段(strict=True)]#严格字面量

def _字符串注解(元数据):
    """字符串编译成严格字符串，最小与最大在这里是长度。"""
    约束={'strict':True}#不接受别的类型转成字符串
    if 元数据.get('最小') is not None:
        约束['min_length']=元数据['最小']#长度下限
    if 元数据.get('最大') is not None:
        约束['max_length']=元数据['最大']#长度上限
    return 标注[str,字段(**约束)]#带长度约束的字符串

def _数字注解(元数据):
    """数字编译成严格整数与严格浮点的联合。约束挂在两支上，因为联合本身挂不了。"""
    约束={}#数值约束
    if 元数据.get('最小') is not None:
        约束['ge']=元数据['最小']#包含式下限
    if 元数据.get('最大') is not None:
        约束['le']=元数据['最大']#包含式上限
    if 元数据.get('步进') is not None:
        约束['multiple_of']=元数据['步进']#步进；相对 0 取模，旧实现相对下限取模，步进为 1 时两者一致
    return 联合类型[_加约束(严格整数,约束),_加约束(严格浮点,约束)]#排除布尔的数字

def _数组注解(节点):
    """数组编译成带长度约束的列表。"""
    约束={}#长度约束
    if 节点.元数据.get('最小') is not None:
        约束['min_length']=节点.元数据['最小']#长度下限
    if 节点.元数据.get('最大') is not None:
        约束['max_length']=节点.元数据['最大']#长度上限
    元素=_编译(节点.内层) if 节点.内层 is not None else 任意类型#元素注解
    return _加约束(list[元素],约束)#带长度约束的列表

def _联合注解(成员表):
    """联合编译成从左到右取第一个命中，与配置文件里的书写顺序一致。"""
    成员们=[_编译(项) for 项 in 成员表 or []]#各支注解
    if not 成员们:
        raise 校验错误('联合模式至少要有一个成员')#空联合没有可命中的支
    if len(成员们)==1:
        return 成员们[0]#单支不必包联合
    return 标注[联合类型[tuple(成员们)],字段(union_mode='left_to_right')]#按顺序试

def _默认工厂(默认):
    """生成每次交出新副本的默认值工厂，避免多个实例共享同一个可变默认。"""
    def 取默认():
        """交出默认值的一份新副本。"""
        return 克隆(默认)#新副本
    return 取默认#工厂

def _字段声明(子节点):
    """按子节点的必填与默认，给出建模型要的 (注解, 字段) 二元组。"""
    注解=_编译(子节点)#字段注解
    默认=子节点.元数据.get('默认')#声明的默认值
    if 默认 is not None:
        return 注解,字段(default_factory=_默认工厂(默认))#缺席时补默认
    if 子节点.元数据.get('必填'):
        return 注解,字段()#必需字段，缺席即报错
    return 可选[注解],字段(default=None)#可选字段，缺席为空

def _对象模型(节点):
    """对象编译成动态模型：声明字段各带默认，未声明的键原样留在 extra 里。"""
    字段们={}#建模型的字段表
    for 键,子 in (节点.字段表 or {}).items():
        if not isinstance(键,str) or not 键.isidentifier() or 键.startswith('_'):
            raise 校验错误(f'对象字段名 {_写值(键)} 不能建模：要求是不以下划线开头的合法标识符')#大声失败
        字段们[键]=_字段声明(子)#字段声明
    return 建模型('模式对象',__config__=模型配置(extra='allow'),**字段们)#保留未声明键的模型

def _编译(节点):
    """把一个模式节点编译成 pydantic 注解。"""
    类型=节点.类型#节点类型
    if 类型=='any':
        return 任意类型#任意值
    if 类型=='const':
        return _常量注解(节点.常量值)#字面量
    if 类型=='string':
        return _字符串注解(节点.元数据)#字符串
    if 类型=='number':
        return _数字注解(节点.元数据)#数字
    if 类型=='boolean':
        return 严格布尔#布尔
    if 类型=='array':
        return _数组注解(节点)#数组
    if 类型=='dict':
        键注解=_编译(节点.键模式) if 节点.键模式 is not None else str#键注解
        值注解=_编译(节点.内层) if 节点.内层 is not None else 任意类型#值注解
        return dict[键注解,值注解]#映射
    if 类型=='object':
        return _对象模型(节点)#对象
    if 类型=='union':
        return _联合注解(节点.成员表)#联合
    raise 校验错误(f'不支持的模式类型 "{类型}"')#类型不认识

#============================== 收结果与收诊断 ==============================
def _收结果(结果):
    """把 pydantic 的输出收回普通数据：模型转字典，缺席又没有默认值的声明字段不出现在输出里。"""
    if hasattr(结果,'model_fields_set'):
        已给=结果.model_fields_set#输入里显式写了的字段
        收={}#归一化输出
        for 键 in type(结果).model_fields:
            值=getattr(结果,键)#字段值
            if 值 is None and 键 not in 已给:
                continue#既没给也没有默认值，输出里不出现这个键
            收[键]=_收结果(值)#递归收
        for 键,值 in (getattr(结果,'model_extra',None) or {}).items():
            收[键]=值#未声明的键原样保留
        return 收#字典形态
    if isinstance(结果,list):
        return [_收结果(项) for 项 in 结果]#逐项收
    if isinstance(结果,dict):
        return {键:_收结果(值) for 键,值 in 结果.items()}#逐值收
    return 结果#标量原样

def _下降(节点,键):
    """按一个路径段在模式树上下降一层，走不下去则为 None。"""
    if 节点 is None:
        return None#断了
    if 节点.类型=='object':
        return (节点.字段表 or {}).get(键)#按字段名取
    if 节点.类型=='dict' or 节点.类型=='array':
        return 节点.内层#容器走内层
    if 节点.类型=='union':
        for 成员 in 节点.成员表 or []:
            命中=_下降(成员,键)#哪一支能下降
            if 命中 is not None:
                return 命中#取第一支
        return None#各支都走不下去
    return None#标量没有下一层

def 路径上节点(根,路径):
    """按设置路径解析模式节点；走不下去的段返回 None。"""
    节点=根#从根开始
    for 键 in 路径:
        节点=_下降(节点,键)#下降一层
        if 节点 is None:
            return None#断了
    return 节点#落到的节点

def _规整位置(根,位置):
    """把 pydantic 的错误位置过滤成模式树上真实存在的路径。联合分支这类合成段到此为止。"""
    路径=[]#真实路径
    节点=根#当前节点
    下标=0#位置游标
    while 下标<len(位置):
        下一=_下降(节点,位置[下标])#试着下降
        if 下一 is None:
            return 路径,节点,True#合成段，后面的丢掉
        路径.append(位置[下标])#这一段是真的
        节点=下一#下降
        下标+=1#前进
    return 路径,节点,False#整条位置都在树上

def _中文诊断(项):
    """把一条 pydantic 错误收成中文消息。"""
    类型=项.get('type')#错误类型
    上下文=项.get('ctx') or {}#约束值
    输入文本=_写值(项.get('input'))#实际输入
    if 类型=='missing':
        return '缺少必填值'#必填却没给
    期望=_类型期望.get(类型)#类型不符
    if 期望 is not None:
        return f'期望{期望}，实际是 {输入文本}'#类型不符
    if 类型=='literal_error':
        return f'期望 {上下文.get("expected")}，实际是 {输入文本}'#不是声明的字面量
    if 类型=='greater_than_equal':
        return f'期望数值不小于 {上下文.get("ge")}，实际是 {输入文本}'#低于下限
    if 类型=='less_than_equal':
        return f'期望数值不大于 {上下文.get("le")}，实际是 {输入文本}'#超过上限
    if 类型=='multiple_of':
        return f'期望是 {上下文.get("multiple_of")} 的整数倍，实际是 {输入文本}'#不是整数倍
    if 类型=='string_too_short':
        return f'期望字符串长度不小于 {上下文.get("min_length")}，实际是 {输入文本}'#太短
    if 类型=='string_too_long':
        return f'期望字符串长度不大于 {上下文.get("max_length")}，实际是 {输入文本}'#太长
    if 类型=='too_short':
        return f'期望长度不小于 {上下文.get("min_length")}，实际是 {输入文本}'#容器太短
    if 类型=='too_long':
        return f'期望长度不大于 {上下文.get("max_length")}，实际是 {输入文本}'#容器太长
    return 项.get('msg') or '校验失败'#其余照抄 pydantic 的说法

def _收诊断(根,错误):
    """把 pydantic 的校验失败收成一条带中文路径的 校验错误。"""
    项们=错误.errors()#全部错误
    if not 项们:
        return 校验错误('校验失败')#没有明细
    项=项们[0]#第一条就是要报的位置
    路径,落点,有剩余=_规整位置(根,项.get('loc') or ())#过滤合成段
    if 有剩余 and 落点 is not None and 落点.类型=='union':
        return 校验错误(f'期望 {落点.转字符串()}，实际是 {_写值(项.get("input"))}',路径)#联合各支都不匹配
    return 校验错误(_中文诊断(项),路径)#具体一条

#============================== 写回时的精简 ==============================
def _简化(节点,值):
    """递归去掉与模式默认值相同的部分。联合不知道命中了哪一支，原样交回。"""
    if 节点 is None or 值 is None:
        return 值#没有模式或没有值
    if 节点.类型=='object' and isinstance(值,dict):
        字段表=节点.字段表 or {}#声明字段
        收={}#精简结果
        for 键,项 in 值.items():
            子=字段表.get(键)#该键的模式
            if 子 is not None and 深入比较(项,子.元数据.get('默认')):
                continue#与声明的默认值相同，不必写回
            收[键]=_简化(子,项)#递归精简
        return 收#精简对象
    if 节点.类型=='array' and isinstance(值,list):
        return [_简化(节点.内层,项) for 项 in 值]#逐项精简
    if 节点.类型=='dict' and isinstance(值,dict):
        return {键:_简化(节点.内层,项) for 键,项 in 值.items()}#逐值精简
    return 值#其余原样

#============================== 模式节点 ==============================
class 模式:
    """可直接调用的模式节点，校验输入并交出归一化输出。"""
    def __init__(自身,选项=None):
        """把选项装配到本节点上。"""
        选项=选项 or {}#空选项
        if isinstance(选项,模式):
            选项=选项._导出选项()#从另一个节点复制
        自身.类型=选项.get('类型')#类型标签
        自身.元数据=dict(选项.get('元数据') or {})#默认值、约束与展示信息
        自身.键模式=选项.get('键模式')#字典的键模式
        自身.内层=选项.get('内层')#数组元素或字典值的模式
        自身.成员表=选项.get('成员表')#联合的成员模式
        自身.字段表=选项.get('字段表')#对象的字段模式
        自身.常量值=选项.get('常量值')#常量模式的取值
        自身._适配器=None#首次校验时才编译

    def _导出选项(自身):
        """导出一份可用来复制本节点的选项。"""
        return {
            '类型':自身.类型,#类型标签
            '元数据':dict(自身.元数据),#元数据副本
            '键模式':自身.键模式,#键模式
            '内层':自身.内层,#内层模式
            '成员表':list(自身.成员表) if 自身.成员表 is not None else None,#成员副本
            '字段表':dict(自身.字段表) if 自身.字段表 is not None else None,#字段副本
            '常量值':自身.常量值,#常量取值
        }#选项

    @property
    def 适配器(自身):
        """本节点的 pydantic 适配器，首次访问时编译整棵子树。"""
        if 自身._适配器 is None:
            自身._适配器=类型适配器(_编译(自身))#编译并缓存
        return 自身._适配器#适配器

    def __call__(自身,数据=None):
        """校验输入并交出归一化输出。"""
        if 数据 is None:
            if 自身.元数据.get('必填'):
                raise 校验错误('缺少必填值')#必填却没给
            回落=自身.元数据.get('默认')#默认值
            if 回落 is None:
                return None#没有默认值，空输入原样通过
            数据=克隆(回落)#默认值每次都给一份新的
        try:
            结果=自身.适配器.validate_python(数据)#交给 pydantic
        except pydantic校验错误 as 错误:
            raise _收诊断(自身,错误) from None#换成带中文路径的错误
        return _收结果(结果)#收回普通数据

    def __str__(自身):
        """收成紧凑的类型文本。"""
        return 自身.转字符串()#默认不内联

    def 转字符串(自身,内联=False):
        """收成紧凑的类型文本，内联时联合会加括号。"""
        类型=自身.类型#节点类型
        if 类型=='any':
            return 'any'#任意
        if 类型=='const':
            return json.dumps(自身.常量值,ensure_ascii=False) if isinstance(自身.常量值,str) else str(自身.常量值)#字面量
        if 类型=='string':
            return 'string'#字符串
        if 类型=='number':
            return 'number'#数字
        if 类型=='boolean':
            return 'boolean'#布尔
        if 类型=='array':
            return f'{自身.内层.转字符串(True)}[]'#元素类型加方括号
        if 类型=='dict':
            return f'{{ [key: {自身.键模式.转字符串()}]: {自身.内层.转字符串()} }}'#索引签名
        if 类型=='object':
            字段表=自身.字段表 or {}#字段模式
            if not 字段表:
                return '{}'#空对象
            片段=[f'{键}{"" if 内层.元数据.get("必填") else "?"}: {内层.转字符串()}' for 键,内层 in 字段表.items()]#逐字段
            return '{ '+', '.join(片段)+' }'#花括号字段列表
        if 类型=='union':
            文本=' | '.join(内层.转字符串() for 内层 in 自身.成员表 or [])#各支类型
            return f'({文本})' if 内联 else 文本#内联时加括号
        return f'模式<{类型}>'#类型不认识

    #============================== 元数据 ==============================
    def 额外(自身,键,值):
        """复制一份本节点，并在它的元数据上挂一项。"""
        克隆节点=模式(自身._导出选项())#复制节点
        克隆节点.元数据[键]=值#写入元数据
        return 克隆节点#新节点

    def 必填(自身,值=True):
        """标记空输入非法，除非有默认值能补上。"""
        return 自身.额外('必填',值)#必填

    def 默认(自身,值):
        """设置空输入时的回落值。"""
        return 自身.额外('默认',值)#默认值

    def 描述(自身,文本):
        """挂上给人看的描述文案。"""
        return 自身.额外('描述',文本)#描述

    def 最大(自身,值):
        """设置包含式上限。字符串与容器上是长度，数字上是取值。"""
        return 自身.额外('最大',值)#上限

    def 最小(自身,值):
        """设置包含式下限。字符串与容器上是长度，数字上是取值。"""
        return 自身.额外('最小',值)#下限

    def 步进(自身,值):
        """设置数字的步进约束。"""
        return 自身.额外('步进',值)#步长

    def 角色(自身,角色名,额外=None):
        """挂上界面渲染角色与可选的附加信息。"""
        克隆节点=自身.额外('角色',角色名)#写入角色
        克隆节点.元数据['角色附加']=额外#附加信息
        return 克隆节点#新节点

    #============================== 序列化 ==============================
    def 转JSON(自身):
        """序列化成纯数据的模式树，供配置界面消费。"""
        数据={#节点字段
            '类型':自身.类型,#类型标签
            '元数据':{键:值 for 键,值 in 自身.元数据.items() if not callable(值)},#丢掉不能序列化的函数
        }#节点字段结束
        if 自身.类型=='const':
            数据['常量值']=自身.常量值#常量取值
        if 自身.键模式 is not None:
            数据['键模式']=自身.键模式.转JSON()#键模式
        if 自身.内层 is not None:
            数据['内层']=自身.内层.转JSON()#内层模式
        if 自身.成员表 is not None:
            数据['成员表']=[项.转JSON() for 项 in 自身.成员表]#各支
        if 自身.字段表 is not None:
            数据['字段表']={键:项.转JSON() for 键,项 in 自身.字段表.items()}#各字段
        return 数据#纯数据模式树

    @staticmethod
    def 从JSON(数据):
        """从 转JSON 的纯数据重建模式树。"""
        if 数据 is None:
            return None#空节点
        节点=模式({'类型':数据.get('类型'),'元数据':数据.get('元数据'),'常量值':数据.get('常量值')})#本层节点
        节点.键模式=模式.从JSON(数据.get('键模式'))#键模式
        节点.内层=模式.从JSON(数据.get('内层'))#内层模式
        成员表=数据.get('成员表')#各支
        节点.成员表=[模式.从JSON(项) for 项 in 成员表] if 成员表 is not None else None#各支节点
        字段表=数据.get('字段表')#各字段
        节点.字段表={键:模式.从JSON(项) for 键,项 in 字段表.items()} if 字段表 is not None else None#各字段节点
        return 节点#重建的节点

    def 简化(自身,值):
        """去掉等于模式默认值的部分，交出可写回配置文件的最短形态。"""
        return _简化(自身,值)#递归精简

    #============================== 推断 ==============================
    @staticmethod
    def 推断(源=None):
        """从字面量、内建类型或已有模式推断出模式。"""
        if 源 is None:
            return 模式.任意()#没给就当任意
        if isinstance(源,模式):
            return 源#已经是模式
        if isinstance(源,type):
            if 源 is str:
                return 模式.字符串().必填()#字符串
            if 源 is bool:
                return 模式.布尔().必填()#布尔
            if 源 is int or 源 is float:
                return 模式.数字().必填()#数字
        elif isinstance(源,(str,bool,int,float)):
            return 模式.常量(源).必填()#字面量当常量
        raise TypeError(f'无法从 {源} 推断出模式')#不认识的形态

    @staticmethod
    def 自然数():
        """非负整数。"""
        return 模式.数字().步进(1).最小(0)#自然数

def _建工厂(类型标签,参数名们):
    """生成建某类型节点的工厂，按参数名顺序装位置参数。"""
    def 工厂(类,*位置参数):
        """按参数名顺序把位置参数装到新节点上。"""
        节点=模式({'类型':类型标签})#新节点
        for 下标,参数名 in enumerate(参数名们):
            参数=位置参数[下标] if 下标<len(位置参数) else None#对应位置参数
            if 参数名=='键模式':
                节点.键模式=参数 if 参数 is not None else 模式.字符串()#字典键默认是字符串
            elif 参数名=='内层':
                节点.内层=模式.推断(参数)#推断元素模式
            elif 参数名=='成员表':
                节点.成员表=[模式.推断(项) for 项 in 参数]#推断各支模式
            elif 参数名=='字段表':
                节点.字段表={键:模式.推断(项) for 键,项 in 参数.items()}#推断各字段模式
            else:
                setattr(节点,参数名,参数)#常量值等直接写
        if 类型标签 in ('object','dict'):
            节点.元数据['默认']={}#对象与字典默认是空映射
        elif 类型标签=='array':
            节点.元数据['默认']=[]#数组默认是空列表
        return 节点#新节点
    return 工厂#工厂

模式.任意=classmethod(_建工厂('any',[]))#任意值
模式.常量=classmethod(_建工厂('const',['常量值']))#常量
模式.字符串=classmethod(_建工厂('string',[]))#字符串
模式.数字=classmethod(_建工厂('number',[]))#数字
模式.布尔=classmethod(_建工厂('boolean',[]))#布尔
模式.数组=classmethod(_建工厂('array',['内层']))#数组
模式.字典=classmethod(_建工厂('dict',['内层','键模式']))#字典
模式.对象=classmethod(_建工厂('object',['字段表']))#对象
模式.联合=classmethod(_建工厂('union',['成员表']))#联合

模式.校验错误=校验错误#让调用方从模式上取到错误类型
