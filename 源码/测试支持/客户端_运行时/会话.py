import threading#中止信号
from ...api.会话控制器.客户端 import (#会话控制器客户端面
    创建作用域,作用域标签,可变会话事件源,会话搜索结果上限,#作用域与事件源
)#结束导入
from .夹具 import 会话快照#会话快照工厂

__all__=['夹具会话','测试会话']#仅中文公开名

空保留信息={'referenceCount':0,'retainedBy':{}}#空保留

def 创建快照存储(初值):#简易快照存储
    """对齐 createSnapshotStore：getSnapshot / subscribe / update / set。"""
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
        """原地变换并通知。"""
        变换(状态[0])#变换
        for 回调 in list(监听者):#通知
            回调()#触发
    def 设置(值):#整值替换
        """替换并通知。"""
        状态[0]=值#写
        for 回调 in list(监听者):#通知
            回调()#触发
    return {'getSnapshot':取快照,'subscribe':订阅,'update':更新,'set':设置}#面

def 冻结保留源(计数):#冻结保留源计数
    """对齐 freezeRetainedBy。"""
    return dict(计数)#拷贝视图

class 中止信号:#对齐 AbortSignal
    """可监听的中止信号。"""

    def __init__(自身):#构造
        """未中止。"""
        自身._事件=threading.Event()#事件
        自身._原因=None#原因
        自身._监听=[]#abort 监听

    @property
    def aborted(自身):#是否已中止
        """是否已中止。"""
        return 自身._事件.is_set()#已置位

    @property
    def reason(自身):#中止原因
        """中止原因。"""
        return 自身._原因#原因

    def throwIfAborted(自身):#已中止则抛
        """已中止则抛出原因。"""
        if 自身._事件.is_set():#已中止
            raise 自身._原因 if 自身._原因 is not None else Exception('aborted')#抛

    def addEventListener(自身,类型,回调,选项=None):#加监听
        """只认 abort。"""
        if 类型!='abort':#其它
            return#忽略
        自身._监听.append(回调)#登记
        if 自身._事件.is_set():#已中止
            回调()#立即

    def removeEventListener(自身,类型,回调):#移除监听
        """移除 abort 监听。"""
        if 类型!='abort':#其它
            return#忽略
        try:#可能不在
            自身._监听.remove(回调)#移除
        except ValueError:#不在
            pass#忽略

    def 中止(自身,原因=None):#中止
        """置位并通知。"""
        if 自身._事件.is_set():#已中止
            return#幂等
        自身._原因=原因#原因
        自身._事件.set()#置位
        for 回调 in list(自身._监听):#通知
            回调()#触发

class 中止控制器:#对齐 AbortController
    """中止控制器。"""

    def __init__(自身):#构造
        """新建信号。"""
        自身.signal=中止信号()#信号

    def abort(自身,原因=None):#中止
        """中止信号。"""
        自身.signal.中止(原因)#中止

def 合并中止信号(信号列表):#对齐 AbortSignal.any
    """任一中止则合成信号中止。"""
    合成=中止信号()#合成
    def 转发():#转发
        """把先到的原因带到合成信号。"""
        for 信号 in 信号列表:#找已中止
            if 信号.aborted:#命中
                合成.中止(信号.reason)#转发
                return#结束
    for 信号 in 信号列表:#订各源
        信号.addEventListener('abort',转发,{'once':True})#一次
        if 信号.aborted:#已中止
            转发()#立即
            break#结束
    return 合成#合成

class 解析器:#对齐 Promise.withResolvers
    """一次结算的解析器。"""

    def __init__(自身):#构造
        """未决。"""
        自身._完成=threading.Event()#完成
        自身._结果=None#结果
        自身._错误=None#错误
        自身._已定=False#是否已定
        自身.promise=自身#自身可等待

    def resolve(自身,值=None):#成功
        """兑现。"""
        if 自身._已定:#已定
            return#忽略
        自身._已定=True#标记
        自身._结果=值#结果
        自身._完成.set()#放行

    def reject(自身,错误):#失败
        """拒绝。"""
        if 自身._已定:#已定
            return#忽略
        自身._已定=True#标记
        自身._错误=错误#错误
        自身._完成.set()#放行

    def 等待(自身):#等待结算
        """阻塞至结算；失败则抛。"""
        自身._完成.wait()#等
        if 自身._错误 is not None:#失败
            raise 自身._错误#抛
        return 自身._结果#结果

    def 吞未处理(自身):#吞拒绝
        """对齐 void promise.catch(() => {})。"""
        def 后台():#后台等
            """吞异常。"""
            try:#等
                自身.等待()#等待
            except Exception:#吞
                pass#忽略
        threading.Thread(target=后台,daemon=True).start()#后台

