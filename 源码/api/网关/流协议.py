'网关自有 Remote 流与事件结果的线路报文'
import json#报文
import threading#中止观察
from ...类型化远程调用.协议 import 是否远程json值#无损 JSON
from ...客户端.连接.rpc import 中止控制器#取消通道

远程流复用路径='/api/remote.mux'#全部 Remote 流的 WebSocket 路径
远程事件流端点='$events'#转发事件的逻辑流
远程事件结果端点='$events/result'#瀑布结果的一元端点
远程事件流载荷={'args':{}}#打开转发事件流的空载荷
远程事件流就绪={'type':'ready'}#宿主事件源就绪

def 已中止(信号):
    '中止信号看 aborted，threading.Event 看 is_set。无信号视为未中止'
    if 信号 is None:#无
        return False#未中止
    if getattr(信号,'aborted',False):#AbortSignal
        return True#已中止
    置位=getattr(信号,'is_set',None)#Event
    if callable(置位):#有
        return bool(置位())#是否置位
    return False#未中止

def 若中止则抛(信号):
    '已中止则抛出原因'
    if 信号 is None:#无
        return#继续
    if hasattr(信号,'throwIfAborted'):#中止信号
        信号.throwIfAborted()#抛
        return#继续
    if not 已中止(信号):#还活着
        return#继续
    原因=getattr(信号,'reason',None)#原因
    if isinstance(原因,BaseException):#是异常
        raise 原因#原样
    raise Exception('The operation was aborted.')#没有原因

def 空拆除():
    '没有可摘的监听'
    return None

def 挂中止(信号,回调):
    '中止时调用回调。返回摘掉监听的函数'
    if 信号 is None:#无
        return 空拆除#空
    if hasattr(信号,'addEventListener'):#AbortSignal
        信号.addEventListener('abort',回调,{'once':True})#登记
        def 摘监听():
            '摘掉'
            信号.removeEventListener('abort',回调)#摘
        return 摘监听#拆除
    if isinstance(信号,threading.Event):#连接控制器交给代际源的是 Event
        停=threading.Event()#观察线程停
        def 看():
            '轮询到置位或被摘掉'
            while not 停.is_set():#还要看
                if 信号.is_set():#中止了
                    回调()#通知
                    return#停
                信号.wait(0.05)#短等
        threading.Thread(target=看,daemon=True).start()#观察
        def 摘事件():
            '让观察线程退出，不碰调用方的 Event'
            停.set()#停
        return 摘事件#拆除
    return 空拆除#没有监听面

def 合并信号(*信号列表):
    '对应 AbortSignal.any。任一中止则结果中止，原因取那一路'
    控制器=中止控制器()#结果
    摘掉=[]#拆除器
    def 传播(来源):
        '这一路中止时中止结果'
        def 回调():
            '只中止一次'
            if not 控制器.signal.aborted:#还没
                控制器.abort(getattr(来源,'reason',None))#带上原因
        return 回调#监听
    for 信号 in 信号列表:#每一路
        if 信号 is None:#跳过空
            continue#下一
        if 已中止(信号):#已经中止
            控制器.abort(getattr(信号,'reason',None))#立刻
            for 摘 in 摘掉:#不必再听
                摘()#摘
            return 控制器.signal#结果
        摘掉.append(挂中止(信号,传播(信号)))#听
    return 控制器.signal#结果

def 是记录(值):
    '非数组对象'
    return type(值) is dict#普通字典

def 精确键(值,期望):
    '自有键恰好等于期望'
    if type(值) is not dict:#不是对象
        return False#否
    if len(值)!=len(期望):#数量不同
        return False#否
    for 键 in 期望:#每个都要在
        if 键 not in 值:#缺
            return False#否
    return True#是

def 合法标识(值):
    '非空字符串'
    return isinstance(值,str) and len(值)>0#非空

def 是否远程事件标识(值):
    '非空事件关联标识'
    return 合法标识(值)#非空字符串

def 是否远程事件客户端标识(值):
    '非空事件流代际标识'
    return 合法标识(值)#非空字符串

def 是否远程事件智能体标识(值):
    '非空智能体标识'
    return 合法标识(值)#非空字符串

