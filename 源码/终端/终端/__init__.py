"""按所有者作用域的持久 PTY 注册表。后端负责终端机制，本服务负责 id、发布、授权与等待清理。"""
import threading,weakref#后台清槽与已拆除所有者弱集
from concurrent.futures import Future as _原生Future#单次操作结果
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#服务基类
聚合错误=cordis.聚合错误#搭建与清理双失败聚合
from ...工具.超时 import 中止控制器,合成信号,取已中止,取原因值#取消控制器、合成信号与旗标读取
from .类型 import (
    终端后端清理错误,#搭建清理双失败
    终端会话标识值,#会话id品牌基底
    终端等待原因,#等待原因
    终端信号,#信号
    终端会话状态种类,#会话状态
    终端创建请求字段,#创建请求
    终端后端创建规格字段,#后端规格
    终端发送请求字段,#发送请求
    终端发送增量字段,#发送增量
    终端发送结果字段,#发送结果
    终端发送操作字段,#发送操作
    终端回滚读取请求字段,#回滚请求
    终端回滚读取结果字段,#回滚结果
    终端信号结果字段,#信号结果
    终端会话快照字段,#会话快照
    终端后端会话字段,#后端会话
    终端后端字段,#后端
    终端创建结果字段,#创建结果
)#再导出公开类型

终端错误码=(#稳定失败码
    'DUPLICATE_BACKEND',#重复后端
    'DUPLICATE_NAME',#重复名称
    'FOREIGN_SESSION',#他人会话
    'NO_BACKEND',#无后端
    'NO_SESSION',#无会话
    'OWNER_NOT_LIVE',#所有者不在场
    'SEND_ACTIVE',#已有活动发送
    'SERVICE_DISPOSING',#服务拆除中
)#错误码结束
class 终端错误(Exception):#带稳定错误码的错误
    """携带稳定 TerminalErrorCode 的错误。"""
    def __init__(自身,消息,码):#记下消息与码
        """记下可读消息与稳定码。"""
        super().__init__(消息)#交给Exception
        自身.code=码#稳定失败码
        自身.码=码#中文别名
        自身.name='TerminalError'#固定类名

def 终端会话标识(值):#把注册表签发的字符串打成会话身份
    """把注册表签发的字符串打成 TerminalSessionId。"""
    return 值#打上品牌（运行时即原字符串）

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

class 操作任务:#单次异步结果
    def __init__(自身):#构造未决任务
        自身._future=_原生Future()#底层 Future
    def 兑现(自身,值=None):#成功结算
        if not 自身._future.done():#尚未结算
            自身._future.set_result(值)#写入结果
        return 值#返回兑现值
    def 拒绝(自身,错误):#失败结算
        if not 自身._future.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._future.set_exception(错误)#原样拒绝
            else:#非异常
                自身._future.set_exception(Exception(错误))#包装拒绝
    def wait(自身,超时=None):#阻塞等待
        return 自身._future.result(timeout=超时)#取结果或抛错
    def 等待(自身,超时=None):#兼容外来调用
        return 自身.wait(超时)#转发

def _是否thenable(值):#判定可等待对象
    if 值 is None:#空不是
        return False#不是
    if callable(getattr(值,'wait',None)):#Future 风格
        return True#可等待
    return callable(getattr(值,'等待',None))#外来 thenable

def _等待(值):#统一阻塞到结算
    if callable(getattr(值,'wait',None)):#Future 风格
        return 值.wait()#等待
    return 值.等待()#外来 thenable

def 解开(值):#可等待则等待否则原样
    """可等待则等待，否则原样返回。"""
    if _是否thenable(值):#可等待
        return _等待(值)#等待
    return 值#同步值

