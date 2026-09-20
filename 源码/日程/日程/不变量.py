"""本包拥有的严格日程流不变量。"""
from .领域 import 折叠日程事件,日程日志错误#折叠校验与日志错误

包名='@deepseek-ai/dsh-schedule'#本包的不变量所有权名
名称='schedule-invariant'#配套不变量插件名
依赖=['invariants']#依赖invariants服务

def 校验(事件列表,失败):
    """在其 fork 后缀策略下校验一条自有事件流（ownEvents 已切掉继承前缀）。"""
    try:#折叠完整流
        折叠日程事件(事件列表)#自有后缀
    except 日程日志错误 as 错误:#折叠拒绝
        失败(str(错误))#报告畸形流

def 安装(上下文,失败):
    """为已拥有事件流安装回放与追加前校验。会话是对象，header 是 dict，events 是事件 dict 元组。"""
    for 会话 in 上下文.sessions.列出():#回放已有会话
        校验(会话.ownEvents(),失败)#按自有后缀校验
    def 会话已创建(会话,*其余):
        """新会话创建时校验初始流。"""
        校验(会话.ownEvents(),失败)#校验初始流
    上下文.监听('session/created',会话已创建,{'全局':True})#全局监听创建
    def 内部派发(_模式,事件名,参数,*其余):
        """提交前检查 session/event。"""
        if 事件名!='session/event':#只关心会话事件
            return#放过
        会话=参数[0]#第一参是会话
        事件=参数[1]#第二参是事件
        if 事件['type']!='schedule/change':#只校验日程变更
            return#放过
        校验([*会话.ownEvents(),事件],失败)#候选追加后的完整自有流
    上下文.监听('internal/dispatch',内部派发,{'全局':True})#全局监听派发

安装.inject=['sessions']#安装器还依赖 sessions

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)#登记

__all__=['包名','名称','依赖','安装','应用']#仅中文公开名
name=名称#Cordis 插件名
inject=依赖#Cordis 依赖声明
apply=应用#Cordis 插件入口
default=应用#Cordis 默认导出