def 等待打开(打开,信号=None):#等待打开
    """带可选中止的打开等待。"""
    if 信号 is None:#无信号
        打开.等待()#直接等
        return#结束
    if 信号.aborted:#已中止
        raise 信号.reason if 信号.reason is not None else Exception('aborted')#抛
    中止解析=解析器()#中止侧
    def 于中止():#中止回调
        """拒绝中止侧。"""
        中止解析.reject(信号.reason if 信号.reason is not None else Exception('aborted'))#拒绝
    信号.addEventListener('abort',于中止,{'once':True})#听一次
    try:#竞态
        if 信号.aborted:#再查
            于中止()#拒绝
        打开完成=解析器()#打开侧
        def 跑打开():#跑打开
            """兑现或拒绝打开侧。"""
            try:#等打开
                打开.等待()#等待
                打开完成.resolve()#成功
            except Exception as 错误:#失败
                打开完成.reject(错误)#拒绝
        threading.Thread(target=跑打开,daemon=True).start()#后台打开
        while not 打开完成._完成.is_set() and not 中止解析._完成.is_set():#竞态
            打开完成._完成.wait(0.05)#短等
            if 中止解析._完成.is_set():#中止先到
                break#结束
        if 中止解析._完成.is_set() and not 打开完成._完成.is_set():#中止赢
            中止解析.等待()#抛中止
        打开完成.等待()#抛打开结果
    finally:#清理
        信号.removeEventListener('abort',于中止)#移除

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
        raise Exception(f'test session "{自身.sessionId}": prompt is not stubbed — supply it on the fixture\'s session face')#英文诊断

    def beginSubmission(自身):#开始提交
        """最小本地回声登记。"""
        自身._submissionSeq+=1#序号
        return {'requestId':f'test-submission-{自身._submissionSeq}','abandon':lambda:None}#句柄

    def readAttachment(自身,_附件标识):#未桩读附件
        """响亮失败桩。"""
        raise Exception(f'test session "{自身.sessionId}": readAttachment is not stubbed — supply it on the fixture\'s session face')#英文诊断

    def updateQueue(自身,*_参数,**_关键字):#未桩更新队列
        """响亮失败桩。"""
        raise Exception(f'test session "{自身.sessionId}": updateQueue is not stubbed — supply it on the fixture\'s session face')#英文诊断

    def cancel(自身,*_参数,**_关键字):#未桩取消
        """响亮失败桩。"""
        raise Exception(f'test session "{自身.sessionId}": cancel is not stubbed — supply it on the fixture\'s session face')#英文诊断

    def command(自身,*_参数,**_关键字):#未桩命令
        """响亮失败桩。"""
        raise Exception(f'test session "{自身.sessionId}": command is not stubbed — supply it on the fixture\'s session face')#英文诊断

    def loadOlder(自身,*_参数,**_关键字):#未桩加载更旧
        """响亮失败桩。"""
        raise Exception(f'test session "{自身.sessionId}": loadOlder is not stubbed — supply it on the fixture\'s session face')#英文诊断

    def loadThrough(自身,*_参数,**_关键字):#未桩加载至
        """响亮失败桩。"""
        raise Exception(f'test session "{自身.sessionId}": loadThrough is not stubbed — supply it on the fixture\'s session face')#英文诊断

    def rename(自身,*_参数,**_关键字):#未桩重命名
        """响亮失败桩。"""
        raise Exception(f'test session "{自身.sessionId}": rename is not stubbed — supply it on the fixture\'s session face')#英文诊断

