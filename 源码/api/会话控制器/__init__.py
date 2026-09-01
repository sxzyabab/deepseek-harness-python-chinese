"""Session Remote 宿主拥有者入口。

对齐上游 `@deepseek-ai/dsh-api-session-controller`。公开面仅中文名。

智能体激活、命令、控制流与历史分页分别见子模块；客户端半边在 `客户端/运行时`。
"""
import os#进程 cwd
from ...依赖 import schemastery#配置字段
数字字段=schemastery.数字字段#配置字段
布尔字段=schemastery.布尔字段#配置字段
from ...typert.协议 import 远程服务,远程 as _远程#Remote 基类
from .常量 import 默认冷空白探测最大字节#默认策略
from .目录 import 构建模型目录#模型目录
from .模型选择投影 import 安装模型选择投影#投影
from .文件引用 import 会话文件引用#文件引用
from .技能目录 import 会话技能目录#技能目录
from .工具 import 取字段,解开,远程错误,信号已中止#辅助

__all__=['名称','注入','配置','会话控制器','应用','构建模型目录','会话文件引用','会话技能目录']#仅中文公开名

名称='session-controller'#插件名
注入=[#依赖
    'agentDefaultModel','agents','attachments','llm','sessions',
    'sessionProjections','sessionQuery','typert','workspaceRegistry',
]#结束

配置={#部署策略
    'coldBlankProbeMaxBytes':数字字段(默认值=默认冷空白探测最大字节),#冷探测上限
    'nativeOpen':布尔字段(),#原生打开覆盖
}#配置结束

