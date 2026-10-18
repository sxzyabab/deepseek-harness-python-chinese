'根 sessions 服务：列表存储、引用保留与作用域'
import os#路径基名
import re#分叉标题
import threading
from ....基础设施.通用工具 import 获取内部数据,启动守护线程
from .传输 import 会话搜索结果上限,创建会话控制流#传输
from .作用域 import 创建作用域,作用域标签,作用域身份#作用域
from .会话簇 import 会话簇#会话簇
from ..异常 import 会话创建错误,会话分叉错误,失败说明#本包异常
from ..远程错误与并发 import 已中止,若已中止则抛出#中止查询

__all__=['会话创建错误','会话分叉错误','客户端会话服务','应用客户端会话']#仅中文公开名

依赖=['connection','fileUpload','typert','remote','remote.commands','remote.session','remote.subagents']

空保留信息={'referenceCount':0,'retainedBy':{}}#空保留

半角分叉标题=re.compile(r'^(.*?)\(([0-9]+)\)\Z',re.ASCII)#半角尾编号
全角分叉标题=re.compile(r'^(.*?)（([0-9]+)）\Z')#全角尾编号

class _快照存储:
    'getSnapshot / subscribe / set'
    def __init__(自身,初值):
        '初值'
        自身._状态=初值#状态
        自身._监听=set()#订阅者
    def getSnapshot(自身):
        '读'
        return 自身._状态#状态
    def subscribe(自身,监听):
        '订'
        自身._监听.add(监听)#登记
        return lambda:自身._监听.discard(监听)#取消
    def set(自身,下一):
        '写并广播'
        自身._状态=下一#写
        for 回调 in list(自身._监听):#派发
            try:
                回调()#通知
            except Exception as 错误:
                print('[session-controller] list store subscriber failed:',type(错误).__name__,失败说明(错误))#日志，去掉绝对路径

    def __getitem__(自身,键):
        '调用方按 getSnapshot、subscribe、set 这三个名字取方法'
        if 键=='getSnapshot':#读
            return 自身.getSnapshot#方法
        if 键=='subscribe':#订
            return 自身.subscribe#方法
        if 键=='set':#写
            return 自身.set#方法
        raise KeyError(键)#没有这个名字

def _展示标题(标题,工作目录,标识):
    '持久标题、项目基名，然后 id'
    if 标题 is not None and 标题!='':#有标题
        return 标题#标题
    if 工作目录 is not None and 工作目录!='':#有 cwd
        基=os.path.basename(工作目录.rstrip('\\/'))#基名
        if 基!='':#有
            return 基#基名
    return 标识#id

def _递增分叉标题(标题):
    '递增尾部分叉编号'
    ascii匹配=半角分叉标题.match(标题)#半角
    if ascii匹配 is not None:#命中
        return ascii匹配.group(1)+'('+str(int(ascii匹配.group(2))+1)+')'#递增
    全角=全角分叉标题.match(标题)#全角
    if 全角 is not None:#命中
        return 全角.group(1)+'（'+str(int(全角.group(2))+1)+'）'#递增
    return 标题+' (1)'#起始