class 测试会话引用:#测试会话引用
    """对齐 TestSessionReference。"""

    def __init__(自身,会话标识,世代,释放回调):#构造
        """记下身份、世代与释放回调。"""
        自身.sessionId=会话标识#会话 id
        自身._世代=世代#世代
        自身._释放回调=释放回调#释放回调
        自身._已释放=中止控制器()#释放控制器
        自身._就绪=解析器()#就绪
        自身.ready=自身._就绪#就绪面
        自身._就绪.吞未处理()#吞未处理拒绝

    @property
    def binding(自身):#读绑定
        """活引用才有绑定。"""
        if 自身._世代 is None or not 自身._世代['live']:#已释放
            raise Exception(f'Session reference "{自身.sessionId}" is released')#英文诊断
        return 自身._世代['binding']#返回绑定

    def attachOpening(自身,打开,信号=None):#附着打开
        """打开就绪后解析 binding。"""
        等待信号=自身._已释放.signal if 信号 is None else 合并中止信号([自身._已释放.signal,信号])#合成
        def 跑():#跑等待
            """成功解析或拒绝就绪。"""
            try:#等待打开
                等待打开(打开,等待信号)#等待
                等待信号.throwIfAborted()#检查中止
                自身._就绪.resolve(自身.binding)#解析绑定
            except Exception as 错误:#失败
                自身._就绪.reject(错误)#拒绝
        threading.Thread(target=跑,daemon=True).start()#后台

    def release(自身):#释放
        """释放引用。"""
        原因=Exception(f'Session reference "{自身.sessionId}" is released')#原因
        回调=自身._释放回调#回调
        自身._已释放.abort(原因)#中止
        自身._就绪.reject(原因)#拒绝就绪
        自身._世代=None#清空世代
        自身._释放回调=None#清空回调
        if 回调 is not None:#有回调
            回调()#调用释放

    def __enter__(自身):#进入
        """支持 with。"""
        return 自身#自身

    def __exit__(自身,*_参数):#退出
        """释放。"""
        自身.release()#释放
        return False#不吞

