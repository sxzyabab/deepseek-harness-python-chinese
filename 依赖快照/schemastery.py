"""schemastery 模式校验器。"""
import json,math,re
from cosmokit import (
    克隆,#深克隆
    深度相等,#深比较
    是否可空,#空值判断
    是否普通对象,#普通对象判断
    映射值,#映射值
)

模式序号=0#全局序号
模式引用=None#序列化引用表
解析器表={}#类型名 → 解析函数
格式化表={}#类型名 → 格式化函数

class 校验错误(TypeError):
    """模式校验失败时抛出的错误。"""
    def __init__(自身,消息,选项):
        """用路径前缀拼出校验消息。"""
        #拼接路径前缀
        前缀='$'#根前缀
        for 片段 in 选项.get('路径') or []:
            if isinstance(片段,str):
                前缀+='.'+片段#对象键
            elif isinstance(片段,int):
                前缀+='['+str(片段)+']'#下标
            else:
                前缀+=f'[Symbol({片段})]'#符号键
        if 前缀.startswith('.'):
            前缀=前缀[1:]#去掉开头点
        全文=('' if 前缀=='$' else f'{前缀} ')+消息#完整消息
        super().__init__(全文)#写入消息
        自身.选项=选项#保存选项
        自身.名称='ValidationError'#错误名

校验错误.校验错误品牌=True#挂上品牌

def 检查范围(数据,元,描述,选项,跳过最小=False):
    """检查数值是否落在元数据的最小最大之间。"""
    #读取范围
    最大=元.get('最大',math.inf)#上限
    最小=元.get('最小',-math.inf)#下限
    if 数据>最大:
        raise 校验错误(f'expected {描述} <= {最大} but got {数据}',选项)#超过上限
    if 数据<最小 and not 跳过最小:
        raise 校验错误(f'expected {描述} >= {最小} but got {数据}',选项)#低于下限

def 十进制移位(数据,位数):
    """把小数点右移指定位数。"""
    #科学计数不拆字符串
    文本=str(数据)#数字文本
    if 'e' in 文本 or 'E' in 文本:
        return 数据*math.pow(10,位数)#直接乘
    点=文本.find('.')#小数点位置
    if 点==-1:
        return 数据*math.pow(10,位数)#整数
    小数=文本[点+1:]#小数部分
    整数=文本[:点]#整数部分
    if len(小数)<=位数:
        return float(整数+小数.ljust(位数,'0'))#补零
    return float(整数+小数[:位数]+'.'+小数[位数:])#插入新小数点

def 是否倍数(数据,最小,步进):
    """判断数据相对最小是否为步进的倍数。"""
    #取步进绝对值
    步进=abs(步进)#绝对值
    if not re.match(r'^\d+\.\d+$',str(步进)):
        return (数据-最小)%步进==0#整数步进
    点=str(步进).find('.')#小数点
    位数=len(str(步进)[点+1:])#小数位数
    return abs(十进制移位(数据,位数)-十进制移位(最小,位数))%十进制移位(步进,位数)==0#移位后取模

def 解析属性(数据,键,模式实例,选项):
    """解析对象或数组上的一个属性。"""
    #带子路径解析
    try:
        子选项=dict(选项)#拷贝选项
        子选项['路径']=list(选项.get('路径') or [])+[键]#追加路径
        值,适配=补齐二元(模式.解析(数据[键] if _有键(数据,键) else None,模式实例,子选项))#解析
        if 适配 is not None:
            数据[键]=适配#写回适配输入
        return 值#属性值
    except Exception as 错误:
        if not (选项 or {}).get('自动修复'):
            raise 错误#不自动修复则抛出
        if isinstance(数据,dict):
            数据.pop(键,None)#删除非法键
        elif isinstance(数据,list) and isinstance(键,int) and 0<=键<len(数据):
            del 数据[键]#删除非法下标
        return 模式实例.元.get('默认')#回落到默认

def _有键(数据,键):
    """数据上是否存在该键。"""
    #列表用下标，映射用 in
    if isinstance(数据,list):
        return isinstance(键,int) and 0<=键<len(数据)#下标合法
    if isinstance(数据,dict):
        return 键 in 数据#键存在
    return False#其它类型

