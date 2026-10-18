'宿主工作区远程拥有者：显式命令与重连安全状态'
import json,os,sys,threading#帧文本、家目录、平台、查找超时
import ntpath as 窗口路径#win32 路径
import posixpath as 正斜杠路径#posix 路径
from ...工具.原生命令 import 运行原生命令#系统文档目录
from ...类型化远程调用.协议 import 远程服务,远程 as 远程装饰#远程服务与方法标记
from ...客户端.连接.rpc import 中止控制器,中止信号#寿命与超时
from ..网关.流协议 import 已中止,若中止则抛 as 若已中止则抛出#寿命与超时
from .命令 import 工作区命令#变更
from .提要 import 工作区提要,工作区视图#基线与投影
from .目录选择器 import 目录选择器控制器#目录选择子插件
from .默认目录 import 校验文档目录#文档路径
from .默认工作区 import 默认工作区目录名#固定叶目录名
from . import (
    命令,
    提要,
    类型,
    默认目录,
    默认工作区,
    目录选择器,
    异常,
    客户端,
)

__all__=[
    '命令','提要','类型','默认目录','默认工作区','目录选择器','异常','客户端',
    '工作区控制器','目录选择器控制器',
]

名称='workspace-controller'#插件显示名
依赖=['remoteAccess','typert','workspaceRegistry']#访问过滤、类型注册表、工作区登记


class 配置模式:
    '首次使用目录策略。超时缺省 10000 毫秒，文档目录可以不给'

    def 校验数据(自身,配置=None):
        '补上超时默认值。文档目录给出时必须是字符串，超时必须是大于等于 1 的整数'
        if 配置 is None:#加载器没给
            配置={}#空
        if not isinstance(配置,dict):#不是对象
            raise TypeError('workspace controller config must be a dict')#拒绝
        结果={'documentsDirectory':None,'documentsLookupTimeoutMs':10000}#缺省
        if 'documentsDirectory' in 配置 and 配置['documentsDirectory'] is not None:#给了目录
            目录=配置['documentsDirectory']#目录
            if not isinstance(目录,str):#不是字符串
                raise TypeError('documentsDirectory must be a string')#拒绝
            结果['documentsDirectory']=目录#留下
        if 'documentsLookupTimeoutMs' in 配置 and 配置['documentsLookupTimeoutMs'] is not None:#给了超时
            超时=配置['documentsLookupTimeoutMs']#超时
            if isinstance(超时,bool) or (not isinstance(超时,int)) or 超时<1:#不是正整数
                raise TypeError('documentsLookupTimeoutMs must be a natural number >= 1')#拒绝
            结果['documentsLookupTimeoutMs']=超时#留下
        return 结果#解析后的配置

    def __call__(自身,配置=None):
        '直接调用时同样解析'
        return 自身.校验数据(配置)#解析


配置=配置模式()#类上的 Config