class 会话控制器(远程服务):#Session Remote 服务
    """生成 ctx.remote.session 命名空间。"""
    注入=注入#类级注入
    配置=配置#Cordis 配置

    def __init__(自身,上下文,配置值=None,内部=None):#构造
        """组装智能体、命令、控制与历史子控制器。"""
        super().__init__(上下文,'sessionController',{'namespace':'session'})#注册
        配置值=配置值 or {}#缺省
        内部=内部 or {}#可替换集成
        安装模型选择投影(上下文)#模型选择投影
        from .智能体 import 会话智能体控制器#延迟导入
        from .命令 import 会话命令控制器#延迟导入
        from .控制 import 会话控制控制器#延迟导入
        from .历史 import 会话历史控制器#延迟导入
        from .列表 import 会话列表#延迟导入
        自身._智能体们=会话智能体控制器(上下文)#智能体
        自身._命令=会话命令控制器(上下文,自身._智能体们,os.getcwd())#命令
        自身._控制=会话控制控制器(上下文)#控制
        自身._历史=会话历史控制器(上下文,lambda 观测:自身._晋升(观测))#历史
        自身._列表=会话列表(上下文,取字段(配置值,'coldBlankProbeMaxBytes') or 默认冷空白探测最大字节)#列表
        自身._打开路径=取字段(内部,'openPath')#打开路径
        自身._能否打开=取字段(内部,'canOpenPath')#能否打开
        if 自身._打开路径 is None:#缺省
            from ...工具.原生命令 import openNativePath as 打开原生路径#导入
            自身._打开路径=打开原生路径#默认
        if 自身._能否打开 is None:#缺省探测
            def 探测():#探测函数
                """配置或集成或平台。"""
                if 取字段(配置值,'nativeOpen') is not None:#显式
                    return bool(取字段(配置值,'nativeOpen'))#配置
                if 取字段(内部,'openPath') is not None:#注入
                    return True#有
                from ...工具.原生命令 import canOpenNativePath as 能否打开原生路径#导入
                return bool(能否打开原生路径())#平台
            自身._能否打开=探测#函数
        自身._晋升们=set()#后台晋升任务
        上下文.plugin(会话文件引用)#子插件
        上下文.plugin(会话技能目录)#子插件
        上下文.on('session/created',lambda 会话:上下文.emit('api-session/added',自身._列表.摘要(会话)))#创建
        上下文.on('session/disposed',lambda 会话:上下文.emit('api-session/removed',取字段(会话,'id')))#销毁
        上下文.on('agent/status',lambda 载荷:上下文.emit('api-session/status',取字段(载荷,'agent').id,取字段(载荷,'status')=='running'))#状态
        上下文.on('agent/error',lambda 载荷:上下文.emit('api-session/error',取字段(载荷,'agent').id,str(取字段(载荷,'error'))))#错误
        def 会话事件(会话,事件):#会话事件
            """消费选择与活动。"""
            if 取字段(事件,'type')=='request/header':#请求头
                智能体=上下文.agents.get(取字段(会话,'id'))#智能体
                if 智能体 is not None and 取字段(智能体,'session') is 会话:#匹配
                    头=取字段(取字段(事件,'data'),'header')#头
                    配置=取字段(头,'config')#配置
                    自身._智能体们.消费选择(智能体,取字段(配置,'provider'),取字段(配置,'model'),取字段(配置,'reasoningEffort'))#消费
            if 取字段(事件,'type')=='user/message' and 取字段(取字段(取字段(事件,'data'),'source'),'kind')=='user':#用户消息
                上下文.emit('api-session/activity',取字段(会话,'id'),取字段(事件,'time'))#活动
        上下文.on('session/event',会话事件)#订阅
        上下文.effect(lambda:自身._等待晋升(),'session-controller.promotions')#晋升拆除

    def _等待晋升(自身):#等待全部晋升
        """拆除时等待后台晋升。"""
        for 任务 in list(自身._晋升们):#逐个
            try:#等待
                解开(任务)#等待
            except Exception:#忽略
                pass#继续

    def _晋升(自身,观测):#后台激活
        """快照交付后晋升普通会话。"""
        def 跑():#任务体
            """解析并激活观测到的会话。"""
            try:#解析
                结果=解开(自身._智能体们.解析观测智能体(观测))#解析
                if isinstance(结果,dict) and 'error' in 结果:#失败
                    自身.ctx.emit('api-session/error',取字段(取字段(观测,'header'),'id'),取字段(取字段(结果,'error'),'message'))#报错
            except Exception as 错误:#意外
                自身.ctx.logger.error('session-controller: background activation failed: '+str(错误))#日志
        任务=跑()#启动（同步）
        自身._晋升们.add(任务)#登记
        try:#清理
            自身._晋升们.discard(任务)#移除
        except Exception:#忽略
            pass#继续

    def resolveAgent(自身,会话标识):#解析智能体
        """为其它域解析或恢复普通会话。"""
        return 自身._智能体们.解析智能体(会话标识)#委托

    def inspect(自身,会话标识,信号=None):#检视
        """不激活智能体地检视会话。"""
        附着=自身.ctx.sessions.get(会话标识)#附着
        if 附着 is not None:#附着
            return {'meta':附着.header,'events':list(附着.events)}#即时
        from .智能体 import 检视会话#检视
        return 检视会话(自身.ctx,会话标识,信号)#冷读

    @_远程('list')
    def list(自身,_请求,信号):#列会话
        """冷安全列出可见会话。"""
        return {'items':解开(自身._列表.列表(信号))}#列表

    @_远程('search')
    def search(自身,请求,信号):#搜索
        """搜索消息内容。"""
        return 自身._列表.搜索(取字段(请求,'query'),信号)#搜索

    @_远程('create')
    def create(自身,请求):#创建
        """创建或幂等采用会话。"""
        return 自身._命令.create(请求)#委托

    @_远程('selectModel')
    def selectModel(自身,请求):#选模型
        """显式恢复后选择会话本地模型。"""
        return 自身._命令.selectModel(请求)#委托

    @_远程
    def modelCatalog(自身):#模型目录
        """描述当前可路由模型。"""
        return 构建模型目录(自身.ctx)#目录

    @_远程
    def canOpenWorkspacePath(自身):#能否打开路径
        """报告能否原生打开工作区路径。"""
        return bool(自身._能否打开())#探测

    @_远程('openWorkspacePath')
    def openWorkspacePath(自身,请求,信号):#打开路径
        """原生打开工作区路径。"""
        路径=取字段(请求,'path') or ''#路径
        if 路径=='':#空
            raise 远程错误('gateway/bad-request','session.openWorkspacePath requires a non-empty path',{})#拒绝
        if 信号已中止(信号):#取消
            raise 远程错误('gateway/cancelled','path open was aborted',{})#取消
        try:#打开
            解开(自身._打开路径(路径,信号))#打开
            return {'opened':True}#确认
        except Exception as 错误:#失败
            if 信号已中止(信号):#取消
                raise 远程错误('gateway/cancelled','path open was aborted',{},cause=错误)#取消
            raise 远程错误('gateway/internal','path open failed: '+str(错误),{},cause=错误)#内部

    @_远程('rename')
    def rename(自身,请求):#重命名
        """重命名会话。"""
        return 自身._命令.rename(请求)#委托

    @_远程('fork')
    def fork(自身,请求):#分叉
        """分叉已完成回合前缀。"""
        return 自身._命令.fork(请求)#委托

    @_远程('prompt')
    def prompt(自身,请求,信号):#投入提示
        """显式恢复后投入提示。"""
        if 信号已中止(信号):#取消
            raise 远程错误('gateway/cancelled','prompt was aborted',{})#取消
        return 自身._命令.prompt(请求)#委托

    @_远程('attachment')
    def attachment(自身,请求):#读附件
        """读取会话日志引用的图像。"""
        return 自身._命令.attachment(请求)#委托

    @_远程('updateQueue')
    def updateQueue(自身,请求):#改队列
        """变更待处理队列项。"""
        return 自身._命令.updateQueue(请求)#委托

    @_远程('cancel')
    def cancel(自身,请求):#取消
        """取消活动回合。"""
        return 自身._命令.cancel(请求)#委托

    @_远程('page')
    def page(自身,请求,信号):#历史页
        """读冷安全历史页。"""
        return 自身._历史.page(请求,信号)#委托

    @_远程('follow')
    def follow(自身,请求,信号):#跟随日志
        """跟随会话事件流。"""
        yield from 自身._历史.follow(请求,信号)#流

    @_远程('control')
    def control(自身,信号):#控制流
        """流式会话控制基线与增量。"""
        yield from 自身._控制.control(信号)#流

def 应用(上下文,配置值=None):#安装会话控制器
    """挂载 Session Remote 拥有者。"""
    会话控制器(上下文,配置值)#构造即登记