class _会话引用:
    '一次独立使用的精确 Client 代引用'
    def __init__(自身,会话标识,记录,释放引用):
        '记下'
        自身.sessionId=会话标识#id
        自身._记录=记录#记录
        自身._释放引用=释放引用#释放
        自身._就绪=threading.Event()#就绪门
        自身._就绪错误=None#错误
        自身._已释=False#已释
    @property
    def binding(自身):
        '共享绑定'
        if 自身._记录 is None or not 自身._记录.get('live'):#已释
            raise RuntimeError('Session reference "'+str(自身.sessionId)+'" is released')#拒绝
        return 自身._记录['binding']
    @property
    def ready(自身):
        '等待初始打开'
        自身._就绪.wait()#等
        if 自身._就绪错误 is not None:
            raise 自身._就绪错误#抛
        return 自身.binding
    def attachOpening(自身,打开任务,信号=None):
        '附着打开。共享历史继续跑，这次等待可以被取消或释放打断'
        def 后台():
            '等打开落定'
            try:
                if 信号 is not None:#有信号
                    若已中止则抛出(信号)#已取消
                打开结果=打开任务() if callable(打开任务) else 打开任务#共享打开
                if hasattr(打开结果,'然后'):#期约
                    完成=threading.Event()#落定
                    错误盒=[]#失败
                    def 成功(_值=None):
                        '打开完成'
                        完成.set()#醒
                    def 失败(错误):
                        '打开失败'
                        错误盒.append(错误)#记下
                        完成.set()#醒
                    打开结果.然后(成功,失败)#接上
                    while not 完成.is_set():#还在等历史
                        if 自身._已释:#释放只打断这次等待
                            return#停
                        if 信号 is not None and 已中止(信号):#取消
                            原因=getattr(信号,'reason',None)#原因
                            if 原因 is None:#再看中文槽
                                原因=getattr(信号,'原因',None)#原因
                            if not isinstance(原因,BaseException):#无异常
                                原因=RuntimeError('aborted')#中止
                            raise 原因#打断等待
                        完成.wait(0.05)#短等
                    if len(错误盒)>0:#失败
                        raise 错误盒[0]#抛
                if 自身._已释:#释放已另行唤醒
                    return#停
                自身._就绪.set()#就绪
            except BaseException as 错误:
                if not 自身._已释 and 自身._就绪错误 is None:#这次等待的失败
                    自身._就绪错误=错误#记下
                自身._就绪.set()#唤醒
        启动守护线程(后台)#启
    def release(自身):
        '释放一次'
        if 自身._已释:#已
            return#空
        自身._已释=True#标记
        释放=自身._释放引用#回调
        自身._记录=None#清
        自身._释放引用=None#清
        自身._就绪错误=RuntimeError('Session reference "'+str(自身.sessionId)+'" is released')#错误
        自身._就绪.set()#唤醒
        if 释放 is not None:#有
            释放()#释
    def __enter__(自身):
        'with 进入'
        return 自身#自身
    def __exit__(自身,_类型,_值,_回溯):
        'with 退出'
        自身.release()#释
        return False#不吞