def 补齐二元(结果):
    """把解析结果收成二元组。"""
    #单值补 None
    if not isinstance(结果,(list,tuple)):
        return 结果,None#只有输出
    if len(结果)==1:
        return 结果[0],None#没有适配
    return 结果[0],结果[1]#输出与适配

def 合并对象(结果,数据):
    """把数据中结果没有的键补进去。"""
    #只补缺失键
    for 键 in 数据:
        if 键 in 结果:
            continue#已有
        结果[键]=数据[键]#补入

class 模式:
    """可调用的模式实例，校验输入并返回归一输出。"""
    def __new__(类,选项=None):
        """从选项构造模式；带引用表则还原共享节点。"""
        global 模式序号#分配序号
        if 选项 is None:
            选项={}#空选项
        if isinstance(选项,模式) and getattr(选项,'引用',None):
            选项={'引用':选项.引用,'序号':选项.序号}#从实例取引用
        引用=选项.get('引用') if isinstance(选项,dict) else getattr(选项,'引用',None)#引用表
        if 引用:
            还原=映射值(引用,lambda 项,键:模式._从纯选项(项))#还原节点
            def 取引用(序号):
                """按序号取还原后的节点。"""
                return 还原[序号]#引用节点
            for 键 in 还原:
                节点=还原[键]#当前节点
                if getattr(节点,'键模式',None) is not None:
                    节点.键模式=取引用(节点.键模式)#还原键模式
                if getattr(节点,'内层',None) is not None:
                    节点.内层=取引用(节点.内层)#还原内层
                if getattr(节点,'列表',None) is not None:
                    节点.列表=[取引用(项) for 项 in 节点.列表]#还原列表
                if getattr(节点,'字典',None) is not None:
                    节点.字典=映射值(节点.字典,lambda 项,子键:取引用(项))#还原字典
            目标序号=选项.get('序号') if isinstance(选项,dict) else 选项.序号#根序号
            return 还原[目标序号]#返回根节点
        实例=object.__new__(类)#新实例
        return 实例#交给 init

    @staticmethod
    def _从纯选项(选项):
        """不走引用还原的直接构造。"""
        #绕过 __new__ 的引用分支
        实例=object.__new__(模式)#新实例
        实例._装配(选项 if isinstance(选项,dict) else 选项.__dict__)#装配
        return 实例#已装配实例

    def __init__(自身,选项=None):
        """把选项装配到模式实例上。"""
        #引用还原已在 __new__ 返回其它对象
        if getattr(自身,'_已装配',False):
            return#已装配
        自身._装配(选项 or {})#装配选项

    def _装配(自身,选项):
        """把选项字段写到实例上。"""
        global 模式序号#分配序号
        #拷贝已知字段
        if isinstance(选项,模式):
            选项=选项._导出选项()#从实例导出
        自身.类型=选项.get('类型') or 选项.get('type')#类型标签
        自身.元=dict(选项.get('元') or 选项.get('meta') or {})#元数据
        自身.键模式=选项.get('键模式') or 选项.get('sKey')#键模式
        自身.内层=选项.get('内层') or 选项.get('inner')#内层
        自身.列表=选项.get('列表') or 选项.get('list')#成员列表
        自身.字典=选项.get('字典') or 选项.get('dict')#字段表
        自身.常量值=选项.get('常量值') if '常量值' in 选项 else 选项.get('value')#常量
        自身.引用=选项.get('引用') or 选项.get('refs')#引用表
        自身.序号=模式序号#分配序号
        模式序号+=1#递增
        自身.模式品牌=True#打上品牌
        自身._已装配=True#避免 __init__ 重复装配

    def _导出选项(自身):
        """导出可用来复制的选项。"""
        #收集字段
        return {
            '类型':自身.类型,#类型
            '元':dict(自身.元),#元数据
            '键模式':自身.键模式,#键模式
            '内层':自身.内层,#内层
            '列表':list(自身.列表) if 自身.列表 is not None else None,#列表
            '字典':dict(自身.字典) if 自身.字典 is not None else None,#字典
            '常量值':自身.常量值,#常量
        }#选项

    def __call__(自身,数据=None,选项=None):
        """校验输入并返回归一输出。"""
        #走解析器
        return 模式.解析(数据,自身,选项 or {})[0]#只取输出

    @property
    def 标准协议(自身):
        """Standard Schema V1 适配。"""
        #构造校验闭包
        def 校验(值):
            """按标准协议校验。"""
            try:
                return {'value':模式.解析(值,自身,{})[0]}#成功
            except 校验错误 as 错误:
                return {'issues':[{'message':str(错误),'path':错误.选项.get('路径')}]}#问题列表
        return {'version':1,'vendor':'schemastery','validate':校验}#协议对象

    def 转JSON(自身):
        """序列化本模式，保留共享与递归引用。"""
        global 模式引用#序列化引用表
        if 模式引用 is not None:
            if 自身.序号 not in 模式引用:
                模式引用[自身.序号]=json.loads(json.dumps(自身._可序列化(),default=str))#登记
            return 自身.序号#返回序号
        模式引用={自身.序号:自身._可序列化()}#开始序列化
        模式引用[自身.序号]=json.loads(json.dumps(自身._可序列化(),default=str))#去掉不可序列化
        结果={'序号':自身.序号,'引用':模式引用}#带引用表的根
        模式引用=None#清掉引用表
        return 结果#序列化结果

    def _可序列化(自身):
        """导出可 JSON 化的字段。"""
        #去掉函数
        数据=自身._导出选项()#选项
        数据['序号']=自身.序号#带上序号
        return {键:值 for 键,值 in 数据.items() if not callable(值)}#去掉函数

    def 额外(自身,键,值):
        """挂上任意元数据。"""
        #克隆并写元数据
        克隆模式=模式(自身._导出选项())#新节点
        克隆模式.元={**克隆模式.元,键:值}#写入
        return 克隆模式#克隆

    def 必填(自身,值=True):
        """标记空输入非法，除非默认能补上。"""
        return 自身.额外('必填',值)#写必填

    def __str__(自身,内联=False):
        """收成紧凑的类型字符串。"""
        #查格式化表
        格式化=格式化表.get(自身.类型)#格式化函数
        if 格式化:
            return 格式化(自身,内联)#格式化
        return f'Schema<{自身.类型}>'#回退

    def 转字符串(自身,内联=False):
        """收成紧凑的类型字符串。"""
        return 自身.__str__(内联)#委托

    def 角色(自身,角色名,额外=None):
        """挂上渲染角色与可选元数据。"""
        克隆模式=模式(自身._导出选项())#新节点
        克隆模式.元={**克隆模式.元,'角色':角色名,'额外':额外}#写入
        return 克隆模式#克隆

    def 默认(自身,值):
        """设置空输入时的回落值。"""
        return 自身.额外('默认',值)#写默认

    def 描述(自身,文本):
        """挂上描述文案。"""
        return 自身.额外('描述',文本)#写描述

    def 最大(自身,值):
        """设置包含式上限。"""
        return 自身.额外('最大',值)#写最大

    def 最小(自身,值):
        """设置包含式下限。"""
        return 自身.额外('最小',值)#写最小

    def 步进(自身,值):
        """设置数字步进约束。"""
        return 自身.额外('步进',值)#写步进

    @staticmethod
    def 扩展(类型名,解析):
        """为自定义类型登记解析器。"""
        解析器表[类型名]=解析#登记

    @staticmethod
    def 解析(数据,模式实例,选项=None,严格=False):
        """按模式节点校验，返回 [输出, 适配输入?]。"""
        #空模式直接通过
        if 选项 is None:
            选项={}#默认选项
        if not 模式实例:
            return [数据]#无模式
        忽略=选项.get('忽略')#忽略谓词
        if 忽略 and 忽略(数据,模式实例):
            return [数据]#跳过
        if 是否可空(数据):
            if 模式实例.元.get('必填'):
                raise 校验错误('missing required value',选项)#缺必填
            回落=模式实例.元.get('默认')#默认值
            if 是否可空(回落):
                return [数据]#没有默认
            数据=克隆(回落)#用默认克隆
        回调=解析器表.get(模式实例.类型)#类型解析器
        if not 回调:
            raise 校验错误(f'unsupported type "{模式实例.类型}"',选项)#未知类型
        try:
            return 回调(数据,模式实例,选项,严格)#解析
        except Exception as 错误:
            if not 模式实例.元.get('宽松'):
                raise 错误#非宽松则抛出
            return [模式实例.元.get('默认')]#宽松回落默认

    @staticmethod
    def 推断(源=None):
        """从原始值、构造器或已有模式推断模式。"""
        #空值则任意
        if 是否可空(源):
            return 模式.任意()#任意
        if isinstance(源,(str,int,float,bool)) and not isinstance(源,type):
            return 模式.常量(源).必填()#常量
        if getattr(源,'模式品牌',False):
            return 源#已是模式
        if isinstance(源,type):
            if 源 is str:
                return 模式.字符串().必填()#字符串
            if 源 is int or 源 is float:
                return 模式.数字().必填()#数字
            if 源 is bool:
                return 模式.布尔().必填()#布尔
        raise TypeError(f'cannot infer schema from {源}')#无法推断

    @staticmethod
    def 自然数():
        """非负整数。"""
        return 模式.数字().步进(1).最小(0)#自然数

