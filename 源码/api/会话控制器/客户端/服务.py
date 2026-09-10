"""根 sessions 服务：列表存储、选择、作用域与绑定。

对齐上游 `session-controller/src/client/sessions/service.ts`。公开面仅中文名。
"""
import os#路径基名
import re#分叉标题
from .传输 import 会话搜索结果上限,创建会话控制流#传输
from .作用域 import 创建作用域,作用域标签#作用域
from .管理器 import 会话管理器#管理器

__all__=['会话创建错误','会话分叉错误','客户端会话服务','应用客户端会话']#仅中文公开名

注入=['connection','fileUpload','typert','remote','remote.commands','remote.session','remote.subagents']#依赖

class _快照存储:
    """getSnapshot / subscribe / set；对齐 createSnapshotStore。"""
    def __init__(自身,初值):
        """初值。"""
        自身._状态=初值#状态
        自身._监听=set()#订阅者
    def getSnapshot(自身):
        """读。"""
        return 自身._状态#状态
    def subscribe(自身,监听):
        """订。"""
        自身._监听.add(监听)#登记
        return lambda:自身._监听.discard(监听)#取消
    def set(自身,下一):
        """写并广播。"""
        自身._状态=下一#写
        for 回调 in list(自身._监听):#派发
            try:
                回调()#通知
            except Exception as 错误:
                print('[session-controller] list store subscriber failed:',错误)#日志

class 会话创建错误(Exception):
    """结构化 session 创建失败。"""
    def __init__(自身,远程失败,请求会话标识=None):
        """记下失败。"""
        码=远程失败.code if hasattr(远程失败,'code') else 远程失败.get('code')#码
        消息=远程失败.message if hasattr(远程失败,'message') else 远程失败.get('message')#消息
        super().__init__('session create failed: '+str(码)+': '+str(消息))#文案
        自身.name='SessionCreateError'#名
        自身.rpcError=远程失败#失败
        自身.requestedSessionId=请求会话标识#请求 id

class 会话分叉错误(Exception):
    """结构化 session 分叉失败。"""
    def __init__(自身,远程失败,源会话标识):
        """记下失败。"""
        码=远程失败.code if hasattr(远程失败,'code') else 远程失败.get('code')#码
        消息=远程失败.message if hasattr(远程失败,'message') else 远程失败.get('message')#消息
        super().__init__('session fork failed: '+str(码)+': '+str(消息))#文案
        自身.name='SessionForkError'#名
        自身.rpcError=远程失败#失败
        自身.sourceSessionId=源会话标识#源

def _展示标题(标题,工作目录,标识):
    """持久标题、项目基名，然后 id。"""
    if 标题 is not None and 标题!='':#有标题
        return 标题#标题
    if 工作目录 is not None and 工作目录!='':#有 cwd
        基=os.path.basename(工作目录.rstrip('\\/'))#基名
        if 基!='':#有
            return 基#基名
    return 标识#id

def _递增分叉标题(标题):
    """递增尾部分叉编号。"""
    ascii匹配=re.match(r'^(.*?)\((\d+)\)$',标题)#半角
    if ascii匹配 is not None:#命中
        return ascii匹配.group(1)+'('+str(int(ascii匹配.group(2))+1)+')'#递增
    全角=re.match(r'^(.*?)（(\d+)）$',标题)#全角
    if 全角 is not None:#命中
        return 全角.group(1)+'（'+str(int(全角.group(2))+1)+'）'#递增
    return 标题+' (1)'#起始