class 工作区控制器(远程服务):
    '生成远程 workspace 命名空间的宿主服务'
    name=名称#插件名
    inject=依赖#框架槽
    Config=配置#配置模式

    def __init__(自身,上下文,配置值=None):
        '登记资源字段、命令、提要，并挂上目录选择子插件'
        super().__init__(上下文,'workspaceController',{'namespace':'workspace'})#服务与命名空间
        上下文.typert.resources.register('workspace',{'field':'workspaceId'})#工作区资源字段
        自身.配置=工作区控制器.Config(配置值)#解析配置
        if 自身.配置['documentsDirectory'] is not None:#部署覆盖了文档目录
            校验文档目录(自身.配置['documentsDirectory'])#必须完全限定
        自身.命令=工作区命令(上下文)#变更
        自身.提要=工作区提要(上下文)#跟随
        上下文.启动插件(目录选择器控制器)#目录选择。后端没接上时不回答挑选动词

    @远程装饰('create')
    def create(自身,请求):
        '创建或幂等解析一个已有目录上的工作区'
        return 自身.命令.create(请求)#委托

    @远程装饰('initializeDefault')
    def initializeDefault(自身,信号):
        '首次使用时准备默认工作区。目录名固定，不创建会话'

        def 解析默认目录():
            '在文档目录下拼出默认工作区路径，不创建文件'
            超时控制=中止控制器()#查找截止
            def 到期():
                '到点后中止查找'
                超时控制.中止配套信号(TimeoutError('Signal timed out.'))#超时
            定时=threading.Timer(自身.配置['documentsLookupTimeoutMs']/1000.0,到期)#毫秒转秒
            定时.daemon=True#随进程退出
            定时.start()#开始计时
            try:#结束时停掉计时
                合成=中止信号.任一([信号,超时控制.信号])#调用方寿命和截止
                平台=sys.platform#本机
                路径模块=窗口路径 if 平台=='win32' else 正斜杠路径#按平台拼接
                若已中止则抛出(合成)#已经取消
                目录=自身.配置['documentsDirectory']#部署覆盖
                if 目录 is None:#问操作系统
                    if 平台=='darwin':#macOS
                        输出=运行原生命令('osascript',[
                            '-e','POSIX path of (path to documents folder from user domain without folder creation)',
                        ],合成._事件)#文档夹
                    elif 平台=='win32':#Windows
                        输出=运行原生命令('powershell.exe',[
                            '-NoLogo','-NoProfile','-NonInteractive','-Command',
                            '[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); '
                            +'[Environment]::GetFolderPath([Environment+SpecialFolder]::MyDocuments, '
                            +'[Environment+SpecialFolderOption]::DoNotVerify)',
                        ],合成._事件)#我的文档
                    elif 平台=='linux':#Linux
                        输出=运行原生命令('xdg-user-dir',['DOCUMENTS'],合成._事件)#XDG 文档
                    else:#没有系统文档目录
                        raise RuntimeError('system Documents directory is unavailable on '+平台)#拒绝
                    目录=输出['stdout']#标准输出
                    while 目录.endswith('\n') or 目录.endswith('\r'):#去掉尾部换行
                        目录=目录[:-1]#剥一层
                    家=路径模块.normpath(os.path.expanduser('~'))#家目录
                    if 目录=='' or (平台=='linux' and 路径模块.normpath(目录)==家):#关掉或回到家目录
                        raise RuntimeError('system Documents directory is unavailable')#拒绝
                目录=校验文档目录(目录,平台)#完全限定
                若已中止则抛出(合成)#查找期间被取消
                return 路径模块.join(目录,'deepseek-harness',默认工作区目录名)#候选路径
            finally:#不再等待截止
                定时.cancel()#停表
                if not 已中止(超时控制.信号):#截止还没触发
                    超时控制.中止配套信号()#放掉合成里等截止的线程

        工作区=自身.ctx.workspaceRegistry.initializeDefault(解析默认目录)#创建或复用
        if 工作区 is None:#这次不具备首次使用条件
            return None#不创建
        return {'workspace':工作区视图(工作区)}#耐久工作区

    @远程装饰('rename')
    def rename(自身,请求):
        '把工作区改成不重复的非空白标题'
        return 自身.命令.rename(请求)#委托

    @远程装饰('delete')
    def delete(自身,请求):
        '去掉工作区登记，文件和会话仍留着'
        return 自身.命令.delete(请求)#委托

    @远程装饰('insertBefore')
    def insertBefore(自身,请求):
        '移动工作区在登记显示顺序中的位置'
        return 自身.命令.insertBefore(请求)#委托

    @远程装饰('insertSessionBefore')
    def insertSessionBefore(自身,请求):
        '移动一个已入账会话在工作区里的位置'
        return 自身.命令.insertSessionBefore(请求)#委托

    @远程装饰('archiveSession')
    def archiveSession(自身,请求):
        '把已知会话从工作区分组面上藏起来'
        return 自身.命令.archiveSession(请求)#委托

    @远程装饰('unarchiveSession')
    def unarchiveSession(自身,请求):
        '把已归档会话放回分组面'
        return 自身.命令.unarchiveSession(请求)#委托

    @远程装饰('pinSession')
    def pinSession(自身,请求):
        '把未归档会话钉到未钉会话前面'
        return 自身.命令.pinSession(请求)#委托

    @远程装饰('unpinSession')
    def unpinSession(自身,请求):
        '去掉钉住，不改已保存的会话顺序'
        return 自身.命令.unpinSession(请求)#委托

    @远程装饰({'mode':'stream'})
    def follow(自身,信号):
        '先给一份过滤后的基线，再给有序增量。非所有者只看见 allows 放行的工作区和会话'
        访问=自身.ctx.remoteAccess#当前调用的访问面
        已交付=set()#这一代已经交给对方、还没移除的工作区

        def 可见(工作区号):
            '这份工作区对当前调用方是否可见'
            return 访问.是否允许({'kind':'workspace','id':工作区号})#工作区资源

        def 会话列(会话标识列):
            '留下当前调用方能看见的会话'
            结果=[]#可见会话
            for 会话标识 in 会话标识列:#逐个
                if 访问.是否允许({'kind':'session','id':会话标识}):#会话资源
                    结果.append(会话标识)#留下
            return 结果#过滤后

        def 过滤(值):
            '只留可见工作区，并把它记成这一代已交付的集合'
            项列=[]#可见行
            for 项 in 值['items']:#每一行
                if 可见(项['workspaceId']):#放行
                    项列.append(项)#留下
            已交付.clear()#重新记
            for 项 in 项列:#可见行
                已交付.add(项['workspaceId'])#交付
            投影=[]#会话也过滤
            for 项 in 项列:#每一行
                投影.append({**项,'sessionIds':会话列(项['sessionIds'])})#换会话列
            return {
                'items':投影,#工作区
                'archivedSessionIds':会话列(值['archivedSessionIds']),#归档
                'pinnedSessionIds':会话列(值['pinnedSessionIds']),#钉住
            }#过滤后的基线

        for 帧 in 自身.提要.follow(信号):#提要的帧里没有 replace
            种类=帧['type']#帧种类
            if 种类=='baseline':#开口
                yield {'type':'baseline','value':过滤(帧['value'])}#过滤后的基线
            elif 种类=='upsert':#一行变更
                工作区号=帧['workspace']['workspaceId']#这一行
                if 可见(工作区号):#仍然可见
                    已交付.add(工作区号)#记成已交付
                    yield {
                        'type':'upsert',
                        'workspace':{**帧['workspace'],'sessionIds':会话列(帧['workspace']['sessionIds'])},
                    }#过滤会话
                elif 工作区号 in 已交付:#曾经交付，现在不再可见
                    yield {'type':'replace','value':过滤(自身.提要.读取基线())}#整份替换，不用 remove
            elif 种类=='remove':#登记删除
                if 帧['workspaceId'] in 已交付:#只通知收过这一行的一方
                    已交付.remove(帧['workspaceId'])#忘掉
                    yield 帧#删除
            elif 种类=='order':#顺序
                需要替换=False#有已交付的工作区变得不可见
                for 工作区号 in 帧['workspaceIds']:#新顺序
                    if 工作区号 in 已交付 and (not 可见(工作区号)):#丢了可见性
                        需要替换=True#要整份替换
                        break#不用再看
                if 需要替换:#不能用去掉一行来表达
                    yield {'type':'replace','value':过滤(自身.提要.读取基线())}#整份替换
                else:#仍可见的顺序
                    yield {'type':'order','workspaceIds':[工作区号 for 工作区号 in 帧['workspaceIds'] if 可见(工作区号)]}#过滤
            elif 种类=='archived':#归档集
                yield {'type':'archived','archivedSessionIds':会话列(帧['archivedSessionIds'])}#过滤
            elif 种类=='pinned':#钉住集
                yield {'type':'pinned','pinnedSessionIds':会话列(帧['pinnedSessionIds'])}#过滤
            else:#封闭联合之外
                raise RuntimeError('unreachable Workspace follow frame: '+json.dumps(帧,ensure_ascii=False))#不应到达


默认=工作区控制器#类插件
name=名称#框架槽
inject=依赖#框架槽
default=默认#框架槽
