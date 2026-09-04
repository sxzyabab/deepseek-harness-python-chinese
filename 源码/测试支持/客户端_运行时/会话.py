"""声明式 fixture 之上的测试拥有 Session Controller 面。

对齐上游 `client-runtime/src/sessions.ts`。公开面仅中文名。
"""
from ...客户端.连接.客户端.接口 import 会话搜索结果上限#搜索结果上限
from ...内核.作用域 import 创建作用域,获取作用域#作用域铸造与读标签
from .夹具 import 会话快照#会话快照工厂

__all__=['夹具会话','测试会话']#仅中文公开名
Error=Exception#错误别名

class 可变会话事件源:#可变事件源
    """会话拥有的事件馈送；对齐 MutableSessionEventSource 公开面。"""

    def __init__(自身):#构造
        """空窗口。"""
        自身._listeners=set()#订阅者
        自身._entries=[]#条目
        自身._hasMore=False#是否有更多
        自身._revision=0#修订
        自身._snapshot={'entries':[],'hasMore':False,'revision':0,'change':{'kind':'replace','entries':[]}}#快照

    def getSnapshot(自身):#读快照
        """返回缓存窗口快照。"""
        return 自身._snapshot#快照

    def subscribe(自身,监听):#订阅
        """订阅窗口发布。"""
        自身._listeners.add(监听)#登记
        def 退订():#退订
            """取消。"""
            自身._listeners.discard(监听)#删除
        return 退订#退订器

    def replace(自身,条目,有更多=False):#整窗替换
        """替换完整连续窗口。"""
        自身._entries=list(条目)#重置
        自身._发布(有更多,{'kind':'replace','entries':list(条目)})#发布

    def prepend(自身,条目,有更多=False):#前置页
        """前置一页更早内容。"""
        自身._entries=[*条目,*自身._entries]#拼到左侧
        自身._发布(有更多,{'kind':'prepend','entries':list(条目)})#发布

    def append(自身,条目):#追加尾
        """追加一个连续存活条目。"""
        自身._entries=[*自身._entries,条目]#拼到右侧
        自身._发布(自身._hasMore,{'kind':'append','entries':[条目]})#发布

    def _发布(自身,有更多,变更):#发布新修订
        """升修订并通知。"""
        自身._hasMore=有更多#写 hasMore
        自身._revision+=1#升修订
        自身._snapshot={'entries':list(自身._entries),'hasMore':有更多,'revision':自身._revision,'change':变更}#新快照
        for 监听 in list(自身._listeners):#通知
            监听()#触发

def 创建快照存储(初值):#简易快照存储
    """对齐 createSnapshotStore。"""
    状态=[dict(初值) if isinstance(初值,dict) else 初值]#状态盒
    监听者=set()#订阅者
    def 取快照():#读
        """返回当前。"""
        return 状态[0]#状态
    def 订阅(回调):#订阅
        """登记。"""
        监听者.add(回调)#加入
        return lambda:监听者.discard(回调)#退订
    def 更新(变换):#更新
        """变换并通知。"""
        变换(状态[0])#变换
        for 回调 in list(监听者):#通知
            回调()#触发
    return {'getSnapshot':取快照,'subscribe':订阅,'update':更新}#面

