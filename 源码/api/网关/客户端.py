"""生成 Typert Remote 描述符的客户端投影。

对齐上游 `api/gateway/src/client/index.ts`。公开面仅中文名。
贡献安装带追踪的 remote.<namespace> 服务；方法查找、调用与类型暴露都不走 Proxy。
"""
import threading#后台串行与监听器盯住
from concurrent.futures import Future as _原生Future#单次操作结果
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis 服务基类

__all__=[#仅中文公开名
    '注入','应用','客户端远程服务','远程命名空间服务',
    '拼端点','远程服务键','作用域投影','要求严格描述符',
    'inject','apply','ClientRemoteService',
]#公开面结束

注入=['typert','connection']#依赖 typert 与 connection
inject=注入#上游名

命名空间保留字段=frozenset(['ctx','empty','invokeRemote','methods','name','namespace'])#方法名不得占用

def _是否thenable(值):#判定可等待对象
    """对象是否可 wait 或 等待。"""
    if 值 is None:#空不是
        return False#不是
    if callable(getattr(值,'wait',None)):#Future 风格
        return True#可等待
    return callable(getattr(值,'等待',None))#纤程等

class _操作任务:#本文件内单次异步结果
    """单次操作的 Future 包装。"""
    def __init__(自身):#构造未决任务
        """构造未决任务。"""
        自身._future=_原生Future()#底层 Future
    def 兑现(自身,值=None):#成功结算
        """成功结算。"""
        if not 自身._future.done():#尚未结算
            自身._future.set_result(值)#写入结果
        return 值#返回兑现值
    def 拒绝(自身,错误):#失败结算
        """失败结算。"""
        if not 自身._future.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._future.set_exception(错误)#原样拒绝
            else:#非异常
                自身._future.set_exception(Exception(错误))#包装拒绝
    def wait(自身,超时=None):#阻塞等待
        """阻塞等到结算。"""
        return 自身._future.result(timeout=超时)#取结果或抛错

def _已结算(值=None):#立刻结算的任务
    """立刻兑现的操作任务。"""
    任务=_操作任务()#新任务
    任务.兑现(值)#立刻成功
    return 任务#已完成

def _等待(值):#统一阻塞到结算
    """wait 或 等待。"""
    if callable(getattr(值,'wait',None)):#Future 风格
        return 值.wait()#等待
    return 值.等待()#纤程等

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 解开(值):#可等待则等待
    """可等待则等待，否则原样。"""
    if _是否thenable(值):#可等待
        return _等待(值)#等待
    return 值#同步

def 拼端点(描述符):#从描述符拼规范端点
    """返回 namespace/method。"""
    return 描述符['namespace']+'/'+描述符['method']#端点

def 远程服务键(命名空间):#把命名空间编成 Cordis 服务键
    """remote. 前缀。"""
    return 'remote.'+命名空间#服务键

def 内部失败(消息):#组装内部失败信封
    """internal 码、消息、空细节。"""
    return {'ok':False,'error':{'code':'internal','message':消息,'details':{}}}#信封

def 已撤(端点):#挂载已撤的内部失败
    """方法已不再挂载。"""
    return 内部失败('client api: Remote method '+端点+' is no longer mounted')#已撤

def 载体失败(端点,错误):#载体抛错折成内部失败
    """带上错误消息。"""
    消息=错误.args[0] if isinstance(错误,BaseException) and 错误.args else str(错误)#消息
    return 内部失败('client api: '+端点+' failed: '+str(消息))#失败

def 要求严格编解码(编解码,端点,字段):#断言编解码为严格模式
    """弱模式不允许出现在客户端生成描述符。"""
    if 取字段(编解码,'mode')!='strict':#弱模式
        raise Exception('client api: generated Remote '+端点+' field '+repr(字段)+' has no strict codec')#无严格编解码

def 要求严格描述符(描述符):#客户端生成描述符的每个编解码都必须是严格模式
    """结果、参数与 Context 身份编解码均须 strict。"""
    端点=拼端点(描述符)#端点
    要求严格编解码(描述符['result'],端点,'result')#结果
    for 参数 in 描述符['parameters']:#每个参数
        要求严格编解码(参数['codec'],端点,参数['wire'])#按线字段
    if 描述符['invocation']['kind']=='context':#上下文调用
        要求严格编解码(描述符['invocation']['codec'],端点,描述符['invocation']['wire'])#身份

