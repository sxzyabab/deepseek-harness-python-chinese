"""本地 PTY 后端经过校验的配置。"""
from ...依赖 import schemastery#外部依赖胶水
模式=schemastery.模式#配置校验库

安全整数上限=9007199254740991#JS Number.MAX_SAFE_INTEGER

配置=模式.对象({#对外插件配置模式
    'backendType':模式.字符串().默认('shell'),#默认后端类型
    'shellPath':模式.字符串().默认('/bin/bash'),#默认shell路径
    'shellArgs':模式.数组(模式.字符串()).默认(['--noprofile','--norc','-i']),#默认shell参数
    'rows':模式.数字().默认(40),#默认行数
    'cols':模式.数字().默认(160),#默认列数
    'scrollbackLines':模式.数字().默认(10000),#默认回滚行数
    'scrollbackMaxBytes':模式.数字().默认(4*1024*1024),#默认回滚字节
    'maxReadBytes':模式.数字().默认(256*1024),#默认单次读取字节
    'pollIntervalMs':模式.数字().默认(50),#默认轮询间隔
    'exactProbeAfterMs':模式.数字().默认(150),#默认精确探测延迟
    'idleSilenceMs':模式.数字().默认(3000),#默认空闲静默
    'handoffGraceMs':模式.数字().默认(500),#默认交接宽限
    'timeoutMs':模式.数字().默认(30000),#默认超时
    'disposeGraceMs':模式.数字().默认(3000),#默认拆除宽限
})#配置模式结束
Config=配置#Cordis配置模式

def 是否安全整数(值):#对齐JS Number.isSafeInteger
    """对齐 JS Number.isSafeInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是整数
    if isinstance(值,int):#整数
        return abs(值)<=安全整数上限#落在安全范围
    if isinstance(值,float) and 值.is_integer():#整值浮点
        return abs(值)<=安全整数上限#落在安全范围
    return False#其它类型

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

数值字段=(#须为正安全整数的配置键
    'rows','cols','scrollbackLines','scrollbackMaxBytes','maxReadBytes',#尺寸与缓冲
    'pollIntervalMs','exactProbeAfterMs','idleSilenceMs','handoffGraceMs','timeoutMs','disposeGraceMs',#计时
)#数值字段结束

def 校验配置(配置值):#断言每个数值配置字段都是正的安全整数，且上下限能组合
    """断言每个数值配置字段都是正的安全整数，且上下限能组合；把输入收窄为已完全解析的配置。"""
    if len(取字段(配置值,'backendType') or '')==0:#空后端类型
        raise Exception('terminal-bash: backendType must be non-empty')#拒绝空后端类型
    if len(取字段(配置值,'shellPath') or '')==0:#空shell路径
        raise Exception('terminal-bash: shellPath must be non-empty')#拒绝空shell路径
    for 名称 in 数值字段:#逐数值字段
        值=取字段(配置值,名称)#字段值
        if isinstance(值,bool) or (not isinstance(值,(int,float))) or (not 是否安全整数(值)) or 值<=0:#非正安全整数
            raise Exception('terminal-bash: '+名称+' must be a positive safe integer')#拒绝非法数值
    if 取字段(配置值,'maxReadBytes')>取字段(配置值,'scrollbackMaxBytes'):#单次读取超过回滚上限
        raise Exception('terminal-bash: maxReadBytes must not exceed scrollbackMaxBytes')#拒绝越界读取上限
    if 取字段(配置值,'handoffGraceMs')<取字段(配置值,'pollIntervalMs'):#宽限短于一轮轮询
        raise Exception('terminal-bash: handoffGraceMs must be at least pollIntervalMs so one readiness poll runs inside the grace window')#拒绝过短交接宽限
