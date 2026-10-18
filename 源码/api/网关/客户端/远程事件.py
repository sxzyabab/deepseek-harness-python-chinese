'转发 Remote 事件订阅与投递的客户端所有者'
import threading#代际泵
from uuid import uuid4 as 生成标识#私有事件前缀
from ....类型化远程调用.协议 import 是否远程json值,是否协议拥有值#结果与拥有值
from ..流协议 import (#事件报文
    远程事件流端点,远程事件结果端点,远程事件流载荷,
    是否远程事件标识,是否远程事件客户端标识,是否远程事件智能体标识,
    投影远程事件拒绝,已中止,合并信号,
)#导入结束
下一环=object()#瀑布走到头的私有标记，不会和 JSON 结果撞上

def 是记录(值):
    '普通对象'
    return type(值) is dict#字典

def 精确键(值,键列表):
    '恰好这些键'
    if type(值) is not dict or len(值)!=len(键列表):#数量
        return False#否
    for 键 in 键列表:#每一个
        if 键 not in 值:#缺
            return False#否
    return True#是

def 有效事件名(值):
    '非空字符串'
    return isinstance(值,str) and len(值)>0#非空

def 无效帧():
    '下行帧不合法'
    raise TypeError('client api: invalid forwarded Remote event frame')#拒绝

class 客户端远程事件:
    'Cordis 登记、代际泵送、瀑布分发和 HTTP 回复'
    def __init__(自身,拥有方,连接,流打开器):
        '拥有方上下文、Connection 和流打开器'
        自身._拥有方=拥有方#根
        自身._连接=连接#HTTP
        自身._流打开器=流打开器#打开 $events
        自身._前缀='internal/api-gateway/remote-event/'+str(生成标识())+'/'#私有前缀
        自身._活动代际=None#当前泵
        自身._活动结束=None#泵结束
        自身._取消登记=连接.registerGenerationSource(自身._运行代际)#登记代际源

    def 订阅(自身,调用方,事件,监听器):
        '在调用纤程上登记监听器'
        拆除=调用方.监听(自身._事件键(事件),监听器)#登记
        def 拆除器():
            '撤掉这一次登记'
            拆除()#撤
        return 拆除器#拆除器

    def 拆除(自身):
        '撤回代际源并等待活动工作静默'
        自身._取消登记()#撤源
        if 自身._活动结束 is not None:#有泵
            自身._活动结束.wait()#等

    def _事件键(自身,事件):
        '私有事件键'
        return 自身._前缀+事件#键

    def _报告错误(自身,事件,错误):
        '监听失败只记日志'
        print('client api: Remote event '+json_事件(事件)+' listener threw:',错误)#诊断

    def _运行代际(自身,信号,就绪):
        '跟踪当前代际，供拆除时等待'
        结束=threading.Event()#这一代结束
        def 跑():
            '泵送'
            try:#泵
                自身._泵送(信号,就绪)#阻塞
            finally:#记下结束
                if 自身._活动结束 is 结束:#还是这一代
                    自身._活动代际=None#摘
                结束.set()#放开
        自身._活动结束=结束#当前
        线程=threading.Thread(target=跑,daemon=True)#连接控制器已经在线程里调用源
        线程.start()#启动
        结束.wait()#源调用是阻塞的，这里等泵结束

    def _泵送(自身,信号,就绪):
        '经转发流泵送一代'
        客户标识=None#开口之后才有
        from ....客户端.连接.rpc import 中止控制器#这一代的失败
        失败控制=中止控制器()#应答失败
        代际信号=合并信号(信号,失败控制.signal)#合并
        活动={ }#事件标识到取消
        源=自身._流打开器(远程事件流端点,远程事件流载荷,代际信号)#流
        流失败=False#流是否抛了
        流错误=None#原因
        try:#读帧
            for 值 in 源:#逐帧
                if 客户标识 is None:#必须先就绪
                    开口=解析就绪(值)#就绪
                    客户标识=开口['clientId']#代际
                    就绪(开口['host'])#报告宿主
                    continue#下一帧
                帧=解析帧(值)#下行
                if 帧['type']=='cancel':#宿主取消
                    控制=活动.get(帧['eventId'])#这一次
                    if 控制 is not None:#还在
                        控制.abort(Exception('client api: Remote event was cancelled by the Host'))#取消
                    continue#下一
                if 帧['type']=='emit':#通知
                    自身._投递(帧)#并行投递
                    continue#下一
                控制=中止控制器()#这次瀑布
                活动[帧['eventId']]=控制#记下
                投递信号=合并信号(代际信号,控制.signal)#合并
                try:#应答
                    自身._应答(帧,客户标识,投递信号)#应答
                except Exception as 错误:#应答失败
                    if not 已中止(投递信号):#不是取消
                        失败控制.abort(错误)#失败这一代
                finally:#摘掉
                    活动.pop(帧['eventId'],None)#摘
        except Exception as 错误:#流失败
            流失败=True#记下
            流错误=错误#原因
        finally:#结束还在跑的瀑布
            for 控制 in list(活动.values()):#每一个
                控制.abort(Exception('client api: Remote event generation ended'))#结束
        if 已中止(失败控制.signal):#应答把这一代失败了
            原因=失败控制.signal.reason#原因
            if isinstance(原因,BaseException):#异常
                raise 原因#抛
            raise Exception('client api: Remote event result delivery failed')#包装
        if 已中止(信号):#调用方取消
            return#静默
        if 流失败:#流抛了
            raise 流错误#原样
        raise Exception('client api: forwarded Remote event stream ended unexpectedly')#不该自己结束

    def _投递(自身,帧):
        '并行投递 emit。监听失败记日志'
        try:#并发广播会聚合错误
            自身._拥有方.并发广播(自身._事件键(帧['event']),*帧['args'])#投递
        except Exception as 错误:#监听失败
            自身._报告错误(帧['event'],错误)#日志

    def _应答(自身,帧,客户标识,信号):
        '瀑布应答并 HTTP 回报'
        适配器=自身._拥有方.typert.contexts.getClient('agent')#智能体上下文
        解析值=None#解析结果
        try:#解析失败只记日志
            if 适配器 is not None:#有适配器
                解析值=适配器['resolve'](帧['agentId']) if isinstance(适配器,dict) else 适配器.resolve(帧['agentId'])#解析
        except Exception as 错误:#解析失败
            自身._报告错误(帧['event'],错误)#日志
        拥有=解析值 if 是否协议拥有值(解析值) else None#要释放的
        try:#无论成败都释放拥有值
            目标=拥有.值 if 拥有 is not None else 解析值#上下文
            结局={'kind':'next'}#默认委托
            if 目标 is not None:#有上下文
                try:#瀑布
                    结局=自身._分发瀑布(目标,帧,信号)#分发
                except Exception as 错误:#监听拒绝
                    if 已中止(信号):#取消则不回报
                        return#停
                    结局={'kind':'rejected','error':投影远程事件拒绝(错误)}#拒绝
            if 已中止(信号):#取消
                return#不回报
            if 结局['kind']=='result' and 'value' not in 结局:#无值
                结局体={'kind':'result'}#不带 value
            else:#原样
                结局体=结局#原样
            结果={'clientId':客户标识,'eventId':帧['eventId'],'outcome':结局体}#结果
            响应=自身._连接.rpc.call('/api',远程事件结果端点,{'args':结果},信号)#HTTP
            if not 响应['ok']:#失败
                raise Exception(响应['error']['message'])#抛
        finally:#释放
            if 拥有 is not None:#有
                拥有.拆除()#释放

    def _分发瀑布(自身,目标,帧,信号):
        '把请求交给目标上下文的瀑布'
        请求=dict(帧['request'])#拷贝
        请求['agent']=目标#智能体上下文
        请求['signal']=信号#取消
        def 续体():
            '没有监听认领'
            return 下一环#标记
        值=目标.链式拦截(目标,自身._事件键(帧['event']),请求,续体)#瀑布
        if 值 is not 下一环 and 值 is not None and not 是否远程json值(值):#结果必须无损
            raise TypeError('Remote event listener result is not lossless JSON data')#拒绝
        if 值 is 下一环:#委托
            return {'kind':'next'}#next
        return {'kind':'result','value':值}#结果