def 解析(编解码,值,端点,字段):#用严格 schema 解析线值
    """弱模式没有 schema。"""
    if 取字段(编解码,'mode')!='strict':#弱模式
        raise Exception('client api: generated Remote '+端点+' field '+repr(字段)+' has no strict codec')#无严格
    try:#走 schema.parse
        return 编解码['schema'].parse(值)#解析
    except Exception as 原因:#解析失败
        raise Exception('client api: '+端点+' rejected '+repr(字段)) from 原因#字段被拒绝

def 作用域投影(描述符):#从描述符推导作用域投影
    """Context 调用或 scope+唯一 lookup。"""
    if 描述符['invocation']['kind']=='context':#调用约定本身就是上下文
        return {#用调用约定上的上下文、线字段与编解码
            'context':描述符['invocation']['context'],#上下文
            'wire':描述符['invocation']['wire'],#线字段
            'codec':描述符['invocation']['codec'],#编解码
        }#结束
    if 描述符.get('scope') is None:#没有 scope
        return None#无投影
    查找们=[{'parameter':参数,'index':下标} for 下标,参数 in enumerate(描述符['parameters']) if 参数['source']=='lookup']#lookup 参数
    选中=查找们[0] if len(查找们)==1 else None#必须恰好一个
    if 选中 is None or 选中['parameter']['wire']!=描述符['scope']['wire'] or 选中['parameter'].get('lookup')!=描述符['scope']['context']:#不对齐
        raise Exception('client api: generated Remote '+拼端点(描述符)+' scope must select its only lookup parameter')#scope 必须选中唯一查找
    return {#用 scope 与该查找参数拼投影
        'context':描述符['scope']['context'],#上下文
        'wire':描述符['scope']['wire'],#线字段
        'codec':选中['parameter']['codec'],#编解码
        'parameterIndex':选中['index'],#被吃掉的下标
    }#结束

class 远程命名空间服务(服务):#一个远程命名空间下的方法集合
    """直接与作用域变体的方法表。"""

    @staticmethod
    def 断言方法可用(命名空间,方法):#类级：方法名不得与命名空间服务字段冲突
        """保留字段或原型成员则抛。"""
        if 方法 in 命名空间保留字段 or hasattr(远程命名空间服务,方法):#冲突
            raise Exception('client api: method '+repr(命名空间+'/'+方法)+' conflicts with its namespace service')#冲突

    def __init__(自身,上下文,名,调用远程):#构造命名空间服务
        """以 remote.命名空间 登记。"""
        super().__init__(上下文,远程服务键(名))#登记
        自身.namespace=名#命名空间名
        自身.invokeRemote=调用远程#委托回远程服务
        自身.methods={}#方法名 → 变体记录

    def 断言方法可用实例(自身,方法):#实例级再查
        """连实例自有字段一起检查。"""
        远程命名空间服务.断言方法可用(自身.namespace,方法)#类级
        if hasattr(自身,方法) and 方法 not in 自身.methods:#实例上已有但不是已挂方法
            raise Exception('client api: method '+repr(自身.namespace+'/'+方法)+' conflicts with its namespace service')#冲突

    @property
    def empty(自身):#是否已无任何方法
        """表空则为空。"""
        return len(自身.methods)==0#空

    def has(自身,种类,方法):#是否已挂该变体
        """对应槽非空。"""
        记录=自身.methods.get(方法)#记录
        return 记录 is not None and 记录.get(种类) is not None#有槽

    def installDirect(自身,描述符,令牌):#安装直接变体
        """写入 direct 槽。"""
        自身._安装(描述符['method'],'direct',{'descriptor':描述符,'token':令牌})#安装

    def installScoped(自身,描述符,投影,令牌):#安装作用域变体
        """写入 scoped 槽。"""
        自身._安装(描述符['method'],'scoped',{'descriptor':描述符,'projection':投影,'token':令牌})#安装

    def _安装(自身,方法,种类,值):#首次定义访问器，再写入对应槽
        """方法名不得冲突。"""
        自身.断言方法可用实例(方法)#断言
        记录=自身.methods.get(方法)#已有
        新建=记录 is None#是否第一次
        if 新建:#第一次
            记录={}#空记录
            自身.methods[方法]=记录#写入表
            def 发出(*位置参数,本=自身,名=方法):#真正发出调用
                """取值时捕获调用方上下文与当前变体。"""
                调用方=本.ctx#调用方上下文
                当前=本.methods.get(名)#当前变体记录
                直接=取字段(当前,'direct') if 当前 else None#直接
                作用域=取字段(当前,'scoped') if 当前 else None#作用域
                return 本.invokeRemote(直接,作用域,调用方,位置参数)#委托
            setattr(自身,方法,发出)#挂可调用
        if 种类=='direct':#直接
            记录['direct']=值#写入
        else:#作用域
            记录['scoped']=值#写入

    def remove(自身,种类,方法,令牌):#按令牌去掉一个变体
        """没有记录或令牌不是自己则不动。"""
        记录=自身.methods.get(方法)#变体记录
        当前=取字段(记录,种类) if 记录 else None#该槽
        if 记录 is None or 取字段(当前,'token') is not 令牌:#不是自己
            return#不动
        if 种类=='direct':#去掉直接
            记录.pop('direct',None)#删
        else:#去掉作用域
            记录.pop('scoped',None)#删
        if 记录.get('direct') is not None or 记录.get('scoped') is not None:#另一变体还在
            return#保留
        自身.methods.pop(方法,None)#从表删除
        if hasattr(自身,方法):#有访问器
            delattr(自身,方法)#删掉

