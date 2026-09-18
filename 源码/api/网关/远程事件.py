"""转发 Remote 事件订阅与投递的 Client 所有者。

对齐上游 `api/gateway/src/client/remote-events.ts`。公开面仅中文名。
异步代际改为线程泵送；受拥有 Context 在瀑布落定后拆除。
"""
import threading#代际泵送
import uuid#事件前缀
from ...typert.协议.拥有值 import 是否协议拥有值#受拥有识别
from .网关 import 中止控制器,中止信号#中止

__all__=['客户端远程事件']#仅中文公开名

#常量
远程事件流端点='$events'#事件流端点
远程事件结果端点='$events/result'#结果端点
远程事件流载荷={'args':{}}#空载荷
远程事件下一环=object()#链末标记


def _投影拒绝(错误):
    """监听拒绝保留的错误字段。"""
    if isinstance(错误,BaseException):#异常
        return {'name':type(错误).__name__,'message':str(错误)}#投影
    return {'name':'Error','message':str(错误)}#其它


def _转错误(原因,消息):
    """转为 Error。"""
    return 原因 if isinstance(原因,BaseException) else Exception(消息,原因)#错误


def _是否记录(值):
    """普通对象记录。"""
    return isinstance(值,dict)#dict


def _精确键(值,键列表):
    """恰好这些键。"""
    return len(值)==len(键列表) and all(键 in 值 for 键 in 键列表)#精确


def _有效事件名(值):
    """非空字符串。"""
    return isinstance(值,str) and len(值)>0#名


def _是否远程json(值,深度=0):
    """无损 JSON 数据。"""
    if 深度>32:#过深
        return False#否
    if 值 is None or isinstance(值,(bool,int,float,str)):#标量
        return True#是
    if isinstance(值,list):#列表
        return all(_是否远程json(项,深度+1) for 项 in 值)#逐项
    if isinstance(值,dict):#对象
        return all(isinstance(键,str) and _是否远程json(子,深度+1) for 键,子 in 值.items())#键值
    return False#否


def _解析就绪(值):
    """代际开口。"""
    if (not _是否记录(值) or not _精确键(值,['type','clientId','host'])
            or 值.get('type')!='ready' or not isinstance(值.get('clientId'),str)
            or not _是否记录(值.get('host')) or not _精确键(值['host'],['home'])
            or not isinstance(值['host'].get('home'),str)):#非法
        raise TypeError('client api: forwarded Remote event stream did not begin with ready')#拒绝
    return {'clientId':值['clientId'],'host':{'home':值['host']['home']}}#就绪


def _解析帧(值):
    """下行帧。"""
    if not _是否记录(值):#非法
        raise TypeError('client api: invalid forwarded Remote event frame')#拒绝
    if (值.get('type')=='cancel' and _精确键(值,['type','eventId'])
            and isinstance(值.get('eventId'),str)):#取消
        return {'type':'cancel','eventId':值['eventId']}#取消
    if (值.get('type')=='emit' and _精确键(值,['type','event','args'])
            and _有效事件名(值.get('event')) and isinstance(值.get('args'),list)
            and _是否远程json(值['args'])):#发射
        return {'type':'emit','event':值['event'],'args':值['args']}#发射
    if (值.get('type')=='waterfall' and _精确键(值,['type','event','eventId','agentId','request'])
            and _有效事件名(值.get('event')) and isinstance(值.get('eventId'),str)
            and isinstance(值.get('agentId'),str) and _是否记录(值.get('request'))
            and 'agent' not in 值['request'] and 'signal' not in 值['request']
            and _是否远程json(值['request'])):#瀑布
        return {
            'type':'waterfall','event':值['event'],'eventId':值['eventId'],
            'agentId':值['agentId'],'request':值['request'],
        }#调用
    raise TypeError('client api: invalid forwarded Remote event frame')#拒绝


