'通过 Cordis 服务与已注册提供方做在线 Typert Remote 分发'
import inspect,json,math,threading#签名、报文、有限数、事件队列
from uuid import uuid4 as 生成标识#代际与瀑布标识
from ...依赖.cordis.服务 import 服务#服务基类
from ...工具.超时 import 定时器延迟上限毫秒#心跳上限
from collections import deque#事件帧队列
from ...基础设施.通用工具 import 获取内部数据#解开调用方上下文壳
from ...类型化远程调用.协议 import 取远程错误,是否远程json值,远程方法列表,远程错误#绑定、JSON 与失败
from ...客户端.连接.rpc import 中止控制器,中止信号,登记进程内网关,投递进程内事件#调用取消与本进程客户端
from .异常 import 网关错误,远程已取消#分发失败
from .访问 import 调用资源,事件资源#非所有者资源
from .网关 import 远程流复用服务器,拒绝远程流升级#复用套接字
from .流协议 import (#线路报文与取消
    远程流复用路径,远程事件流端点,远程事件结果端点,远程事件流就绪,
    已中止,若中止则抛 as 若已中止则抛出,挂中止,合并信号,
    是否远程事件智能体标识,解析远程事件结果,投影远程事件请求,还原远程事件拒绝,
)#导入结束

默认心跳毫秒=2000#未配置时的 ping 间隔
默认收件箱字节=262144#一条逻辑流可缓冲的上行字节
源JSON编解码={'mode':'src-json'}#弱 JSON 编解码
永不中止=中止控制器().signal#没有载体信号时用这一路

class 网关配置:
    '传输配置。心跳从 1 到定时器上限，默认 2000；上行收件箱至少 1 字节，默认 262144'
    def 校验数据(自身,数据=None):
        '缺席字段用默认值。校验通过后返回完整配置'
        if 数据 is None:#没有配置
            数据={}#空
        if type(数据) is not dict:#必须是对象
            raise TypeError('gateway config must be an object')#拒绝
        心跳=数据['websocketHeartbeatIntervalMs'] if 'websocketHeartbeatIntervalMs' in 数据 else 默认心跳毫秒#心跳
        收件箱=数据['streamInboxBytes'] if 'streamInboxBytes' in 数据 else 默认收件箱字节#收件箱
        if type(心跳) is bool or type(心跳) is not int or 心跳<1 or 心跳>定时器延迟上限毫秒:#心跳非法
            raise ValueError('websocketHeartbeatIntervalMs must be an integer from 1 through '+str(定时器延迟上限毫秒))#拒绝
        if type(收件箱) is bool or type(收件箱) is not int or 收件箱<1:#收件箱非法
            raise ValueError('streamInboxBytes must be an integer of at least 1')#拒绝
        return {'websocketHeartbeatIntervalMs':心跳,'streamInboxBytes':收件箱}#归一化

配置=网关配置()#加载器读取的模式

def 是对象(值):
    '对应 JS 的对象或函数。数字、字符串、布尔和 None 不是'
    if 值 is None or isinstance(值,(str,bytes,bool,int,float)):#原始值
        return False#不是
    return True#是

def 是普通对象(值):
    '数组不是普通对象。这里要求 dict'
    return type(值) is dict#普通字典

def 拼端点(命名空间,方法):
    '返回 namespace/method'
    return 命名空间+'/'+方法#端点

def 取原始(接收方):
    '壳下面的服务实例。没有壳则就是接收方'
    if not 是对象(接收方):#没有实例
        return 接收方#原样
    目标=获取内部数据(接收方,'代理目标',None)#壳的目标
    if 是对象(目标):#是壳
        return 目标#实例
    return 接收方#本身

def 含客户(列表,客户):
    '按身份判断代际是否还在投递里'
    for 项 in 列表:#逐个
        if 项 is 客户:#同一个
            return True#在
    return False#不在

def 摘客户(列表,客户):
    '按身份从投递列表摘掉'
    for 下标,项 in enumerate(列表):#逐个
        if 项 is 客户:#同一个
            列表.pop(下标)#摘
            return#停

def 对等信号(对等):
    '对等端上的取消信号'
    if isinstance(对等,dict):#字典
        return 对等['signal']#信号
    return 对等.signal#属性

def 主体种类(对等):
    'principal.kind'
    主体=对等['principal'] if isinstance(对等,dict) else 对等.principal#主体
    if isinstance(主体,dict):#字典
        return 主体.get('kind')#种类
    return getattr(主体,'kind',None)#属性

def 交互方式(对等):
    'interactions'
    if isinstance(对等,dict):#字典
        return 对等.get('interactions')#字段
    return getattr(对等,'interactions',None)#属性

def 断言对等存活(对等,端点):
    '对等端已拆除则拒绝'
    if 对等 is None or 已中止(对等信号(对等)):#没有或已中止
        raise 网关错误('gateway/peer-disposed',端点,'the calling Peer has been disposed')#拒绝

def 要求交互(对等,端点):
    '转发事件只接受 interactions=answer'
    if 交互方式(对等)!='answer':#不是 answer
        raise 网关错误('gateway/interactions-forbidden',端点,'forwarded Remote events require interactions=answer')#拒绝

def 调用失败(错误):
    '把捕获错误折成 RPC 失败信封'
    远程=取远程错误(错误)#远程失败原样过
    if 远程 is not None:#是远程失败
        return {'ok':False,'error':{'code':远程.code,'message':远程.message,'details':远程.details}}#信封
    if isinstance(错误,BaseException):#异常
        消息=getattr(错误,'message',None)#Error.message
        if not isinstance(消息,str) or 消息=='':#没有 message
            消息=str(错误)#String(error)
    else:#不是异常
        消息=str(错误)#字符串化
    return {'ok':False,'error':{'code':'gateway/internal','message':消息,'details':{}}}#内部

def 线路错误(错误):
    '流失败要的 code、message、details'
    return 调用失败(错误)['error']#错误体

def 流中止失败(端点,原因):
    '远程失败原样作为流失败。其它中止是取消'
    if 取远程错误(原因) is not None:#已经是远程失败
        return 原因#原样
    return 远程已取消(端点,原因)#取消

def 释放上行(源):
    '没有人读的上行交还，让它别再缓冲。不额外等待'
    if 源 is None:#无
        return#停
    try:#取迭代器
        迭代=iter(源)#迭代器
    except TypeError:#不是可迭代
        return#停
    交还=getattr(迭代,'交还',None)#收件箱
    if callable(交还):#有
        交还()#交还
        return#完
    关闭=getattr(迭代,'close',None)#生成器
    if callable(关闭):#有
        关闭()#关闭

def 读取绑定(值,原始,服务键,端点,命名空间=None):
    '与接收方一致才通过'
    if (type(值) is not dict
            or 值.get('service') is not 原始
            or 值.get('serviceKey')!=服务键
            or not isinstance(值.get('namespace'),str)
            or (命名空间 is not None and 值.get('namespace')!=命名空间)):#不一致
        raise 网关错误(
            'gateway/binding-invalid',
            端点,
            'Service '+json.dumps(服务键)+' has an inconsistent typertRemote binding',
        )#拒绝
    return 值#绑定

def 无效签名(端点,方法):
    'SRC 参数必须是不重复的标识符，不能解构、默认或剩余'
    raise 网关错误(
        'gateway/signature-invalid',
        端点,
        'SRC method '+json.dumps(方法)+' must use unique identifier parameters without destructuring, defaults, or rest',
    )#拒绝