class 夹具会话:#fixture 会话面
    """fixture 支撑的会话面。"""

    def __init__(自身,会话标识,存储,覆盖):#构造
        """记下身份、store 与行为覆盖。"""
        自身.sessionId=会话标识#会话 id
        自身._store=存储#快照 store
        自身.eventSource=可变会话事件源()#事件源
        自身._submissionSeq=0#提交序号
        投影值={}#投影值
        投影监听={}#按键监听
        投影面缓存={}#按键面缓存
        def 取面(键):#取投影面
            """按键稳定面。"""
            if 键 not in 投影面缓存:#未缓存
                def 订阅(回调):#订阅
                    """登记。"""
                    投影监听.setdefault(键,set()).add(回调)#加入
                    return lambda:投影监听.get(键,set()).discard(回调)#退订
                投影面缓存[键]={'getSnapshot':lambda 键名=键:投影值.get(键名),'subscribe':订阅}#新建面
            return 投影面缓存[键]#返回面
        def 写投影(键,值):#写投影
            """写并通知。"""
            投影值[键]=值#写投影
            for 回调 in list(投影监听.get(键,())):#通知
                回调()#触发
        自身.projections={'faceOf':取面,'set':写投影}#投影面
        for 键,值 in (覆盖 or {}).items():#嫁接覆盖
            setattr(自身,键,值)#嫁接

    def getSnapshot(自身):#读快照
        """fixture 的 Session Controller 快照。"""
        return 自身._store['getSnapshot']()#读快照

    def subscribe(自身,回调):#订阅
        """订阅 fixture 快照变更。"""
        return 自身._store['subscribe'](回调)#转 store

    def prompt(自身,*_参数,**_关键字):#未桩 prompt
        """响亮失败桩。"""
        raise Error(f'test session "{自身.sessionId}": prompt is not stubbed — supply it on the fixture\'s session face')#英文诊断

    def beginSubmission(自身):#开始提交
        """最小本地回声登记。"""
        自身._submissionSeq+=1#序号
        return {'requestId':f'test-submission-{自身._submissionSeq}','abandon':lambda:None}#句柄

    def readAttachment(自身,_附件标识):#未桩读附件
        """响亮失败桩。"""
        raise Error(f'test session "{自身.sessionId}": readAttachment is not stubbed — supply it on the fixture\'s session face')#英文诊断

    def updateQueue(自身,*_参数,**_关键字):#未桩更新队列
        """响亮失败桩。"""
        raise Error(f'test session "{自身.sessionId}": updateQueue is not stubbed — supply it on the fixture\'s session face')#英文诊断

    def cancel(自身,*_参数,**_关键字):#未桩取消
        """响亮失败桩。"""
        raise Error(f'test session "{自身.sessionId}": cancel is not stubbed — supply it on the fixture\'s session face')#英文诊断

    def command(自身,*_参数,**_关键字):#未桩命令
        """响亮失败桩。"""
        raise Error(f'test session "{自身.sessionId}": command is not stubbed — supply it on the fixture\'s session face')#英文诊断

    def loadOlder(自身,*_参数,**_关键字):#未桩加载更旧
        """响亮失败桩。"""
        raise Error(f'test session "{自身.sessionId}": loadOlder is not stubbed — supply it on the fixture\'s session face')#英文诊断

    def loadThrough(自身,*_参数,**_关键字):#未桩加载至
        """响亮失败桩。"""
        raise Error(f'test session "{自身.sessionId}": loadThrough is not stubbed — supply it on the fixture\'s session face')#英文诊断

    def rename(自身,*_参数,**_关键字):#未桩重命名
        """响亮失败桩。"""
        raise Error(f'test session "{自身.sessionId}": rename is not stubbed — supply it on the fixture\'s session face')#英文诊断

