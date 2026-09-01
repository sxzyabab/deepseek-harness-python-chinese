"""配置域 Remote 拥有者：`settings` 与并列的 `credentials`。

对齐上游 `@deepseek-ai/dsh-api-settings-controller`。公开面仅中文名。
"""
import os#路径
from ...依赖 import schemastery#配置字段
布尔字段=schemastery.布尔字段#配置字段
from ...typert.协议 import 远程服务,远程 as _远程#Remote 基类
from .凭据 import 凭据控制器#凭据命名空间
from .工具 import 取字段,解开,远程错误,远程错误消息,信号已中止#辅助
from .辅助 import 命名空间视图,拒绝写入#投影与拒绝

__all__=['名称','注入','配置','设置控制器','应用','凭据控制器']#仅中文公开名

名称='settings-controller'#插件名
注入=[]#无类级额外注入

配置={#原生打开策略
    'nativeOpen':布尔字段(),#可覆盖桌面打开探测
}#配置结束

class 设置控制器(远程服务):#设置 Remote 服务
    """生成 ctx.remote.settings 命名空间。"""
    def __init__(自身,上下文,配置值=None,内部=None):#构造
        """登记 settings 命名空间并挂载凭据子插件。"""
        super().__init__(上下文,'settingsController',{'namespace':'settings'})#注册
        内部=内部 or {}#可替换集成
        自身._打开路径=取字段(内部,'openPath')#打开路径
        自身._打开文本=取字段(内部,'openTextFile')#打开文本
        自身._能否打开=取字段(内部,'canOpenPath')#探测
        if 自身._打开路径 is None:#缺省打开路径
            from ...工具.原生命令 import openNativePath as 打开原生路径#延迟导入
            自身._打开路径=打开原生路径#默认
        if 自身._打开文本 is None:#缺省打开文本
            from ...工具.原生命令 import openNativeTextFile as 打开文本文档#延迟导入
            自身._打开文本=打开文本文档#默认
        if 自身._能否打开 is None:#缺省探测
            def 缺省能否打开():#探测
                """配置覆盖或集成存在或平台支持。"""
                if 取字段(配置值,'nativeOpen') is not None:#显式配置
                    return bool(取字段(配置值,'nativeOpen'))#配置
                if 取字段(内部,'openPath') is not None:#测试注入
                    return True#可打开
                from ...工具.原生命令 import canOpenNativePath as 能否打开原生路径#延迟导入
                return bool(能否打开原生路径())#平台
            自身._能否打开=缺省能否打开#函数
        上下文.plugin(凭据控制器)#并列凭据命名空间

    @_远程
    def describe(自身):#描述全部命名空间
        """红化描述全部注册命名空间。"""
        设置=自身._提供方()#提供方
        return {#描述面
            'writable':取字段(设置,'writable'),#可写
            'hasDocument':取字段(设置,'documentPath') is not None,#有本地文档
            'namespaces':[命名空间视图(项) for 项 in 设置.describe({'redactSecrets':True})],#红化视图
        }#结束

    @_远程
    def canOpenAgentPresetDirectory(自身):#能否打开预设目录
        """报告能否原生打开智能体预设目录。"""
        return bool(自身._能否打开())#探测

    @_远程
    def update(自身,命名空间,补丁,期望修订=None):#合并写入
        """合并 user 段补丁。"""
        return 自身._写入(命名空间,'update',补丁,期望修订)#写

    @_远程
    def replace(自身,命名空间,整段,期望修订=None):#整段替换
        """整段替换 user 段。"""
        return 自身._写入(命名空间,'replace',整段,期望修订)#写

    @_远程
    def mutate(自身,命名空间,操作们,期望修订=None):#路径编辑
        """按路径编辑 user 段。"""
        return 自身._写入(命名空间,'mutate',操作们,期望修订)#写

    @_远程
    def openSettingsDocument(自身,信号):#打开设置文档
        """物化并原生打开设置文档。"""
        设置=自身._提供方()#提供方
        if 信号已中止(信号):#已取消
            raise 远程错误('gateway/cancelled','settings document open was aborted',{})#取消
        try:#准备文档
            路径=解开(设置.prepareDocument())#准备
        except Exception as 错误:#失败
            if 信号已中止(信号):#取消
                raise 远程错误('gateway/cancelled','settings document preparation was aborted',{},cause=错误)#取消
            raise 远程错误('gateway/internal','settings document preparation failed: '+远程错误消息(错误),{},cause=错误)#内部
        if 路径 is None:#无文档
            raise 远程错误('gateway/internal','settings provider has no local document to open',{})#拒绝
        if 信号已中止(信号):#取消
            raise 远程错误('gateway/cancelled','settings document open was aborted',{})#取消
        try:#打开
            解开(自身._打开文本(路径,信号))#打开
            return {'opened':True}#确认
        except Exception as 错误:#失败
            if 信号已中止(信号):#取消
                raise 远程错误('gateway/cancelled','settings document open was aborted',{},cause=错误)#取消
            raise 远程错误('gateway/internal','path open failed: '+远程错误消息(错误),{},cause=错误)#内部

    @_远程
    def openAgentPresetDirectory(自身,智能体预设,信号):#打开预设目录
        """打开用户预设目录或仅返回路径。"""
        if not 智能体预设:#空 id
            raise 远程错误('gateway/bad-request','agent preset id must not be empty',{})#拒绝
        预设们=自身.ctx.get('agentPresets')#可选预设服务
        if 预设们 is None:#未组合
            raise 远程错误('agent-preset/not-found','this deployment composes no agent presets',{'agentPreset':智能体预设,'available':[]})#拒绝
        预设=解开(预设们.resolve(智能体预设))#解析
        if 取字段(预设,'trust')!='user':#只读
            raise 远程错误('agent-preset/read-only','agent-presets: preset "'+str(取字段(预设,'id'))+'" cannot be written: it ships with the deployment',{'agentPreset':取字段(预设,'id'),'reason':'it ships with the deployment'})#拒绝
        目录=os.path.dirname(str(取字段(预设,'path')))#目录
        if not 自身._能否打开():#不能原生打开
            return {'opened':False,'path':目录}#仅返回路径
        try:#打开
            解开(自身._打开路径(目录,信号))#打开
            return {'opened':True}#确认
        except Exception as 错误:#失败
            if 信号已中止(信号):#取消
                raise 远程错误('gateway/cancelled','path open was aborted',{},cause=错误)#取消
            raise 远程错误('gateway/internal','path open failed: '+远程错误消息(错误),{},cause=错误)#内部

    def _写入(自身,命名空间,模式,输入,期望修订):#统一写入
        """执行 update/replace/mutate 并返回红化视图。"""
        if not isinstance(命名空间,str) or 命名空间=='':#非法 ns
            raise 远程错误('gateway/bad-request','invalid payload for settings.'+模式,{'issues':[{'message':'ns invalid'}]})#拒绝
        设置=自身._提供方()#提供方
        try:#写
            if 模式=='update':#合并
                解开(设置.update(命名空间,输入,期望修订))#update
            elif 模式=='replace':#替换
                解开(设置.replace(命名空间,输入,期望修订))#replace
            else:#路径
                解开(设置.mutate(命名空间,输入,期望修订))#mutate
        except Exception as 错误:#拒绝
            raise 拒绝写入(命名空间,错误)#分类
        描述符=None#写后读
        for 候选 in 设置.describe({'redactSecrets':True}):#扫描
            if 取字段(候选,'ns')==命名空间:#命中
                描述符=候选#记下
                break#结束
        if 描述符 is None:#写后消失
            raise 远程错误('gateway/internal','settings namespace "'+命名空间+'" was disposed after the '+模式,{})#内部
        return 命名空间视图(描述符)#红化视图

    def _提供方(自身):#解析 settings 提供方
        """取 settings 提供方或报告如何挂载。"""
        设置=自身.ctx.get('settings')#可选
        if 设置 is None:#缺席
            raise 远程错误('gateway/internal','settings service is absent: this deployment does not mount a settings provider (e.g. @deepseek-ai/dsh-settings-file) in its composition',{})#拒绝
        return 设置#提供方

def 应用(上下文,配置值=None):#安装设置控制器
    """挂载 settings 与 credentials Remote 拥有者。"""
    设置控制器(上下文,配置值)#构造即登记