class 客户端远程事件:
    """拥有 Cordis 登记、代际泵送、瀑布分发与 HTTP 回复。"""

    def __init__(自身,拥有方,连接,开流):
        """拥有方 Context、Connection 与流打开器。"""
        自身._拥有方=拥有方#根
        自身._连接=连接#连接
        自身._开流=开流#打开器
        自身._前缀='internal/api-gateway/remote-event/'+str(uuid.uuid4())+'/'#前缀
        自身._活动代际=None#活动线程
        自身._停止=threading.Event()#停止
        自身._取消登记=连接.registerGenerationSource(自身._跑代际) if hasattr(连接,'registerGenerationSource') else (lambda:None)#代际源
        if not hasattr(连接,'registerGenerationSource'):#无代际源则自启
            自身._启动本地代际()#本地泵

    def 订阅(自身,调用方,事件,监听器):
        """在调用 fiber 登记监听器。"""
        键=自身._事件键(事件)#键
        拆除=调用方.on(键,监听器) if hasattr(调用方,'on') else 调用方.监听(键,监听器)#登记
        def 退订():
            """拆除本精确登记。"""
            拆除()#拆
        return 退订#拆除器

    def 拆除(自身):
        """撤回代际源并等待活动工作静默。"""
        自身._取消登记()#撤
        自身._停止.set()#停
        代=自身._活动代际#线程
        if 代 is not None:#有
            代.join(timeout=30)#等

    def _事件键(自身,事件):
        """私有事件键。"""
        return 自身._前缀+事件#键

    def _报告错误(自身,事件,错误):
        """报告监听失败。"""
        print('client api: Remote event',repr(事件),'listener threw:',错误)#日志

    def _启动本地代际(自身):
        """无 registerGenerationSource 时自启一代。"""
        控=中止控制器()#控
        def 就绪(_宿主):
            """就绪回调空操作。"""
            return None#无
        自身._跑代际(控.信号,就绪)#跑

    def _跑代际(自身,信号,就绪):
        """跟踪当前代际。"""
        def 任务():
            """泵送。"""
            try:
                自身._泵送(信号,就绪)#泵
            except BaseException as 错误:
                if not (hasattr(信号,'事件') and 信号.事件.is_set()):#非取消
                    print('client api: Remote event generation failed:',错误)#日志
            finally:
                if 自身._活动代际 is 线:#仍是本代
                    自身._活动代际=None#清空
        线=threading.Thread(target=任务,daemon=True)#线程
        自身._活动代际=线#记下
        线.start()#启
        return 线#线程

    def _投递(自身,帧):
        """并行投递 emit。"""
        try:
            if hasattr(自身._拥有方,'parallel'):#并行
                自身._拥有方.parallel(自身._事件键(帧['event']),*帧['args'])#派
            else:#同步
                自身._拥有方.emit(自身._事件键(帧['event']),*帧['args'])#发
        except BaseException as 错误:
            自身._报告错误(帧['event'],错误)#报告

    def _泵送(自身,信号,就绪):
        """经转发流泵送一代。"""
        客户端标识=None#id
        失败控=中止控制器()#失败
        代际信号=中止信号.任一([信号,失败控.信号]) if hasattr(中止信号,'任一') else 信号#合成
        活动={}#eventId → AbortController
        源=自身._开流(远程事件流端点,远程事件流载荷,代际信号)#流
        流失败=False#失败
        流错误=None#错误
        try:
            for 值 in 源:#逐项
                if 自身._停止.is_set():#停
                    break#停
                if 客户端标识 is None:#开口
                    开口=_解析就绪(值)#就绪
                    客户端标识=开口['clientId']#id
                    就绪(开口['host'])#宿主
                    continue#下一项
                帧=_解析帧(值)#帧
                if 帧['type']=='cancel':#取消
                    控=活动.get(帧['eventId'])#控
                    if 控 is not None:#有
                        控.中止(Exception('client api: Remote event was cancelled by the Host'))#中止
                    continue#下一项
                if 帧['type']=='emit':#发射
                    自身._投递(帧)#投递
                    continue#下一项
                控=中止控制器()#控
                活动[帧['eventId']]=控#记
                投递信号=中止信号.任一([代际信号,控.信号]) if hasattr(中止信号,'任一') else 代际信号#合成
                def 应答(帧本=帧,投递=投递信号,标识=客户端标识):
                    """瀑布应答。"""
                    try:
                        自身._应答(帧本,标识,投递)#答
                    except BaseException as 错误:
                        if not (hasattr(投递,'事件') and 投递.事件.is_set()):#未取消
                            失败控.中止(错误)#失败代际
                    finally:
                        活动.pop(帧本['eventId'],None)#摘
                threading.Thread(target=应答,daemon=True).start()#后台
        except BaseException as 错误:
            流失败=True#失败
            流错误=错误#记
        finally:
            for 控 in list(活动.values()):#中止挂起
                控.中止(Exception('client api: Remote event generation ended'))#中止
        if hasattr(失败控.信号,'事件') and 失败控.信号.事件.is_set():#结果失败
            raise _转错误(getattr(失败控.信号,'reason',None),'client api: Remote event result delivery failed')#抛
        if hasattr(信号,'事件') and 信号.事件.is_set():#代际取消
            return#静默
        if 流失败:#流失败
            raise 流错误#抛
        raise Exception('client api: forwarded Remote event stream ended unexpectedly')#意外结束

    def _应答(自身,帧,客户端标识,信号):
        """瀑布应答并 HTTP 回报。"""
        绑定器=自身._拥有方.typert.contexts.getClient('agent')#绑定器
        解析结果=None#解析
        try:
            解析结果=绑定器.resolve(帧['agentId']) if 绑定器 is not None else None#解析
        except BaseException as 错误:
            自身._报告错误(帧['event'],错误)#报告
        拥有=解析结果 if 是否协议拥有值(解析结果) else None#受拥有
        try:
            目标=拥有.值 if 拥有 is not None else 解析结果#上下文
            结局={'kind':'next'}#默认委托
            if 目标 is not None:#有目标
                try:
                    结局=自身._分发瀑布(目标,帧,信号)#瀑布
                except BaseException as 错误:
                    if hasattr(信号,'事件') and 信号.事件.is_set():#取消
                        return#静默
                    结局={'kind':'rejected','error':_投影拒绝(错误)}#拒绝
            if hasattr(信号,'事件') and 信号.事件.is_set():#取消
                return#静默
            结果结局=结局
            if 结局.get('kind')=='result' and 结局.get('value') is None:#无值结果
                结果结局={'kind':'result'}#去 value
            结果={'clientId':客户端标识,'eventId':帧['eventId'],'outcome':结果结局}#结果
            响应=自身._连接.rpc.call('/api',远程事件结果端点,{'args':结果},信号)#回报
            if not 响应.get('ok',False):#失败
                raise Exception(响应['error']['message'] if isinstance(响应.get('error'),dict) else 'result failed')#抛
        finally:
            if 拥有 is not None:#释放
                拥有.拆除()#拆

    def _分发瀑布(自身,目标,帧,信号):
        """瀑布分发。"""
        请求=dict(帧['request'])#拷
        请求['agent']=目标#上下文
        请求['signal']=信号#信号
        def 下一环():
            """链末。"""
            return 远程事件下一环#标记
        if hasattr(目标,'waterfall'):#瀑布
            值=目标.waterfall(目标,自身._事件键(帧['event']),请求,下一环)#派
        else:#无瀑布则下一环
            值=远程事件下一环#委托
        if 值 is not 远程事件下一环 and 值 is not None and not _是否远程json(值):#非法
            raise TypeError('Remote event listener result is not lossless JSON data')#拒绝
        if 值 is 远程事件下一环:#委托
            return {'kind':'next'}#下一环
        return {'kind':'result','value':值}#结果
