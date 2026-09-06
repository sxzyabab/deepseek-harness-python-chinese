"""生成 Typert Remote 描述符的客户端投影。

对齐上游 `api/gateway/src/client/index.ts`。公开面仅中文名。
贡献安装带追踪的 remote.<namespace> 服务；方法查找、调用与类型暴露都不走 Proxy。
"""
import threading#后台串行与监听器盯住
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis 服务基类
from .网关 import 网关错误,操作任务,中止控制器,中止信号#本包异常与并发原语

__all__=[#仅中文公开名
    '注入','应用','客户端远程服务','远程命名空间服务',
    '拼端点','远程服务键','作用域投影','要求严格描述符',
]#公开面结束

注入=['typert','connection']#依赖 typert 与 connection

命名空间保留字段=frozenset(['ctx','empty','invokeRemote','methods','name','namespace'])#方法名不得占用

def 拼端点(描述符):
    """返回 namespace/method。描述符为 dict。"""
    return 描述符['namespace']+'/'+描述符['method']#端点

def 远程服务键(命名空间):
    """remote. 前缀。"""
    return 'remote.'+命名空间#服务键

def 内部失败(消息):
    """internal 码、消息、空细节。"""
    return {'ok':False,'error':{'code':'internal','message':消息,'details':{}}}#信封

def 已撤(端点):
    """方法已不再挂载。"""
    return 内部失败('client api: Remote method '+端点+' is no longer mounted')#已撤

def 载体失败(端点,错误):
    """带上错误消息。"""
    消息=错误.args[0] if isinstance(错误,BaseException) and len(错误.args)>0 else str(错误)#消息
    return 内部失败('client api: '+端点+' failed: '+str(消息))#失败

def 要求严格编解码(编解码,端点,字段):
    """弱模式不允许出现在客户端生成描述符。编解码为 dict。"""
    if 'mode' not in 编解码 or 编解码['mode']!='strict':#弱模式
        raise 网关错误('definition-unavailable',端点,'client api: generated Remote '+端点+' field '+repr(字段)+' has no strict codec')#无严格编解码

def 要求严格描述符(描述符):
    """结果、参数与 Context 身份编解码均须 strict。描述符为 dict。"""
    端点=拼端点(描述符)#端点
    要求严格编解码(描述符['result'],端点,'result')#结果
    for 参数 in 描述符['parameters']:#每个参数
        要求严格编解码(参数['codec'],端点,参数['wire'])#按线字段
    if 描述符['invocation']['kind']=='context':#上下文调用
        要求严格编解码(描述符['invocation']['codec'],端点,描述符['invocation']['wire'])#身份

def 解析(编解码,值,端点,字段):
    """弱模式没有 schema。编解码为 dict。"""
    if 'mode' not in 编解码 or 编解码['mode']!='strict':#弱模式
        raise 网关错误('definition-unavailable',端点,'client api: generated Remote '+端点+' field '+repr(字段)+' has no strict codec')#无严格
    try:
        return 编解码['schema'].parse(值)#解析
    except (TypeError,ValueError,KeyError,AttributeError) as 原因:
        raise 网关错误('input-invalid',端点,'client api: '+端点+' rejected '+repr(字段)) from 原因#字段被拒绝

