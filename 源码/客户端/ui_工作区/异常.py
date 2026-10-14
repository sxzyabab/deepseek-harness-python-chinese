import os

def 页面失败文案(错误):
    '页面上给调用方看的失败句。去掉绝对路径、用户名和环境变量，其余原文保留。'
    if isinstance(错误,BaseException):
        名=type(错误).__name__
        消息=getattr(错误,'message',None)
        if isinstance(消息,str) and 消息!='':
            原文=消息
        elif len(错误.args)>0:
            原文=str(错误.args[0])
        else:
            原文=''
    else:
        名=''
        原文=str(错误)
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
    说明=' '.join(留下).strip()
    if 说明=='':
        return 名 if 名!='' else '失败'
    return 说明

class 工作区错误(Exception):
    '本包工作区浏览器失败'

class 目录浏览错误(Exception):
    '目录浏览业务失败'
    def __init__(自身,rpc错误):
        'rpc错误为 RemoteFailure dict'
        自身.rpcError=rpc错误
        码=rpc错误['code'] if isinstance(rpc错误,dict) and 'code' in rpc错误 else ''
        文=rpc错误['message'] if isinstance(rpc错误,dict) and 'message' in rpc错误 else str(rpc错误)
        super().__init__('目录浏览失败: '+str(码)+': '+页面失败文案(文))
        自身.name='DirectoryBrowseError'