def 若已中止则抛出(信号):#已取消则抛出精确原因
    """对齐 AbortSignal.throwIfAborted：有方法则调；否则按旗标抛出原因。"""
    if 信号 is None:#无信号
        return#放过
    方法=getattr(信号,'throwIfAborted',None)#英文API
    if callable(方法):#有方法
        方法()#抛出
        return#已检查
    方法中=getattr(信号,'抛若中止',None)#中文API
    if callable(方法中):#有中文方法
        方法中()#抛出
        return#已检查
    if not 取已中止(信号):#未中止
        return#放过
    原因=取原因值(信号)#取出原因
    if isinstance(原因,BaseException):#原因本就是异常
        raise 原因#原样抛出
    if 原因 is not None:#非异常原因
        raise Exception(str(原因))#包成异常
    错误=Exception('This operation was aborted')#缺省中止文案
    错误.name='AbortError'#固定AbortError名
    raise 错误#抛出

def 调后端方法(会话,英文名,中文名,*位置参数):#优先英文入口否则中文
    """调用后端会话方法，兼容中英文方法名。"""
    方法=getattr(会话,英文名,None)#英文入口
    if callable(方法):#有英文
        return 方法(*位置参数)#调用
    方法中=getattr(会话,中文名,None)#中文入口
    if callable(方法中):#有中文
        return 方法中(*位置参数)#调用
    raise AttributeError(英文名)#两边都没有

def 后台清发送槽(记录,操作):#发送结束后清掉活动槽
    """对齐 void operation.done.then(清,清)：成败都清槽。"""
    def 盯():#后台等到结算
        """等到发送结算后清槽。"""
        try:#等待结算
            解开(取字段(操作,'done'))#等done
        except BaseException:#失败也算结算
            pass#吸收，只为清槽
        if 取字段(记录,'active') is 操作:#仍是这次发送才清
            记录['active']=None#清活动发送
    工作=threading.Thread(target=盯)#后台线程
    工作.daemon=True#不挡住退出
    工作.start()#立刻开跑