class 客户端会话服务:
    '根 sessions 服务'

    def __init__(自身,上下文,远程):
        '构造并接线'
        自身._上下文=上下文#根上下文
        自身._远程=远程#远程
        自身.searchResultLimit=会话搜索结果上限#上限
        自身._会话簇=会话簇(远程)#会话簇
        自身.list=_快照存储({'ids':[],'byId':{},'phase':'pending','projectionsBySession':{}})#列表
        自身._作用域表={}#作用域
        自身._保留观察={}#观察者
        自身._已关=False
        自身._会话簇.订阅(自身._投影列表)#订阅

    def retain(自身,目标,选项):
        '保留精确 Client 代并启动共享初始历史打开'
        源=选项['source']#源
        信号=选项.get('signal')#信号
        if 信号 is not None:#有
            若已中止则抛出(信号)#已取消
        if 自身._已关:#已关
            raise RuntimeError('Session Controller is disposed')#拒绝
        标识=自身._会话簇.resolveTarget(目标)
        引用=自身._保留作用域(标识,源)#引用
        try:
            引用.attachOpening(自身._会话簇.get(标识).open,信号)
            return 引用#引用
        except BaseException:
            引用.release()#释
            raise#抛

    def using(自身,目标,选项,操作):
        '经回调落定持有一次引用'
        引用=自身.retain(目标,选项)#保留
        try:
            引用.ready#等就绪
            return 操作(引用)#回调
        finally:
            引用.release()#释

    def retainInfo(自身,标识):
        '观察本地引用计数'
        if 标识 not in 自身._保留观察:#新建
            监听=set()
            def 取快照():
                '读'
                return 自身._保留快照(标识)#快照
            def 订阅(回调):
                '订'
                监听.add(回调)#登记
                return lambda:监听.discard(回调)#取消
            自身._保留观察[标识]={'listeners':监听,'published':自身._保留快照(标识),'source':{'getSnapshot':取快照,'subscribe':订阅}}#观察
        return 自身._保留观察[标识]['source']#源

    def retainAgentScope(自身,标识):
        '网关同步保留，无历史 I/O'
        if 自身._已关:#已关
            raise RuntimeError('Session Controller is disposed')#拒绝
        return 自身._保留作用域(标识,'gateway')#引用

    def create(自身,选项=None):
        '创建或采纳会话'
        if 选项 is None:#缺省
            选项={}#空
        结果=自身._会话簇.create(选项)
        if not 结果.get('ok'):
            raise 会话创建错误(结果['error'],选项.get('sessionId'))#抛
        自身._投影列表()#投影
        return 结果['value']['sessionId']#id

    def subagentAddress(自身,标识):
        '取子地址'
        return 自身._会话簇.subagentAddress(标识)#委托

    def refreshProjections(自身,会话标识):
        '不打开会话地重读投影'
        return 自身._会话簇.refreshProjections(会话标识)#委托

    def refresh(自身):
        '刷新列表'
        自身._会话簇.refreshList()#委托

    def search(自身,查询,信号=None):
        '搜索'
        return 自身._会话簇.search(查询,信号)#委托

    def fork(自身,选项):
        '分叉；可选递增标题'
        结果=自身._会话簇.fork(选项)#分叉
        if not 结果.get('ok'):
            raise 会话分叉错误(结果['error'],选项['sessionId'])#抛
        自身._投影列表()#投影
        子标识=结果['value']['sessionId']#子
        if 选项.get('increaseTitle'):#递增标题
            源标题=自身.list.getSnapshot()['byId'].get(选项['sessionId'],{}).get('title')#标题
            if isinstance(源标题,str) and 源标题!='':#有
                引用=自身.retain(子标识,{'source':'controllerOperation'})#保留
                try:
                    引用.ready#等
                    引用.binding['session'].rename(_递增分叉标题(源标题))#改名
                finally:
                    引用.release()#释
        return 子标识#id

    def scope(自身,标识):
        '取作用域上下文'
        记录=自身._作用域表[标识] if 标识 in 自身._作用域表 else None#记录
        return None if 记录 is None else 记录['ctx']#上下文

    def scopeOf(自身,上下文):
        '读作用域标签'
        return 作用域标签(上下文)#标签

    def sessionOf(自身,上下文):
        '从作用域上下文取会话面'
        标识=作用域标签(上下文)#标签
        if 标识 is None:#无
            return None#无
        记录=自身._作用域表[标识] if 标识 in 自身._作用域表 else None#记录
        if 记录 is None:#无
            return None#无
        if 作用域身份(记录['ctx']) is not 作用域身份(上下文):#异代
            return None#无
        return 记录['binding']['session']#面

    def binding(自身,标识):
        '稳定会话绑定'
        记录=自身._作用域表[标识] if 标识 in 自身._作用域表 else None#记录
        return None if 记录 is None else 记录['binding']

    def handleControlFrame(自身,帧):
        '控制帧入口'
        自身._会话簇.handleControlFrame(帧)#委托

    def handleSessionAdded(自身,摘要):
        '列表新增'
        自身._会话簇.handleSessionAdded(摘要)#委托

    def handleSessionRemoved(自身,会话标识):
        '列表移除'
        自身._会话簇.handleSessionRemoved(会话标识)#委托

    def handleSessionStatus(自身,会话标识,运行中):
        '状态'
        自身._会话簇.handleSessionStatus(会话标识,运行中)#委托

    def handleSessionActivity(自身,会话标识,更新于):
        '活动'
        自身._会话簇.handleSessionActivity(会话标识,更新于)#委托

    def handleSessionError(自身,会话标识,消息):
        '错误'
        自身._会话簇.handleSessionError(会话标识,消息)#委托

    def handleConnected(自身):
        '重连'
        自身._会话簇.handleConnected()#委托

    def dispose(自身):
        '拆除服务'
        自身._已关=True#关
        for 标识 in list(自身._作用域表.keys()):#全部作用域
            记录=自身._作用域表[标识]#记录
            自身._退役作用域(标识,记录)#拆
        自身._会话簇.dispose()#会话簇

    def _保留作用域(自身,标识,源):
        '保留作用域'
        记录=自身._作用域表[标识] if 标识 in 自身._作用域表 else 自身._物化作用域(标识)#记录
        先前=记录['retention']#先前
        按源=dict(先前.get('retainedBy',{}))#拷
        按源[源]=按源.get(源,0)+1#加
        记录['retention']={'referenceCount':先前.get('referenceCount',0)+1,'retainedBy':按源}#写
        def 释放():
            '释放一次'
            if not 记录.get('live'):#已死
                return#空
            计数=记录['retention']['referenceCount']-1#减
            源表=dict(记录['retention']['retainedBy'])#拷
            源计数=源表.get(源,0)#源
            if 源计数<=1:#去源
                源表.pop(源,None)#删
            else:#减
                源表[源]=源计数-1#写
            记录['retention']=空保留信息 if 计数==0 else {'referenceCount':计数,'retainedBy':源表}#写
            if 计数==0:#退役
                自身._退役作用域(标识,记录)#退役
            else:#发布
                自身._发布保留(标识)#发布
        引用=_会话引用(标识,记录,释放)#引用
        if 标识 not in 自身.list.getSnapshot()['byId'] and 自身._会话簇.subagentAddress(标识) is not None:#目录子行
            自身._投影列表()#投影
        自身._发布保留(标识)#发布
        return 引用#引用

    def _保留快照(自身,标识):
        '保留快照'
        记录=自身._作用域表[标识] if 标识 in 自身._作用域表 else None#记录
        return 空保留信息 if 记录 is None else 记录['retention']#快照

    def _发布保留(自身,标识):
        '发布保留计数'
        状态=自身.list.getSnapshot()#状态
        行=状态['byId'].get(标识)#行
        按源=自身._保留快照(标识)['retainedBy']#按源
        if 行 is not None and 行.get('retainedBy') is not 按源:#变
            新行=dict(行)#拷
            新行['retainedBy']=按源#写
            新按标识=dict(状态['byId'])#拷
            新按标识[标识]=新行#写
            自身.list.set({**状态,'byId':新按标识})#写
        观察=自身._保留观察[标识] if 标识 in 自身._保留观察 else None#观察
        快照=自身._保留快照(标识)#快照
        if 观察 is None or 观察['published'] is 快照:#无变
            return#空
        观察['published']=快照#写
        for 回调 in list(观察['listeners']):#派发
            try:
                回调()#通知
            except Exception as 错误:
                print('[session-controller] reference sources',错误)#日志

    def _物化作用域(自身,标识):
        '物化作用域'
        句柄=创建作用域(自身._上下文,标识)#铸造
        实例=自身._会话簇.get(标识)#实例
        实例.绑定作用域(句柄['ctx'])
        绑定={
            'sessionId':标识,
            'session':实例,
            'eventSource':实例.eventSource,
            'ctx':句柄['ctx'],
        }
        记录={'fiber':句柄['fiber'],'ctx':句柄['ctx'],'binding':绑定,'session':实例,'retention':空保留信息,'live':True}#记录
        自身._作用域表[标识]=记录#入表
        return 记录#记录

    def _退役作用域(自身,标识,记录,拆除纤程=True):
        '退役作用域'
        if not 记录.get('live'):#已死
            return#空
        记录['live']=False#死
        if 自身._作用域表.get(标识) is 记录:#本代
            自身._作用域表.pop(标识,None)#删
        记录['session'].解绑作用域()#解绑
        自身._会话簇.drop(标识,记录['session'])#丢
        自身._投影列表()#投影
        自身._发布保留(标识)#发布
        if 拆除纤程:#拆纤程
            纤程=记录['fiber']#纤程
            if hasattr(纤程,'dispose'):#可拆
                纤程.dispose()#拆

    def _投影列表(自身):
        '会话簇快照 → SessionListState'
        先前=自身.list.getSnapshot()['byId']#先前
        快照=自身._会话簇.getListSnapshot()#快照
        标识列表=[]#ids
        按标识={}#byId
        for 项 in 快照['items']:#逐行
            标识列表.append(项['sessionId'])#id
            标题=项.get('title')#标题
            行={
                'id':项['sessionId'],
                'displayTitle':_展示标题(标题,项.get('cwd'),项['sessionId']),
                'running':项.get('running',False),
                'retainedBy':自身._保留快照(项['sessionId'])['retainedBy'],
                'blank':项.get('blank',True),
                'updatedAt':项.get('updatedAt',0),
            }#摘要
            if 'formatStatus' in 项:#格式
                行['formatStatus']=项['formatStatus']#写入
            if 'projectionValues' in 项:#投影值，含 subagentCatalog、subagentTiming、tokenUsage
                行['projectionValues']=项['projectionValues']#写入
            if 标题 is not None:#标题
                行['title']=标题#写入
            if 'cwd' in 项:#目录
                行['cwd']=项['cwd']#写入
            if 'parentSessionId' in 项:#父
                行['parentId']=项['parentSessionId']#写入
            if 'origin' in 项:#来源
                行['origin']=项['origin']#写入
            按标识[项['sessionId']]=行#收下
        for 父标识,投影 in 快照.get('projectionsBySession',{}).items():#按父投影补子行
            值表=投影.get('values') if isinstance(投影,dict) else None#值
            目录=值表.get('subagentCatalog') if isinstance(值表,dict) else None#名录
            if not isinstance(目录,list):#无
                continue#下一父
            for 子 in 目录:#子
                if not isinstance(子,dict) or 子.get('mode')=='external':#外部任务不进列表
                    continue#跳过
                子标识=子.get('id')#id
                if 子标识 is None:#无身份
                    continue#跳过
                摘要=按标识.get(子标识)#已有行
                投影值=摘要.get('projectionValues') if 摘要 is not None and 'projectionValues' in 摘要 else 自身._会话簇.projectionValues(子标识)#投影
                投影标题=投影值.get('title') if isinstance(投影值,dict) else None#标题
                标题=投影标题 if isinstance(投影标题,str) and 投影标题!='' else None#标题
                展示=标题 if 标题 is not None else (子.get('label') if 子.get('label') is not None else 子标识)#展示
                if 摘要 is None:#新行
                    运行=False#未打开
                    if 子标识 in 自身._作用域表:#已保留
                        运行=自身._作用域表[子标识]['session'].getSnapshot().get('running',False)#快照
                    按标识[子标识]={
                        'id':子标识,'displayTitle':展示,'parentId':父标识,'origin':'subagent',
                        'running':运行,'blank':False,'updatedAt':0,
                        'retainedBy':自身._保留快照(子标识)['retainedBy'],
                        **({} if 投影值 is None else {'projectionValues':投影值}),
                        **({} if 标题 is None else {'title':标题}),
                    }#行
                elif 摘要.get('displayTitle')!=展示 or 摘要.get('projectionValues') is not 投影值:#变了
                    新行=dict(摘要)#拷
                    新行['displayTitle']=展示#展示
                    if 投影值 is not None:#投影
                        新行['projectionValues']=投影值#写
                    按标识[子标识]=新行#写
        for 标识,记录 in 自身._作用域表.items():#保留中的子会话
            if 标识 in 按标识:#已有
                continue#跳过
            地址=自身._会话簇.subagentAddress(标识)#地址
            if 地址 is None:#不是子会话
                continue#跳过
            先前行=先前.get(标识)#先前
            会话快照=记录['session'].getSnapshot()#快照
            投影值=自身._会话簇.projectionValues(标识)#投影
            投影标题=投影值.get('title') if isinstance(投影值,dict) else None#标题
            标题=投影标题 if isinstance(投影标题,str) and 投影标题!='' else (先前行.get('title') if isinstance(先前行,dict) else None)#标题
            行=dict(先前行 if 先前行 is not None else {'id':标识,'displayTitle':标识,'updatedAt':0})#底
            行['running']=会话快照.get('running',False)#运行
            行['retainedBy']=记录['retention']['retainedBy']#保留
            行['blank']=会话快照.get('blank',True)#空白
            行['parentId']=地址['parentSessionId']#父
            行['origin']='subagent'#来源
            if 投影值 is not None:#投影
                行['projectionValues']=投影值#写入
            if isinstance(标题,str) and 标题!='':#有标题
                行['title']=标题#写入
                行['displayTitle']=标题#展示
            按标识[标识]=行#收下
        自身.list.set({
            'ids':标识列表,
            'byId':按标识,
            'phase':快照.get('phase','pending'),
            'projectionsBySession':快照.get('projectionsBySession',{}),
        })#写

