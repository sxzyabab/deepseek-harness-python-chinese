"""Session Remote 宿主拥有者入口。

对齐上游 `@deepseek-ai/dsh-api-session-controller`。公开面仅中文名。

智能体激活、命令、控制流与历史分页分别见子模块；客户端半边在 `客户端/运行时`。
"""
import os#进程 cwd
from ...依赖.schemastery import 数字字段,布尔字段#配置字段
from ...typert.协议 import 远程服务,远程 as _远程#Remote 基类
from .常量 import 默认冷空白探测最大字节#默认策略
from .目录 import 构建模型目录#模型目录
from .模型选择投影 import 安装模型选择投影#投影
from .文件引用 import 会话文件引用#文件引用
from .技能目录 import 会话技能目录#技能目录
from .远程错误与并发 import 远程错误,已中止,在线程执行#远程错误与并发

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

class 会话控制器(远程服务):
    """生成 ctx.remote.session 命名空间。"""
    inject=注入#框架槽：类级注入
    Config=配置#框架槽：Cordis 配置

    def __init__(自身,上下文,配置值=None,内部=None):
        """组装智能体、命令、控制与历史子控制器。配置值与内部为 dict。"""
        super().__init__(上下文,'sessionController',{'namespace':'session'})#注册
        if 配置值 is None:#缺省
            配置值={}#空
        if 内部 is None:#可替换集成
            内部={}#空
        安装模型选择投影(上下文)#模型选择投影
        from .智能体 import 会话智能体控制器#延迟导入
        from .命令 import 会话命令控制器#延迟导入
        from .控制 import 会话控制控制器#延迟导入
        from .历史 import 会话历史控制器#延迟导入
        from .列表 import 会话列表#延迟导入
        自身._智能体控制器=会话智能体控制器(上下文)#智能体
        自身._命令=会话命令控制器(上下文,自身._智能体控制器,os.getcwd())#命令
        自身._控制=会话控制控制器(上下文)#控制
        自身._历史=会话历史控制器(上下文,自身._晋升)#历史
        探测上限=配置值['coldBlankProbeMaxBytes'] if 'coldBlankProbeMaxBytes' in 配置值 and 配置值['coldBlankProbeMaxBytes'] is not None else 默认冷空白探测最大字节#列表
        自身._列表=会话列表(上下文,探测上限)#列表
        自身._打开路径=内部['openPath'] if 'openPath' in 内部 else None#打开路径
        自身._能否打开=内部['canOpenPath'] if 'canOpenPath' in 内部 else None#能否打开
        if 自身._打开路径 is None:#缺省
            from ...工具.原生命令 import openNativePath as 打开原生路径#导入
            自身._打开路径=打开原生路径#默认
        if 自身._能否打开 is None:#缺省探测
            def 探测():
                """配置或集成或平台。"""
                if 'nativeOpen' in 配置值:#显式
                    return bool(配置值['nativeOpen'])#配置
                if 'openPath' in 内部:#注入
                    return True#有
                from ...工具.原生命令 import canOpenNativePath as 能否打开原生路径#导入
                return bool(能否打开原生路径())#平台
            自身._能否打开=探测#函数
        自身._晋升任务集合=set()#后台晋升任务
        上下文.启动插件(会话文件引用)#子插件
        上下文.启动插件(会话技能目录)#子插件
        def 会话创建(会话):
            """创建。"""
            上下文.广播('api-session/added',自身._列表.摘要(会话))#创建
        def 会话销毁(会话):
            """销毁。"""
            上下文.广播('api-session/removed',会话.id)#销毁
        def 智能体状态(载荷):
            """状态。载荷为 dict。"""
            上下文.广播('api-session/status',载荷['agent'].id,载荷['status']=='running')#状态
        def 智能体错误(载荷):
            """错误。载荷为 dict。"""
            上下文.广播('api-session/error',载荷['agent'].id,str(载荷['error']))#错误
        def 会话事件(会话,事件):
            """消费选择与活动。事件为 dict。"""
            if 事件['type']=='request/header':#请求头
                智能体=上下文.agents.get(会话.id)#智能体
                if 智能体 is not None and 智能体.session is 会话:#匹配
                    头=事件['data']['header']#头
                    配置块=头['config']#配置
                    力度=配置块['reasoningEffort'] if 'reasoningEffort' in 配置块 else None#推理
                    自身._智能体控制器.消费选择(智能体,配置块['provider'],配置块['model'],力度)#消费
            源=None#来源
            if 'data' in 事件 and isinstance(事件['data'],dict) and 'source' in 事件['data']:#有来源
                源=事件['data']['source']#来源
            种类=源['kind'] if isinstance(源,dict) and 'kind' in 源 else None#kind
            if 事件['type']=='user/message' and 种类=='user':#用户消息
                上下文.广播('api-session/activity',会话.id,事件['time'])#活动
        def 等待晋升():
            """晋升拆除。"""
            自身._等待晋升()#委托
        上下文.监听('session/created',会话创建)#创建
        上下文.监听('session/disposed',会话销毁)#销毁
        上下文.监听('agent/status',智能体状态)#状态
        上下文.监听('agent/error',智能体错误)#错误
        上下文.监听('session/event',会话事件)#订阅
        上下文.副作用(等待晋升,'session-controller.promotions')#晋升拆除

    def _等待晋升(自身):
        """拆除时等待后台晋升。"""
        for 任务 in list(自身._晋升任务集合):#逐个
            try:
                任务.等待()#等待
            except BaseException:
                pass#继续

    def _晋升(自身,观测):
        """快照交付后晋升普通会话。"""
        def 执行晋升():
            """解析并激活观测到的会话。"""
            try:
                结果=自身._智能体控制器.解析观测智能体(观测)#解析
                if isinstance(结果,dict) and 'error' in 结果:#失败
                    信封=结果['error']#错误
                    消息=信封.message if hasattr(信封,'message') else (信封['message'] if isinstance(信封,dict) and 'message' in 信封 else str(信封))#消息
                    自身.ctx.广播('api-session/error',观测.header['id'],消息)#报错
            except BaseException as 错误:
                自身.ctx.日志.错误('session-controller: background activation failed: '+str(错误))#日志
        任务=在线程执行(执行晋升)#后台
        自身._晋升任务集合.add(任务)#登记
        def 收尾():
            """任务落后定后从表移除。"""
            try:
                任务.等待()#等待
            except BaseException:
                pass#忽略
            自身._晋升任务集合.discard(任务)#移除
        收=在线程执行(收尾)#收尾线程
        自身._晋升任务集合.add(收)#登记收尾以免拆除时漏等

    def resolveAgent(自身,会话标识):
        """为其它域解析或恢复普通会话。"""
        return 自身._智能体控制器.解析智能体(会话标识)#委托

    def inspect(自身,会话标识,信号=None):
        """不激活智能体地检视会话。"""
        附着=自身.ctx.sessions.get(会话标识)#附着
        if 附着 is not None:#附着
            return {'meta':附着.header,'events':list(附着.events)}#即时
        from .智能体 import 检视会话#检视
        return 检视会话(自身.ctx,会话标识,信号)#冷读

    @_远程('list')
    def list(自身,_请求,信号):
        """冷安全列出可见会话。"""
        return {'items':自身._列表.列表(信号)}#列表

    @_远程('search')
    def search(自身,请求,信号):
        """搜索消息内容。请求为 dict。"""
        return 自身._列表.搜索(请求['query'],信号)#搜索

    @_远程('create')
    def create(自身,请求):
        """创建或幂等采用会话。"""
        return 自身._命令.create(请求)#委托

    @_远程('selectModel')
    def selectModel(自身,请求):
        """显式恢复后选择会话本地模型。"""
        return 自身._命令.selectModel(请求)#委托

    @_远程
    def modelCatalog(自身):
        """描述当前可路由模型。"""
        return 构建模型目录(自身.ctx)#目录

    @_远程
    def canOpenWorkspacePath(自身):
        """报告能否原生打开工作区路径。"""
        return bool(自身._能否打开())#探测

    @_远程('openWorkspacePath')
    def openWorkspacePath(自身,请求,信号):
        """原生打开工作区路径。请求为 dict。"""
        路径=请求['path'] if 'path' in 请求 and 请求['path'] is not None else ''#路径，|| 空串
        if 路径=='':#空
            raise 远程错误('gateway/bad-request','session.openWorkspacePath requires a non-empty path',{})#拒绝
        if 已中止(信号):#取消
            raise 远程错误('gateway/cancelled','path open was aborted',{})#取消
        try:
            自身._打开路径(路径,信号)#打开
            return {'opened':True}#确认
        except (OSError,ValueError,TypeError) as 错误:
            if 已中止(信号):#取消
                raise 远程错误('gateway/cancelled','path open was aborted',{},原因=错误)#取消
            raise 远程错误('gateway/internal','path open failed: '+str(错误),{},原因=错误)#内部

    @_远程('rename')
    def rename(自身,请求):
        """重命名会话。"""
        return 自身._命令.rename(请求)#委托

    @_远程('fork')
    def fork(自身,请求):
        """分叉已完成回合前缀。"""
        return 自身._命令.fork(请求)#委托

    @_远程('prompt')
    def prompt(自身,请求,信号):
        """显式恢复后投入提示。"""
        if 已中止(信号):#取消
            raise 远程错误('gateway/cancelled','prompt was aborted',{})#取消
        return 自身._命令.prompt(请求)#委托

    @_远程('attachment')
    def attachment(自身,请求):
        """读取会话日志引用的图像。"""
        return 自身._命令.attachment(请求)#委托

    @_远程('updateQueue')
    def updateQueue(自身,请求):
        """变更待处理队列项。"""
        return 自身._命令.updateQueue(请求)#委托

    @_远程('cancel')
    def cancel(自身,请求):
        """取消活动回合。"""
        return 自身._命令.cancel(请求)#委托

    @_远程('page')
    def page(自身,请求,信号):
        """读冷安全历史页。"""
        return 自身._历史.page(请求,信号)#委托

    @_远程('follow')
    def follow(自身,请求,信号):
        """跟随会话事件流。"""
        yield from 自身._历史.follow(请求,信号)#流

    @_远程('control')
    def control(自身,信号):
        """流式会话控制基线与增量。"""
        yield from 自身._控制.control(信号)#流

def 应用(上下文,配置值=None):
    """挂载 Session Remote 拥有者。"""
    会话控制器(上下文,配置值)#构造即登记

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
Config=配置#框架槽