def 解析任意(数据,模式实例=None,选项=None,严格=False):
    """任意值原样通过。"""
    return [数据]#原样

def 解析常量(数据,模式实例,选项,严格=False):
    """必须等于常量。"""
    if 深度相等(数据,模式实例.常量值):
        return [模式实例.常量值]#命中常量
    raise 校验错误(f'expected {模式实例.常量值} but got {数据}',选项)#不匹配

def 解析字符串(数据,模式实例,选项,严格=False):
    """校验字符串及长度。"""
    if not isinstance(数据,str):
        raise 校验错误(f'expected string but got {数据}',选项)#不是字符串
    检查范围(len(数据),模式实例.元,'string length',选项)#长度
    return [数据]#通过

def 解析数字(数据,模式实例,选项,严格=False):
    """校验数字、范围与步进。"""
    if not isinstance(数据,(int,float)) or isinstance(数据,bool):
        raise 校验错误(f'expected number but got {数据}',选项)#不是数字
    检查范围(数据,模式实例.元,'number',选项)#范围
    步进=模式实例.元.get('步进')#步进
    if 步进 and not 是否倍数(数据,模式实例.元.get('最小') or 0,步进):
        raise 校验错误(f'expected number multiple of {步进} but got {数据}',选项)#不是倍数
    return [数据]#通过

