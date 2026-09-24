"""网关自有 Remote 流与事件结果 RPC 的线协议报文。"""
import json
from ...typert.协议 import 是否远程json值

__all__=[
    '远程流复用路径','远程事件流端点','远程事件结果端点','远程事件流载荷','远程事件流就绪',
    '解析远程事件结果','投影远程事件请求','投影远程事件拒绝','还原远程事件拒绝',
    '是否远程事件标识','是否远程事件客户端标识','是否远程事件智能体标识',
    '解析远程流客户端报文','解析远程流服务端报文',
]

远程流复用路径='/api/remote.mux'#复用套接字路由
远程事件流端点='$events'#转发事件流
远程事件结果端点='$events/result'#事件结果 RPC
远程事件流载荷={'args':{}}#开口空载荷
远程事件流就绪={'type':'ready'}#就绪判别

def 是否记录(值):
    """非数组对象。"""
    return isinstance(值,dict)

def 是否普通记录(值):
    """普通 dict。"""
    return isinstance(值,dict)

def 精确键(值,期望):
    """自有键恰好等于期望。"""
    键列表=list(值.keys())
    return len(键列表)==len(期望) and all(键 in 值 for 键 in 期望)

def 仅含键(值,必需,可选):
    """含全部必需键，且无其它键。"""
    键列表=list(值.keys())
    return all(键 in 值 for 键 in 必需) and all(键 in 必需 or 键 in 可选 for 键 in 键列表)

def 合法标识(值):
    """非空字符串。"""
    return isinstance(值,str) and len(值)>0

def 是否远程事件标识(值):
    """非空事件关联标识。"""
    return 合法标识(值)

def 是否远程事件客户端标识(值):
    """非空事件流代际标识。"""
    return 合法标识(值)

def 是否远程事件智能体标识(值):
    """非空智能体标识。"""
    return 合法标识(值)

def 字符串属性(值,键):
    """对象上的字符串属性。"""
    if 值 is None:
        return None
    候选=值.get(键) if isinstance(值,dict) else getattr(值,键,None)
    return 候选 if isinstance(候选,str) else None

def 解析远程事件拒绝(值):
    """校验拒绝字段。"""
    if (not 是否记录(值) or not 仅含键(值,['name','message'],['code','details'])
            or not isinstance(值.get('name'),str) or 值.get('name')==''
            or not isinstance(值.get('message'),str)
            or ('code' in 值 and not isinstance(值.get('code'),str))
            or ('details' in 值 and not 是否远程json值(值.get('details')))):
        raise Exception('api gateway: invalid Remote event rejection')
    出={'name':值['name'],'message':值['message']}
    if isinstance(值.get('code'),str):
        出['code']=值['code']
    if 'details' in 值:
        出['details']=值['details']
    return 出

def 解析远程事件结果(值):
    """解析 `$events/result` 载荷。"""
    if (not 是否记录(值) or not 精确键(值,['clientId','eventId','outcome'])
            or not 是否远程事件客户端标识(值.get('clientId'))
            or not 是否远程事件标识(值.get('eventId'))
            or not 是否记录(值.get('outcome'))):
        raise Exception('api gateway: invalid Remote event result')
    结局=值['outcome']
    if 结局.get('kind')=='next' and 精确键(结局,['kind']):
        return {'clientId':值['clientId'],'eventId':值['eventId'],'outcome':{'kind':'next'}}
    if (结局.get('kind')=='result'
            and (精确键(结局,['kind']) or 精确键(结局,['kind','value']))
            and ('value' not in 结局 or 是否远程json值(结局.get('value')))):
        结果结局={'kind':'result'}
        if 'value' in 结局:
            结果结局['value']=结局['value']
        return {'clientId':值['clientId'],'eventId':值['eventId'],'outcome':结果结局}
    if 结局.get('kind')=='rejected' and 精确键(结局,['kind','error']):
        return {
            'clientId':值['clientId'],'eventId':值['eventId'],
            'outcome':{'kind':'rejected','error':解析远程事件拒绝(结局['error'])},
        }
    raise Exception('api gateway: invalid Remote event result')