def 作用域投影(描述符):
    """Context 调用或 scope+唯一 lookup。描述符为 dict。"""
    if 描述符['invocation']['kind']=='context':#调用约定本身就是上下文
        return {#用调用约定上的上下文、线字段与编解码
            'context':描述符['invocation']['context'],#上下文
            'wire':描述符['invocation']['wire'],#线字段
            'codec':描述符['invocation']['codec'],#编解码
        }#结束
    if 'scope' not in 描述符 or 描述符['scope'] is None:#没有 scope
        return None#无投影
    查找列表=[{'parameter':参数,'index':下标} for 下标,参数 in enumerate(描述符['parameters']) if 参数['source']=='lookup']#lookup 参数
    选中=查找列表[0] if len(查找列表)==1 else None#必须恰好一个
    查找键=选中['parameter']['lookup'] if 选中 is not None and 'lookup' in 选中['parameter'] else None#lookup 键
    if 选中 is None or 选中['parameter']['wire']!=描述符['scope']['wire'] or 查找键!=描述符['scope']['context']:#不对齐
        raise 网关错误('signature-invalid',拼端点(描述符),'client api: generated Remote '+拼端点(描述符)+' scope must select its only lookup parameter')#scope 必须选中唯一查找
    return {#用 scope 与该查找参数拼投影
        'context':描述符['scope']['context'],#上下文
        'wire':描述符['scope']['wire'],#线字段
        'codec':选中['parameter']['codec'],#编解码
        'parameterIndex':选中['index'],#被吃掉的下标
    }#结束

class 远程命名空间服务(服务):
    """直接与作用域变体的方法表。"""

    @staticmethod
    def 断言方法可用(命名空间,方法):
        """保留字段或原型成员则抛。"""
        if 方法 in 命名空间保留字段 or hasattr(远程命名空间服务,方法):#冲突
            raise 网关错误('binding-invalid',命名空间+'/'+方法,'client api: method '+repr(命名空间+'/'+方法)+' conflicts with its namespace service')#冲突

    def __init__(自身,上下文,名,调用远程):
        """以 remote.命名空间 登记。"""
        super().__init__(上下文,远程服务键(名))#登记
        自身.namespace=名#命名空间名
        自身.invokeRemote=调用远程#委托回远程服务
        自身.methods={}#方法名 → 变体记录

    def 断言方法可用实例(自身,方法):
        """连实例自有字段一起检查。"""
        远程命名空间服务.断言方法可用(自身.namespace,方法)#类级
        if hasattr(自身,方法) and 方法 not in 自身.methods:#实例上已有但不是已挂方法
            raise 网关错误('binding-invalid',自身.namespace+'/'+方法,'client api: method '+repr(自身.namespace+'/'+方法)+' conflicts with its namespace service')#冲突

    @property
    def empty(自身):
        """表空则为空。"""
        return len(自身.methods)==0#空

    def has(自身,种类,方法):
        """对应槽非空。"""
        if 方法 not in 自身.methods:#无记录
            return False#没有
        记录=自身.methods[方法]#记录
        return 种类 in 记录 and 记录[种类] is not None#有槽

    def installDirect(自身,描述符,令牌):
        """写入 direct 槽。描述符为 dict。"""
        自身._安装(描述符['method'],'direct',{'descriptor':描述符,'token':令牌})#安装

    def installScoped(自身,描述符,投影,令牌):
        """写入 scoped 槽。描述符与投影为 dict。"""
        自身._安装(描述符['method'],'scoped',{'descriptor':描述符,'projection':投影,'token':令牌})#安装

    def _安装(自身,方法,种类,值):
        """首次定义访问器，再写入对应槽。值为 dict。"""
        自身.断言方法可用实例(方法)#断言
        记录=自身.methods[方法] if 方法 in 自身.methods else None#已有
        新建=记录 is None#是否第一次
        if 新建:#第一次
            记录={}#空记录
            自身.methods[方法]=记录#写入表
            def 发出(*位置参数,本=自身,名=方法):
                """取值时捕获调用方上下文与当前变体。"""
                调用方=本.ctx#调用方上下文
                当前=本.methods[名] if 名 in 本.methods else None#当前变体记录
                直接=当前['direct'] if 当前 is not None and 'direct' in 当前 else None#直接
                作用域=当前['scoped'] if 当前 is not None and 'scoped' in 当前 else None#作用域
                return 本.invokeRemote(直接,作用域,调用方,位置参数)#委托
            setattr(自身,方法,发出)#挂可调用
        记录[种类]=值#写入对应槽

    def remove(自身,种类,方法,令牌):
        """没有记录或令牌不是自己则不动。"""
        if 方法 not in 自身.methods:#无记录
            return#不动
        记录=自身.methods[方法]#变体记录
        当前=记录[种类] if 种类 in 记录 else None#该槽
        if 当前 is None or 当前['token'] is not 令牌:#不是自己
            return#不动
        if 种类=='direct':#去掉直接
            记录.pop('direct',None)#删
        else:#去掉作用域
            记录.pop('scoped',None)#删
        if ('direct' in 记录 and 记录['direct'] is not None) or ('scoped' in 记录 and 记录['scoped'] is not None):#另一变体还在
            return#保留
        自身.methods.pop(方法,None)#从表删除
        if hasattr(自身,方法):#有访问器
            delattr(自身,方法)#删掉

