"""包内权限预设事件不变量。"""
import json#诊断里序列化未知预设名
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现的拆除器

包名='@deepseek-ai/dsh-permission-presets'#本包名，用于登记所有权
名称='permission-presets-invariant'#配套插件名
注入=['invariants']#依赖不变量服务
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 校验事件(上下文对象,事件,失败):#校验单条预设事件
    """校验本包事件字段，忽略无关事件。"""
    if 取字段(事件,'type')=='permission/preset':#预设意图事件
        预设=取字段(取字段(事件,'data'),'preset')#所选预设名
        名表=list(上下文对象.permissionPresets.names)#当前公布表键
        if 预设 not in 名表:#点名未知预设
            失败('permission/preset names unknown preset '+json.dumps(预设,ensure_ascii=False))#报告不可解析

def 安装(上下文对象,失败):#安装解析性校验
    """安装校验：已加载和新追加的预设事件必须仍可解析。"""
    for 会话 in 上下文对象.sessions.list():#扫描已加载会话
        for 事件 in 取字段(会话,'events') or []:#回放历史事件
            校验事件(上下文对象,事件,失败)#校验历史
    def 内部派发(_模式,事件名,参数,*其余):#拦截新追加
        """提交前检查 session/event。"""
        if 事件名!='session/event':#只关心会话事件
            return#放过
        事件=参数[1]#第二参是刚追加的事件
        校验事件(上下文对象,事件,失败)#校验新事件
    上下文对象.on('internal/dispatch',内部派发,{'global':True})#全局监听

安装.inject=['permissionPresets','sessions']#还依赖预设服务与会话

def 应用(上下文对象):#对外导出配套入口
    """登记权限不变量配套，返回安装成功后已登记项的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#向不变量服务登记安装器

apply=应用#Cordis 插件入口
