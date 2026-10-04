'网关分发失败与远程流载体失败'
from ...类型化远程调用.协议.异常 import 远程错误#Remote 标记与失败

__all__=['网关错误','远程调用已取消','远程流载体错误']#仅中文公开名

class 网关错误(远程错误):
    '在被调业务方法之外产生的分发失败'
    def __init__(自身,码,端点,消息,选项=None):
        '消息中不嵌入边界值。选项为 dict'
        if 选项 is None:#无选项
            选项={}#空
        if not 码.startswith('gateway/'):#线路码带 gateway/ 前缀
            码='gateway/'+码#补前缀
        原因=选项['cause'] if 'cause' in 选项 else None#可选原因
        细节={'endpoint':端点}#端点
        if 'field' in 选项 and 选项['field'] is not None:#有字段
            细节['field']=选项['field']#字段
        全文='typert gateway: '+端点+': '+消息#带端点前缀
        super().__init__(码,全文,细节,原因=原因 if isinstance(原因,BaseException) else None)#构造
        自身.name='TypertGatewayError'#固定错误名
        自身.endpoint=端点#端点
        自身.field=选项['field'] if 'field' in 选项 else None#可选线字段

class 远程调用已取消(Exception):
    'Remote 调用已被取消'
    def __init__(自身,端点,原因):
        '记下端点与原因'
        super().__init__('Remote invocation "'+端点+'" was aborted')#消息
        自身.name='RemoteInvocationCancelled'#按结构识别
        自身.endpoint=端点#端点
        if isinstance(原因,BaseException):#原因已是异常
            自身.__cause__=原因#挂原因

class 远程流载体错误(Exception):
    '可由域传输重试的物理 Remote 流套接字失败'

    def __init__(自身,消息,原因=None):
        '记下消息与可选因果'
        super().__init__(消息)#构造
        自身.name='RemoteStreamCarrierError'#稳定名
        if isinstance(原因,BaseException):#有因果
            自身.__cause__=原因#挂上