class 客户端远程服务(服务):
    """安装带类型的客户端远程服务。"""

    def __init__(自身,上下文):
        """以 remote 名登记。"""
        super().__init__(上下文,'remote')#登记
        自身.ownerCtx=上下文#拥有方上下文
        自身.namespaces={}#已安装命名空间
        自身.subscriptions={}#按事件名分组的订阅
        自身.mutations=操作任务()#挂载拆除串行队列尾
        自身.mutations.兑现(None)#初始已结算
        def 清订阅():
            """拆除时清空订阅表。"""
            自身.subscriptions.clear()#清空
        上下文.副作用(清订阅,'api-gateway.client.subscriptions')#生命周期

    def mount(自身,贡献):
        """把挂载纳入调用方效果。贡献为 dict。"""
        调用方=自身.ctx#调用方上下文
        def 执行挂载():
            """安装贡献。"""
            return 自身.挂载贡献(调用方,贡献)#挂载
        拆除=自身.入队(执行挂载).等待()#串行等到完成
        def 卸():
            """同样串行。"""
            自身.入队(拆除).等待()#拆除
        return 卸#拆除函数

    def on(自身,事件,监听器):
        """按登记本身识别而不是按监听器函数。"""
        订阅={'listener':监听器}#本次登记
        监听列表=自身.listeners(事件)#取或创建
        监听列表.append(订阅)#追加
        def 退订():
            """按登记对象找下标。"""
            try:
                监听列表.remove(订阅)#删除
            except ValueError:
                pass#已不在
        return 退订#拆除器

    def dispatch(自身,事件,参数):
        """隔离同步抛错的监听器。翻译时监听器已是同步回调。"""
        if 事件 not in 自身.subscriptions:#没有订阅
            return#直接返回
        监听列表=自身.subscriptions[事件]#取该事件
        for 项 in list(监听列表):#按快照逐个
            监听=项['listener']#监听器
            def 报告(错误):
                """报告监听器抛错。"""
                print('client api: Remote event',repr(事件),'listener threw:',错误)#报告
            try:
                监听(*参数)#同步调用
            except BaseException as 错误:
                报告(错误)#报告

    def listeners(自身,事件):
        """空数组会保留。"""
        if 事件 not in 自身.subscriptions:#还没有
            自身.subscriptions[事件]=[]#新建
        return 自身.subscriptions[事件]#可追加

    def 入队(自身,操作):
        """前一步无论成败都跑本次。返回操作任务。"""
        前=自身.mutations#当前队列尾
        任务=操作任务()#本次结果
        锚=操作任务()#队列尾锚，吞掉成败
        def 跑():
            """前任失败不挡本次；锚始终成功。"""
            try:
                try:
                    前.等待()#等前任
                except BaseException:
                    pass#吞前任失败
                值=操作() if callable(操作) else 操作#执行同步回调
                任务.兑现(值)#交给调用方
            except BaseException as 错误:
                任务.拒绝(错误)#调用方看见拒绝
            finally:
                锚.兑现(None)#队列继续
        线=threading.Thread(target=跑)#工作线程
        线.daemon=True#不挡住退出
        线.start()#启动
        自身.mutations=锚#钉成新尾巴
        return 任务#本次结果

    def 挂载贡献(自身,调用方,贡献):
        """先校验，再逐个安装；中途失败回滚。贡献为 dict。"""
        自身.校验贡献(贡献)#校验
        拆除远程=调用方.typert.remotes.register(贡献)#向 Typert 登记
        已装=[]#已安装描述符的拆除器
        try:
            for 描述符 in 贡献['descriptors']:#每个描述符
                已装.append(自身.安装(描述符))#安装
        except BaseException:
            for 拆除 in reversed(已装):#逆序拆除
                拆除()#拆除
            拆除远程()#撤 Typert
            raise#原样抛
        def 整拆():
            """逆序拆除描述符再撤登记。"""
            for 拆除 in reversed(已装):#逆序
                拆除()#拆除
            拆除远程()#撤
        return 整拆#拆除器

    def 校验贡献(自身,贡献):
        """本贡献内与已挂载命名空间不冲突。贡献为 dict。"""
        直接表={}#本贡献内的直接方法
        作用域表={}#本贡献内的作用域方法
        def 加入(表,描述符,种类):
            """冲突则抛。"""
            方法集合=表[描述符['namespace']] if 描述符['namespace'] in 表 else set()#已见方法
            if 描述符['method'] in 方法集合:#本贡献内重复
                raise 网关错误('binding-invalid',拼端点(描述符),'client api: contribution repeats '+种类+' method '+拼端点(描述符))#重复
            方法集合.add(描述符['method'])#记下
            表[描述符['namespace']]=方法集合#写回
            句柄=自身.namespaces[描述符['namespace']] if 描述符['namespace'] in 自身.namespaces else None#已挂载
            服务实例=句柄['service'] if 句柄 is not None and 'service' in 句柄 else None#服务
            if 服务实例 is not None and 服务实例.has(种类,描述符['method']):#该变体已挂着
                raise 网关错误('binding-invalid',拼端点(描述符),'client api: '+种类+' method '+拼端点(描述符)+' is already mounted')#已挂载
        for 描述符 in 贡献['descriptors']:#逐个
            要求严格描述符(描述符)#只要严格
            if 描述符['invocation']['kind']=='direct':#直接
                加入(直接表,描述符,'direct')#记入
            if 作用域投影(描述符) is not None:#能投影
                加入(作用域表,描述符,'scoped')#记入
        命名空间集合=set(直接表)|set(作用域表)#本贡献涉及
        for 命名空间 in 命名空间集合:#检查每个
            句柄=自身.namespaces[命名空间] if 命名空间 in 自身.namespaces else None#已有
            服务实例=句柄['service'] if 句柄 is not None and 'service' in 句柄 else None#服务
            if 服务实例 is None:#还要新建
                if hasattr(自身,命名空间):#与远程服务自身字段冲突
                    raise 网关错误('binding-invalid',命名空间,'client api: namespace '+repr(命名空间)+' conflicts with the Remote service')#冲突
                服务键=远程服务键(命名空间)#将要登记的键
                if 自身.ownerCtx.获取服务(服务键) is not None:#已有活动服务
                    raise 网关错误('binding-invalid',命名空间,'client api: namespace '+repr(命名空间)+' conflicts with an existing Remote namespace')#冲突
            直接方法=直接表[命名空间] if 命名空间 in 直接表 else set()#直接
            作用域方法=作用域表[命名空间] if 命名空间 in 作用域表 else set()#作用域
            方法名集合=set(直接方法)|set(作用域方法)#将出现的方法
            for 方法 in 方法名集合:#逐个
                if 服务实例 is None:#尚未有实例
                    远程命名空间服务.断言方法可用(命名空间,方法)#类检查
                else:#已有实例
                    服务实例.断言方法可用实例(方法)#实例检查

    def 安装(自身,描述符):
        """先直接后作用域；失败作废令牌并回滚。描述符为 dict。"""
        令牌={'active':True,'abort':中止控制器()}#存活令牌
        已装=[]#已装变体
        try:
            if 描述符['invocation']['kind']=='direct':#直接
                已装.append(自身.安装直接(描述符,令牌))#直接
            投影=作用域投影(描述符)#作用域
            if 投影 is not None:#有投影
                已装.append(自身.安装作用域(描述符,投影,令牌))#作用域
        except BaseException:
            令牌['active']=False#作废
            令牌['abort'].中止()#中止
            for 拆除 in reversed(已装):#回滚
                拆除()#拆除
            raise#抛
        def 卸():
            """幂等。"""
            if not 令牌['active']:#已拆
                return#返回
            令牌['active']=False#标记
            令牌['abort'].中止()#中止
            for 拆除 in reversed(已装):#逆序
                拆除()#拆除
        return 卸#拆除器

    def 安装直接(自身,描述符,令牌):
        """取或创建命名空间。描述符为 dict。"""
        命名空间=自身.取命名空间(描述符['namespace'])#句柄
        try:
            命名空间['service'].installDirect(描述符,令牌)#安装
        except BaseException:
            自身.卸命名空间(描述符['namespace'],命名空间)#尝试丢掉空命名空间
            raise#抛
        def 卸():
            """按令牌去掉直接变体。"""
            命名空间['service'].remove('direct',描述符['method'],令牌)#去掉
            自身.卸命名空间(描述符['namespace'],命名空间)#若已空则拆
        return 卸#拆除器

    def 安装作用域(自身,描述符,投影,令牌):
        """取或创建命名空间。描述符与投影为 dict。"""
        命名空间=自身.取命名空间(描述符['namespace'])#句柄
        try:
            命名空间['service'].installScoped(描述符,投影,令牌)#安装
        except BaseException:
            自身.卸命名空间(描述符['namespace'],命名空间)#尝试丢掉
            raise#抛
        def 卸():
            """按令牌去掉作用域变体。"""
            命名空间['service'].remove('scoped',描述符['method'],令牌)#去掉
            自身.卸命名空间(描述符['namespace'],命名空间)#若已空则拆
        return 卸#拆除器

    def 取命名空间(自身,名):
        """已安装则直接返回。"""
        if 名 in 自身.namespaces:#已安装
            return 自身.namespaces[名]#返回
        服务盒={'service':None}#插件 apply 里同步赋上
        def 插件应用(插件上下文):
            """构造命名空间服务。"""
            def 委托调用(直接,作用域,调用方,参数):
                """转给远程服务。"""
                return 自身.调用方法(直接,作用域,调用方,参数)#委托
            服务盒['service']=远程命名空间服务(插件上下文,名,委托调用)#构造
        光纤=自身.ownerCtx.启动插件({'name':远程服务键(名),'apply':插件应用})#登记插件
        try:
            光纤.等待()#等到服务已登记
        except BaseException:
            光纤.拆除()#拆除
            raise#抛
        if 服务盒['service'] is None:#没构造
            raise 网关错误('service-unavailable',名,'client api: namespace '+repr(名)+' did not start')#未启动
        句柄={'service':服务盒['service'],'dispose':光纤.拆除}#记下
        自身.namespaces[名]=句柄#写入
        return 句柄#返回

    def 卸命名空间(自身,名,句柄):
        """命名空间已空且仍是当前句柄时拆除。句柄为 dict。"""
        if (not 句柄['service'].empty) or (名 not in 自身.namespaces) or (自身.namespaces[名] is not 句柄):#不空或已换
            return#不动
        自身.namespaces.pop(名,None)#从表去掉
        句柄['dispose']()#拆除插件

    def 调用方法(自身,直接,作用域,调用方,值列表):
        """有身份则走作用域；否则直接；仅作用域则仍走作用域。直接与作用域为 dict。"""
        if 作用域 is not None:#有作用域变体
            绑定器=自身.ownerCtx.typert.contexts.getClient(作用域['projection']['context'])#客户端绑定器
            身份=绑定器.identity(调用方) if 绑定器 is not None else None#读身份
            if 身份 is not None:#有身份
                return 自身.调用(作用域['descriptor'],作用域['projection'],作用域['token'],调用方,值列表,{'value':身份})#作用域
        if 直接 is not None:#无身份则走直接
            return 自身.调用(直接['descriptor'],None,直接['token'],调用方,值列表)#直接
        if 作用域 is not None:#没有直接则仍走作用域
            return 自身.调用(作用域['descriptor'],作用域['projection'],作用域['token'],调用方,值列表)#作用域
        raise 网关错误('method-unavailable','','client api: Remote method is no longer mounted')#都不在了

    def 调用(自身,描述符,投影,令牌,调用方,值列表,已绑身份=None):
        """按描述符组线参数并经 Connection 发出 RPC。描述符为 dict。"""
        端点=拼端点(描述符)#端点
        if not 令牌['active']:#已撤
            return 已撤(端点)#已撤
        投影下标=投影['parameterIndex'] if 投影 is not None and 'parameterIndex' in 投影 else None#被吃掉的下标
        期望=len(描述符['parameters'])-(0 if 投影下标 is None else 1)#业务参数个数
        有调用方信号=('cancellation' in 描述符 and 描述符['cancellation'] is not None) and len(值列表)==期望+1#多传的那个视为取消信号
        if len(值列表)!=期望 and not 有调用方信号:#个数不符
            约定=str(期望)+' argument(s)' if 'cancellation' not in 描述符 or 描述符['cancellation'] is None else str(期望)+' business argument(s) plus an optional AbortSignal'#约定文案
            raise 网关错误('arguments-invalid',端点,'client api: '+端点+' expected '+约定+', got '+str(len(值列表)))#组装错误
        参数={}#具名线参数
        if 投影 is not None:#需要注入上下文身份
            绑定器=None if 已绑身份 is not None else 自身.ownerCtx.typert.contexts.getClient(投影['context'])#绑定器
            if 已绑身份 is None and 绑定器 is None:#既无预绑定也无绑定器
                raise 网关错误('context-unavailable',端点,'client api: '+端点+' has no Client Context binder for '+repr(投影['context']))#无绑定器
            身份=已绑身份['value'] if 已绑身份 is not None else (绑定器.identity(调用方) if 绑定器 is not None else None)#身份
            if 身份 is None:#读不到
                raise 网关错误('context-unavailable',端点,'client api: '+端点+' requires a '+repr(投影['context'])+' Context')#需要上下文
            参数[投影['wire']]=解析(投影['codec'],身份,端点,投影['wire'])#编进线字段
        值下标=0#位置参数游标
        for 参数下标,参数描述 in enumerate(描述符['parameters']):#按描述符顺序
            if 投影 is not None and 参数下标==投影下标:#被作用域吃掉
                continue#跳过
            值=解析(参数描述['codec'],值列表[值下标],端点,参数描述['wire'])#解析
            if 值 is not None:#省略键不写线字段
                参数[参数描述['wire']]=值#写入
            值下标+=1#下一个
        连接=自身.ownerCtx.获取服务('connection')#活动连接
        if 连接 is None:#没有
            raise 网关错误('service-unavailable',端点,'client api: '+端点+' has no active Connection')#无连接
        调用方信号=值列表[期望] if 有调用方信号 else None#调用方信号
        信号=令牌['abort'].信号 if 调用方信号 is None else 中止信号.任一([令牌['abort'].信号,调用方信号])#合成
        try:
            结果=连接.rpc.call('/api',端点,{'args':参数},信号)#经 /api 同步调用
            if not 令牌['active']:#返回前已撤
                return 已撤(端点)#已撤
            if 'ok' not in 结果 or not 结果['ok']:#业务或分发失败
                return {'ok':False,'error':结果['error']}#原样
            return {'ok':True,'value':解析(描述符['result'],结果['value'],端点,'result')}#成功
        except BaseException as 错误:
            return 载体失败(端点,错误)#折成内部失败

def 应用(上下文):
    """在客户端根上挂载 Remote 服务。"""
    客户端远程服务(上下文)#构造并登记

inject=注入#框架槽
apply=应用#框架槽
