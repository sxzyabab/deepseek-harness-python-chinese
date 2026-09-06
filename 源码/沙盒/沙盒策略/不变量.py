"""沙箱政策的本包拥有会话事件不变量。"""
import json#诊断里序列化未知模式
from .会话模式 import 沙盒模式表#导入合法沙箱模式表

包名='@deepseek-ai/dsh-sandbox-policy'#本包的不变量所有权名
名称='sandbox-policy-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants 服务

def 校验事件(事件,失败):
    """校验本包拥有的事件字段，忽略无关事件。事件是 dict。"""
    if 事件['type']!='sandbox/mode':#非本包事件
        return#忽略
    模式=事件['data']['mode']#载荷模式
    if 模式 not in 沙盒模式表:#模式不在合法表里
        失败('sandbox/mode carries unknown mode '+json.dumps(模式,ensure_ascii=False,separators=(',',':'),allow_nan=False))#未知模式则失败

def 安装(上下文对象,失败):
    """给已加载与新追加的沙箱模式安装校验。"""
    for 会话 in 上下文对象.sessions.列出():#已有会话
        for 事件 in 会话.events:#逐事件校验
            校验事件(事件,失败)#校验本包事件
    def 内部派发(_模式,事件名,参数,*位置参数):
        """提交前检查 session/event。"""
        if 事件名!='session/event':#只看会话事件
            return#放过
        事件=参数[1]#取出事件
        校验事件(事件,失败)#校验本包事件
    上下文对象.监听('internal/dispatch',内部派发,{'全局':True})#全局监听分派

安装.inject=['sessions']#还依赖 sessions

def 应用(上下文对象):
    """注册本包的不变量配套，返回安装成功后已安装注册的 disposer。"""
    return 上下文对象.invariants.register(包名,安装)#登记

__all__=['包名','名称','注入','安装','应用']#仅中文公开名
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明
apply=应用#Cordis 插件入口
default=应用#Cordis 默认导出
