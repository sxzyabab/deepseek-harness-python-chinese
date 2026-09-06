"""本地 PTY 后端经过校验的配置。"""
from ...依赖.schemastery import 字符串字段,数字字段,列表字段#配置字段

安全整数上限=9007199254740991#外来JSON校验点：JS Number.MAX_SAFE_INTEGER

class 终端bash错误(Exception):#本包配置与搭建失败
    """本地 bash 终端配置或搭建非法。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

配置={#对外插件配置模式
    'backendType':字符串字段(默认值='shell'),#默认后端类型
    'shellPath':字符串字段(默认值='/bin/bash'),#默认shell路径
    'shellArgs':列表字段(字符串字段(),默认值=['--noprofile','--norc','-i']),#默认shell参数
    'rows':数字字段(默认值=40),#默认行数
    'cols':数字字段(默认值=160),#默认列数
    'scrollbackLines':数字字段(默认值=10000),#默认回滚行数
    'scrollbackMaxBytes':数字字段(默认值=4*1024*1024),#默认回滚字节
    'maxReadBytes':数字字段(默认值=256*1024),#默认单次读取字节
    'pollIntervalMs':数字字段(默认值=50),#默认轮询间隔
    'exactProbeAfterMs':数字字段(默认值=150),#默认精确探测延迟
    'idleSilenceMs':数字字段(默认值=3000),#默认空闲静默
    'handoffGraceMs':数字字段(默认值=500),#默认交接宽限
    'timeoutMs':数字字段(默认值=30000),#默认超时
    'disposeGraceMs':数字字段(默认值=3000),#默认拆除宽限
}#配置模式结束

数值字段=(#须为正安全整数的配置键
    'rows','cols','scrollbackLines','scrollbackMaxBytes','maxReadBytes',#尺寸与缓冲
    'pollIntervalMs','exactProbeAfterMs','idleSilenceMs','handoffGraceMs','timeoutMs','disposeGraceMs',#计时
)#数值字段结束

def 校验配置(配置值):#断言每个数值配置字段都是正的安全整数，且上下限能组合
    """断言每个数值配置字段都是正的安全整数，且上下限能组合；把输入收窄为已完全解析的配置。"""
    if len(配置值['backendType'])==0:#空后端类型
        raise 终端bash错误('terminal-bash: backendType must be non-empty')#拒绝空后端类型
    if len(配置值['shellPath'])==0:#空shell路径
        raise 终端bash错误('terminal-bash: shellPath must be non-empty')#拒绝空shell路径
    for 名称 in 数值字段:#逐数值字段
        值=配置值[名称]#字段值
        if isinstance(值,bool):#布尔不是数字
            raise 终端bash错误('terminal-bash: '+名称+' must be a positive safe integer')#拒绝非法数值
        if isinstance(值,int):#整数
            合法=值>0 and 值<=安全整数上限#正且安全
        elif isinstance(值,float) and 值.is_integer():#整值浮点
            合法=值>0 and 值<=安全整数上限#正且安全
        else:#其它类型
            合法=False#非法
        if not 合法:#非正安全整数
            raise 终端bash错误('terminal-bash: '+名称+' must be a positive safe integer')#拒绝非法数值
    if 配置值['maxReadBytes']>配置值['scrollbackMaxBytes']:#单次读取超过回滚上限
        raise 终端bash错误('terminal-bash: maxReadBytes must not exceed scrollbackMaxBytes')#拒绝越界读取上限
    if 配置值['handoffGraceMs']<配置值['pollIntervalMs']:#宽限短于一轮轮询
        raise 终端bash错误('terminal-bash: handoffGraceMs must be at least pollIntervalMs so one readiness poll runs inside the grace window')#拒绝过短交接宽限

__all__=['配置','校验配置','终端bash错误']#公开面