class 终端会话服务(服务):#可替换PTY后端与精确智能体会话的进程内注册表
    """可替换 PTY 后端与精确智能体会话的进程内注册表。注册为 `ctx.terminals`。"""
    def __init__(自身,ctx):#注册为terminals服务
        """以 terminals 名注册服务，并在作用域拆除时清理全部 PTY。"""
        super().__init__(ctx,'terminals')#绑定服务名
        自身.backends={}#按类型登记后端
        自身.后端们=自身.backends#中文别名
        自身.sessions={}#已发布会话
        自身.会话们=自身.sessions#中文别名
        自身.reservedNames={}#正在占用的显示名：所有者→名集合
        自身.预留名表=自身.reservedNames#中文别名
        自身.pendingSpawns={}#未发布搭建：所有者→搭建列表
        自身.未发布搭建表=自身.pendingSpawns#中文别名
        自身.ownerCleanups={}#所有者拆除器
        自身.所有者清理=自身.ownerCleanups#中文别名
        自身.disposedOwners=weakref.WeakSet()#已拆除的所有者
        自身.已拆所有者=自身.disposedOwners#中文别名
        自身.nextId=0#下一个会话序号
        自身.下一序号=0#中文别名
        自身.disposing=False#是否正在拆除服务
        自身.拆除中=False#中文别名
        def 拆除体():#作用域拆除时清理全部PTY
            """登记服务拆除。"""
            def 拆除():#服务拆除回调
                """清理全部 PTY。"""
                return 自身.拆除全部()#可能返回可等待
            return 拆除#返回拆除器
        ctx.effect(拆除体,'pty teardown')#作用域拆除时清理全部PTY

    def 登记后端(自身,后端):#在本effect作用域登记一种后端类型
        """在本 effect 作用域登记一种后端类型。类型非空且唯一；返回只撤掉这一次贡献的 disposer。"""
        类型=取字段(后端,'type')#后端类型名
        if 类型 is None or len(类型)==0:#拒绝空类型
            raise Exception('pty backend type must be non-empty')#拒绝空类型
        if 类型 in 自身.backends:#类型已占用
            raise 终端错误('a PTY backend named "'+str(类型)+'" is already registered','DUPLICATE_BACKEND')#拒绝重复后端
        def 挂上():#按effect登记
            """写入注册表并在拆除时删除。"""
            自身.backends[类型]=后端#写入注册表
            def 撤贡献():#撤贡献
                """仍是自己才删。"""
                if 自身.backends.get(类型) is 后端:#仍是自己才删
                    自身.backends.pop(类型,None)#删除
            return 撤贡献#撤贡献结束
        释放=自身.ctx.effect(挂上,'pty.registerBackend()')#effect名
        def 同步拆除():#对外disposer
            """丢掉 effect 返回值的同步拆除。"""
            释放()#拆除
        return 同步拆除#对外disposer

    def 列出后端(自身):#按登记顺序列出已注册后端类型
        """按登记顺序列出已注册后端类型，返回新的类型名数组。"""
        return list(自身.backends.keys())#按插入序复制

    def 搭建(自身,所有者,请求,信号=None):#搭建并发布会话
        """后端搭建成功后创建并发布一次按所有者作用域的会话。"""
        自身.断言可用()#服务拆除中则拒绝
        若已中止则抛出(信号)#已经取消则失败
        自身.确保所有者清理(所有者)#确保所有者拆除钩子
        类型=取字段(请求,'type')#后端类型
        后端=自身.backends.get(类型)#按类型取后端
        if 后端 is None:#无后端
            raise 终端错误('no PTY backend registered for "'+str(类型)+'"','NO_BACKEND')#无后端
        名称=取字段(请求,'name')#可选显示名
        if 名称 is not None and len(名称)==0:#拒绝空名
            raise Exception('PTY session name must be non-empty')#拒绝空名
        释放名=自身.预留名称(所有者,名称)#预留显示名
        搭建预留=自身.预留搭建(所有者)#预留未发布搭建
        if 信号 is None:#调用方未给取消时
            后端信号=搭建预留['signal']#只用预留取消
        else:#与预留取消合成
            后端信号=合成信号(信号,搭建预留['signal'])#AbortSignal.any
        自身.nextId=自身.nextId+1#递增序号
        自身.下一序号=自身.nextId#同步中文别名
        会话标识=终端会话标识('pty-'+str(自身.nextId))#签发会话id
        会话=None#后端会话
        清理失败=None#清理失败
        try:#搭建并发布
            规格={#交给后端的规格
                'sessionId':会话标识,#会话id
                'owner':所有者,#所有者
                'type':类型,#后端类型
                'signal':后端信号,#搭建取消
            }#规格骨架
            if 名称 is not None:#有名则带上
                规格['name']=名称#显示名
            工作目录=取字段(请求,'cwd')#可选工作目录
            if 工作目录 is not None:#有cwd则带上
                规格['cwd']=工作目录#工作目录
            搭建入口=取字段(后端,'spawn')#后端创建入口
            if 搭建入口 is None:#中文入口
                搭建入口=取字段(后端,'搭建')#中文搭建
            会话=解开(搭建入口(规格))#交给后端搭建
            若已中止则抛出(信号)#搭建后再次检查取消
            if 自身.disposing:#服务已开始拆除
                raise 终端错误('PTY service is disposing','SERVICE_DISPOSING')#拒绝发布
            if not 自身.是否在场所有者(所有者):#所有者已不在场
                raise 终端错误('PTY owner is no longer live','OWNER_NOT_LIVE')#拒绝发布
            记录={#已发布记录
                'id':会话标识,#会话id
                'owner':所有者,#所有者
                'name':名称,#显示名
                'type':类型,#后端类型
                'session':会话,#后端会话
                'active':None,#尚无发送
                'closing':None,#尚未关闭
            }#记录结束
            自身.sessions[会话标识]=记录#发布到注册表
            return 自身.快照(记录,取字段(会话,'motd'))#返回带开机信息的快照
        except BaseException as 错误:#搭建失败则回滚
            if isinstance(错误,终端后端清理错误):#后端已报告清理失败
                清理失败={'error':错误.cleanupError}#记下清理失败
            回滚失败=None#回滚失败
            if 会话 is not None and 会话标识 not in 自身.sessions:#已有会话但未发布
                try:#关闭未发布会话
                    解开(调后端方法(会话,'close','关闭','PTY spawn rolled back'))#按回滚关闭
                except BaseException as 关闭错误:#关闭失败
                    回滚失败={'error':关闭错误}#记下回滚失败
                    清理失败=回滚失败#清理失败就是回滚失败
            失败=错误#默认抛原始失败
            try:#取消优先于原始失败
                若已中止则抛出(信号)#调用方取消
                若已中止则抛出(搭建预留['signal'])#预留取消
            except BaseException as 取消错误:#发生了取消
                失败=取消错误#改抛取消
            if 回滚失败 is not None and not 取已中止(信号):#回滚失败且不是调用方取消
                raise 聚合错误([失败,回滚失败['error']],'PTY spawn and rollback both failed')#搭建与回滚双失败
            raise 失败#抛出选定失败
        finally:#无论成败都释放预留
            搭建预留['release'](清理失败)#释放搭建预留
            释放名()#释放显示名

    def 有所有者活动(自身,所有者):#所有者是否有PTY活动
        """测试精确所有者是否有已发布会话或未发布搭建；从搭建到关闭整段为真。"""
        未发布=自身.pendingSpawns.get(所有者)#未发布搭建列表
        if 未发布 is not None and len(未发布)>0:#有未发布搭建
            return True#有活动
        for 记录 in 自身.sessions.values():#扫已发布会话
            if 取字段(记录,'owner') is 所有者:#本所有者
                return True#有活动
        return False#无活动

    def 开始发送(自身,所有者,标识,请求):#开始一次互斥的交互发送
        """开始一次互斥的交互发送，返回可供前台等待或登记任务的在场操作句柄。"""
        记录=自身.期望已拥有(所有者,标识)#校验所有权
        if 取字段(记录,'closing') is not None:#关闭中拒绝
            raise Exception('PTY session '+str(标识)+' is closing')#关闭中拒绝
        if 取字段(记录,'active') is not None:#已有发送
            raise 终端错误('PTY session '+str(标识)+' already has an active send','SEND_ACTIVE')#已有发送
        操作=调后端方法(取字段(记录,'session'),'startSend','开始发送',请求)#交给后端
        记录['active']=操作#记下活动发送
        后台清发送槽(记录,操作)#结束后清槽
        return 操作#返回操作句柄

    def 读取(自身,所有者,标识,请求=None):#读取一页有界回滚
        """从一次已拥有会话读取一页有界回滚。"""
        if 请求 is None:#缺省空请求
            请求={}#空请求
        return 调后端方法(取字段(自身.期望已拥有(所有者,标识),'session'),'read','读取',请求)#校验后交给后端

    def 发信号(自身,所有者,标识,信号名):#经已拥有后端会话投递信号
        """经已拥有的后端会话投递允许的信号，返回投递到的前台进程组身份。"""
        return 解开(调后端方法(取字段(自身.期望已拥有(所有者,标识),'session'),'signal','发信号',信号名))#校验后交给后端

    def 关闭(自身,所有者,标识,原因='model request'):#关闭一次已拥有会话
        """关闭一次已拥有会话，仅在后端清理静止后移除；新关闭为真，同一关闭已在进行中为假。"""
        记录=自身.期望已拥有(所有者,标识)#校验所有权
        已在关=取字段(记录,'closing')#已有关闭在飞
        if 已在关 is not None:#已有关闭在飞
            解开(已在关)#等这次关闭
            return False#不是新关闭
        正在关=调后端方法(取字段(记录,'session'),'close','关闭',原因)#启动后端关闭
        记录['closing']=正在关#钉上关闭栅栏
        try:#等待关闭
            解开(正在关)#等后端静止
            自身.sessions.pop(标识,None)#从注册表移除
            return True#新关闭
        except BaseException:#关闭失败
            记录['closing']=None#清掉失败栅栏
            raise#原样抛出

    def 列出(自身,所有者):#列出恰好一个所有者的新快照
        """列出恰好一个所有者的新快照，按发布顺序。"""
        结果=[]#快照列表
        for 记录 in 自身.sessions.values():#按发布序
            if 取字段(记录,'owner') is 所有者:#只留本所有者
                结果.append(自身.快照(记录))#做成快照
        return 结果#所有者可见快照

    def 断言可用(自身):#服务须仍可用
        """服务拆除中则拒绝。"""
        if 自身.disposing:#拆除中
            raise 终端错误('PTY service is disposing','SERVICE_DISPOSING')#拆除中拒绝

    def 是否在场所有者(自身,所有者):#所有者是否仍在场
        """未拆除且注册表仍是这个实例。"""
        if 所有者 in 自身.disposedOwners:#已拆除
            return False#不在场
        智能体们=自身.ctx.get('agents')#智能体注册表
        if 智能体们 is None:#没有注册表
            return False#不在场
        取=getattr(智能体们,'get',None)#英文get
        if 取 is None:#中文获取
            取=getattr(智能体们,'获取',None)#中文方法
        if 取 is None:#没有查询入口
            return False#不在场
        return 取(取字段(所有者,'id')) is 所有者#仍是这个实例

    def 确保所有者清理(自身,所有者):#确保所有者拆除钩子
        """经精确所有者的作用域挂接一次被等待的清理。"""
        if not 自身.是否在场所有者(所有者):#不在场
            raise 终端错误('agent "'+str(取字段(所有者,'id'))+'" is not the registered PTY owner','OWNER_NOT_LIVE')#拒绝
        if 所有者 in 自身.ownerCleanups:#已挂过
            return#不必再挂
        def 执行体():#所有者作用域拆除时
            """挂接所有者清理。"""
            def 拆除():#所有者拆除回调
                """清掉其 PTY。"""
                自身.disposedOwners.add(所有者)#标记已拆除
                自身.ownerCleanups.pop(所有者,None)#摘掉拆除器
                return 自身.拆除所属(所有者)#清掉其PTY
            return 拆除#返回拆除器
        拆下=所有者.ctx.effect(执行体,'pty.ownerCleanup()')#effect名
        自身.ownerCleanups[所有者]=拆下#记住拆除器

    def 预留名称(自身,所有者,名称):#预留显示名
        """预留所有者本地显示名；无名则返回空释放。"""
        if 名称 is None:#无名则无需释放
            return lambda: None#空释放
        for 记录 in 自身.sessions.values():#已发布重名
            if 取字段(记录,'owner') is 所有者 and 取字段(记录,'name')==名称:#已发布重名
                raise 终端错误('PTY session name "'+str(名称)+'" already exists for this owner','DUPLICATE_NAME')#拒绝
        已预留=自身.reservedNames.get(所有者)#该所有者的预留集
        if 已预留 is None:#尚无集合
            已预留=set()#新建
            自身.reservedNames[所有者]=已预留#写回预留表
        if 名称 in 已预留:#正在创建中
            raise 终端错误('PTY session name "'+str(名称)+'" is already being created','DUPLICATE_NAME')#拒绝
        已预留.add(名称)#占用此名
        def 释放():#释放名
            """去掉此名；空了则摘所有者。"""
            已预留.discard(名称)#去掉此名
            if len(已预留)==0:#空了
                自身.reservedNames.pop(所有者,None)#摘所有者
        return 释放#释放结束

    def 预留搭建(自身,所有者):#预留一次未发布搭建
        """预留一次未发布搭建，返回取消信号与释放句柄。"""
        控制器=中止控制器()#预留取消器
        结算=操作任务()#结算器
        未发布={#未发布记录
            'owner':所有者,#所有者
            'controller':控制器,#取消控制器
            'settled':结算,#结算承诺
            'cleanupFailure':None,#可选清理失败
        }#记录结束
        已有=自身.pendingSpawns.get(所有者)#该所有者的搭建列表
        if 已有 is None:#尚无列表
            已有=[]#新建
            自身.pendingSpawns[所有者]=已有#写回
        已有.append(未发布)#加入
        def 释放(清理失败):#释放预留
            """记下清理失败；无失败则立刻摘掉；并标记已结算。"""
            未发布['cleanupFailure']=清理失败#记下清理失败
            if 清理失败 is None:#无清理失败则立刻摘掉
                自身.摘掉未发布搭建(未发布)#摘掉
            结算.兑现(None)#标记已结算
        return {#预留句柄
            'signal':控制器.信号,#取消信号
            'release':释放,#释放入口
        }#句柄结束

    def 摘掉未发布搭建(自身,未发布):#从预留列表摘掉一次搭建
        """从预留列表摘掉一次搭建。"""
        已有=自身.pendingSpawns.get(取字段(未发布,'owner'))#该所有者的搭建列表
        if 已有 is None:#没有则结束
            return#结束
        try:#去掉这条
            已有.remove(未发布)#去掉
        except ValueError:#已不在列表
            return#结束
        if len(已有)==0:#空了则摘所有者
            自身.pendingSpawns.pop(取字段(未发布,'owner'),None)#摘所有者

    def 取消未发布搭建(自身,所有者,原因):#取消未发布搭建
        """取消指定所有者或全部所有者的未发布搭建，并聚合清理失败。"""
        if 所有者 is None:#不定所有者则全取消
            待取消=[]#摊平全部
            for 列表 in 自身.pendingSpawns.values():#各所有者
                待取消.extend(list(列表))#摊平
        else:#只取该所有者
            待取消=list(自身.pendingSpawns.get(所有者) or [])#只取该所有者
        for 搭建 in 待取消:#逐个取消
            取字段(搭建,'controller').中止(原因)#逐个取消
        for 搭建 in 待取消:#等全部结算
            解开(取字段(搭建,'settled'))#等结算
        失败们=[]#收集清理失败
        for 搭建 in 待取消:#收集清理失败
            清理=取字段(搭建,'cleanupFailure')#可选清理失败
            if 清理 is not None:#有清理失败
                失败们.append(清理['error'])#收集
        for 搭建 in 待取消:#摘掉记录
            自身.摘掉未发布搭建(搭建)#摘掉
        if len(失败们)>0:#有清理失败
            raise 聚合错误(失败们,'failed to roll back unpublished PTY setup')#聚合抛出

    def 期望已拥有(自身,所有者,标识):#取已拥有记录
        """取已拥有记录；未知或他人会话则抛稳定错误。"""
        记录=自身.sessions.get(标识)#按id查找
        if 记录 is None:#未知会话
            raise 终端错误('unknown PTY session '+str(标识),'NO_SESSION')#未知会话
        if 取字段(记录,'owner') is not 所有者:#他人会话
            raise 终端错误('PTY session '+str(标识)+' belongs to another agent','FOREIGN_SESSION')#他人会话
        return 记录#通过校验

    def 快照(自身,记录,开机信息=None):#组装快照或创建结果
        """组装所有者可见快照；传入开机信息时返回创建结果。"""
        结果={#可见字段
            'sessionId':取字段(记录,'id'),#会话id
            'type':取字段(记录,'type'),#后端类型
            'status':调后端方法(取字段(记录,'session'),'status','状态'),#当前状态
        }#快照骨架
        名称=取字段(记录,'name')#可选显示名
        if 名称 is not None:#有名则带上
            结果['name']=名称#显示名
        进程号=取字段(取字段(记录,'session'),'pid')#可选进程id
        if 进程号 is not None:#有pid则带上
            结果['pid']=进程号#进程id
        if 开机信息 is not None:#有开机信息则带上
            结果['motd']=开机信息#开机信息
        return 结果#快照结束

    def 取消并关闭(自身,所有者,取消原因,关闭原因):#取消搭建并关闭会话
        """先取消未发布搭建，再关闭已发布会话；失败则聚合抛出。"""
        失败们=[]#失败收集
        try:#先取消未发布搭建
            自身.取消未发布搭建(所有者,取消原因)#取消
        except BaseException as 错误:#取消失败
            失败们.append(错误)#记下
        记录们=[]#选出要关的记录
        for 记录 in list(自身.sessions.values()):#复制后过滤
            if 所有者 is None or 取字段(记录,'owner') is 所有者:#不定所有者或本所有者
                记录们.append(记录)#收入
        try:#再关闭已发布会话
            自身.关闭记录们(记录们,关闭原因)#关闭
        except BaseException as 错误:#关闭失败
            失败们.append(错误)#记下
        if len(失败们)>0:#有失败则聚合抛出
            raise 聚合错误(失败们,'failed to clean up PTY lifecycle')#聚合抛出

    def 拆除所属(自身,所有者):#拆除一个所有者的全部PTY
        """拆除一个所有者的全部 PTY。"""
        try:#取消并关闭
            自身.取消并关闭(#走统一清理
                所有者,#该所有者
                终端错误('PTY owner is no longer live','OWNER_NOT_LIVE'),#取消原因
                'PTY owner disposed',#关闭原因
            )#取消并关闭结束
        finally:#无论成败都清预留名
            自身.reservedNames.pop(所有者,None)#去掉该所有者的预留名

    def 拆除全部(自身):#拆除服务上的全部PTY
        """拆除服务上的全部 PTY；关闭失败仍会清空注册表并跑所有者清理。"""
        自身.disposing=True#标记拆除中
        自身.拆除中=True#中文旗标
        #拆除尽力而为：关闭失败仍会清空注册表并跑所有者清理，再抛出聚合错误，避免一个卡住的会话把后端、预留或所有者拆卸器遗孤
        try:#取消并关闭全部
            自身.取消并关闭(#不定所有者即全部
                None,#全部所有者
                终端错误('PTY service is disposing','SERVICE_DISPOSING'),#取消原因
                'PTY service disposed',#关闭原因
            )#取消并关闭结束
        finally:#无论成败都清表
            自身.backends.clear()#清后端
            自身.reservedNames.clear()#清预留名
            自身.pendingSpawns.clear()#清未发布搭建
            清理们=list(自身.ownerCleanups.values())#复制拆除器
            自身.ownerCleanups.clear()#清拆除器表
            for 清理 in 清理们:#跑完全部所有者拆除器
                解开(清理())#等待拆除

    def 关闭记录们(自身,记录们,原因):#关闭一组记录
        """并行关闭一组记录；有失败则聚合抛出。"""
        失败们=[]#失败收集
        for 记录 in 记录们:#逐条关闭（语义对齐allSettled）
            正在关=取字段(记录,'closing')#已有关闭
            if 正在关 is None:#没有在飞关闭
                正在关=调后端方法(取字段(记录,'session'),'close','关闭',原因)#新开关闭
            记录['closing']=正在关#钉上栅栏
            try:#等待这次关闭
                解开(正在关)#等静止
                自身.sessions.pop(取字段(记录,'id'),None)#从表移除
            except BaseException as 错误:#关闭失败
                #并发重试可能已持有更新的关闭栅栏，绝不清掉
                if 取字段(记录,'closing') is 正在关:#仍是这次关闭才清栅栏
                    记录['closing']=None#清栅栏
                失败们.append(错误)#记下
        if len(失败们)>0:#有失败则聚合抛出
            raise 聚合错误(失败们,'failed to close '+str(len(失败们))+' PTY session(s)')#聚合抛出

默认=终端会话服务#默认导出会话服务
default=终端会话服务#Cordis默认导出

__all__=['终端会话服务','终端错误','终端错误码','默认','default']#公开面