def 解析布尔(数据,模式实例,选项,严格=False):
    """校验布尔。"""
    if isinstance(数据,bool):
        return [数据]#通过
    raise 校验错误(f'expected boolean but got {数据}',选项)#不是布尔

def 解析数组(数据,模式实例,选项,严格=False):
    """校验元素数组。"""
    if not isinstance(数据,list):
        raise 校验错误(f'expected array but got {数据}',选项)#不是数组
    跳过最小=not 是否可空((模式实例.内层.元 if 模式实例.内层 else {}).get('默认'))#内层有默认则跳过最小
    检查范围(len(数据),模式实例.元,'array length',选项,跳过最小)#长度
    return [[解析属性(数据,下标,模式实例.内层,选项) for 下标 in range(len(数据))]]#逐项解析

def 解析字典(数据,模式实例,选项,严格=False):
    """校验普通对象的值与可选键模式。"""
    if not 是否普通对象(数据):
        raise 校验错误(f'expected object but got {数据}',选项)#不是对象
    结果={}#输出
    for 键 in list(数据.keys()):
        try:
            正规键=模式.解析(键,模式实例.键模式,选项)[0]#解析键
        except Exception as 错误:
            if 严格:
                continue#严格模式跳过非法键
            raise 错误#非严格则抛出
        结果[正规键]=解析属性(数据,键,模式实例.内层,选项)#解析值
        数据[正规键]=数据[键]#写回正规键
        if 键!=正规键:
            del 数据[键]#删旧键
    return [结果]#字典输出

def 解析对象(数据,模式实例,选项,严格=False):
    """按字段表校验普通对象。"""
    if not 是否普通对象(数据):
        raise 校验错误(f'expected object but got {数据}',选项)#不是对象
    结果={}#输出
    字典=模式实例.字典 or {}#字段表
    for 键 in 字典:
        值=解析属性(数据,键,字典[键],选项)#解析字段
        if not 是否可空(值) or 键 in 数据:
            结果[键]=值#有值或原对象有该键
    if not 严格:
        合并对象(结果,数据)#补未声明键
    return [结果]#对象输出

def 解析联合(数据,模式实例,选项,严格=False):
    """命中任一成员即通过。"""
    消息=[]#失败收集
    for 内层 in 模式实例.列表 or []:
        try:
            return 模式.解析(数据,内层,选项,严格)#命中即返回
        except Exception as 错误:
            消息.append(错误)#记下失败
    raise 校验错误(f'expected {模式实例.转字符串()} but got {json.dumps(数据,default=str)}',选项)#全失败