class 客户端远程服务(服务):#客户端远程服务
    """安装带类型的客户端远程服务。"""

    def __init__(自身,上下文):#构造并登记
        """以 remote 名登记。"""
        super().__init__(上下文,'remote')#登记
        自身.ownerCtx=上下文#拥有方上下文
        自身.namespaces={}#已安装命名空间
        自身.subscriptions={}#按事件名分组的订阅
        自身.mutations=_已结算(None)#挂载拆除串行队列尾
        def 清订阅():#拆除时清空订阅表
            """清空。"""
            自身.subscriptions.clear()#清空
        上下文.effect(lambda:清订阅,'api-gateway.client.subscriptions')#生命周期

    def mount(自身,贡献):#挂载一份远程贡献
        """把挂载纳入调用方效果。"""
        调用方=自身.ctx#调用方上下文
        def 执行挂载():#串行执行挂载
            """安装贡献。"""
            return 自身.挂载贡献(调用方,贡献)#挂载
        拆除=自身.入队(执行挂载)#串行
        拆除=解开(拆除)#等到完成
        def 卸():#拆除该效果
            """同样串行。"""
            return 自身.入队(拆除)#拆除
        return 卸#拆除函数

    def on(自身,事件,监听器):#按事件名订阅远程事件
        """按登记本身识别而不是按监听器函数。"""
        订阅={'listener':监听器}#本次登记
        监听们=自身.listeners(事件)#取或创建
        监听们.append(订阅)#追加
        def 退订():#拆除时只去掉自己
            """按登记对象找下标。"""
            try:#可能已不在
                监听们.remove(订阅)#删除
            except ValueError:#不在
                pass#忽略
        return 退订#拆除器

    def dispatch(自身,事件,参数):#向已订阅监听器投递一帧
        """隔离同步抛错或可等待对象拒绝的监听器。"""
        监听们=自身.subscriptions.get(事件)#取该事件
        if 监听们 is None:#没有订阅
            return#直接返回
        for 项 in list(监听们):#按快照逐个
            监听=项['listener']#监听器
            def 报告(错误):#打到控制台
                """报告监听器抛错。"""
                print('client api: Remote event',repr(事件),'listener threw:',错误)#报告
            try:#调用
                落定=监听(*参数)#可能返回可等待对象
                if _是否thenable(落定):#异步
                    def 盯住(任务=落定):#收住拒绝
                        """把异步拒绝接到诊断。"""
                        try:#等待
                            _等待(任务)#等待
                        except Exception as 错误:#拒绝
                            报告(错误)#报告
                    线=threading.Thread(target=盯住)#后台
                    线.daemon=True#不挡退出
                    线.start()#启动
            except Exception as 错误:#同步抛错
                报告(错误)#报告

    def listeners(自身,事件):#取或创建某事件的订阅数组
        """空数组会保留。"""
        监听们=自身.subscriptions.get(事件)#已有
        if 监听们 is None:#还没有
            监听们=[]#新建
            自身.subscriptions[事件]=监听们#写入
        return 监听们#可追加

    def 入队(自身,操作):#把挂载拆除操作串到队列尾
        """前一步无论成败都跑本次。"""
        前=自身.mutations#当前队列尾
        任务=_操作任务()#本次结果
        锚=_操作任务()#队列尾锚，吞掉成败
        def 跑():#串到前任之后
            """前任失败不挡本次；锚始终成功。"""
            try:#前任失败不得毒化
                try:#等前任
                    解开(前)#等
                except Exception:#吞前任失败
                    pass#绕过
                值=操作() if callable(操作) else 操作#执行
                值=解开(值)#展平可等待
                任务.兑现(值)#交给调用方
            except BaseException as 错误:#失败
                任务.拒绝(错误)#调用方看见拒绝
            finally:#锚始终成功
                锚.兑现(None)#队列继续
        线=threading.Thread(target=跑)#工作线程
        线.daemon=True#不挡住退出
        线.start()#启动
        自身.mutations=锚#钉成新尾巴
        return 任务#本次结果

    def 挂载贡献(自身,调用方,贡献):#安装一份贡献的描述符并登记到 Typert
        """先校验，再逐个安装；中途失败回滚。"""
        自身.校验贡献(贡献)#校验
        拆除远程=调用方.typert.remotes.register(贡献)#向 Typert 登记
        已装=[]#已安装描述符的拆除器
        try:#逐个安装
            for 描述符 in 贡献['descriptors']:#每个描述符
                已装.append(自身.安装(描述符))#安装
        except Exception:#中途失败
            for 拆除 in reversed(已装):#逆序拆除
                解开(拆除())#拆除
            解开(拆除远程())#撤 Typert
            raise#原样抛
        def 整拆():#整份贡献的拆除器
            """逆序拆除描述符再撤登记。"""
            for 拆除 in reversed(已装):#逆序
                解开(拆除())#拆除
            解开(拆除远程())#撤
        return 整拆#拆除器

    def 校验贡献(自身,贡献):#校验贡献内与已挂载命名空间不冲突
        """本贡献内与已挂载查重。"""
        直接表={}#本贡献内的直接方法
        作用域表={}#本贡献内的作用域方法
        def 加入(表,描述符,种类):#记入并查重
            """冲突则抛。"""
            方法们=表.get(描述符['namespace']) or set()#已见方法
            if 描述符['method'] in 方法们:#本贡献内重复
                raise Exception('client api: contribution repeats '+种类+' method '+拼端点(描述符))#重复
            方法们.add(描述符['method'])#记下
            表[描述符['namespace']]=方法们#写回
            句柄=自身.namespaces.get(描述符['namespace'])#已挂载
            服务实例=取字段(句柄,'service') if 句柄 else None#服务
            if 服务实例 is not None and 服务实例.has(种类,描述符['method']):#该变体已挂着
                raise Exception('client api: '+种类+' method '+拼端点(描述符)+' is already mounted')#已挂载
        for 描述符 in 贡献['descriptors']:#逐个
            要求严格描述符(描述符)#只要严格
            if 描述符['invocation']['kind']=='direct':#直接
                加入(直接表,描述符,'direct')#记入
            if 作用域投影(描述符) is not None:#能投影
                加入(作用域表,描述符,'scoped')#记入
        命名空间们=set(直接表)|set(作用域表)#本贡献涉及
        for 命名空间 in 命名空间们:#检查每个
            句柄=自身.namespaces.get(命名空间)#已有
            服务实例=取字段(句柄,'service') if 句柄 else None#服务
            if 服务实例 is None:#还要新建
                if hasattr(自身,命名空间):#与远程服务自身字段冲突
                    raise Exception('client api: namespace '+repr(命名空间)+' conflicts with the Remote service')#冲突
                服务键=远程服务键(命名空间)#将要登记的键
                if 自身.ownerCtx.get(服务键) is not None:#已有活动服务
                    raise Exception('client api: namespace '+repr(命名空间)+' conflicts with an existing Remote namespace')#冲突
            方法名们=set(直接表.get(命名空间) or [])|set(作用域表.get(命名空间) or [])#将出现的方法
            for 方法 in 方法名们:#逐个
                if 服务实例 is None:#尚未有实例
                    远程命名空间服务.断言方法可用(命名空间,方法)#类检查
                else:#已有实例
                    服务实例.断言方法可用实例(方法)#实例检查

    def 安装(自身,描述符):#按描述符安装直接与作用域变体
        """先直接后作用域；失败作废令牌并回滚。"""
        令牌={'active':True,'abort':中止控制器()}#存活令牌
        已装=[]#已装变体
        try:#安装
            if 描述符['invocation']['kind']=='direct':#直接
                已装.append(自身.安装直接(描述符,令牌))#直接
            投影=作用域投影(描述符)#作用域
            if 投影 is not None:#有投影
                已装.append(自身.安装作用域(描述符,投影,令牌))#作用域
        except Exception:#失败
            令牌['active']=False#作废
            令牌['abort'].abort()#中止
            for 拆除 in reversed(已装):#回滚
                解开(拆除())#拆除
            raise#抛
        def 卸():#描述符拆除器
            """幂等。"""
            if not 令牌['active']:#已拆
                return#返回
            令牌['active']=False#标记
            令牌['abort'].abort()#中止
            for 拆除 in reversed(已装):#逆序
                解开(拆除())#拆除
        return 卸#拆除器

    def 安装直接(自身,描述符,令牌):#把直接变体装进命名空间服务
        """取或创建命名空间。"""
        命名空间=自身.取命名空间(描述符['namespace'])#句柄
        try:#挂直接方法
            命名空间['service'].installDirect(描述符,令牌)#安装
        except Exception:#失败
            自身.卸命名空间(描述符['namespace'],命名空间)#尝试丢掉空命名空间
            raise#抛
        def 卸():#直接变体拆除器
            """按令牌去掉直接变体。"""
            命名空间['service'].remove('direct',描述符['method'],令牌)#去掉
            自身.卸命名空间(描述符['namespace'],命名空间)#若已空则拆
        return 卸#拆除器

    def 安装作用域(自身,描述符,投影,令牌):#把作用域变体装进命名空间服务
        """取或创建命名空间。"""
        命名空间=自身.取命名空间(描述符['namespace'])#句柄
        try:#挂作用域方法
            命名空间['service'].installScoped(描述符,投影,令牌)#安装
        except Exception:#失败
            自身.卸命名空间(描述符['namespace'],命名空间)#尝试丢掉
            raise#抛
        def 卸():#作用域变体拆除器
            """按令牌去掉作用域变体。"""
            命名空间['service'].remove('scoped',描述符['method'],令牌)#去掉
            自身.卸命名空间(描述符['namespace'],命名空间)#若已空则拆
        return 卸#拆除器

    def 取命名空间(自身,名):#取或创建命名空间服务
        """已安装则直接返回。"""
        句柄=自身.namespaces.get(名)#已有
        if 句柄 is not None:#已安装
            return 句柄#返回
        服务盒={'service':None}#插件 apply 里同步赋上
        def 插件应用(插件上下文):#插件 apply
            """构造命名空间服务。"""
            服务盒['service']=远程命名空间服务(#构造
                插件上下文,#上下文
                名,#命名空间
                lambda 直接,作用域,调用方,参数:自身.调用方法(直接,作用域,调用方,参数),#委托
            )#结束
        光纤=自身.ownerCtx.plugin({'name':远程服务键(名),'apply':插件应用})#登记插件
        try:#等待就绪
            解开(光纤)#等到服务已登记
        except Exception:#启动失败
            解开(光纤.dispose())#拆除
            raise#抛
        if 服务盒['service'] is None:#没构造
            raise Exception('client api: namespace '+repr(名)+' did not start')#未启动
        句柄={'service':服务盒['service'],'dispose':光纤.dispose}#记下
        自身.namespaces[名]=句柄#写入
        return 句柄#返回

    def 卸命名空间(自身,名,句柄):#命名空间已空且仍是当前句柄时拆除
        """还有方法或句柄已换则不动。"""
        if not 句柄['service'].empty or 自身.namespaces.get(名) is not 句柄:#不空或已换
            return#不动
        自身.namespaces.pop(名,None)#从表去掉
        解开(句柄['dispose']())#拆除插件

    def 调用方法(自身,直接,作用域,调用方,值们):#按当前上下文有无身份选择变体
        """有身份则走作用域；否则直接；仅作用域则仍走作用域。"""
        if 作用域 is not None:#有作用域变体
            绑定器=自身.ownerCtx.typert.contexts.getClient(作用域['projection']['context'])#客户端绑定器
            身份=绑定器.identity(调用方) if 绑定器 is not None else None#读身份
            if 身份 is not None:#有身份
                return 自身.调用(作用域['descriptor'],作用域['projection'],作用域['token'],调用方,值们,{'value':身份})#作用域
        if 直接 is not None:#无身份则走直接
            return 自身.调用(直接['descriptor'],None,直接['token'],调用方,值们)#直接
        if 作用域 is not None:#没有直接则仍走作用域
            return 自身.调用(作用域['descriptor'],作用域['projection'],作用域['token'],调用方,值们)#作用域
        raise Exception('client api: Remote method is no longer mounted')#都不在了

    def 调用(自身,描述符,投影,令牌,调用方,值们,已绑身份=None):#按描述符组线参数并经 Connection 发出 RPC
        """挂载已撤则没有请求结果。"""
        端点=拼端点(描述符)#端点
        if not 令牌['active']:#已撤
            return 已撤(端点)#已撤
        期望=len(描述符['parameters'])-(0 if 投影 is None or 投影.get('parameterIndex') is None else 1)#业务参数个数
        有调用方信号=描述符.get('cancellation') is not None and len(值们)==期望+1#多传的那个视为取消信号
        if len(值们)!=期望 and not 有调用方信号:#个数不符
            约定=str(期望)+' argument(s)' if 描述符.get('cancellation') is None else str(期望)+' business argument(s) plus an optional AbortSignal'#约定文案
            raise Exception('client api: '+端点+' expected '+约定+', got '+str(len(值们)))#组装错误
        参数={}#具名线参数
        if 投影 is not None:#需要注入上下文身份
            绑定器=None if 已绑身份 is not None else 自身.ownerCtx.typert.contexts.getClient(投影['context'])#绑定器
            if 已绑身份 is None and 绑定器 is None:#既无预绑定也无绑定器
                raise Exception('client api: '+端点+' has no Client Context binder for '+repr(投影['context']))#无绑定器
            身份=已绑身份['value'] if 已绑身份 is not None else (绑定器.identity(调用方) if 绑定器 else None)#身份
            if 身份 is None:#读不到
                raise Exception('client api: '+端点+' requires a '+repr(投影['context'])+' Context')#需要上下文
            参数[投影['wire']]=解析(投影['codec'],身份,端点,投影['wire'])#编进线字段
        值下标=0#位置参数游标
        for 参数下标,参数描述 in enumerate(描述符['parameters']):#按描述符顺序
            if 投影 is not None and 参数下标==投影.get('parameterIndex'):#被作用域吃掉
                continue#跳过
            值=解析(参数描述['codec'],值们[值下标],端点,参数描述['wire'])#解析
            if 值 is not None:#undefined 不写线字段
                参数[参数描述['wire']]=值#写入
            值下标+=1#下一个
        连接=自身.ownerCtx.get('connection')#活动连接
        if 连接 is None:#没有
            raise Exception('client api: '+端点+' has no active Connection')#无连接
        调用方信号=值们[期望] if 有调用方信号 else None#调用方信号
        信号=令牌['abort'].signal if 调用方信号 is None else 合并中止(令牌['abort'].signal,调用方信号)#合成
        try:#发出 RPC
            结果=解开(连接.rpc.call('/api',端点,{'args':参数},信号))#经 /api 调用
            if not 令牌['active']:#返回前已撤
                return 已撤(端点)#已撤
            if not 取字段(结果,'ok'):#业务或分发失败
                return {'ok':False,'error':结果['error']}#原样
            return {'ok':True,'value':解析(描述符['result'],结果['value'],端点,'result')}#成功
        except Exception as 错误:#载体抛错
            return 载体失败(端点,错误)#折成内部失败

def 中止控制器():#简易中止控制器
    """提供 signal.aborted 与 abort()。"""
    旗={'aborted':False}#旗
    class 信号:#中止信号
        @property
        def aborted(自身):#是否已中止
            """读旗。"""
            return 旗['aborted']#旗
    def 中止():#触发中止
        """置旗。"""
        旗['aborted']=True#中止
    return type('控制器',(),{'signal':信号(),'abort':staticmethod(中止)})()#控制器

def 合并中止(甲,乙):#任一中止即中止
    """简化：包装成检查两信号的信号。"""
    class 合成:#合成信号
        @property
        def aborted(自身):#是否已中止
            """甲或乙。"""
            return 取字段(甲,'aborted') or 取字段(乙,'aborted')#或
    return 合成()#合成信号

def 应用(上下文):#安装客户端远程服务
    """在客户端根上挂载 Remote 服务。"""
    客户端远程服务(上下文)#构造并登记

apply=应用#上游名
ClientRemoteService=客户端远程服务#上游名
