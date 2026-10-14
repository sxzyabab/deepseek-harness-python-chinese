import os#只用于从说明里去掉路径和用户名

def 失败说明(错误):
    '调用方看得见的失败句。去掉绝对路径、用户名和环境变量，其余原文保留。'
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
    if 说明!='':
        return 说明
    if isinstance(错误,BaseException):
        return type(错误).__name__
    return 说明

class 文件上传错误(Exception):#本包失败
    '文件上传包内的本地失败'
    def __init__(自身,消息=''):#构造本地失败
        '记下说明；去掉绝对路径、用户名和环境变量。'
        干净=失败说明(消息)#说明
        if 干净=='':#掏空
            干净='文件上传失败'#兜底
        super().__init__(干净)#人类诊断

class 远程错误(文件上传错误):#结构兼容 RemoteError
    '一次远程调用失败：真实异常，携带稳定码与细节。判别按 code，不按类型链'
    def __init__(自身,码,消息,细节=None,选项=None):#构造远程错误
        '写入码、消息、细节与可选因果。说明去掉绝对路径。'
        干净=失败说明(消息)#说明
        if 干净=='':#掏空
            干净=str(码)#用稳定码
        super().__init__(干净)#人类诊断
        自身.code=码#稳定失败码
        自身.message=干净#跨线路消息
        自身.details={} if 细节 is None else 细节#结构化细节
        自身.isDSHRemoteError=True#结构标记
        自身.name='RemoteError'#错误名
        if 选项 is not None and 'cause' in 选项:#有因果
            自身.__cause__=选项['cause']#挂上原因