def 断言JSON值(值,祖先):
    'null、字符串、布尔、有限数字、稠密数组、普通对象'
    if 值 is None or isinstance(值,str) or isinstance(值,bool):#JSON 标量
        return#通过
    if isinstance(值,float):#浮点
        if math.isfinite(值):#有限
            return#通过
        raise TypeError('non-finite number is not JSON-safe')#拒绝
    if isinstance(值,int):#整数。布尔已在前面返回
        return#通过
    if not 是对象(值):#函数之类以外的原始值已处理
        raise TypeError(type(值).__name__+' is not JSON-safe')#拒绝
    身份=id(值)#循环
    if 身份 in 祖先:#环
        raise TypeError('cyclic value is not JSON-safe')#拒绝
    祖先.add(身份)#入栈
    try:#检查内部
        if isinstance(值,list):#数组
            for 项 in 值:#稠密，Python 列表没有空洞
                断言JSON值(项,祖先)#元素
            return#通过
        if type(值) is not dict:#非普通对象
            raise TypeError('non-plain object is not JSON-safe')#拒绝
        for 键,项 in 值.items():#自有键
            if not isinstance(键,str):#符号键在 Python 里不会出现，非字符串键拒绝
                raise TypeError('symbol property is not JSON-safe')#拒绝
            断言JSON值(项,祖先)#值
    finally:#出栈
        祖先.discard(身份)#去掉

def 解码(编解码,值,端点,字段):
    '严格模式先走 schema，再断言 JSON 安全'
    try:#边界失败都折成 input-invalid
        if isinstance(编解码,dict) and 编解码.get('mode')=='strict':#严格
            值=编解码['create']().parse(值)#schema
            if 值 is None:#可选输入编解码可以返回空
                return 值#空
        断言JSON值(值,set())#JSON 安全
        return 值#通过
    except 网关错误:#已经是网关错误
        raise#原样
    except Exception as 原因:#其它失败
        raise 网关错误(
            'gateway/input-invalid',
            端点,
            'wire field '+json.dumps(字段)+' failed boundary validation',
            {'cause':原因,'field':字段},
        )#折成输入无效

def 断言远程事件名(帧):
    '事件名必须是非空字符串'
    名=帧.get('event') if isinstance(帧,dict) else getattr(帧,'event',None)#名字
    if not isinstance(名,str) or 名=='':#空
        raise TypeError('typert gateway: Remote event name must be a nonempty string')#拒绝

def 远程请求(端点,载荷,信号,对等):
    '从 /api 载荷还原调用请求。已拆除的对等端直接拒绝'
    断言对等存活(对等,端点)#先看对等端
    段=端点.split('/')#两段
    if len(段)!=2 or 段[0]=='' or 段[1]=='':#不是 namespace/method
        raise Exception('invalid Remote endpoint '+json.dumps(端点))#拒绝
    if (type(载荷) is not dict
            or len(载荷)!=1
            or 'args' not in 载荷
            or type(载荷['args']) is not dict):#必须恰好一个 args 对象
        raise Exception('Remote payload must contain exactly one plain-object args field')#拒绝
    return {'namespace':段[0],'method':段[1],'args':载荷['args'],'signal':信号,'peer':对等}#请求

def 空上行():
    '没有上行时立即结束'
    if False:#让它成为生成器
        yield None#不会执行

class 远程事件队列:
    '一代客户端的拉取队列。中止时丢掉还没交出的帧'
    def __init__(自身):
        '空队列'
        自身.帧=deque()#帧
        自身.已关=False#是否关闭
        自身._条件=threading.Condition()#读者等待

    def 推入(自身,帧):
        '入队。已关闭则丢'
        with 自身._条件:#互斥
            if 自身.已关:#关了
                return#丢
            自身.帧.append(帧)#入队
            自身._条件.notify_all()#叫醒

    def 结束(自身):
        '关闭。重复调用无效果'
        with 自身._条件:#互斥
            if 自身.已关:#已经
                return#停
            自身.已关=True#关
            自身._条件.notify_all()#叫醒

    def 迭代(自身,信号):
        '拉到关闭或中止'
        摘=挂中止(信号,自身.结束)#中止时结束
        try:#保证摘掉
            while True:#直到结束
                下一项=None#本轮
                有=False#是否取出
                with 自身._条件:#互斥
                    if len(自身.帧)>0 and not 已中止(信号):#有帧且还活着
                        下一项=自身.帧.popleft()#取出
                        有=True#有
                    elif 自身.已关 or 已中止(信号):#结束
                        return#停
                    else:#等
                        自身._条件.wait()#阻塞
                        continue#再看
                if 有:#锁外交出
                    yield 下一项#一帧
        finally:#摘监听
            摘()#摘

class 上行解码器:
    'invocation.uplink() 返回的迭代。每项先过编解码，被拒绝则失败整条逻辑流'
    def __init__(自身,上行,编解码,端点,信号,中止):
        '挂上中止，让堵在 next 上的读者醒来'
        自身.编解码=编解码#编解码
        自身.端点=端点#端点
        自身.信号=信号#方法看到的信号
        自身.中止=中止#失败整条流
        自身.已关=False#下行结束
        自身.迭代=iter(上行)#载体迭代器
        def 当中止():
            '取消时让收件箱的下一次读取抛出'
            失败=流中止失败(端点,getattr(信号,'reason',None))#失败
            失败方法=getattr(上行,'失败',None)#收件箱
            if callable(失败方法):#是收件箱
                失败方法(失败 if isinstance(失败,BaseException) else Exception(str(失败)))#叫醒
        自身._摘=挂中止(信号,当中止)#监听

    def __iter__(自身):
        '自己就是迭代器'
        return 自身#自己

    def __next__(自身):
        '下一项。取消则抛。源结束则结束'
        if 已中止(自身.信号):#已取消
            失败=流中止失败(自身.端点,getattr(自身.信号,'reason',None))#失败
            if isinstance(失败,BaseException):#异常
                raise 失败#抛
            raise Exception(str(失败))#其它
        if 自身.已关:#已经结束
            raise StopIteration#结束
        try:#取下一项
            下一项=next(自身.迭代)#载体
        except StopIteration:#源结束
            自身._收尾()#摘监听
            raise#结束
        try:#解码
            if 下一项 is None and 自身.编解码.get('mode')=='src-json':#缺席的 value
                值=None#项本身就是空
            else:#按编解码
                值=解码(自身.编解码,下一项,自身.端点,'uplink')#解码
        except Exception:#编解码失败则失败整条流
            自身.中止()#中止
            raise#交给方法
        return 值#一项

    def 交还(自身):
        '下行结束或方法不再读。未读项丢掉'
        if not 自身.已关:#还开着
            自身._收尾()#关
            关闭=getattr(自身.迭代,'交还',None)#收件箱
            if not callable(关闭):#生成器
                关闭=getattr(自身.迭代,'close',None)#close
            if callable(关闭):#有
                关闭()#交还

    def _收尾(自身):
        '标记关闭并摘掉中止监听'
        自身.已关=True#关
        自身._摘()#摘

class 网关调用:
    '方法通过 this.ctx.invocation 读到的这一次调用。字段名保持 request、peer、signal'
    def __init__(自身,请求,服务名,对等,信号,上行):
        '上行在第一次 uplink() 时才解码'
        自身.request=请求#namespace、method、args
        自身.service=服务名#服务键
        自身.peer=对等#对等端
        自身.signal=信号#方法看到的信号
        自身._上行=上行#载体与编解码
        自身._解码器=None#第一次才建
        自身._已取=False#只能取一次

    def __getitem__(自身,键):
        '已有调用方按字典读 request 和 peer'
        if 键=='request':#请求
            return 自身.request#请求
        if 键=='peer':#对等端
            return 自身.peer#对等端
        if 键=='service':#服务
            return 自身.service#服务
        if 键=='signal':#信号
            return 自身.signal#信号
        if 键=='uplinkWindow':#窗口
            return 自身.uplinkWindow#窗口
        raise KeyError(键)#没有

    @property
    def uplinkWindow(自身):
        '载体给的帧容量。没有则 None'
        return 自身._上行.get('window')#窗口

    def uplink(自身):
        '每次调用只能取一次。没有声明上行时用 JSON 安全检查'
        if 自身._已取:#第二次
            raise Exception('typert gateway: '+自身._上行['endpoint']+': invocation.uplink() is available once per call')#拒绝
        自身._已取=True#占住
        自身._解码器=上行解码器(
            自身._上行['source'],
            自身._上行['codec'],
            自身._上行['endpoint'],
            自身.signal,
            自身._上行['abort'],
        )#解码器
        return 自身._解码器#迭代

    def 关闭(自身):
        '下行结束。没人取过的上行也交还，之后再 uplink() 会抛'
        if 自身._解码器 is not None:#取过
            自身._解码器.交还()#交还
            return#完
        自身._已取=True#禁止再取
        释放上行(自身._上行['source'])#交还载体

