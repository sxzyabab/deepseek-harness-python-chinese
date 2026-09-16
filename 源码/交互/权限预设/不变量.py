"""包内权限预设事件不变量。"""
import json#诊断里序列化未知预设名
from . import 自动预设#实验性 Auto 预设名
包名='@deepseek-ai/dsh-permission-presets'#本包名，用于登记所有权
名称='permission-presets-invariant'#配套插件名
注入=['invariants']#依赖不变量服务

def 校验事件(上下文对象,事件,失败):#校验单条预设事件
    """校验本包事件字段，忽略无关事件。事件是 dict。"""
    if 事件['type']=='permission/preset':#预设意图事件
        预设=事件['data']['preset']#所选预设名
        if 预设==自动预设:#Auto 由集成门把守
            return#放过
        名表=list(上下文对象.permissionPresets.名表)#当前公布表键
        if 预设 not in 名表:#点名未知预设
            失败('permission/preset names unknown preset '+json.dumps(预设,ensure_ascii=False,separators=(',',':'),allow_nan=False))#报告不可解析

def 安装(上下文对象,失败):#安装解析性校验
    """安装校验：已加载和新追加的预设事件必须仍可解析。"""
    for 会话 in 上下文对象.sessions.列出():#扫描已加载会话
        事件列表=会话.events if 会话.events is not None else []#历史事件
        for 事件 in 事件列表:#回放历史事件
            校验事件(上下文对象,事件,失败)#校验历史
    def 内部派发(_模式,事件名,参数,*位置参数):#拦截新追加
        """提交前检查 session/event。"""
        if 事件名!='session/event':#只关心会话事件
            return#放过
        事件=参数[1]#第二参是刚追加的事件
        校验事件(上下文对象,事件,失败)#校验新事件
    上下文对象.监听('internal/dispatch',内部派发,{'全局':True})#全局监听

安装.inject=['permissionPresets','sessions']#还依赖预设服务与会话

def 应用(上下文对象):#对外导出配套入口
    """登记权限不变量配套，返回安装成功后已登记项的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#向不变量服务登记安装器

__all__=['包名','名称','注入','安装','应用']#仅中文公开名
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
apply=应用#Cordis插件入口
default=应用#Cordis默认导出