def 字符串属性(值,键):
    '对象上的字符串属性。没有或不是字符串则 None'
    if 值 is None:#无对象
        return None#无
    if isinstance(值,dict):#字典
        候选=值.get(键)#取值
    else:#其它对象
        候选=getattr(值,键,None)#属性
    if isinstance(候选,str):#是字符串
        return 候选#用它
    return None#不是

def 是中止信号(值):
    '有 aborted，并且能监听或是 Event'
    if 值 is None:#空
        return False#否
    if hasattr(值,'aborted') and hasattr(值,'addEventListener'):#AbortSignal
        return True#是
    return isinstance(值,threading.Event)#连接代际的取消

def 解析远程事件结果(值):
    '解析 $events/result 载荷'
    if (not 是记录(值)
            or not 精确键(值,['clientId','eventId','outcome'])
            or not 是否远程事件客户端标识(值['clientId'])
            or not 是否远程事件标识(值['eventId'])
            or not 是记录(值['outcome'])):#外形不对
        raise Exception('api gateway: invalid Remote event result')#拒绝
    结局=值['outcome']#结局
    if 结局.get('kind')=='next' and 精确键(结局,['kind']):#委托
        return {'clientId':值['clientId'],'eventId':值['eventId'],'outcome':{'kind':'next'}}#结果
    if 结局.get('kind')=='result' and (精确键(结局,['kind']) or 精确键(结局,['kind','value'])):#有值或无值
        if 'value' in 结局 and not 是否远程json值(结局['value']):#值不是无损 JSON
            raise Exception('api gateway: invalid Remote event result')#拒绝
        if 'value' in 结局:#带值
            结局体={'kind':'result','value':结局['value']}#带值
        else:#无值
            结局体={'kind':'result'}#无值
        return {'clientId':值['clientId'],'eventId':值['eventId'],'outcome':结局体}#结果
    if 结局.get('kind')=='rejected' and 精确键(结局,['kind','error']):#拒绝
        错误=结局['error']#拒绝体
        if (not 是记录(错误)
                or not ('name' in 错误 and 'message' in 错误)
                or any(键 not in ('name','message','code','details') for 键 in 错误)
                or not isinstance(错误.get('name'),str)
                or 错误['name']==''
                or not isinstance(错误.get('message'),str)
                or ('code' in 错误 and not isinstance(错误['code'],str))
                or ('details' in 错误 and not 是否远程json值(错误['details']))):#拒绝字段不对
            raise Exception('api gateway: invalid Remote event rejection')#拒绝
        拒绝体={'name':错误['name'],'message':错误['message']}#必填
        if isinstance(错误.get('code'),str):#有码
            拒绝体['code']=错误['code']#带上
        if 'details' in 错误:#有细节
            拒绝体['details']=错误['details']#带上
        return {#结果
            'clientId':值['clientId'],
            'eventId':值['eventId'],
            'outcome':{'kind':'rejected','error':拒绝体},
        }#结果结束
    raise Exception('api gateway: invalid Remote event result')#其余都无效

def 投影远程事件请求(值,主体):
    '去掉 waterfall 请求上的 agent 与 signal'
    if type(值) is not dict or 'agent' not in 值 or 值['agent'] is not 主体:#必须直接带上这个智能体
        raise TypeError('api gateway: Remote event request must carry its scoped Agent directly')#拒绝
    信号=值.get('signal')#取消
    if 'signal' in 值 and not 是中止信号(信号):#给了但不是信号
        raise TypeError('api gateway: Remote event request signal must be an AbortSignal')#拒绝
    请求={}#JSON 字段
    for 键 in 值:#自有键
        if 键=='agent' or 键=='signal':#运输时去掉
            continue#跳
        if not isinstance(键,str):#非 JSON 键
            raise TypeError('api gateway: Remote event request has a non-JSON property')#拒绝
        请求[键]=值[键]#留下
    if not 是否远程json值(请求):#必须无损
        raise TypeError('api gateway: Remote event request is not lossless JSON data')#拒绝
    结果={'request':请求}#请求
    if 'signal' in 值:#有信号才带
        结果['signal']=信号#宿主取消
    return 结果#投影

