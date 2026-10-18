'网关分发失败与远程流载体失败'
from ...类型化远程调用.协议.异常 import 远程错误#线路失败

__all__=['网关错误','远程流载体错误','远程已取消','协议违规']#公开名

class 网关错误(远程错误):
    '在被调业务方法之外产生的分发失败'
    def __init__(自身,码,端点,消息,选项=None):
        '消息中不嵌入边界值。选项为 dict，可含 cause 与 field'
        if 选项 is None:#无选项
            选项={}#空
        字段=选项['field'] if 'field' in 选项 else None#可选线字段
        细节={'endpoint':端点}#端点
        if 字段 is not None:#有字段
            细节['field']=字段#带上
        原因=选项['cause'] if 'cause' in 选项 else None#可选原因
        因果=原因 if isinstance(原因,BaseException) else None#只把异常挂上
        super().__init__(码,'typert gateway: '+端点+': '+消息,细节,因果)#构造
        自身.name='TypertGatewayError'#固定错误名
        自身.endpoint=端点#端点
        自身.field=字段#字段

class 远程流载体错误(Exception):
    '可由域传输重试的物理 Remote 流套接字失败'
    def __init__(自身,消息,原因=None):
        '记下消息与可选因果。原因可以是异常，或带 cause 的选项'
        super().__init__(消息)#构造
        自身.name='RemoteStreamCarrierError'#稳定名
        因果=原因#待挂
        if isinstance(原因,dict) and 'cause' in 原因:#ErrorOptions
            因果=原因['cause']#取出
        if isinstance(因果,BaseException):#是异常
            自身.__cause__=因果#挂上

def 远程已取消(端点,原因):
    '载体取消折成 gateway/cancelled。多处抛出'
    因果=原因 if isinstance(原因,BaseException) else None#只挂异常
    return 远程错误('gateway/cancelled','Remote invocation "'+端点+'" was aborted',{},因果)#失败

def 协议违规(消息):
    '宿主侧流协议违规，标成 gateway/internal 以便界面进入错误态'
    return 远程错误('gateway/internal',消息,{})#失败
