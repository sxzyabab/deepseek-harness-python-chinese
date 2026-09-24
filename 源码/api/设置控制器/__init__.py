"""配置域远程拥有者：settings 与并列的 credentials。"""
from ...typert.协议 import 远程服务,远程 as _远程
from .凭据 import 凭据控制器
from .远程错误与中止 import 远程错误,远程错误消息,已中止
from .投影与写入 import 命名空间视图,拒绝写入
from .类型 import 设置文档打开值

__all__=['包名','名称','依赖','应用','默认','设置控制器','凭据控制器','设置文档打开值']

包名='@deepseek-ai/dsh-api-settings-controller'
名称='settings-controller'
依赖=[]

class 设置控制器(远程服务):
    """生成 remote.settings 命名空间。"""
    def __init__(自身,上下文,内部=None):
        """登记 settings 命名空间并挂载凭据子插件。"""
        super().__init__(上下文,'settingsController',{'namespace':'settings'})
        if 内部 is None:
            内部={}
        自身._打开文本=内部['openTextFile'] if 'openTextFile' in 内部 else None
        if 自身._打开文本 is None:
            from ...工具.原生命令 import openNativeTextFile as 打开文本文档
            自身._打开文本=打开文本文档
        上下文.启动插件(凭据控制器)

    @_远程
    def describe(自身):
        """红化描述全部注册命名空间。"""
        设置=自身._提供方()
        return {
            'writable':设置.writable,
            'hasDocument':True,
            'namespaces':[命名空间视图(项) for 项 in 设置.describe({'redactSecrets':True})],
        }

    @_远程
    def update(自身,命名空间,补丁,期望修订=None):
        """合并 user 段补丁。"""
        return 自身._写入(命名空间,'update',补丁,期望修订)

    @_远程
    def replace(自身,命名空间,整段,期望修订=None):
        """整段替换 user 段。"""
        return 自身._写入(命名空间,'replace',整段,期望修订)

    @_远程
    def mutate(自身,命名空间,操作列表,期望修订=None):
        """按路径编辑 user 段。"""
        return 自身._写入(命名空间,'mutate',操作列表,期望修订)

    @_远程
    def openSettingsDocument(自身,信号):
        """物化并原生打开设置文档。"""
        设置=自身._提供方()
        if 已中止(信号):
            raise 远程错误('gateway/cancelled','settings document open was aborted',{})
        try:
            路径=设置.prepareDocument()
        except BaseException as 错误:
            if 已中止(信号):
                raise 远程错误('gateway/cancelled','settings document preparation was aborted',{},原因=错误)
            raise 远程错误('gateway/internal','settings document preparation failed: '+远程错误消息(错误),{},原因=错误)
        if 已中止(信号):
            raise 远程错误('gateway/cancelled','settings document open was aborted',{})
        try:
            自身._打开文本(路径,信号)
            return {'opened':True}
        except BaseException as 错误:
            if 已中止(信号):
                raise 远程错误('gateway/cancelled','settings document open was aborted',{},原因=错误)
            raise 远程错误('gateway/internal','path open failed: '+远程错误消息(错误),{},原因=错误)

    def _写入(自身,命名空间,模式,输入,期望修订):
        """执行 update/replace/mutate 并返回红化视图。"""
        if not isinstance(命名空间,str) or 命名空间=='':
            raise 远程错误('gateway/bad-request','invalid payload for settings.'+模式,{'issues':[{'message':'ns invalid'}]})
        设置=自身._提供方()
        try:
            if 模式=='update':
                设置.update(命名空间,输入,期望修订)
            elif 模式=='replace':
                设置.replace(命名空间,输入,期望修订)
            else:
                设置.mutate(命名空间,输入,期望修订)
        except BaseException as 错误:
            raise 拒绝写入(命名空间,错误)
        描述符=None
        for 候选 in 设置.describe({'redactSecrets':True}):
            if 候选['ns']==命名空间:
                描述符=候选
                break
        if 描述符 is None:
            raise 远程错误('gateway/internal','settings namespace "'+命名空间+'" was disposed after the '+模式,{})
        return 命名空间视图(描述符)

    def _提供方(自身):
        """取 settings 提供方或报告如何挂载。"""
        设置=自身.ctx.获取服务('settings')
        if 设置 is None:
            raise 远程错误('gateway/internal','settings service is absent: mount @deepseek-ai/dsh-settings with @deepseek-ai/dsh-config-editor in the profile composition',{})
        return 设置

def 应用(上下文,配置值=None):
    """挂载 settings 与 credentials Remote 拥有者。"""
    设置控制器(上下文)

默认=应用
name=名称
inject=依赖
apply=应用
default=默认