class 客户端会话服务:
    """根 sessions 服务。"""

    def __init__(自身,上下文,远程):
        """构造并接线。"""
        自身._上下文=上下文#根上下文
        自身._远程=远程#远程
        自身.searchResultLimit=会话搜索结果上限#上限
        自身._选择=_快照存储({})#选择存储
        初选=自身._选择.getSnapshot()#初选
        自身._管理器=会话管理器(
            远程,
            初选['sessionId'] if 'sessionId' in 初选 else None,
            初选['subagentAddress'] if 'subagentAddress' in 初选 else None,
        )#管理器
        自身.list=_快照存储(自身._投影列表状态())#列表存储
        自身._作用域表={}#作用域
        自身._监视=自身._管理器.getListSnapshot().get('current')#台上
        自身._延迟移除=set()#延迟移除
        自身._管理器.订阅(自身._列表变)#订阅管理器

    def create(自身,选项=None):
        """创建或采纳会话。"""
        if 选项 is None:#缺省
            选项={}#空
        结果=自身._管理器.create(选项)#创建
        if not 结果.get('ok'):#失败
            raise 会话创建错误(结果['error'],选项.get('sessionId'))#抛
        return 结果['value']['sessionId']#id

    def open(自身,标识):
        """选择会话为当前。"""
        自身._管理器.select(标识)#选择
        自身._选择.set({'sessionId':标识})#持久选择
        自身._上台(标识)#上台

    def openSubagent(自身,地址):
        """打开健康目录子项。"""
        自身._管理器.selectSubagent(地址)#选择
        自身._选择.set({'sessionId':地址['childSessionId'],'subagentAddress':地址})#持久
        自身._上台(地址['childSessionId'])#上台

    def subagentAddress(自身,标识):
        """取子地址。"""
        return 自身._管理器.subagentAddress(标识)#委托

    def setSubagentCatalogOpen(自身,父会话标识,打开):
        """目录打开态。"""
        自身._管理器.setSubagentCatalogOpen(父会话标识,打开)#委托

    def refreshSubagents(自身,父会话标识):
        """刷新子目录。"""
        自身._管理器.refreshSubagents(父会话标识)#委托

    def clear(自身):
        """清除当前选择。"""
        自身._管理器.clearSelection()#清
        自身._选择.set({})#清持久
        自身._上台(None)#下台

    def refresh(自身):
        """刷新列表。"""
        自身._管理器.refreshList()#委托

    def search(自身,查询,信号=None):
        """搜索。"""
        return 自身._管理器.search(查询,信号)#委托

    def fork(自身,选项):
        """分叉；可选递增标题。"""
        结果=自身._管理器.fork(选项)#分叉
        if not 结果.get('ok'):#失败
            raise 会话分叉错误(结果['error'],选项['sessionId'])#抛
        子标识=结果['value']['sessionId']#子
        if 选项.get('increaseTitle'):#递增标题
            快照=自身._管理器.getListSnapshot()#列表
            源标题=None#标题
            for 项 in 快照['items']:#找源
                if 项['sessionId']==选项['sessionId']:#命中
                    源标题=项.get('title')#标题
                    break#停
            if isinstance(源标题,str) and 源标题!='':#有
                实例=自身._管理器.get(子标识)#子实例
                实例.rename(_递增分叉标题(源标题))#改名
        自身.open(子标识)#打开子
        return 子标识#id

    def scope(自身,标识):
        """取作用域上下文。"""
        记录=自身._解析作用域(标识)#记录
        return None if 记录 is None else 记录['ctx']#上下文

    def scopeOf(自身,上下文):
        """读作用域标签。"""
        return 作用域标签(上下文)#标签

    def sessionOf(自身,上下文):
        """从作用域上下文取会话面。"""
        标识=作用域标签(上下文)#标签
        if 标识 is None:#无
            return None#无
        绑定=自身.binding(标识)#绑定
        return None if 绑定 is None else 绑定['session']#面

    def binding(自身,标识):
        """稳定会话绑定。"""
        记录=自身._解析作用域(标识)#记录
        return None if 记录 is None else 记录['binding']#绑定

    def handleControlFrame(自身,帧):
        """控制帧入口。"""
        自身._管理器.handleControlFrame(帧)#委托

    def handleSessionAdded(自身,摘要):
        """列表新增。"""
        自身._管理器.handleSessionAdded(摘要)#委托

    def handleSessionRemoved(自身,会话标识):
        """列表移除。"""
        自身._管理器.handleSessionRemoved(会话标识)#委托
        if 自身._监视==会话标识:#台上
            自身._延迟移除.add(会话标识)#延迟
        else:#立即
            自身._拆除作用域(会话标识)#拆

    def handleSessionStatus(自身,会话标识,运行中):
        """状态。"""
        自身._管理器.handleSessionStatus(会话标识,运行中)#委托

    def handleSessionActivity(自身,会话标识,更新于):
        """活动。"""
        自身._管理器.handleSessionActivity(会话标识,更新于)#委托

    def handleSessionError(自身,会话标识,消息):
        """错误。"""
        自身._管理器.handleSessionError(会话标识,消息)#委托

    def handleConnected(自身):
        """重连。"""
        自身._管理器.handleConnected()#委托

    def dispose(自身):
        """拆除服务。"""
        for 标识 in list(自身._作用域表.keys()):#全部作用域
            自身._拆除作用域(标识)#拆
        自身._管理器.dispose()#管理器

    def _列表变(自身):
        """管理器列表变 → 投影存储。"""
        自身.list.set(自身._投影列表状态())#写
        当前=自身._管理器.getListSnapshot().get('current')#当前
        if 当前!=自身._监视:#台变
            旧=自身._监视#旧台
            自身._监视=当前#新台
            if 旧 is not None and 旧 in 自身._延迟移除:#延迟拆
                自身._延迟移除.discard(旧)#清
                自身._拆除作用域(旧)#拆
            if 当前 is not None:#新台
                自身._解析作用域(当前)#确保作用域
                自身._管理器.get(当前).open()#打开窗口

    def _投影列表状态(自身):
        """管理器快照 → SessionListState。"""
        快照=自身._管理器.getListSnapshot()#快照
        标识列表=[]#ids
        按标识={}#byId
        for 项 in 快照['items']:#逐行
            标识列表.append(项['sessionId'])#id
            标题=项.get('title')#标题
            按标识[项['sessionId']]={
                'id':项['sessionId'],
                'displayTitle':_展示标题(标题,项.get('cwd'),项['sessionId']),
                'running':项.get('running',False),
                'blank':项.get('blank',True),
                'updatedAt':项.get('updatedAt',0),
                **({'title':标题} if 标题 is not None else {}),
                **({'cwd':项['cwd']} if 'cwd' in 项 else {}),
                **({'parentId':项['parentSessionId']} if 'parentSessionId' in 项 else {}),
                **({'origin':项['origin']} if 'origin' in 项 else {}),
                **({'completed':项['completed']} if 'completed' in 项 else {}),
                **({'projectionValues':项['projectionValues']} if 'projectionValues' in 项 else {}),
            }#摘要
        return {
            'ids':标识列表,
            'byId':按标识,
            'current':快照.get('current'),
            'phase':快照.get('phase','pending'),
            'subagentsByParent':快照.get('subagentsByParent',{}),
            'jobsBySession':快照.get('jobsBySession',{}),
            'currentAddress':快照.get('currentAddress'),
        }#状态

    def _上台(自身,标识):
        """台位转移。"""
        旧=自身._监视#旧
        自身._监视=标识#新
        if 旧 is not None and 旧!=标识:#旧台
            if 旧 in 自身._延迟移除:#延迟
                自身._延迟移除.discard(旧)#清
                自身._拆除作用域(旧)#拆
        if 标识 is not None:#新台
            自身._解析作用域(标识)#铸造
            自身._管理器.get(标识).open()#打开

    def _解析作用域(自身,标识):
        """惰性铸造作用域与绑定。"""
        if 标识 in 自身._作用域表:#已有
            return 自身._作用域表[标识]#记录
        快照=自身._管理器.getListSnapshot()#列表
        在列表=any(项['sessionId']==标识 for 项 in 快照['items'])#在列表
        if (not 在列表) and 自身._管理器.subagentAddress(标识) is None:#未知
            return None#无
        句柄=创建作用域(自身._上下文,标识)#铸造
        实例=自身._管理器.get(标识)#实例
        实例.绑定作用域(句柄['ctx'])#绑定
        绑定={
            'sessionId':标识,
            'session':实例,
            'eventSource':实例.eventSource,
            'ctx':句柄['ctx'],
        }#绑定
        记录={'fiber':句柄['fiber'],'ctx':句柄['ctx'],'binding':绑定,'session':实例}#记录
        自身._作用域表[标识]=记录#入表
        return 记录#记录

    def _拆除作用域(自身,标识):
        """拆除作用域记录。"""
        记录=自身._作用域表.pop(标识,None)#取出
        if 记录 is None:#无
            return#空
        记录['session'].解绑作用域()#解绑
        光纤=记录['fiber']#光纤
        if hasattr(光纤,'dispose'):#可拆
            光纤.dispose()#拆
        自身._管理器.drop(标识)#丢实例

