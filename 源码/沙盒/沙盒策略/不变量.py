"""沙箱政策的本包拥有会话事件不变量。"""
import json#诊断里序列化未知模式
from ...依赖 import cordis#外部依赖胶水
from .会话模式 import 沙盒模式表#导入合法沙箱模式表

包名='@deepseek-ai/dsh-sandbox-policy'#本包的不变量所有权名
名称='sandbox-policy-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants 服务
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 校验事件(事件,失败):#校验一条会话事件
    """校验本包拥有的事件字段，忽略无关事件。"""
    if 取字段(事件,'type')=='sandbox/mode' and 取字段(取字段(事件,'data'),'mode') not in 沙盒模式表:#模式不在合法表里
        失败('sandbox/mode carries unknown mode '+json.dumps(取字段(取字段(事件,'data'),'mode'),ensure_ascii=False))#未知模式则失败

def 安装(上下文对象,失败):#安装已加载与新追加校验
    """给已加载与新追加的沙箱模式安装校验。"""
    for 会话 in 上下文对象.sessions.list():#已有会话
        for 事件 in 取字段(会话,'events') or []:#逐事件校验
            校验事件(事件,失败)#校验本包事件
    def 内部派发(_模式,事件名,参数,*其余):#新追加事件
        """提交前检查 session/event。"""
        if 事件名!='session/event':#只看会话事件
            return#放过
        事件=参数[1]#取出事件
        校验事件(事件,失败)#校验本包事件
    上下文对象.on('internal/dispatch',内部派发,{'global':True})#全局监听分派

安装.inject=['sessions']#还依赖 sessions

def 应用(上下文对象):#注册本包的不变量配套
    """注册本包的不变量配套，返回安装成功后已安装注册的 disposer。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#注册本包不变量并包成已决议承诺

apply=应用#Cordis 插件入口