class 网关服务(服务):
    '用严格生成定义或保守 SRC 标记，对照当前服务与 Typert 提供方做解析'
    inject=['typert','remoteAccess']#依赖
    Config=配置#传输配置

    def __init__(自身,上下文,配置值=None):
        '向活动的 Typert 注册表登记网关。配置先按模式归一化'
        super().__init__(上下文,'typertGateway')#服务键
        已解析=配置.校验数据({} if 配置值 is None else 配置值)#默认值
        自身.wireStream={#载体适配器。键保持 open 与 failure
            'open':自身.打开线路流,
            'failure':线路错误,
        }#适配器结束
        自身.源声明=None#SRC 端点缓存
        自身.远程事件=None#唯一转发源
        自身.远程事件客户端={ }#代际
        自身.待决远程事件={ }#瀑布
        def 清声明():
            '服务表变化后重扫 SRC'
            自身.源声明=None#丢掉
        上下文.监听('internal/service',清声明)#服务变化
        def 挂进程内():
            '本进程的客户端直接调用这份网关'
            return 登记进程内网关(自身)#拆除时摘掉
        上下文.副作用(挂进程内,'api-gateway: in-process client')#跟插件走
        def 挂连接(连接上下文):
            '在 /api 上拦截本网关认领的端点'
            def 处理(端点,载荷,信号,对等=None):
                '连接目前只传端点、载荷、信号。对等端要由连接补上'
                return 自身.分发RPC(端点,载荷,信号,对等)#分发
            连接上下文.connection.rpc['intercept']('/api',自身.认领端点,处理,None)#拦截
        上下文.依赖启动(['connection'],挂连接)#有连接才挂
        def 挂网页(网页上下文):
            '应用就绪之后才接受复用升级'
            def 开始听():
                '登记升级路由'
                def 打开复用(端点,载荷,上行,对等,控制,窗口):
                    '复用服务器的打开函数已经带上对等端和控制'
                    return 自身.打开线路流(端点,载荷,上行,对等,控制.signal,控制,窗口)#打开
                复用=远程流复用服务器(
                    打开复用,
                    自身.wireStream['failure'],
                    已解析['websocketHeartbeatIntervalMs'],
                    已解析['streamInboxBytes'],
                )#复用服务器
                def 效应():
                    '拆除时关掉复用'
                    def 拆除():
                        '关闭全部套接字'
                        复用.关闭()#关
                    yield 拆除#先登记清理
                    def 处理(请求,套接字,头):
                        '准入之后交给复用服务器'
                        准入=网页上下文.connection.admitConnection(请求)#准入
                        if isinstance(准入,dict) and 'rejection' in 准入:#拒绝
                            拒绝远程流升级(套接字,准入['rejection'])#HTTP 拒绝
                            return#不升级
                        已释放={'v':False}#释放只做一次
                        def 释放():
                            '同步摘掉 API 对等端'
                            if 已释放['v']:#已经
                                return#停
                            已释放['v']=True#占住
                            try:#释放可能失败
                                准入['release']()#释放
                            except Exception as 错误:#失败
                                print('[api-gateway] Peer release failed:',错误)#诊断
                        def 当错误():
                            '出错也释放'
                            释放()#释放
                        def 当关闭():
                            '关闭时摘掉错误监听并释放'
                            摘=getattr(套接字,'off',None)#可能有
                            if callable(摘):#有
                                摘('error',当错误)#摘
                            释放()#释放
                        if hasattr(套接字,'on'):#有事件
                            套接字.on('error',当错误)#出错
                        if hasattr(套接字,'once'):#有一次
                            套接字.once('close',当关闭)#关闭
                        if getattr(套接字,'destroyed',False):#已经拆了
                            当关闭()#释放
                            return#不升级
                        try:#升级
                            复用.处理升级(请求,套接字,头,准入['peer'])#服务
                        except Exception as 错误:#升级失败
                            释放()#释放
                            if hasattr(套接字,'destroy'):#可拆
                                套接字.destroy()#拆
                            print('[api-gateway] Remote stream upgrade failed:',错误)#诊断
                    路由={'path':远程流复用路径,'handler':处理}#升级路由
                    yield 网页上下文.webServer.registerUpgrade(路由)#登记
                网页上下文.副作用(效应,'api-gateway: '+远程流复用路径+' WebSocket')#生命周期
            就绪=网页上下文.反射.获取服务('appReady')#启动器就绪
            if 就绪 is None:#没有就绪门
                开始听()#马上听
            else:#等就绪
                def 等就绪():
                    '就绪前不接受流'
                    已关={'v':False}#拆除后不再听
                    def 到了():
                        '就绪回调'
                        if not 已关['v']:#还活着
                            开始听()#开始
                    取消=就绪.onReady(到了)#登记
                    def 拆除():
                        '取消尚未发生的就绪回调'
                        已关['v']=True#关
                        取消()#摘
                    return 拆除#拆除器
                网页上下文.副作用(等就绪,'api-gateway: application readiness')#等就绪
        上下文.依赖启动(['connection','webServer'],挂网页)#两者都在才挂

    def 有活动客户端(自身):
        '是否有尚未取消、并且能回答瀑布的所有者事件流'
        for 客户 in 自身.远程事件客户端.values():#每一代
            if 客户['回答'] and not 已中止(客户['信号']):#所有者且活着
                return True#有
        return False#没有

    def 登记远程事件(自身,源,宿主):
        '登记本应用选定的转发事件源。返回拆除器'
        if 自身.远程事件 is not None:#已经有
            raise Exception('typert gateway: forwarded Remote event source is already registered')#拒绝
        寿命=中止控制器()#源的寿命
        流=源(寿命.signal)#事件流
        完成=threading.Event()#消费结束
        登记={'寿命':寿命,'完成':完成,'宿主':{'home':宿主['home']}}#登记
        def 消费():
            '消费。源自己结束且不是拆除，则关掉全部挂起'
            try:#消费
                自身.消费远程事件(流,寿命.signal)#消费
            except Exception as 错误:#失败
                if 自身.远程事件 is not 登记 or 已中止(寿命.signal):#已经换掉或拆除
                    完成.set()#结束
                    return#不关别人的
                自身.关闭远程事件(错误)#拒绝挂起
                if 自身.远程事件 is 登记:#还是这一份
                    自身.远程事件=None#摘掉
                寿命.abort(错误)#中止
            完成.set()#结束
        threading.Thread(target=消费,daemon=True).start()#不堵登记
        自身.远程事件=登记#占住
        def 拆除():
            '摘掉这一份并等消费静默'
            if 自身.远程事件 is 登记:#还是这一份
                自身.远程事件=None#摘掉
                错误=Exception('typert gateway: forwarded Remote event source was removed')#原因
                登记['寿命'].abort(错误)#中止
                自身.关闭远程事件(错误)#拒绝挂起
            登记['完成'].wait()#等静默
        return 拆除#拆除器

    def 认领端点(自身,端点):
        '两端非空。严格定义、曾见或 SRC 声明命中则认领'
        if 端点==远程事件结果端点:#结果端点归网关
            return True#认领
        段=端点.split('/')#两段
        if len(段)!=2 or 段[0]=='' or 段[1]=='':#非法
            return False#不认领
        if 自身.ctx.typert.local.get(端点) is not None or 自身.ctx.typert.local.hasSeen(端点):#严格或曾见
            return True#认领
        if 自身.源声明 is None:#还没扫
            自身.源声明=自身.收集源声明()#扫一次
        return 端点 in 自身.源声明#SRC

    def 收集源声明(自身):
        '遍历服务上的 typertRemote 绑定'
        认领=set()#端点
        for 服务键,定义 in 自身.ctx.反射.属性表.items():#反射属性
            if 定义.get('类型')!='服务':#不是服务
                continue#下一个
            接收方=取原始(自身.ctx.反射.获取服务(服务键))#实现
            if not 是对象(接收方):#没有
                continue#下一个
            绑定=getattr(接收方,'typertRemote',None)#绑定
            if type(绑定) is not dict or not isinstance(绑定.get('namespace'),str):#不像绑定
                continue#下一个
            命名空间=绑定['namespace']#命名空间
            for 标记 in 远程方法列表(接收方):#方法
                认领.add(拼端点(命名空间,标记['exportName'] if 'exportName' in 标记 else 标记['method']))#端点
        return 认领#集合

    def 直接执行(自身,端点,载荷,信号):
        '本进程调用宿主方法，返回它交出的对象。不编码，不套流载体'
        对等={'principal':{'kind':'owner'},'interactions':'answer','signal':永不中止}#所有者
        请求=远程请求(端点,载荷,信号,对等)#还原请求
        准备=自身.准备调用(请求,中止控制器())#解析到方法对象
        是流=准备['描述符'].get('mode')=='stream'#描述符上的流
        调用标记=准备['描述符'].get('invocation')#调用标记
        if isinstance(调用标记,dict) and 调用标记.get('mode')=='stream':#流标在调用上
            是流=True#也是流
        if 是流:#生成器交给调用方自己迭代
            return 准备['方法'](*准备['参数'])#对象
        try:#一元
            return 准备['方法'](*准备['参数'])#对象
        finally:#用完这次调用
            准备['调用'].关闭()#交还

    def 调用(自身,请求):
        '调用一个在线 Remote 方法，不假设载体信封'
        return 自身.调用已准备(自身.准备调用(请求,中止控制器()))#准备后调用

    def 调用已准备(自身,准备):
        '一元调用。流方法必须走流载体'
        if 准备['描述符'].get('mode') is not None:#是流
            raise 网关错误(
                'gateway/signature-invalid',
                准备['端点'],
                'stream Remote methods must be opened through the stream carrier',
            )#拒绝
        try:#业务方法
            return 准备['方法'](*准备['参数'])#结果
        except Exception as 错误:#业务或中止
            if 已中止(准备['调用'].signal):#调用已被取消
                raise 远程已取消(准备['端点'],错误)#取消
            raise#业务错误原样
        finally:#一元调用的上行只在方法运行时可读
            准备['调用'].关闭()#交还

    def 打开流(自身,请求):
        '打开一条流方法，返回可取消的迭代'
        return 自身.打开业务流(请求,中止控制器())#打开

    def 打开业务流(自身,请求,控制):
        '流方法返回迭代。一元方法不能从这里打开'
        准备=自身.准备调用(请求,控制)#准备
        if 准备['描述符'].get('mode') is None:#一元
            准备['调用'].关闭()#交还
            raise 网关错误(
                'gateway/signature-invalid',
                准备['端点'],
                'unary Remote methods cannot be opened through the stream carrier',
            )#拒绝
        try:#调用方法
            源=准备['方法'](*准备['参数'])#迭代或生成器
        except Exception as 错误:#方法抛了
            准备['调用'].关闭()#交还
            if 已中止(准备['调用'].signal):#已取消
                raise 远程已取消(准备['端点'],错误)#取消
            raise#原样
        可迭代=是对象(源) and (hasattr(源,'__iter__') or hasattr(源,'__next__'))#迭代
        if not 可迭代:#不是迭代
            准备['调用'].关闭()#交还
            raise 网关错误(
                'gateway/result-invalid',
                准备['端点'],
                'stream Remote method did not return Iterable or AsyncIterable',
                {'field':'result'},
            )#拒绝
        return 自身.可取消流(源,准备['端点'],准备['调用'])#包一层取消

    def 可取消流(自身,源,端点,调用):
        '消费业务迭代。取消时先关上行再交还迭代器'
        信号=调用.signal#方法信号
        迭代=iter(源)#迭代器
        def 当中止():
            '中止时没有单独的赛跑，下一轮循环会看到'
            return None#循环里检查
        摘=挂中止(信号,当中止)#挂上。真正叫醒靠上行失败
        try:#消费
            while True:#直到结束或取消
                if 已中止(信号):#取消
                    失败=流中止失败(端点,getattr(信号,'reason',None))#失败
                    if isinstance(失败,BaseException):#异常
                        raise 失败#抛
                    raise Exception(str(失败))#其它
                try:#下一项
                    值=next(迭代)#取
                except StopIteration:#结束
                    return#停
                yield 值#交出
        finally:#清理
            摘()#摘监听
            调用.关闭()#先关上行
            交还=getattr(迭代,'close',None)#生成器
            if callable(交还):#有
                交还()#交还

    def 分发RPC(自身,端点,载荷,信号,对等):
        '事件结果走专门路径，其余进入一元调用'
        if 端点==远程事件结果端点:#瀑布结果
            try:#失败折成信封
                断言对等存活(对等,端点)#对等端
                要求交互(对等,端点)#必须 answer
                if 主体种类(对等)!='owner':#只有所有者
                    raise 网关错误('gateway/invocation-unavailable',端点,'only owner Peers answer forwarded Remote events')#拒绝
                if (type(载荷) is not dict or len(载荷)!=1 or 'args' not in 载荷):#恰好 args
                    raise Exception('typert gateway: Remote event result requires exactly one plain-object args field')#拒绝
                结果=解析远程事件结果(载荷['args'])#结果
                客户=自身.远程事件客户端.get(结果['clientId'])#代际
                if 客户 is None:#没有这条流
                    raise Exception('typert gateway: Remote event result identifies no active event stream')#拒绝
                if 客户['对等'] is not 对等:#不是这条对等端
                    raise 网关错误('gateway/interactions-forbidden',端点,'Remote event result belongs to another Peer')#拒绝
                自身.收取远程事件结果(客户,结果)#结算
                return {'ok':True}#无 value
            except Exception as 错误:#折成信封
                return 调用失败(错误)#失败
        return 自身.调用RPC(端点,载荷,信号,对等)#一元

    def 打开线路流(自身,端点,载荷,上行,对等,信号,控制,上行窗口=None):
        'WebSocket 和进程内载体共用。事件流不读上行'
        if 端点==远程事件流端点:#转发事件
            释放上行(上行)#马上交还，避免进有界收件箱
            断言对等存活(对等,端点)#对等端
            要求交互(对等,端点)#answer
            return 自身.打开远程事件(载荷,信号,对等)#事件迭代
        请求=远程请求(端点,载荷,信号,对等)#普通请求
        请求['uplink']=上行#上行
        请求['uplinkWindow']=上行窗口#窗口
        return 自身.打开业务流(请求,控制)#业务流

    def 打开远程事件(自身,载荷,信号,对等):
        '打开一条转发事件流。载荷必须是 {args:{}}'
        参数=载荷.get('args') if type(载荷) is dict else None#args
        if (type(载荷) is not dict
                or len(载荷)!=1
                or 'args' not in 载荷
                or type(参数) is not dict
                or len(参数)!=0):#必须是空 args
            raise 网关错误(
                'gateway/arguments-invalid',
                远程事件流端点,
                'forwarded Remote event stream requires an empty args object',
            )#拒绝
        登记=自身.远程事件#当前源
        if 登记 is None:#没有源
            raise 网关错误(
                'gateway/service-unavailable',
                远程事件流端点,
                'forwarded Remote event source is unavailable',
            )#拒绝
        寿命=合并信号(信号,登记['寿命'].signal,对等信号(对等))#三路取消
        客户标识=str(生成标识())#代际
        while 客户标识 in 自身.远程事件客户端:#撞了
            客户标识=str(生成标识())#再抽
        客户={#这一代
            '对等':对等,
            '标识':客户标识,
            '队列':远程事件队列(),
            '信号':寿命,
            '投递':{},
            '主体':对等['principal'] if isinstance(对等,dict) else 对等.principal,
            '回答':主体种类(对等)=='owner',
        }#客户结束
        自身.远程事件客户端[客户标识]=客户#登记
        if 客户['回答']:#所有者补上还没结束的瀑布
            for 挂起 in 自身.待决远程事件.values():#每一个
                自身.投递远程事件(挂起,客户)#补投
        try:#先就绪再拉队列
            就绪=dict(远程事件流就绪)#type ready
            就绪['clientId']=客户标识#代际
            就绪['host']=登记['宿主']#宿主事实
            yield 就绪#开口
            yield from 客户['队列'].迭代(寿命)#后续帧
        finally:#代际结束
            自身.移除远程事件客户端(客户)#摘掉

    def 消费远程事件(自身,源,信号):
        '消费应用事件源。意外结束则抛'
        for 分发 in 源:#逐条
            if 已中止(信号):#源被取消
                if isinstance(分发,dict) and 'context' in 分发:#瀑布
                    分发['reject'](getattr(信号,'reason',None))#拒绝
                return#停
            if isinstance(分发,dict) and 'context' in 分发:#瀑布
                自身.启动远程事件(分发)#启动
            else:#通知
                自身.广播远程事件(分发)#广播
        if not 已中止(信号):#不该自己结束
            raise Exception('typert gateway: forwarded Remote event source ended unexpectedly')#拒绝

    def 广播远程事件(自身,帧):
        '向所有代际推 emit。非所有者由资源判定整条收或整条不收'
        断言远程事件名(帧)#名字
        if not isinstance(帧.get('args'),list) or not 是否远程json值(帧['args']):#参数必须是无损 JSON 数组
            raise TypeError('typert gateway: Remote event '+json.dumps(帧.get('event'))+' arguments are not lossless JSON data')#拒绝
        线路={'type':'emit','event':帧['event'],'args':帧['args']}#线路帧
        投递进程内事件(帧['event'],帧['args'])#本进程的客户端不走套接字
        已解析=False#资源只算一次
        资源=None#资源
        for 客户 in 自身.远程事件客户端.values():#每一代
            if not 客户['回答']:#非所有者
                if not 已解析:#第一次
                    资源=事件资源(帧.get('resources'),帧['args'])#资源
                    已解析=True#算过
                if 资源 is None:#资源无效则谁也不给
                    continue#跳过
                判定=自身.ctx.remoteAccess.判定访问({#判定
                    'principal':客户['主体'],
                    'action':'event:'+帧['event'],
                    'resources':资源,
                })#判定结束
                if 判定['kind']=='deny':#拒绝
                    continue#不推
            客户['队列'].推入(线路)#推

    def 启动远程事件(自身,源):
        '把一次瀑布投递给现有的所有者代际'
        try:#校验失败则拒绝源
            断言远程事件名(源)#名字
            if not 是否远程事件智能体标识(源['context']['agentId']):#要有智能体标识
                raise TypeError('typert gateway: scoped Remote events require a non-empty Agent identity')#拒绝
            投影=投影远程事件请求(源['request'],源['context']['subject'])#去掉 agent 和 signal
            标识=str(生成标识())#事件标识
            while 标识 in 自身.待决远程事件:#撞了
                标识=str(生成标识())#再抽
            挂起={'标识':标识,'源':源}#先占住，效应里要引用
            try:#上下文已经释放则直接 next
                def 效应(挂起=挂起):
                    '上下文释放时取消'
                    def 拆除():
                        'Agent Context 没了'
                        自身.取消远程事件(挂起,Exception('typert gateway: Remote event Agent Context was released'))#取消
                    return 拆除#拆除器
                拆除上下文=源['context']['value'].副作用(
                    效应,
                    'api-gateway: Remote event '+json.dumps(源['event']),
                )#登记
            except Exception:#登记失败
                源['resolve']({'kind':'next'})#交给宿主链
                return#停
            信号表=[]#要听的信号
            if 投影.get('signal') is not None:#请求上有信号
                信号表.append(投影['signal'])#听
            def 中止时(挂起=挂起,信号表=信号表):
                '任一信号中止则取消瀑布'
                原因=None#原因
                for 一路 in 信号表:#找已经中止的
                    if 已中止(一路):#中止了
                        原因=getattr(一路,'reason',None)#原因
                        break#用这一路
                if isinstance(原因,BaseException):#异常
                    自身.取消远程事件(挂起,原因)#用它
                else:#其它
                    错误=Exception('typert gateway: Remote event was cancelled')#包装
                    if 原因 is not None:#有原因
                        错误.__cause__=原因 if isinstance(原因,BaseException) else None#挂不上非异常
                    自身.取消远程事件(挂起,错误)#取消
            帧={#线路帧
                'type':'waterfall',
                'event':源['event'],
                'eventId':标识,
                'agentId':源['context']['agentId'],
                'request':投影['request'],
            }#帧结束
            摘掉=[]#信号拆除
            def 放信号():
                '摘掉信号监听'
                for 摘 in 摘掉:#逐个
                    摘()#摘
            挂起.update({#补齐
                '帧':帧,
                '投递':[],
                '放上下文':拆除上下文,
                '放信号':放信号,
            })#补齐结束
            自身.待决远程事件[标识]=挂起#登记
            for 一路 in 信号表:#听
                摘掉.append(挂中止(一路,中止时))#登记
            if any(已中止(一路) for 一路 in 信号表):#登记时已经中止
                中止时()#马上取消
            else:#投递给现有所有者
                for 客户 in 自身.远程事件客户端.values():#每一代
                    if 客户['回答']:#所有者
                        自身.投递远程事件(挂起,客户)#投递
        except Exception as 错误:#校验失败
            源['reject'](错误)#拒绝源

    def 投递远程事件(自身,挂起,客户):
        '把瀑布帧推给一代'
        if not 含客户(挂起['投递'],客户):#还没
            挂起['投递'].append(客户)#记下
        客户['投递'][挂起['标识']]=挂起#反向
        客户['队列'].推入(挂起['帧'])#推

    def 收取远程事件结果(自身,客户,结果):
        '结算一次客户端瀑布结果。过期结果无效果'
        挂起=自身.待决远程事件.get(结果['eventId'])#挂起
        if 挂起 is None or not 含客户(挂起['投递'],客户):#已经结束或不是这一代
            return#无效果
        自身.移除远程事件投递(挂起,客户)#摘掉这一代
        结局=结果['outcome']#结局
        if 结局['kind']=='result':#有结果
            结算={'kind':'result'}#结算
            if 'value' in 结局:#有值才带
                结算['value']=结局['value']#值
            自身.结算远程事件(挂起,结算)#兑现
        elif 结局['kind']=='rejected':#拒绝
            自身.取消远程事件(挂起,还原远程事件拒绝(结局['error']))#取消
        elif len(挂起['投递'])==0:#都委托了
            自身.结算远程事件(挂起,{'kind':'next'})#交给下一段

    def 移除远程事件投递(自身,挂起,客户):
        '摘掉一代对某瀑布的投递'
        摘客户(挂起['投递'],客户)#正向
        客户['投递'].pop(挂起['标识'],None)#反向

    def 移除远程事件客户端(自身,客户):
        '代际结束'
        自身.远程事件客户端.pop(客户['标识'],None)#摘掉
        for 挂起 in list(客户['投递'].values()):#还指着它的瀑布
            自身.移除远程事件投递(挂起,客户)#摘
        客户['队列'].结束()#队列关闭

    def 结算远程事件(自身,挂起,结局):
        '兑现源监听'
        自身.结束远程事件(挂起)#收尾
        挂起['源']['resolve'](结局)#兑现

    def 取消远程事件(自身,挂起,原因):
        '拒绝源监听。已经不是这一份则不动'
        if 自身.待决远程事件.get(挂起['标识']) is not 挂起:#不是当前
            return#停
        自身.结束远程事件(挂起)#收尾
        挂起['源']['reject'](原因)#拒绝

    def 结束远程事件(自身,挂起):
        '摘掉挂起并通知各代际取消'
        自身.待决远程事件.pop(挂起['标识'],None)#摘掉
        挂起['放信号']()#摘信号
        挂起['放上下文']()#摘上下文
        客户们=list(挂起['投递'])#当前代际
        for 客户 in 客户们:#摘投递
            自身.移除远程事件投递(挂起,客户)#摘
        取消帧={'type':'cancel','eventId':挂起['标识']}#取消帧
        for 客户 in 客户们:#通知
            客户['队列'].推入(取消帧)#推

    def 关闭远程事件(自身,原因):
        '源拆除时拒绝全部挂起，并结束各代际队列'
        for 挂起 in list(自身.待决远程事件.values()):#每一个
            自身.取消远程事件(挂起,原因)#拒绝
        for 客户 in list(自身.远程事件客户端.values()):#每一代
            客户['队列'].结束()#结束

    def 调用RPC(自身,端点,载荷,信号,对等):
        '成功带 value。空结果不带 value。失败折成信封'
        try:#准备和调用
            准备=自身.准备调用(远程请求(端点,载荷,信号,对等),中止控制器())#准备
            值=自身.调用已准备(准备)#调用
            return 自身.编码结果(值,准备['描述符']['result'])#信封
        except Exception as 错误:#折成信封
            return 调用失败(错误)#失败

    def 编码结果(自身,值,编解码):
        '严格模式走 encode。否则抽出字节附件'
        附件=[]#字节附件
        路径=[]#当前路径
        def 写字节(数据,所在路径):
            '记一条附件，值的位置写成 null'
            附件.append({'path':list(所在路径),'bytes':bytes(数据)})#附件
            return None#JSON 里的 null
        if isinstance(编解码,dict) and 编解码.get('mode')=='strict':#严格
            编码函数=编解码.get('encode')#可能没有
            编码=编码函数(值,写字节) if callable(编码函数) else 值#编码
        else:#运行时
            祖先=set()#环
            def 抽取(输入,键):
                'toJSON 只走一次。字节变成附件'
                当前=输入#当前值
                if 输入 is not None and 是对象(输入) and not isinstance(输入,(bytes,bytearray)):#对象
                    转=输入.get('toJSON') if isinstance(输入,dict) else getattr(输入,'toJSON',None)#toJSON
                    if callable(转):#有
                        当前=转(键)#调用一次
                if isinstance(当前,(bytes,bytearray)):#字节
                    return 写字节(当前,路径)#附件
                if 当前 is None or isinstance(当前,(str,bool,int,float)):#标量
                    return 当前#原样
                身份=id(当前)#环
                if 身份 in 祖先:#环
                    raise TypeError('gateway: circular RPC result')#拒绝
                祖先.add(身份)#入栈
                if isinstance(当前,list):#数组
                    副本=[]#拷贝
                    for 下标 in range(len(当前)):#含空洞位置，Python 没有空洞
                        副本.append(子项(当前[下标],下标))#元素
                else:#对象
                    副本={}#拷贝
                    键列表=list(当前.keys()) if isinstance(当前,dict) else list(getattr(当前,'__dict__',{}).keys())#键
                    for 名 in 键列表:#逐个
                        项=当前[名] if isinstance(当前,dict) else getattr(当前,名)#值
                        if 名=='toJSON' and callable(项):#投影上的 toJSON 不再跑
                            continue#跳
                        抽出=子项(项,名)#递归
                        副本[名]=抽出#写入
                祖先.discard(身份)#出栈
                return 副本#拷贝
            def 子项(项,键):
                '标量直接返回，对象才入路径'
                if 项 is None or not 是对象(项):#标量
                    return 项#原样
                路径.append(键)#入路径
                try:#抽取
                    return 抽取(项,str(键))#抽取
                finally:#出路径
                    路径.pop()#出
            编码=抽取(值,'value')#从根
        结果={'ok':True,'value':编码}#成功
        if len(附件)>0:#有附件
            结果['attachments']=附件#带上
        return 结果#信封

    def 准备调用(自身,请求,控制):
        '解析描述符、访问、接收方和参数。控制在上行被拒绝时失败整条流'
        端点=拼端点(请求['namespace'],请求['method'])#端点
        断言对等存活(请求['peer'],端点)#对等端
        描述符=自身.解析描述符(请求['namespace'],请求['method'],端点)#描述符
        参数=请求['args']#线路参数
        if not 是普通对象(参数):#必须是普通对象
            raise 网关错误('gateway/arguments-invalid',端点,'args must be a plain object')#拒绝
        期望=set(项['wire'] for 项 in 描述符['parameters'])#参数字段
        if 描述符['invocation']['kind']=='context':#上下文身份也是字段
            期望.add(描述符['invocation']['wire'])#加上
        多余=[键 for 键 in 参数 if not isinstance(键,str) or 键 not in 期望]#多出来的
        可缺=set()#json 可以省略的字段
        for 项 in 描述符['parameters']:#逐个
            if 项['source']=='json' and (项.get('acceptsUndefined') is True or 项['codec'].get('mode')=='src-json'):#可省略
                可缺.add(项['wire'])#记下
        缺少=[键 for 键 in 期望 if 键 not in 参数 and 键 not in 可缺]#缺的
        if len(多余)>0 or len(缺少)>0:#对不上
            句子=[]#说明
            if len(缺少)>0:#缺
                句子.append('missing '+', '.join(json.dumps(键) for 键 in 缺少))#缺
            if len(多余)>0:#多
                句子.append('unexpected '+', '.join(json.dumps(str(键)) for 键 in 多余))#多
            raise 网关错误(
                'gateway/arguments-invalid',
                端点,
                'args fields do not match the descriptor: '+'; '.join(句子),
            )#拒绝
        已校验={}#访问判定用的参数
        if 描述符['invocation']['kind']=='context':#身份原样
            已校验[描述符['invocation']['wire']]=参数[描述符['invocation']['wire']]#原样
        for 项 in 描述符['parameters']:#逐个参数
            if 项['wire'] not in 参数:#缺席保持缺席
                continue#下一个
            值=参数[项['wire']]#线路值
            if 项['source']=='json':#JSON 先解码
                已校验[项['wire']]=解码(项['codec'],值,端点,项['wire'])#解码
            else:#查找和身份先留线路值
                已校验[项['wire']]=值#原样
        if 主体种类(请求['peer'])!='owner':#非所有者先访问再查找
            读取器=自身.资源读取器(描述符)#方法上的读取器
            信号=请求['signal'] if 请求.get('signal') is not None else 永不中止#取消槽
            资源=调用资源(自身.ctx.typert,读取器,描述符,已校验,信号)#资源
            if 资源 is None:#资源无效
                判定={'kind':'deny','reason':'resource-invalid'}#拒绝
            else:#问访问服务
                判定=自身.ctx.remoteAccess.判定访问({#请求
                    'principal':请求['peer']['principal'] if isinstance(请求['peer'],dict) else 请求['peer'].principal,
                    'action':描述符['namespace']+'/'+描述符['method'],
                    'resources':资源,
                    'args':已校验,
                })#判定结束
            if 判定['kind']=='deny':#拒绝
                raise 远程错误(
                    'remote-access/denied',
                    'remote access: '+端点+': access denied ('+判定['reason']+')',
                    {'action':端点,'reason':判定['reason']},
                )#拒绝
        接收上下文=自身.解析接收上下文(描述符,已校验,端点)#接收上下文
        接收方=接收上下文.反射.获取服务(描述符['service'])#服务
        if not 是对象(接收方):#没有
            raise 网关错误(
                'gateway/service-unavailable',
                端点,
                'active Service '+json.dumps(描述符['service'])+' is unavailable',
            )#拒绝
        原始=取原始(接收方)#壳下面的实例
        绑定值=getattr(原始,'typertRemote',None)#绑定
        if 绑定值 is None:#没有
            raise 网关错误(
                'gateway/binding-invalid',
                端点,
                'Service '+json.dumps(描述符['service'])+' has no visible typertRemote binding',
            )#拒绝
        读取绑定(绑定值,原始,描述符['service'],端点,描述符['namespace'])#校验
        实参=[]#方法参数
        for 项 in 描述符['parameters']:#按描述符顺序
            实参.append(自身.解析参数(项,已校验,端点))#解析
        载体=请求.get('signal')#载体信号
        是流=描述符.get('mode')=='stream'#流
        if 请求.get('uplink') is None and not 是流:#一元且没有上行
            信号=载体 if 载体 is not None else 永不中止#保持载体信号
        else:#流或有上行，并上控制
            路=[]#要合并的信号
            if 载体 is not None and 载体 is not 控制.signal:#载体不是控制自己
                路.append(载体)#载体
            路.append(控制.signal)#控制
            if 是流:#流还并上对等端寿命
                路.append(对等信号(请求['peer']))#对等端
            信号=合并信号(*路)#合并
        def 中止控制(原因,控制=控制):
            '上行项被拒绝时中止逻辑流'
            控制.abort(原因)#中止
        调用=网关调用(
            {'namespace':请求['namespace'],'method':请求['method'],'args':请求['args']},
            描述符['service'],
            请求['peer'],
            信号,
            {#上行源
                'source':请求['uplink'] if 请求.get('uplink') is not None else 空上行(),
                'window':请求.get('uplinkWindow'),
                'codec':描述符['uplink']['codec'] if 描述符.get('uplink') is not None else 源JSON编解码,
                'endpoint':端点,
                'abort':中止控制,
            },
        )#调用
        if 描述符.get('cancellation') is not None:#方法要信号
            实参.append(信号)#放在最后
        调用上下文=接收上下文.扩展({'invocation':调用})#带上这次调用
        调用接收方=调用上下文.反射.获取服务(描述符['service'])#重新取，ctx 指向这次调用
        实现名=描述符['implementation'] if 描述符.get('implementation') is not None else 描述符['method']#实现名
        方法=getattr(调用接收方,实现名,None)#方法
        if not callable(方法):#不能调用
            raise 网关错误(
                'gateway/method-unavailable',
                端点,
                'active Service '+json.dumps(描述符['service'])+' has no callable method '+json.dumps(实现名),
            )#拒绝
        return {#准备结果
            '端点':端点,
            '描述符':描述符,
            '接收方':调用接收方,
            '参数':实参,
            '方法':方法,
            '调用':调用,
        }#结果结束

    def 资源读取器(自身,描述符):
        '从根服务类上的远程标记读 resources。没有则 None'
        接收方=取原始(自身.ctx.反射.获取服务(描述符['service']))#服务实例
        if not 是对象(接收方):#没有
            return None#无
        成员=描述符['implementation'] if 描述符.get('implementation') is not None else 描述符['method']#方法名
        for 标记 in 远程方法列表(接收方):#标记
            if 标记['method']==成员:#命中
                return 标记.get('resources')#可能没有
        return None#没有

    def 解析描述符(自身,命名空间,方法,端点):
        '有严格定义用之。曾见但已撤回则禁止 SRC'
        严格=自身.ctx.typert.local.get(端点)#严格
        if 严格 is not None:#有
            return 严格#用它
        if 自身.ctx.typert.local.hasSeen(端点):#曾见
            raise 网关错误(
                'gateway/definition-unavailable',
                端点,
                'its strict definition was withdrawn and SRC fallback is forbidden',
            )#禁止回退
        return 自身.解析源描述符(命名空间,方法,端点)#SRC

    def 解析源描述符(自身,命名空间,方法,端点):
        '多个服务导出同一端点则歧义'
        候选=[]#描述符
        for 服务键,定义 in 自身.ctx.反射.属性表.items():#服务
            if 定义.get('类型')!='服务':#不是
                continue#下一个
            接收方=取原始(自身.ctx.反射.获取服务(服务键))#实现
            if not 是对象(接收方):#没有
                continue#下一个
            值=getattr(接收方,'typertRemote',None)#绑定
            if 值 is None:#没有
                continue#下一个
            绑定=读取绑定(值,接收方,服务键,端点)#校验
            if 绑定['namespace']!=命名空间:#命名空间不同
                continue#下一个
            标记=None#命中的标记
            for 一项 in 远程方法列表(接收方):#方法
                导出名=一项['exportName'] if 'exportName' in 一项 else 一项['method']#导出名
                if 导出名==方法:#命中
                    标记=一项#记下
                    break#停
            if 标记 is None:#没有
                continue#下一个
            候选.append(自身.源描述符(绑定,标记,方法,端点))#一个候选
        if len(候选)==0:#没有
            raise 网关错误('gateway/invocation-unavailable',端点,'no active Remote method exports this endpoint')#拒绝
        if len(候选)>1:#歧义
            名字=sorted(一项['service'] for 一项 in 候选)#服务名
            raise 网关错误(
                'gateway/ambiguous-endpoint',
                端点,
                'multiple active Services export this endpoint: '+', '.join(名字),
            )#拒绝
        return 候选[0]#唯一

    def 源描述符(自身,绑定,标记,方法,端点):
        '从签名读参数名，按 lookup 声明推导来源'
        实现=None#方法函数
        for 类 in type(绑定['service']).__mro__:#沿原型
            if 方法 in 类.__dict__:#这一层有
                描述=类.__dict__[方法]#描述
                if callable(描述):#是函数
                    实现=描述#记下
                break#停，即使不是函数也不再往下
        if 实现 is None:#没有
            raise 网关错误(
                'gateway/method-unavailable',
                端点,
                'Remote marker has no prototype method '+json.dumps(方法),
            )#拒绝
        try:#签名
            签名=inspect.signature(实现)#签名
        except (TypeError,ValueError):#没有签名
            无效签名(端点,方法)#拒绝
        名字=[]#参数名
        见过=set()#重复
        for 参数 in 签名.parameters.values():#逐个
            if 参数.name in ('self','自身'):#接收者
                continue#跳
            if 参数.kind not in (inspect.Parameter.POSITIONAL_ONLY,inspect.Parameter.POSITIONAL_OR_KEYWORD):#剩余或仅关键字
                无效签名(端点,方法)#拒绝
            if 参数.default is not inspect.Parameter.empty:#有默认
                无效签名(端点,方法)#拒绝
            if 参数.name in 见过:#重复
                无效签名(端点,方法)#拒绝
            见过.add(参数.name)#记下
            名字.append(参数.name)#留下
        信号下标=名字.index('signal') if 'signal' in 名字 else -1#取消参数
        if 信号下标>=0 and 信号下标!=len(名字)-1:#必须是最后一个
            raise 网关错误(
                'gateway/signature-invalid',
                端点,
                'SRC cancellation parameter signal must be the final parameter',
                {'field':'signal'},
            )#拒绝
        取消={'parameter':'signal'} if 信号下标>=0 else None#取消声明
        业务名=名字 if 取消 is None else 名字[:-1]#去掉 signal
        参数列表=[]#描述符参数
        线路=set()#已用字段
        for 名 in 业务名:#逐个
            匹配=[声明 for 声明 in 自身.ctx.typert.lookups.definitions() if 声明['parameter']==名]#同名查找
            if len(匹配)>1:#多个
                raise 网关错误(
                    'gateway/signature-invalid',
                    端点,
                    'parameter '+json.dumps(名)+' matches multiple lookup providers',
                    {'field':名},
                )#拒绝
            if len(匹配)==0:#JSON
                参数={'name':名,'wire':名,'source':'json','codec':{'mode':'src-json'}}#JSON
            else:#查找
                命中=匹配[0]#唯一
                参数={'name':名,'wire':命中['wire'],'source':'lookup','lookup':命中['key'],'codec':{'mode':'src-json'}}#查找
            if 参数['wire'] in 线路:#字段冲突
                raise 网关错误(
                    'gateway/signature-invalid',
                    端点,
                    'multiple parameters use wire field '+json.dumps(参数['wire']),
                    {'field':参数['wire']},
                )#拒绝
            线路.add(参数['wire'])#记下
            参数列表.append(参数)#加入
        接收={'kind':'direct'}#默认直接
        if 标记['invocation']['kind']=='context':#上下文方法
            提供方=自身.ctx.typert.contexts.getHost(标记['invocation']['context'])#宿主适配器
            if 提供方 is None:#没有
                raise 网关错误(
                    'gateway/context-unavailable',
                    端点,
                    'Context provider '+json.dumps(标记['invocation']['context'])+' is unavailable',
                )#拒绝
            if 提供方['wire'] in 线路:#和参数冲突
                raise 网关错误(
                    'gateway/signature-invalid',
                    端点,
                    'Context identity conflicts with wire field '+json.dumps(提供方['wire']),
                    {'field':提供方['wire']},
                )#拒绝
            接收={#上下文接收
                'kind':'context',
                'context':标记['invocation']['context'],
                'wire':提供方['wire'],
                'codec':{'mode':'src-json'},
            }#接收结束
        描述符={#SRC 描述符
            'id':'src:'+绑定['serviceKey']+'#'+端点,
            'service':绑定['serviceKey'],
            'namespace':绑定['namespace'],
            'method':方法,
            'invocation':接收,
            'parameters':参数列表,
            'result':{'mode':'src-json'},
        }#描述符结束
        if 标记['method']!=方法:#导出名和实现名不同
            描述符['implementation']=标记['method']#实现
        if 标记.get('mode') is not None:#流
            描述符['mode']=标记['mode']#模式
        if 取消 is not None:#有取消
            描述符['cancellation']=取消#取消
        return 描述符#描述符

    def 解析接收上下文(自身,描述符,参数,端点):
        '直接调用用网关自己的上下文'
        if 描述符['invocation']['kind']=='direct':#直接
            return 自身.ctx#自己
        调用=描述符['invocation']#上下文调用
        提供方=自身.ctx.typert.contexts.getHost(调用['context'])#适配器
        if 提供方 is None:#没有
            raise 网关错误(
                'gateway/context-unavailable',
                端点,
                'Context provider '+json.dumps(调用['context'])+' is unavailable',
            )#拒绝
        编解码=调用['codec']#编解码
        if 提供方['wire']!=调用['wire'] or (编解码.get('mode')=='strict' and 提供方.get('wireTypeSymbol')!=编解码.get('typeSymbol')):#对不上
            raise 网关错误(
                'gateway/provider-mismatch',
                端点,
                'Context provider '+json.dumps(调用['context'])+' does not match its strict definition',
                {'field':调用['wire']},
            )#拒绝
        身份=解码(编解码,参数[调用['wire']],端点,调用['wire'])#身份
        try:#解析
            上下文=提供方['resolve'](身份)#解析
        except Exception as 原因:#失败
            if 取远程错误(原因) is not None:#远程失败原样
                raise#原样
            raise 网关错误(
                'gateway/context-failed',
                端点,
                'Context provider '+json.dumps(调用['context'])+' failed',
                {'cause':原因,'field':调用['wire']},
            )#折成上下文失败
        if 上下文 is None:#没有解析到
            raise 网关错误(
                'gateway/context-not-found',
                端点,
                'Context provider '+json.dumps(调用['context'])+' did not resolve the requested identity',
                {'field':调用['wire']},
            )#没找到
        return 上下文#上下文

    def 解析参数(自身,参数描述,参数,端点):
        '缺席的 json 可以省略。lookup 必须出现'
        if 参数描述['wire'] not in 参数:#缺席
            return None#undefined
        if 参数描述['source']=='json':#JSON 已在准备阶段解码过，这里仍按上游再取线路值
            return 参数[参数描述['wire']]#已校验表里的值。JSON 在校验时解码，查找仍是线路值
        值=解码(参数描述['codec'],参数[参数描述['wire']],端点,参数描述['wire'])#查找身份
        键=参数描述.get('lookup')#提供方键
        if 键 is None:#没有键
            raise 网关错误(
                'gateway/lookup-unavailable',
                端点,
                'lookup parameter '+json.dumps(参数描述['name'])+' has no provider key',
                {'field':参数描述['wire']},
            )#拒绝
        提供方=自身.ctx.typert.lookups.get(键)#提供方
        if 提供方 is None:#没有
            raise 网关错误(
                'gateway/lookup-unavailable',
                端点,
                'lookup provider '+json.dumps(键)+' is unavailable',
                {'field':参数描述['wire']},
            )#拒绝
        if 提供方['wire']!=参数描述['wire'] or (参数描述['codec'].get('mode')=='strict' and 提供方.get('wireTypeSymbol')!=参数描述['codec'].get('typeSymbol')):#对不上
            raise 网关错误(
                'gateway/provider-mismatch',
                端点,
                'lookup provider '+json.dumps(键)+' does not match its strict definition',
                {'field':参数描述['wire']},
            )#拒绝
        try:#解析
            解析值=提供方['resolve'](值)#解析
        except Exception as 原因:#失败
            if 取远程错误(原因) is not None:#远程失败原样
                raise#原样
            raise 网关错误(
                'gateway/lookup-failed',
                端点,
                'lookup provider '+json.dumps(键)+' failed',
                {'cause':原因,'field':参数描述['wire']},
            )#折成查找失败
        if 解析值 is None:#没找到
            raise 网关错误(
                'gateway/lookup-not-found',
                端点,
                'lookup provider '+json.dumps(键)+' did not resolve the requested identity',
                {'field':参数描述['wire']},
            )#没找到
        return 解析值#值

默认=网关服务#类插件
default=默认#框架槽
name='typert-gateway'#框架槽
apply=网关服务#类插件入口

from . import 类型,流协议,网关,访问,异常,客户端#同目录模块。客户端只导出包，不转发里面的类

__all__=[#公开名
    '网关服务','网关配置','配置','默认','线路错误',
    '类型','流协议','网关','访问','异常','客户端',
]#公开面结束