模式.扩展('any',解析任意)#任意
模式.扩展('const',解析常量)#常量
模式.扩展('string',解析字符串)#字符串
模式.扩展('number',解析数字)#数字
模式.扩展('boolean',解析布尔)#布尔
模式.扩展('array',解析数组)#数组
模式.扩展('dict',解析字典)#字典
模式.扩展('object',解析对象)#对象
模式.扩展('union',解析联合)#联合

def 定义方法(名称,键列表,格式化):
    """登记格式化并在模式上挂工厂。"""
    格式化表[名称]=格式化#登记格式化
    def 工厂(类,*位置参数):
        """按键列表装配模式节点。"""
        模式实例=模式({'类型':名称})#新节点
        下标=0#参数下标
        for 键 in 键列表:
            参数=位置参数[下标] if 下标<len(位置参数) else None#对应参数
            if 键=='键模式':
                模式实例.键模式=参数 if 参数 is not None else 模式.字符串()#默认字符串键
            elif 键=='内层':
                模式实例.内层=模式.推断(参数)#推断内层
            elif 键=='列表':
                模式实例.列表=[模式.推断(项) for 项 in 参数]#推断成员
            elif 键=='字典':
                模式实例.字典=映射值(参数,lambda 项,子键:模式.推断(项))#推断字段
            elif 键=='常量值':
                模式实例.常量值=参数#常量
            else:
                setattr(模式实例,键,参数)#其它字段
            下标+=1#下一参数
        if 名称=='object' or 名称=='dict':
            模式实例.元['默认']={}#对象默认空映射
        elif 名称=='array':
            模式实例.元['默认']=[]#数组默认空列表
        return 模式实例#工厂结果
    return 工厂#返回工厂

def 格式化任意(模式实例,内联=False):
    """格式化 any。"""
    return 'any'#任意

def 格式化常量(模式实例,内联=False):
    """格式化常量。"""
    值=模式实例.常量值#常量
    return json.dumps(值) if isinstance(值,str) else 值#字符串加引号

def 格式化字符串(模式实例,内联=False):
    """格式化 string。"""
    return 'string'#字符串

def 格式化数字(模式实例,内联=False):
    """格式化 number。"""
    return 'number'#数字

def 格式化布尔(模式实例,内联=False):
    """格式化 boolean。"""
    return 'boolean'#布尔

def 格式化数组(模式实例,内联=False):
    """格式化 array。"""
    return f'{模式实例.内层.转字符串(True)}[]'#元素数组

def 格式化字典(模式实例,内联=False):
    """格式化 dict。"""
    return f'{{ [key: {模式实例.键模式.转字符串()}]: {模式实例.内层.转字符串()} }}'#索引对象

def 格式化对象(模式实例,内联=False):
    """格式化 object。"""
    字典=模式实例.字典 or {}#字段表
    if not 字典:
        return '{}'#空对象
    片段=[]#字段片段
    for 键,内层 in 字典.items():
        可选='' if 内层.元.get('必填') else '?'#可选标记
        片段.append(f'{键}{可选}: {内层.转字符串()}')#字段
    return '{ '+', '.join(片段)+' }'#对象

def 格式化联合(模式实例,内联=False):
    """格式化 union。"""
    结果=' | '.join(内层.转字符串() for 内层 in 模式实例.列表)#各支
    return f'({结果})' if 内联 else 结果#内联加括号

模式.任意=classmethod(定义方法('any',[],格式化任意))#任意
模式.常量=classmethod(定义方法('const',['常量值'],格式化常量))#常量
模式.字符串=classmethod(定义方法('string',[],格式化字符串))#字符串
模式.数字=classmethod(定义方法('number',[],格式化数字))#数字
模式.布尔=classmethod(定义方法('boolean',[],格式化布尔))#布尔
模式.数组=classmethod(定义方法('array',['内层'],格式化数组))#数组
模式.字典=classmethod(定义方法('dict',['内层','键模式'],格式化字典))#字典
模式.对象=classmethod(定义方法('object',['字典'],格式化对象))#对象
模式.联合=classmethod(定义方法('union',['列表'],格式化联合))#联合

模式.校验错误=校验错误#挂上错误类
