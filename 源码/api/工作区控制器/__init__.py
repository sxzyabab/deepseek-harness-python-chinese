"""宿主工作区远程拥有者：显式命令与重连安全状态。"""
import re,threading
from ...依赖.schemastery import 字符串字段,数字字段
from ...typert.协议 import 远程服务,远程 as _远程
from .命令 import 工作区命令
from .提要 import 工作区提要,工作区视图
from .目录选择器 import 目录选择器控制器
from .远程错误与中止 import 远程错误,已中止
from .默认目录 import 校验文档目录,默认工作区目录,文档目录错误

__all__=['包名','名称','依赖','应用','默认','配置','工作区控制器','目录选择器控制器','工作区视图']

包名='@deepseek-ai/dsh-api-workspace-controller'
名称='workspace-controller'
依赖=['typert','workspaceRegistry']

配置={
    'documentsDirectory':字符串字段(),
    'documentsLookupTimeoutMs':数字字段(最小=1,默认值=10000),
}

非法目录名=re.compile(r'[/\\:\0]')

def _工作区标识(值):#品牌化工作区 id
    """尽力把字符串收成工作区标识。"""
    return 值#标识品牌化由 workspace 包拥有

def _工作区记录解析(值):#解析工作区记录
    """解析域记录；完整校验由 workspace 包拥有。"""
    return 值 if isinstance(值,dict) else {}

def _工作区域状态解析(值):#解析域全局状态
    """解析 workspace 域全局状态。"""
    return 值 if isinstance(值,dict) else {}

class 工作区控制器(远程服务):
    """生成远程 workspace 命名空间的宿主服务。"""
    inject=['typert','workspaceRegistry']
    Config=配置

    def __init__(自身,上下文,配置值=None):#构造
        """挂载命令、提要与子目录选择器插件。"""
        super().__init__(上下文,'workspaceController',{'namespace':'workspace'})#注册
        if 配置值 is None:
            配置值={}
        超时=配置值['documentsLookupTimeoutMs'] if 'documentsLookupTimeoutMs' in 配置值 and 配置值['documentsLookupTimeoutMs'] is not None else 10000
        自身._配置={'documentsDirectory':配置值.get('documentsDirectory'),'documentsLookupTimeoutMs':超时}
        if 自身._配置['documentsDirectory'] is not None:
            校验文档目录(自身._配置['documentsDirectory'])
        自身._命令=工作区命令(上下文,_工作区标识)#命令
        自身._提要=工作区提要(上下文,_工作区记录解析,_工作区域状态解析,_工作区标识)#提要
        上下文.启动插件(目录选择器控制器)#子插件

    @_远程('create')
    def create(自身,请求):#创建工作区
        """创建或幂等解析目录上的工作区。"""
        return 自身._命令.create(请求)#委托

    @_远程('initializeDefault')
    def initializeDefault(自身,请求,信号=None):
        """首次使用时初始化或复用默认工作区，不创建会话或消息。"""
        目录名=请求['directoryName'] if 'directoryName' in 请求 else ''
        标题=请求['title'] if 'title' in 请求 else ''
        if (not isinstance(目录名,str) or 目录名.strip()=='' or 目录名!=目录名.strip()
            or 目录名.endswith('.') or 非法目录名.search(目录名) is not None
            or not isinstance(标题,str) or 标题.strip()==''):
            raise 远程错误('gateway/bad-request','default Workspace requires a directory name and non-blank title',{})
        合成=threading.Event()
        if 已中止(信号):
            合成.set()
        def 到期():
            合成.set()
        定时=threading.Timer(自身._配置['documentsLookupTimeoutMs']/1000.0,到期)
        定时.daemon=True
        定时.start()
        def 监视父():
            if 信号 is None:
                return
            信号.wait()
            合成.set()
        监视=threading.Thread(target=监视父)
        监视.daemon=True
        监视.start()
        def 解析默认():
            try:
                路径=默认工作区目录(目录名,自身._配置['documentsDirectory'],合成)
            except 文档目录错误 as 错误:
                raise 远程错误('workspace/invalid-path',str(错误),{},原因=错误)
            finally:
                定时.cancel()
            return {'path':路径,'title':标题}
        工作区=自身.ctx.workspaceRegistry.initializeDefault(解析默认)
        if 工作区 is None:
            return None
        return {'workspace':工作区视图(工作区)}

    @_远程('rename')
    def rename(自身,请求):#重命名
        """重命名工作区。"""
        return 自身._命令.rename(请求)#委托

    @_远程('delete')
    def delete(自身,请求):#删除
        """移除工作区注册。"""
        return 自身._命令.delete(请求)#委托

    @_远程('insertBefore')
    def insertBefore(自身,请求):#调序
        """移动工作区显示顺序。"""
        return 自身._命令.insertBefore(请求)#委托

    @_远程('insertSessionBefore')
    def insertSessionBefore(自身,请求):#调会话序
        """移动工作区内会话顺序。"""
        return 自身._命令.insertSessionBefore(请求)#委托

    @_远程('archiveSession')
    def archiveSession(自身,请求):#归档会话
        """从分组面隐藏会话。"""
        return 自身._命令.archiveSession(请求)#委托

    @_远程('unarchiveSession')
    def unarchiveSession(自身,请求):
        """把已归档会话还原到分组面。"""
        return 自身._命令.unarchiveSession(请求)

    @_远程('pinSession')
    def pinSession(自身,请求):
        """把未归档会话钉到未钉会话之前。"""
        return 自身._命令.pinSession(请求)

    @_远程('unpinSession')
    def unpinSession(自身,请求):
        """去掉钉住，不改已保存会话顺序。"""
        return 自身._命令.unpinSession(请求)

    @_远程('follow')
    def follow(自身,信号):#流式 follow
        """产出基线后有序增量。"""
        if 已中止(信号):#已取消
            return#空
        yield from 自身._提要.follow(信号)#委托提要

def 应用(上下文,配置值=None):
    """挂载工作区 Remote 拥有者。"""
    工作区控制器(上下文,配置值)#构造即登记

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
