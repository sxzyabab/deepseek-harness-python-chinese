'网关分发失败与远程流载体失败'
import os
from ...类型化远程调用.协议.异常 import 远程错误#Remote 标记与失败

__all__=['网关错误','远程调用已取消','远程流载体错误','去掉敏感文案','失败说明']#仅中文公开名

def 去掉敏感文案(文本):
    '去掉绝对路径、用户名和环境变量，其余原文保留。'
    原文=str(文本)
    屏蔽名=set(os.environ)
    屏蔽值=set()
    for 键 in ('USERNAME','USER','LOGNAME','USERPROFILE','HOME'):
        值=os.environ.get(键)
        if isinstance(值,str) and 值!='':
            屏蔽值.add(值)
            基=os.path.basename(值.rstrip('\\/'))
            if 基!='':
                屏蔽值.add(基)
    for 值 in os.environ.values():
        if isinstance(值,str) and (len(值)>=8 or '\\' in 值 or '/' in 值):
            屏蔽值.add(值)
    留下=[]
    for 词 in 原文.split():
        裸=词.strip('\'"')
        统一=裸.replace('\\','/')
        if 统一.startswith('/') or 统一.startswith('~/') or (len(统一)>2 and 统一[0].isalpha() and 统一[1]==':' and 统一[2]=='/'):
            continue
        if 裸.startswith('$') and len(裸)>1:
            continue
        if len(裸)>2 and 裸.startswith('%') and 裸.endswith('%'):
            continue
        if '=' in 裸 and 裸.split('=',1)[0] in 屏蔽名:
            continue
        if 裸 in 屏蔽名 or 裸 in 屏蔽值 or 统一 in 屏蔽值:
            continue
        含敏感=False
        for 项 in 屏蔽值:
            if len(项)>=3 and 项 in 裸:
                含敏感=True
                break
        if 含敏感:
            continue
        留下.append(词)
    return ' '.join(留下).strip()

def 失败说明(错误):
    '保留去掉路径后的说明；说明被掏空时留下异常类型名。'
    说明=去掉敏感文案(错误)
    if 说明!='':
        return 说明
    if isinstance(错误,BaseException):
        return type(错误).__name__
    return 说明

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
        全文=去掉敏感文案('typert gateway: '+端点+': '+消息)#带端点前缀，去掉绝对路径
        if 全文=='':
            全文='typert gateway: '+端点+': '+失败说明(原因 if 原因 is not None else 消息)
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