def json_事件(事件):
    '诊断里的事件名'
    import json#转义
    return json.dumps(事件,ensure_ascii=False)#JSON 字符串

def 解析就绪(值):
    '代际开口'
    if (not 是记录(值)
            or not 精确键(值,['type','clientId','host'])
            or 值.get('type')!='ready'
            or not 是否远程事件客户端标识(值.get('clientId'))
            or not 是记录(值.get('host'))
            or not 精确键(值['host'],['home'])
            or not isinstance(值['host'].get('home'),str)):#不是就绪
        raise TypeError('client api: forwarded Remote event stream did not begin with ready')#拒绝
    return {'clientId':值['clientId'],'host':{'home':值['host']['home']}}#开口

def 解析帧(值):
    '下行帧'
    if not 是记录(值):#不是对象
        无效帧()#拒绝
    if 值.get('type')=='cancel' and 精确键(值,['type','eventId']) and 是否远程事件标识(值.get('eventId')):#取消
        return {'type':'cancel','eventId':值['eventId']}#帧
    if (值.get('type')=='emit'
            and 精确键(值,['type','event','args'])
            and 有效事件名(值.get('event'))
            and isinstance(值.get('args'),list)
            and 是否远程json值(值['args'])):#通知
        return {'type':'emit','event':值['event'],'args':值['args']}#帧
    if (值.get('type')=='waterfall'
            and 精确键(值,['type','event','eventId','agentId','request'])
            and 有效事件名(值.get('event'))
            and 是否远程事件标识(值.get('eventId'))
            and 是否远程事件智能体标识(值.get('agentId'))
            and 是记录(值.get('request'))
            and 'agent' not in 值['request']
            and 'signal' not in 值['request']
            and 是否远程json值(值['request'])):#瀑布
        return {#帧
            'type':'waterfall',
            'event':值['event'],
            'eventId':值['eventId'],
            'agentId':值['agentId'],
            'request':值['request'],
        }#帧结束
    无效帧()#其余

__all__=['客户端远程事件']#公开名
