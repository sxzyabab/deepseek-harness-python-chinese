"""`@deepseek-ai/dsh-settings` 的本包拥有不变量配套。"""
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现的拆除器
from . import json深度相等#导入接缝自身的相等判断

包名='@deepseek-ai/dsh-settings'#本包的不变量所有权名
名称='settings-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

def 安装(上下文对象,失败):#安装提交事件检查
    """安装提交事件约定：settings/updated 只对当前已注册命名空间发出，只在解析值变化时发出，且载荷必须是服务的权威解析值——一律用接缝自身的相等判断判定。"""
    def 监听更新(命名空间,下一值,上一值,*其余):#监听设置更新事件
        """监听已提交的设置解析值变更。"""
        设置=上下文对象.get('settings')#取当前设置服务
        if 设置 is None:#没有活的设置服务
            失败('settings/updated for "'+str(命名空间)+'" emitted without a live settings service')#缺少服务则失败
        当前=设置.get(命名空间)#取该命名空间的权威解析值
        if 当前 is None:#命名空间未注册
            失败('settings/updated for "'+str(命名空间)+'" emitted while the namespace is unregistered')#未注册则失败
        if not json深度相等(当前,下一值):#载荷与权威值不一致
            失败('settings/updated for "'+str(命名空间)+'" does not match the authoritative resolved value')#值不匹配则失败
        if json深度相等(下一值,上一值):#新旧解析值相等
            失败('settings/updated for "'+str(命名空间)+'" emitted without a resolved-value change')#无变化却发出则失败
    上下文对象.on('settings/updated',监听更新)#更新监听结束

def 应用(上下文对象):#对外导出配套入口
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#向不变量服务登记安装器

apply=应用#Cordis插件入口
