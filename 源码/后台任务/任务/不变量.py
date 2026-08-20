"""本包拥有的后台任务快照不变量。"""
import json,math#JSON片段与安全整数判定
from cordis.工具 import 已兑现#立刻兑现的拆除器

包名='@deepseek-ai/dsh-jobs'#本包的不变量所有权名
名称='jobs-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
终态集合=set(('completed','killed','failed'))#终态集合
安全整数上限=9007199254740991#Number.MAX_SAFE_INTEGER

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 化为数字(原始):#对齐JS Number(string)
    """对齐 JS Number(string)；空串为 0，非法为 NaN。"""
    if 原始=='':#空串
        return 0#Number('')===0
    try:#解析浮点
        值=float(原始)#对齐Number
    except Exception:#非法字面量
        return float('nan')#NaN
    if math.isnan(值) or math.isinf(值):#非有限
        return float('nan')#NaN
    return 值#有限数

def 是否安全整数(值):#对齐JS Number.isSafeInteger
    """对齐 JS Number.isSafeInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是整数
    if isinstance(值,int):#整数
        return abs(值)<=安全整数上限#在安全范围内
    if isinstance(值,float):#浮点
        if not math.isfinite(值) or not 值.is_integer():#非有限或非整
            return False#不是安全整数
        return abs(值)<=安全整数上限#在安全范围内
    return False#其它类型

def 编码内容(值):#对齐JSON.stringify的报错片段
    """把值编成 JSON 片段，对齐 TypeScript JSON.stringify。"""
    return json.dumps(值,ensure_ascii=False)#JSON片段

def 校验快照(快照,所有者,失败):#校验一份注册表快照里的跨字段关系
    """校验一份注册表快照里的跨字段关系。"""
    标识=str(取字段(快照,'id'))#原始id字符串
    种类=取字段(快照,'kind')#生产者种类
    种类串='' if 种类 is None else str(种类)#种类字符串
    前缀=种类串+'-'#kind前缀
    序数=化为数字(标识[len(前缀):]) if 标识.startswith(前缀) else float('nan')#前缀后的序数
    if (len(种类串)==0 or (not 标识.startswith(前缀))
        or (not 是否安全整数(序数)) or 序数<1):#kind空或前缀不符或序数非法
        失败('job snapshot id '+编码内容(标识)+' must be '+编码内容(前缀)+' followed by a positive ordinal')#id形态失败
    标签=取字段(快照,'label')#一行标签
    if 标签 is None or len(str(标签))==0:#标签空
        失败('job '+编码内容(标识)+' label must be non-empty')#标签非空
    开始于=取字段(快照,'startedAt')#开始时间
    if (not 是否安全整数(开始于)) or 开始于<0:#开始时间非法
        失败('job '+编码内容(标识)+' startedAt must be a non-negative epoch integer')#startedAt失败
    状态=取字段(快照,'status')#生命周期状态
    结束于=取字段(快照,'finishedAt')#结束时间
    是终态=状态 in 终态集合#是否终态
    if 是终态!=(结束于 is not None):#终态与finishedAt必须同在
        失败('job '+编码内容(标识)+' finishedAt must be present exactly for a terminal status')#finishedAt配对失败
    if 结束于 is not None and ((not 是否安全整数(结束于)) or 结束于<开始于):#早于开始或非整数
        失败('job '+编码内容(标识)+' finishedAt must be an epoch integer no earlier than startedAt')#finishedAt时序失败
    期望所有者=取字段(所有者,'id') if 所有者 is not None else None#完成回调给出的所有者id
    if 取字段(快照,'ownerSession')!=期望所有者:#快照所有者与回调不符
        失败('job '+编码内容(标识)+' ownerSession does not match its completion owner')#所有者不一致

def 安装(上下文对象,失败):#对当前无主记录和每一个终态快照安装检查
    """对当前无主记录和每一个终态快照安装检查。"""
    for 快照 in 上下文对象.jobs.列出():#校验现有无主列表
        校验快照(快照,None,失败)#无主
    def 完成时(快照,所有者,*其余):#终态时再校验
        """终态时再校验。"""
        校验快照(快照,所有者,失败)#带精确所有者
    上下文对象.jobs.任务完成时(完成时)#登记完成监听

安装.inject=['jobs']#安装器还依赖jobs

def 应用(上下文对象):#注册任务注册表不变量配套
    """注册任务注册表不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记本包不变量并包成立即兑现的承诺

apply=应用#Cordis插件入口
