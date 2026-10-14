'工作区控制器远程失败、创建失败与文档目录失败'
import os

__all__=['远程错误','工作区创建错误','工作区归档错误','文档目录错误','去掉敏感文案','失败说明']#仅中文公开名

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

class 远程错误(Exception):
    '远程错误。附加信息做成属性'
    def __init__(自身,码,消息,详情=None,原因=None):
        '记下 code/message/details。文案去掉绝对路径，原因链保留。'
        干净=去掉敏感文案(消息)
        if 干净=='' and 原因 is not None:
            干净=失败说明(原因)
        if 干净=='':
            干净=str(码)
        super().__init__(干净)#消息
        自身.code=码#错误码
        自身.message=干净#消息
        自身.details={} if 详情 is None else 详情#详情
        if 原因 is not None:#原因链
            自身.__cause__=原因#链接

class 工作区归档错误(Exception):
    '归档被宿主拒绝。code 区分仍在运行与找不到会话。'

    def __init__(自身,远程失败):
        '记下宿主业务或折叠后的载体失败'
        码=远程失败['code'] if isinstance(远程失败,dict) else getattr(远程失败,'code',None)#码
        消息=远程失败['message'] if isinstance(远程失败,dict) else getattr(远程失败,'message',None)#消息
        super().__init__('workspace session archive failed: '+str(码)+': '+失败说明(消息))#文案
        自身.name='WorkspaceArchiveError'#错误名
        自身.rpcError=远程失败#远程失败

class 工作区创建错误(Exception):
    '区分 Host 业务错误的结构化创建失败'

    def __init__(自身,远程失败):
        '记下 Host 业务或折叠后的载体失败'
        码=远程失败['code'] if isinstance(远程失败,dict) else getattr(远程失败,'code',None)#码
        消息=远程失败['message'] if isinstance(远程失败,dict) else getattr(远程失败,'message',None)#消息
        super().__init__('workspace create failed: '+str(码)+': '+失败说明(消息))#文案
        自身.name='WorkspaceCreateError'#错误名
        自身.rpcError=远程失败#远程失败

class 文档目录错误(Exception):
    '文档目录解析失败'