def 投影远程事件请求(值,主体):
    """去掉 waterfall 请求上的 agent 与 signal。"""
    if not 是否普通记录(值) or 'agent' not in 值 or 值['agent'] is not 主体:
        raise TypeError('api gateway: Remote event request must carry its scoped Agent directly')
    信号=值.get('signal') if 'signal' in 值 else None
    if 信号 is not None and not (hasattr(信号,'_事件') or hasattr(信号,'事件')):
        raise TypeError('api gateway: Remote event request signal must be an AbortSignal')
    请求={}
    for 键 in 值.keys():
        if 键=='agent' or 键=='signal':
            continue
        if not isinstance(键,str):
            raise TypeError('api gateway: Remote event request has a non-JSON property')
        请求[键]=值[键]
    if not 是否远程json值(请求):
        raise TypeError('api gateway: Remote event request is not lossless JSON data')
    出={'request':请求}
    if 信号 is not None:
        出['signal']=信号
    return 出

def 投影远程事件拒绝(原因):
    """投影为稳定 JSON 拒绝字段。"""
    记录=原因 if isinstance(原因,dict) else (原因 if isinstance(原因,BaseException) else None)
    名=None
    消息=None
    码=None
    细节=None
    if isinstance(记录,BaseException):
        名=getattr(记录,'name',None) or type(记录).__name__
        消息=str(记录)
        码=getattr(记录,'code',None)
        细节=getattr(记录,'details',None)
    elif isinstance(记录,dict):
        名=字符串属性(记录,'name')
        消息=字符串属性(记录,'message')
        码=字符串属性(记录,'code')
        细节=记录.get('details') if 'details' in 记录 else None
    if 名 is None:
        名='Error'
    if 消息 is None:
        消息=str(原因)
    出={'name':名,'message':消息}
    if isinstance(码,str):
        出['code']=码
    if 细节 is not None and 是否远程json值(细节):
        出['details']=细节
    return 出

def 还原远程事件拒绝(拒绝):
    """把线拒绝还原为异常。"""
    错误=Exception(拒绝['message'])
    错误.name=拒绝['name']
    if 'code' in 拒绝:
        错误.code=拒绝['code']
    if 'details' in 拒绝:
        错误.details=拒绝['details']
    return 错误

def 解析报文(文本,校验):
    """解析一条 JSON 对象报文。"""
    try:
        解码=json.loads(文本)
    except Exception as 原因:
        错=Exception('api gateway: Remote stream message is not JSON')
        错.__cause__=原因
        raise 错
    if not 是否记录(解码):
        raise Exception('api gateway: Remote stream message must be an object')
    return 校验(解码)

def 解析远程流客户端报文(文本):
    """解析浏览器到宿主的一条文本报文。"""
    def 校验(值):
        """校验客户端报文。"""
        if ((值.get('type')=='cancel' or 值.get('type')=='end')
                and 精确键(值,['type','streamId']) and 合法标识(值.get('streamId'))):
            return 值
        if (值.get('type')=='item'
                and (精确键(值,['type','streamId']) or 精确键(值,['type','streamId','value']))
                and 合法标识(值.get('streamId'))
                and ('value' not in 值 or 是否远程json值(值.get('value')))):
            return 值
        if (值.get('type')=='open'
                and 精确键(值,['type','streamId','endpoint','payload'])
                and 合法标识(值.get('streamId'))
                and isinstance(值.get('endpoint'),str) and 值.get('endpoint')!=''):
            return 值
        raise Exception('api gateway: invalid Remote stream client message')
    return 解析报文(文本,校验)

def 解析远程流服务端报文(文本):
    """解析宿主到浏览器的一条文本报文。"""
    def 校验(值):
        """校验服务端报文。"""
        if (值.get('type')=='item'
                and (精确键(值,['type','streamId']) or 精确键(值,['type','streamId','value']))
                and 合法标识(值.get('streamId'))):
            return 值
        if 值.get('type')=='end' and 精确键(值,['type','streamId']) and 合法标识(值.get('streamId')):
            return 值
        if (值.get('type')=='error'
                and 精确键(值,['type','streamId','error'])
                and 合法标识(值.get('streamId'))
                and 是否记录(值.get('error'))
                and 精确键(值['error'],['code','message','details'])
                and isinstance(值['error'].get('code'),str)
                and isinstance(值['error'].get('message'),str)
                and 是否记录(值['error'].get('details'))):
            return 值
        raise Exception('api gateway: invalid Remote stream server message')
    return 解析报文(文本,校验)