def 投影远程事件拒绝(原因):
    '投影为稳定 JSON 拒绝字段'
    记录=原因 if 原因 is not None and not isinstance(原因,(str,bytes,bool,int,float)) else None#对象才读字段
    名称=字符串属性(记录,'name')#name
    if 名称 is None:#没有
        名称='Error'#默认
    消息=字符串属性(记录,'message')#message
    if 消息 is None:#没有
        消息=str(原因)#String(reason)
    码=字符串属性(记录,'code')#code
    细节=None#details
    if 记录 is not None:#有对象
        if isinstance(记录,dict):#字典
            细节=记录.get('details')#取
        else:#属性
            细节=getattr(记录,'details',None)#取
    结果={'name':名称,'message':消息}#必填
    if 码 is not None:#有码
        结果['code']=码#带上
    if 细节 is not None and 是否远程json值(细节):#细节可上线路
        结果['details']=细节#带上
    return 结果#拒绝

def 还原远程事件拒绝(拒绝):
    '把线路拒绝还原成异常'
    错误=Exception(拒绝['message'])#消息
    错误.name=拒绝['name']#远程名
    if 'code' in 拒绝:#有码
        错误.code=拒绝['code']#带上
    if 'details' in 拒绝:#有细节
        错误.details=拒绝['details']#带上
    return 错误#异常

def 解析报文(文本,校验):
    '解析一条 JSON 对象报文'
    try:#可能不是 JSON
        解码=json.loads(文本)#解析
    except json.JSONDecodeError as 原因:#语法错误
        raise Exception('api gateway: Remote stream message is not JSON') from 原因#拒绝
    if not 是记录(解码):#必须是对象
        raise Exception('api gateway: Remote stream message must be an object')#拒绝
    return 校验(解码)#再校验字段

def 解析远程流客户端报文(文本):
    '解析浏览器到宿主的一条文本报文'
    def 校验(值):
        '四种帧'
        if 值.get('type') in ('cancel','end') and 精确键(值,['type','streamId']) and 合法标识(值.get('streamId')):#取消或半关
            return 值#通过
        if (值.get('type')=='item'
                and (精确键(值,['type','streamId']) or 精确键(值,['type','streamId','value']))
                and 合法标识(值.get('streamId'))
                and ('value' not in 值 or 是否远程json值(值.get('value')))):#上行项
            return 值#通过
        if (值.get('type')=='open'
                and 精确键(值,['type','streamId','endpoint','payload'])
                and 合法标识(值.get('streamId'))
                and isinstance(值.get('endpoint'),str)
                and len(值['endpoint'])>0):#打开
            return 值#通过
        raise Exception('api gateway: invalid Remote stream client message')#其余无效
    return 解析报文(文本,校验)#解析

def 解析远程流服务端报文(文本):
    '解析宿主到浏览器的一条文本报文'
    def 校验(值):
        '项、结束或错误'
        if (值.get('type')=='item'
                and (精确键(值,['type','streamId']) or 精确键(值,['type','streamId','value']))
                and 合法标识(值.get('streamId'))):#项
            return 值#通过
        if 值.get('type')=='end' and 精确键(值,['type','streamId']) and 合法标识(值.get('streamId')):#结束
            return 值#通过
        错误=值.get('error')#错误体
        if (值.get('type')=='error'
                and 精确键(值,['type','streamId','error'])
                and 合法标识(值.get('streamId'))
                and 是记录(错误)
                and 精确键(错误,['code','message','details'])
                and isinstance(错误.get('code'),str)
                and isinstance(错误.get('message'),str)
                and 是记录(错误.get('details'))):#错误帧
            return 值#通过
        raise Exception('api gateway: invalid Remote stream server message')#其余无效
    return 解析报文(文本,校验)#解析

__all__=[#公开名
    '远程流复用路径','远程事件流端点','远程事件结果端点','远程事件流载荷','远程事件流就绪',
    '已中止','若中止则抛','挂中止','合并信号','是中止信号',
    '是否远程事件标识','是否远程事件客户端标识','是否远程事件智能体标识',
    '解析远程事件结果','投影远程事件请求','投影远程事件拒绝','还原远程事件拒绝',
    '解析远程流客户端报文','解析远程流服务端报文',
]#公开面结束