def 应用客户端会话(上下文):
    """安装 Client Session 状态及其可重连控制流。"""
    远程=上下文.remote#远程根
    服务=客户端会话服务(上下文,远程)#根服务
    if hasattr(上下文,'提供'):#有提供
        上下文.提供('sessions',服务)#注入
    else:#直接挂
        上下文.sessions=服务#挂属性
    def 加(摘要):
        """added。"""
        服务.handleSessionAdded(摘要)#转发
    def 减(会话标识):
        """removed。"""
        服务.handleSessionRemoved(会话标识)#转发
    def 态(会话标识,运行中):
        """status。"""
        服务.handleSessionStatus(会话标识,运行中)#转发
    def 活(会话标识,更新于):
        """activity。"""
        服务.handleSessionActivity(会话标识,更新于)#转发
    def 错(会话标识,消息):
        """error。"""
        服务.handleSessionError(会话标识,消息)#转发
    if hasattr(远程,'$on'):#事件总线
        远程.$on('api-session/added',加)#新增
        远程.$on('api-session/removed',减)#移除
        远程.$on('api-session/status',态)#状态
        远程.$on('api-session/activity',活)#活动
        远程.$on('api-session/error',错)#错误
    控制=创建会话控制流(远程,{
        'accept':服务.handleControlFrame,
        'failed':lambda 错误:print('[session-controller] control stream failed:',错误),
    })#控制流
    控制['启动']()#启动
    def 重连():
        """connection/reset。"""
        服务.handleConnected()#修复
    上下文.监听('connection/reset',重连)#重连
    if hasattr(远程,'$host') and getattr(远程.$host,'home',None) is not None:#已连
        服务.handleConnected()#首连
    if hasattr(上下文,'typert') and hasattr(上下文.typert,'contexts'):#typert
        上下文.typert.contexts.registerClient('agent',{
            'identity':lambda 候选:服务.scopeOf(候选),
            'resolve':lambda 会话标识:服务.scope(会话标识),
        })#登记
    def 拆除():
        """卸载。"""
        控制['拆除']()#拆控制
        服务.dispose()#拆服务
    上下文.副作用(拆除,'session-controller.client.control')#拆除
