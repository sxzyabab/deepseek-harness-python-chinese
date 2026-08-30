"""本包拥有的严格日程流不变量。"""
from ...依赖 import cordis#外部依赖胶水
from .领域 import 折叠日程事件,日程日志错误#折叠校验与日志错误

包名='@deepseek-ai/dsh-schedule'#本包的不变量所有权名
名称='tool-schedule-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 校验(事件们,种子长度,失败):#在其 fork 后缀策略下校验一条完整精确会话流
    """在其 fork 后缀策略下校验一条完整精确会话流。"""
    try:#折叠完整流
        折叠日程事件(事件们,种子长度)#按 seedLength 折叠
    except 日程日志错误 as 错误:#折叠拒绝
        失败(str(错误))#报告畸形流
    except Exception as 错误:#非日程日志错误
        raise 错误#原样抛出

def 安装(上下文对象,失败):#为已拥有事件流安装回放与追加前校验
    """为已拥有事件流安装回放与追加前校验。"""
    for 会话对象 in 上下文对象.sessions.list():#回放已有会话
        头=取字段(会话对象,'header')#会话头
        种子=取字段(头,'seedLength',0) or 0#fork 后缀
        校验(取字段(会话对象,'events'),种子,失败)#按 fork 后缀校验
    def 会话已创建(会话对象,*其余):#新会话创建
        """新会话创建时校验初始流。"""
        头=取字段(会话对象,'header')#会话头
        种子=取字段(头,'seedLength',0) or 0#fork 后缀
        校验(取字段(会话对象,'events'),种子,失败)#校验初始流
    上下文对象.on('session/created',会话已创建,{'global':True})#全局监听创建
    def 内部派发(_模式,事件名,参数,*其余):#监听新派发
        """提交前检查 session/event。"""
        if 事件名!='session/event':#只关心会话事件
            return#放过
        会话=参数[0]#第一参是会话
        事件=参数[1]#第二参是事件
        if 取字段(事件,'type')!='schedule/change':#只校验日程变更
            return#放过
        头=取字段(会话,'header')#会话头
        种子=取字段(头,'seedLength',0) or 0#fork 后缀
        候选=list(取字段(会话,'events'))+[事件]#候选追加后的完整流
        校验(候选,种子,失败)#校验
    上下文对象.on('internal/dispatch',内部派发,{'global':True})#全局监听派发

安装.inject=['sessions']#安装器还依赖 sessions

def 应用(上下文对象):#注册本包拥有的不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺

apply=应用#Cordis插件入口
