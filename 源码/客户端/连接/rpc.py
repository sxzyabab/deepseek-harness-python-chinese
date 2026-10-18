'宿主和浏览器共用的 RPC 结果、期约等待和中止信号'
import json,threading#紧凑 JSON 与中止门闩


def 编码json(值):
    '紧凑 JSON，对齐 JSON.stringify'
    return json.dumps(值,ensure_ascii=False,separators=(',',':'))#无空格


def Rpc标识(标识):
    '把已校验字符串收成连接关联 id'
    return 标识#品牌只留在类型上，运行时仍是原字符串


def 传输错误(错误):
    '把被拒绝的传输操作收成通用失败结果'
    if isinstance(错误,BaseException):#Error.message
        消息=str(错误)#消息正文
    else:#不是异常
        消息=str(错误)#String(error)
    return {'ok':False,'error':{'code':'gateway/internal','message':消息,'details':{}}}#内部失败


def 同步等待(产出):
    '期约阻塞到结算。已经是值就直接返回'
    然后=getattr(产出,'then',None)#期约的 then
    if not callable(然后):#不是期约
        return 产出#原值
    完成=threading.Event()#结算门闩
    盒子={}#值或错误

    def 成功(结果=None):
        '期约兑现'
        盒子['值']=结果#记下
        完成.set()#放开

    def 失败(错误=None):
        '期约拒绝'
        if isinstance(错误,BaseException):#已经是异常
            盒子['错误']=错误#原异常
        elif 错误 is None:#没有原因
            盒子['错误']=Exception('rejected')#占位
        else:#页面或宿主扔来的原因
            盒子['错误']=Exception(str(错误))#收成异常
        完成.set()#放开

    然后(成功,失败)#挂上两个回调
    完成.wait()#等到结算
    if '错误' in 盒子:#被拒绝
        raise 盒子['错误']#交给调用方
    return 盒子.get('值')#兑现的值


class 中止信号:
    '对应 AbortSignal。aborted、reason、addEventListener、throwIfAborted'
    def __init__(自身):
        '尚未中止'
        自身.aborted=False#还没中止
        自身.reason=None#中止原因
        自身._监听=[]#abort 监听
        自身._事件=threading.Event()#等待方的门闩

    def addEventListener(自身,类型,监听,选项=None):
        '只收 abort。once 为真时调用一次后摘掉'
        if 类型!='abort':#其它事件这里没有
            return#不登记
        一次=isinstance(选项,dict) and 选项.get('once') is True#只跑一次
        if 自身.aborted:#已经中止，补发一次
            监听()#立刻调用
            return#不再留下
        自身._监听.append((监听,一次))#记下

    def removeEventListener(自身,类型,监听):
        '按函数身份摘掉 abort 监听'
        if 类型!='abort':#其它事件没有登记
            return#不用摘
        自身._监听=[项 for 项 in 自身._监听 if 项[0] is not 监听]#留下其余

    def throwIfAborted(自身):
        '已中止则抛出原因'
        if not 自身.aborted:#还没中止
            return#继续
        原因=自身.reason#中止原因
        if isinstance(原因,BaseException):#原因本身是异常
            raise 原因#原样抛出
        raise Exception('The operation was aborted.')#没有原因时的固定句


_进程内网关=None#本进程宿主网关。客户端调用它，不经过浏览器
_进程内事件={}#事件名到监听列表
_进程内事件锁=threading.Lock()#订和投递串行


def 登记进程内网关(网关):
    '宿主网关起来时登记。返回拆除'
    global _进程内网关
    _进程内网关=网关#交给客户端

    def 拆除():
        '仍是这一份才摘掉'
        global _进程内网关
        if _进程内网关 is 网关:#还是这一份
            _进程内网关=None#摘掉

    return 拆除#拆除器


def 取进程内网关():
    '当前宿主网关。没有则为空'
    return _进程内网关#可能还没起来


def 订进程内事件(事件,监听器):
    '本进程订一条宿主事件。返回拆除'
    with _进程内事件锁:#串行
        表=_进程内事件.get(事件)#已有
        if 表 is None:#新建
            表=[]#空
            _进程内事件[事件]=表#放入
        表.append(监听器)#记下

    def 拆除():
        '摘掉这一次'
        with _进程内事件锁:#串行
            已有=_进程内事件.get(事件)#当前
            if 已有 is not None and 监听器 in 已有:#还在
                已有.remove(监听器)#摘掉

    return 拆除#拆除器


def 投递进程内事件(事件,参数):
    '把宿主发出的参数交给本进程的监听。一个失败不影响其余'
    with _进程内事件锁:#拷贝
        监听=list(_进程内事件.get(事件,()))#当前
    for 监听器 in 监听:#逐个
        try:#隔离
            监听器(*参数)#参数是列表
        except Exception as 错误:#监听失败
            print('client api: Remote event '+str(事件)+' listener threw:',错误)#诊断


class 中止控制器:
    '对应 AbortController'
    def __init__(自身):
        '新建一份尚未中止的信号'
        自身.signal=中止信号()#信号

    def abort(自身,原因=None):
        '中止并叫醒监听。重复调用无效果'
        信号=自身.signal#信号
        if 信号.aborted:#已经中止
            return#不重复
        信号.aborted=True#标记
        信号.reason=原因#记下原因
        信号._事件.set()#叫醒等待
        待跑=list(信号._监听)#先拷贝
        信号._监听=[]#清空，避免重入再跑
        for 监听,一次 in 待跑:#逐个
            监听()#调用