class 测试会话:#会话测试替身
    """Sessions 测试替身：目录可观察、经生产 createScope 铸造作用域、稳定 Controller 绑定。"""

    def __init__(自身,稳定,根上下文):#构造
        """记下稳定器与根上下文。"""
        自身._stabilize=稳定#稳定器
        自身._rootCtx=根上下文#根上下文
        自身.list=创建快照存储({#初始列表
            'ids':[],'byId':{},'phase':'ready',#空列表就绪
            'subagentsByParent':{},'jobsBySession':{},#子智能体空
        })#初始列表
        自身._records={}#fixture 记录
        自身._generations={}#活世代
        自身._addresses={}#地址
        自身._retentionStores={}#保留 store
        自身._pendingDrops=set()#待拆除
        自身._closed=False#是否关闭
        自身.calls=[]#调用记录
        自身.searchResultLimit=会话搜索结果上限#搜索结果上限
        自身._searchStub=None#搜索桩
        自身._createStub=None#创建桩
        def 根拆除登记():#根拆除
            """Client 世代随根拆除。"""
            def 拆除():#拆除体
                """关闭并拆世代。"""
                自身._closed=True#关闭
                for 标识,世代 in list(自身._generations.items()):#逐世代
                    世代['live']=False#死
                    世代['retention']=dict(空保留信息)#清空保留
                    世代['lifetime'].abort(Exception('test Session Controller is disposed'))#中止寿命
                    自身._发布保留(标识)#发布
                自身._generations.clear()#清世代
                自身._排空拆除()#排空拆除
            return 拆除#拆除器
        根上下文.副作用(根拆除登记,'test sessions: Client generations')#挂根拆除

    def add(自身,夹具):#添加 fixture
        """从 fixture 添加会话。"""
        标识=夹具['id']#会话 id
        if 标识 in 自身._records:#重复
            raise Exception(f'test session "{标识}" already added')#重复
        摘要={#列表行
            'id':标识,'displayTitle':夹具['id'],'running':False,'blank':False,
            'updatedAt':len(自身._records)+1,**(夹具.get('summary') or {}),
            'retainedBy':自身._保留快照(标识)['retainedBy'],#保留源
        }#列表行
        快照=创建快照存储({**会话快照(标识),**(夹具.get('snapshot') or {})})#快照 store
        会话=夹具会话(标识,快照,夹具.get('session') or {})#会话面
        if 夹具.get('events') is not None or 夹具.get('hasMore') is True:#有事件窗
            会话.eventSource.replace(夹具.get('events') or [],夹具.get('hasMore') or False)#初始事件窗
        自身._records[标识]={#写记录
            'summary':摘要,#摘要
            'snapshot':快照,#快照
            'session':会话,#会话面
            'overrides':夹具.get('session') or {},#覆盖
            'projections':{},#投影
            'initialOpen':夹具.get('initialOpen'),#初始打开
        }#记录结束
        def 写列表():#act 内更新列表
            """写列表。"""
            def 变换(草稿):#写
                """追加。"""
                草稿['ids'].append(标识)#追加 id
                草稿['byId'][标识]=摘要#写行
            自身.list['update'](变换)#更新
        自身._stabilize(写列表)#稳定内更新
        return 标识#返回 id

    def updateSessionSnapshot(自身,标识,变换):#更新会话快照
        """经草稿更新生命周期状态。"""
        记录=自身._要求(标识)#取记录
        def 写():#act 内
            """更新 fixture 与世代。"""
            记录['snapshot']['update'](变换)#更新 fixture
            世代=自身._generations.get(标识)#世代
            if 世代 is not None:#有世代
                世代['snapshot']['set'](记录['snapshot']['getSnapshot']())#同步世代
        自身._stabilize(写)#稳定内

    def setProjection(自身,标识,键,值):#写投影
        """写投影到 fixture 与活世代。"""
        记录=自身._要求(标识)#取记录
        记录['projections'][键]=值#记缓存
        def 写():#act 内
            """写面。"""
            记录['session'].projections['set'](键,值)#写 fixture 面
            世代=自身._generations.get(标识)#世代
            if 世代 is not None:#有世代
                世代['session'].projections['set'](键,值)#写世代面
        自身._stabilize(写)#稳定内

    def replaceEvents(自身,标识,条目,有更多=False):#替换事件窗
        """替换完整连续事件窗口。"""
        def 写():#act 内
            """替换。"""
            自身._要求(标识)['session'].eventSource.replace(条目,有更多)#fixture
            世代=自身._generations.get(标识)#世代
            if 世代 is not None:#有世代
                世代['session'].eventSource.replace(条目,有更多)#世代
        自身._stabilize(写)#稳定内

    def prependEvents(自身,标识,条目,有更多=False):#前置事件
        """前置一页更旧事件。"""
        def 写():#act 内
            """前置。"""
            自身._要求(标识)['session'].eventSource.prepend(条目,有更多)#fixture
            世代=自身._generations.get(标识)#世代
            if 世代 is not None:#有世代
                世代['session'].eventSource.prepend(条目,有更多)#世代
        自身._stabilize(写)#稳定内

    def appendEvent(自身,标识,条目):#追加事件
        """追加一条活事件。"""
        def 写():#act 内
            """追加。"""
            自身._要求(标识)['session'].eventSource.append(条目)#fixture
            世代=自身._generations.get(标识)#世代
            if 世代 is not None:#有世代
                世代['session'].eventSource.append(条目)#世代
        自身._stabilize(写)#稳定内

    def updateSummary(自身,标识,补丁):#更新摘要
        """更新会话列表行。"""
        记录=自身._要求(标识)#取记录
        记录['summary']={#合并
            **记录['summary'],**补丁,#旧+补丁
            'retainedBy':自身._保留快照(标识)['retainedBy'],#保留源
        }#摘要结束
        def 写():#写列表
            """写行。"""
            自身.list['update'](lambda 草稿:草稿['byId'].__setitem__(标识,记录['summary']))#写行
        自身._stabilize(写)#稳定内写

    def remove(自身,标识):#移除目录行
        """移除会话目录行。"""
        自身._要求(标识)#校验
        del 自身._records[标识]#删记录
        def 拆除():#act 内
            """写列表并标记世代移除。"""
            def 变换(草稿):#写列表
                """去 id 与行。"""
                草稿['ids']=[已有 for 已有 in 草稿['ids'] if 已有!=标识]#去 id
                草稿['byId']={键:值 for 键,值 in 草稿['byId'].items() if 键!=标识}#去行
            自身.list['update'](变换)#更新
            世代=自身._generations.get(标识)#世代
            if 世代 is not None:#有世代
                世代['snapshot']['update'](lambda 草稿:草稿.__setitem__('removed',True))#标记移除
        自身._stabilize(拆除)#稳定内拆除

    def scope(自身,标识):#借作用域
        """活引用才有作用域。"""
        世代=自身._generations.get(标识)#世代
        return None if 世代 is None else 世代['binding']['ctx']#上下文

    def binding(自身,标识):#取绑定
        """活引用才有绑定。"""
        世代=自身._generations.get(标识)#世代
        return None if 世代 is None else 世代['binding']#绑定

    def retain(自身,目标,选项=None):#保留
        """保留会话引用。"""
        if 选项 is None:#缺省
            选项={'source':'testFixture'}#默认源
        源=选项['source'] if 'source' in 选项 else 'testFixture'#源
        信号=选项['signal'] if 'signal' in 选项 else None#信号
        if 信号 is not None:#有信号
            信号.throwIfAborted()#已取消则抛
        if 自身._closed:#已关闭
            raise Exception('test Session Controller is disposed')#英文诊断
        标识=自身._解析目标(目标)#解析 id
        世代=自身._generations.get(标识)#取世代
        if 世代 is None:#未物化
            世代=自身._物化(标识,自身._要求(标识))#物化
        引用=自身._加世代引用(标识,世代,源)#加引用
        try:#附着打开
            引用.attachOpening(世代['opening'],信号)#附着
            return 引用#返回
        except Exception:#失败
            引用.release()#释放
            raise#再抛

    def using(自身,目标,选项,操作):#借用
        """保留、等就绪、操作、释放。"""
        引用=自身.retain(目标,选项)#保留
        try:#运行
            引用.ready.等待()#等就绪
            return 操作(引用)#操作
        finally:#释放
            引用.release()#释放

    def retainInfo(自身,标识):#保留信息
        """可观察保留信息。"""
        存储=自身._retentionStores.get(标识)#取 store
        if 存储 is None:#未建
            存储=创建快照存储(自身._保留快照(标识))#新建
            自身._retentionStores[标识]=存储#缓存
        return 存储#返回

    def retainFor(自身,所有者上下文,目标,选项=None):#为所有者保留
        """保留并把释放挂到所有者拆除。"""
        if 选项 is None:#缺省
            选项={'source':'testFixture'}#默认源
        引用=自身.retain(目标,选项)#保留
        try:#挂拆除
            def 登记():#登记拆除
                """所有者拆除时释放引用。"""
                return 引用.release#拆除器
            所有者上下文.副作用(登记,'test sessions: owned reference')#挂
            return 引用#返回
        except Exception:#失败
            引用.release()#释放
            raise#再抛

    def scopeOf(自身,上下文):#读作用域标签
        """从上下文读会话作用域标签。"""
        return 作用域标签(上下文)#委托生产

    def sessionOf(自身,上下文):#解析会话面
        """从上下文解析作用域会话面。"""
        标识=作用域标签(上下文)#读标签
        if 标识 is None:#根上下文
            return None#无
        世代=自身._generations.get(标识)#取世代
        if 世代 is None:#无世代
            return None#无
        if 作用域标签(世代['binding']['ctx'])!=作用域标签(上下文):#身份不匹配
            return None#无
        return 世代['session']#返回面

    def stubCreate(自身,实现):#安装创建桩
        """为导航测试安装 Session 创建行为。"""
        自身._createStub=实现#写入

    def create(自身,选项=None):#创建会话
        """经已安装测试行为创建。"""
        自身.calls.append({'method':'create','args':[选项]})#记录
        if 自身._createStub is None:#未桩
            raise Exception('test sessions: create is not stubbed — call stubCreate() first')#英文诊断
        标识=自身._createStub(选项)#走桩
        自身._要求(标识)#要求可寻址
        return 标识#返回

    def subagentAddress(自身,标识):#取子智能体地址
        """解析保留地址或扫目录。"""
        保留=自身._addresses.get(标识)#保留地址
        if 保留 is not None:#命中
            return 保留#返回
        快照=自身.list['getSnapshot']()#列表态
        for 父标识,目录 in 快照['subagentsByParent'].items():#扫目录
            for 条目 in 目录.get('entries',()) if isinstance(目录,dict) else ():#找子
                种类=条目['kind'] if isinstance(条目,dict) and 'kind' in 条目 else None#种类
                子标识=条目['id'] if isinstance(条目,dict) and 'id' in 条目 else None#子 id
                if 种类=='child' and 子标识==标识:#命中
                    模式=条目['mode'] if 'mode' in 条目 else None#模式
                    return {'parentSessionId':父标识,'childSessionId':标识,'mode':模式}#地址
        return None#无

    def setSubagentCatalogOpen(自身,父会话标识,打开):#设置目录开合
        """记录目录消费。"""
        自身.calls.append({'method':'setSubagentCatalogOpen','args':[父会话标识,打开]})#记录

    def refreshSubagents(自身,父会话标识):#刷新子智能体
        """记录目录刷新。"""
        自身.calls.append({'method':'refreshSubagents','args':[父会话标识]})#记录

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
        """世代面或目录 fixture 面。"""
        世代=自身._generations.get(标识)#世代
        return 世代['session'] if 世代 is not None else 自身._要求(标识)['session']#返回

    def disposeScopes(自身):#拆除作用域
        """关闭并拆全部世代。"""
        自身._closed=True#关闭
        for 标识,世代 in list(自身._generations.items()):#逐个
            自身._丢弃(标识,世代)#drop
        自身._排空拆除()#排空

    def _解析目标(自身,目标):#解析目标
        """字符串或地址目标。"""
        if isinstance(目标,str):#字符串
            标识=目标#id
        else:#地址
            标识=目标['childSessionId'] if isinstance(目标,dict) else 目标.childSessionId#子 id
            自身._addresses[标识]=目标#记地址
        自身._要求(标识)#校验目录
        return 标识#返回

    def _加世代引用(自身,标识,世代,源):#加世代引用
        """增加引用计数并返回引用。"""
        旧=世代['retention']#旧保留
        旧源=dict(旧['retainedBy'])#旧源
        旧源[源]=(旧源[源] if 源 in 旧源 else 0)+1#加源
        世代['retention']={'referenceCount':旧['referenceCount']+1,'retainedBy':冻结保留源(旧源)}#新保留
        def 释放回调():#释放回调
            """减引用；零则 drop。"""
            if not 世代['live']:#已死
                return#结束
            计数=世代['retention']['referenceCount']-1#减一
            源表=dict(世代['retention']['retainedBy'])#拆源
            源计数=源表.pop(源,0)#该源
            if 源计数>1:#仍有该源
                源表[源]=源计数-1#减源
            世代['retention']=dict(空保留信息) if 计数==0 else {'referenceCount':计数,'retainedBy':冻结保留源(源表)}#更新
            if 计数==0:#无引用
                自身._丢弃(标识,世代)#drop
            else:#否则发布
                自身._发布保留(标识)#发布
        引用=测试会话引用(标识,世代,释放回调)#引用
        自身._发布保留(标识)#发布
        return 引用#返回

    def _保留快照(自身,标识):#取保留快照
        """世代保留或空。"""
        世代=自身._generations.get(标识)#世代
        return 世代['retention'] if 世代 is not None else dict(空保留信息)#保留

    def _发布保留(自身,标识):#发布保留
        """更新保留 store 与列表行。"""
        保留=自身._保留快照(标识)#当前保留
        存储=自身._retentionStores.get(标识)#store
        if 存储 is not None and 存储['getSnapshot']() is not 保留:#需更新
            存储['set'](保留)#更新 store
        状态=自身.list['getSnapshot']()#列表态
        行=状态['byId'].get(标识)#行
        if 行 is None or 行.get('retainedBy') is 保留['retainedBy']:#无需
            return#结束
        摘要={**行,'retainedBy':保留['retainedBy']}#新摘要
        记录=自身._records.get(标识)#记录
        if 记录 is not None:#有记录
            记录['summary']=摘要#写记录
        自身.list['set']({**状态,'byId':{**状态['byId'],标识:摘要}})#写列表

    def _物化(自身,标识,记录):#物化世代
        """铸造作用域与世代面。"""
        句柄=创建作用域(自身._rootCtx,标识)#铸造作用域
        上下文=句柄['ctx'] if isinstance(句柄,dict) else 句柄.ctx#上下文
        光纤=句柄['fiber'] if isinstance(句柄,dict) else 句柄.fiber#fiber
        快照=创建快照存储(记录['snapshot']['getSnapshot']())#世代快照
        会话=夹具会话(标识,快照,记录['overrides'])#世代面
        窗口=记录['session'].eventSource.getSnapshot()#事件窗
        会话.eventSource.replace(窗口['entries'] if isinstance(窗口,dict) else 窗口.entries,窗口['hasMore'] if isinstance(窗口,dict) else 窗口.hasMore)#拷贝事件
        for 键,值 in 记录['projections'].items():#拷贝投影
            会话.projections['set'](键,值)#写投影
        打开=解析器()#打开控制
        打开.吞未处理()#吞未处理
        寿命=中止控制器()#寿命
        世代={#世代
            'binding':{'sessionId':标识,'session':会话,'eventSource':会话.eventSource,'ctx':上下文},#绑定
            'snapshot':快照,#快照
            'session':会话,#面
            'fiber':光纤,#fiber
            'lifetime':寿命,#寿命
            'opening':打开,#打开
            'retention':dict(空保留信息),#空保留
            'live':True,#活
        }#generation结束
        自身._generations[标识]=世代#登记
        def 作用域拆除登记():#作用域拆除
            """作用域 fiber 拆除时清世代。"""
            def 拆除():#拆除体
                """清登记并中止寿命。"""
                if 世代['live']:#仍活
                    世代['live']=False#死
                    世代['retention']=dict(空保留信息)#清保留
                    if 自身._generations.get(标识) is 世代:#仍是本世代
                        del 自身._generations[标识]#删登记
                    自身._发布保留(标识)#发布
                寿命.abort(Exception(f'test Session generation "{标识}" is disposed'))#中止寿命
                try:#等打开
                    打开.等待()#等
                except Exception:#吞
                    pass#忽略
            return 拆除#拆除器
        上下文.副作用(作用域拆除登记,'test sessions: exact generation')#挂
        自身._启动打开(记录['initialOpen'],寿命.signal,打开)#启动打开
        return 世代#返回

    def _启动打开(自身,初始打开,信号,打开):#启动打开
        """调用 optional initialOpen。"""
        try:#调用
            if 初始打开 is None:#无
                打开.resolve()#立即就绪
                return#结束
            结果=初始打开(信号)#可能同步抛
            if 结果 is None:#同步完成
                打开.resolve()#就绪
            else:#可等待
                def 跑():#跑
                    """等结果。"""
                    try:#等
                        if hasattr(结果,'等待'):#解析器
                            结果.等待()#等
                        打开.resolve()#就绪
                    except Exception as 错误:#失败
                        打开.reject(错误)#拒绝
                threading.Thread(target=跑,daemon=True).start()#后台
        except Exception as 错误:#同步失败
            打开.reject(错误)#拒绝

    def _丢弃(自身,标识,世代):#丢弃世代
        """死世代并拆 fiber。"""
        if not 世代['live']:#已死
            return#结束
        世代['live']=False#死
        世代['retention']=dict(空保留信息)#清保留
        if 自身._generations.get(标识) is 世代:#仍是本世代
            del 自身._generations[标识]#删登记
        世代['lifetime'].abort(Exception(f'test Session generation "{标识}" is released'))#中止
        自身._发布保留(标识)#发布
        光纤=世代['fiber']#fiber
        def 拆():#拆 fiber
            """调用拆除。"""
            if hasattr(光纤,'拆除'):#有拆除
                光纤.拆除()#拆除
            elif callable(光纤):#可调用
                光纤()#拆除
        自身._pendingDrops.add(id(拆))#记待拆除
        try:#拆
            拆()#拆
        except Exception as 错误:#失败
            自身._rootCtx.日志.警告('test Session scope disposal failed:',错误)#警告
        finally:#清
            自身._pendingDrops.discard(id(拆))#删

    def _排空拆除(自身):#排空拆除
        """等到待拆除空。"""
        while len(自身._pendingDrops)!=0:#未空
            threading.Event().wait(0.01)#短睡

    def _要求(自身,标识):#要求已添加
        """要求记录存在。"""
        记录=自身._records.get(标识)#取记录
        if 记录 is None:#缺失
            raise Exception(f'test session "{标识}" is not added')#英文诊断
        return 记录#返回