def 应用客户端会话(上下文,配置=None):
    '安装 Client Session 状态及其可重连控制流'
    远程=上下文.remote#远程根
    服务=客户端会话服务(上下文,远程)#根服务
    上下文.提供服务('sessions',服务)#登记 sessions
    def 转发会话已添加(摘要):
        'added'
        服务.handleSessionAdded(摘要)#转发
    def 转发会话已移除(会话标识):
        'removed'
        服务.handleSessionRemoved(会话标识)#转发
    def 转发会话状态(会话标识,运行中):
        'status'
        服务.handleSessionStatus(会话标识,运行中)#转发
    def 转发会话活动(会话标识,更新于):
        'activity'
        服务.handleSessionActivity(会话标识,更新于)#转发
    def 转发会话错误(会话标识,消息):
        'error'
        服务.handleSessionError(会话标识,消息)#转发
    if 获取内部数据(远程,'on',None) is not None:#事件总线
        获取内部数据(远程,'on')('api-session/added',转发会话已添加)#新增
        获取内部数据(远程,'on')('api-session/removed',转发会话已移除)#移除
        获取内部数据(远程,'on')('api-session/status',转发会话状态)#状态
        获取内部数据(远程,'on')('api-session/activity',转发会话活动)#活动
        获取内部数据(远程,'on')('api-session/error',转发会话错误)#错误
    控制=创建会话控制流(远程,{
        'accept':服务.handleControlFrame,
        'failed':lambda 错误:print('[session-controller] control stream failed:',错误),
    })#控制流
    控制.start()
    def 已连():
        '代际就绪'
        服务.handleConnected()#修复
        控制.restart()#重启
        控制.start()
    if hasattr(上下文,'connection') and hasattr(上下文.connection,'generation'):#代际
        上下文.connection.generation.subscribe(已连)#订阅
    已连()#立即
    if hasattr(上下文,'typert') and hasattr(上下文.typert,'contexts'):#typert
        def 解析(会话标识):
            '解析作用域为受拥有值'
            引用=服务.retainAgentScope(会话标识)#保留
            类={'value':引用.binding['ctx'],'dispose':引用.release}#包装
            return 类#受拥有
        上下文.typert.contexts.registerClient('agent',{
            'identity':lambda 候选:(服务.sessionOf(候选).sessionId if 服务.sessionOf(候选) is not None else None),
            'resolve':解析,
        })#登记
    def 拆除():
        '卸载'
        控制.dispose()#拆控制
        服务.dispose()#拆服务
    上下文.副作用(拆除,'session-controller.client.control')#拆除