class 测试会话:#会话测试替身
    """Sessions 测试替身。"""

    def __init__(自身,稳定,根上下文):#构造
        """记下稳定器与根上下文。"""
        自身._stabilize=稳定#稳定器
        自身._rootCtx=根上下文#根上下文
        自身.list=创建快照存储({#初始列表
            'ids':[],'byId':{},'current':None,'phase':'ready',#空列表就绪
            'subagentsByParent':{},'jobsBySession':{},'currentAddress':None,#子智能体空
        })#初始列表
        自身._records={}#会话记录表
        自身.calls=[]#调用记录
        自身.searchResultLimit=会话搜索结果上限#搜索结果上限
        自身._searchStub=None#搜索桩
        自身._createStub=None#创建桩

    def add(自身,夹具,选项=None):#添加会话
        """从 fixture 添加会话并默认使其成为当前。"""
        if 选项 is None:#缺省
            选项={}#空
        标识=夹具['id']#会话 id
        if 标识 in 自身._records:#重复
            raise Error(f'test session "{标识}" already added')#重复
        摘要={#列表行
            'id':标识,'displayTitle':夹具['id'],'running':False,'blank':False,
            'updatedAt':len(自身._records)+1,**(夹具.get('summary') or {}),
        }#列表行
        快照=创建快照存储({**会话快照(标识),**(夹具.get('snapshot') or {})})#快照 store
        会话=夹具会话(标识,快照,夹具.get('session') or {})#会话面
        if 夹具.get('events') is not None or 夹具.get('hasMore') is True:#有事件窗
            会话.eventSource.replace(夹具.get('events') or [],夹具.get('hasMore') or False)#初始事件窗
        自身._records[标识]={'summary':摘要,'snapshot':快照,'session':会话,'scope':None,'scopeFiber':None,'binding':None}#记入
        def 写列表():#act 内更新列表
            """写列表。"""
            def 变换(草稿):#写
                """追加并可选选中。"""
                草稿['ids'].append(标识)#追加 id
                草稿['byId'][标识]=摘要#写行
                if 选项.get('current') is not False:#默认选中
                    草稿['current']=标识#选中
            自身.list['update'](变换)#更新
        自身._stabilize(写列表)#稳定内更新
        return 标识#返回 id

    def updateSessionSnapshot(自身,标识,变换):#更新会话快照
        """经草稿更新生命周期状态。"""
        记录=自身._要求(标识)#取记录
        自身._stabilize(lambda:记录['snapshot']['update'](变换))#稳定内更新

    def replaceEvents(自身,标识,条目,有更多=False):#替换事件窗
        """替换完整连续事件窗口。"""
        自身._stabilize(lambda:自身._要求(标识)['session'].eventSource.replace(条目,有更多))#稳定内替换

    def prependEvents(自身,标识,条目,有更多=False):#前置事件
        """前置一页更旧事件。"""
        自身._stabilize(lambda:自身._要求(标识)['session'].eventSource.prepend(条目,有更多))#稳定内前置

    def appendEvent(自身,标识,条目):#追加事件
        """追加一条活事件。"""
        自身._stabilize(lambda:自身._要求(标识)['session'].eventSource.append(条目))#稳定内追加

    def updateSummary(自身,标识,补丁):#更新摘要
        """更新会话列表行。"""
        记录=自身._要求(标识)#取记录
        记录['summary']={**记录['summary'],**补丁}#合并摘要
        def 写():#写列表
            """写行。"""
            自身.list['update'](lambda 草稿:草稿['byId'].__setitem__(标识,记录['summary']))#写行
        自身._stabilize(写)#稳定内写

    def setCurrent(自身,标识):#切换当前
        """切换当前选择。"""
        if 标识 is not None:#校验存在
            自身._要求(标识)#校验
        自身._stabilize(lambda:自身.list['update'](lambda 草稿:草稿.__setitem__('current',标识)))#写当前

    def remove(自身,标识):#移除会话
        """移除会话及作用域。"""
        记录=自身._要求(标识)#取记录
        del 自身._records[标识]#删记录
        def 拆除():#拆除
            """写列表并拆作用域。"""
            def 变换(草稿):#写列表
                """去 id 与行。"""
                草稿['ids']=[已有 for 已有 in 草稿['ids'] if 已有!=标识]#去 id
                草稿['byId']={键:值 for 键,值 in 草稿['byId'].items() if 键!=标识}#去行
                if 草稿['current']==标识:#清当前
                    草稿['current']=None#清当前
            自身.list['update'](变换)#更新
            光纤=记录['scopeFiber']#作用域 fiber
            if 光纤 is not None and hasattr(光纤,'dispose'):#有 fiber
                光纤.dispose()#拆除
        自身._stabilize(拆除)#稳定内拆除

    def scope(自身,标识):#取作用域
        """首次触碰时铸造会话作用域。"""
        记录=自身._records.get(标识)#取记录
        if 记录 is None:#未知
            return None#未知
        if 记录['scope'] is None:#首次铸造
            句柄=创建作用域(自身._rootCtx,标识)#铸造作用域
            记录['scope']=句柄.ctx if hasattr(句柄,'ctx') else 句柄.get('ctx')#记上下文
            记录['scopeFiber']=句柄.fiber if hasattr(句柄,'fiber') else 句柄.get('fiber')#记 fiber
        return 记录['scope']#返回

    def binding(自身,标识):#取绑定
        """会话组装绑定。"""
        记录=自身._records.get(标识)#取记录
        if 记录 is None:#未知
            return None#未知
        if 记录['binding'] is None:#记忆化
            记录['binding']=自身._铸造绑定(标识,记录)#铸造
        return 记录['binding']#返回

    def scopeOf(自身,上下文):#读作用域标签
        """从上下文读会话作用域标签。"""
        return 获取作用域(上下文)#委托

    def sessionOf(自身,上下文):#解析会话面
        """从上下文解析作用域会话面。"""
        标识=获取作用域(上下文)#读标签
        if 标识 is None:#根上下文
            return None#无
        记录=自身._records.get(标识)#取记录
        return None if 记录 is None else 记录['session']#取会话面

    def stubCreate(自身,实现):#安装创建桩
        """为导航测试安装 Session 创建行为。"""
        自身._createStub=实现#写入

    def create(自身,选项=None):#创建会话
        """经已安装测试行为创建。"""
        自身.calls.append({'method':'create','args':[选项]})#记录
        if 自身._createStub is None:#未桩
            raise Error('test sessions: create is not stubbed — call stubCreate() first')#英文诊断
        标识=自身._createStub(选项)#走桩
        自身._要求(标识)#要求可寻址
        return 标识#返回

    def open(自身,标识):#打开会话
        """服务级选择调用。"""
        自身.calls.append({'method':'open','args':[标识]})#记录
        自身._要求(标识)#校验
        def 写(草稿):#写列表
            """选中。"""
            草稿['current']=标识#选中
            草稿['currentAddress']=None#清地址
        自身.list['update'](写)#更新

    def openSubagent(自身,地址):#打开子智能体
        """经目录地址打开已有 fixture。"""
        自身.calls.append({'method':'openSubagent','args':[地址]})#记录
        子标识=地址['childSessionId'] if isinstance(地址,dict) else 地址.childSessionId#子会话
        自身._要求(子标识)#校验
        def 写(草稿):#写列表
            """选中子会话。"""
            草稿['current']=子标识#选中
            草稿['currentAddress']=地址#记地址
        自身.list['update'](写)#更新

    def subagentAddress(自身,标识):#取子智能体地址
        """解析当前 fixture 保留的目录地址。"""
        地址=自身.list['getSnapshot']()['currentAddress']#读当前地址
        if 地址 is None:#无
            return None#无
        子=地址['childSessionId'] if isinstance(地址,dict) else getattr(地址,'childSessionId',None)#子 id
        return 地址 if 子==标识 else None#匹配则返回

    def setSubagentCatalogOpen(自身,父会话标识,打开):#设置目录开合
        """记录目录消费。"""
        自身.calls.append({'method':'setSubagentCatalogOpen','args':[父会话标识,打开]})#记录

    def refreshSubagents(自身,父会话标识):#刷新子智能体
        """记录目录刷新。"""
        自身.calls.append({'method':'refreshSubagents','args':[父会话标识]})#记录

    def clear(自身):#清除当前
        """清除当前选择。"""
        自身.calls.append({'method':'clear','args':[]})#记录
        def 写(草稿):#写列表
            """清当前。"""
            草稿['current']=None#清当前
            草稿['currentAddress']=None#清地址
        自身.list['update'](写)#更新

    def refresh(自身):#刷新列表
        """记录列表刷新。"""
        自身.calls.append({'method':'refresh','args':[]})#记录

    def stubSearch(自身,实现):#安装搜索桩
        """替换侧栏搜索结果页。"""
        自身._searchStub=实现#写入

    def search(自身,查询,信号):#搜索
        """对 fixture 语料的内容搜索。"""
        自身.calls.append({'method':'search','args':[查询,信号]})#记录
        值=自身._searchStub(查询,信号) if 自身._searchStub is not None else {'items':[],'hasMore':False}#已桩或空页
        return {'ok':True,'value':值}#结果

    def fork(自身,选项):#fork 桩
        """已记录 fork 桩。"""
        自身.calls.append({'method':'fork','args':[选项]})#记录
        return 选项['sessionId']#回声源 id

    def behavior(自身,标识):#取行为面
        """fixture 的会话面。"""
        return 自身._要求(标识)['session']#返回会话面

    def disposeScopes(自身):#拆除作用域
        """拆除已铸造作用域 fiber。"""
        for 记录 in 自身._records.values():#遍历记录
            光纤=记录['scopeFiber']#fiber
            if 光纤 is not None and hasattr(光纤,'dispose'):#有 fiber
                光纤.dispose()#拆除
                记录['scope']=None#清空
                记录['scopeFiber']=None#清空
                记录['binding']=None#清空

    def _铸造绑定(自身,标识,记录):#铸造绑定
        """铸造绑定。"""
        上下文=自身.scope(标识)#取作用域
        if 上下文 is None:#无作用域
            raise Error(f'test session "{标识}" resolved no scope')#英文诊断
        return {'sessionId':标识,'session':记录['session'],'eventSource':记录['session'].eventSource,'ctx':上下文}#绑定

    def _要求(自身,标识):#要求已添加
        """要求记录存在。"""
        记录=自身._records.get(标识)#取记录
        if 记录 is None:#缺失
            raise Error(f'test session "{标识}" is not added')#英文诊断
        return 记录#返回

FixtureSession=夹具会话#上游名
TestSessions=测试会话#上游名
