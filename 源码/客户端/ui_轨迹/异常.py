import os

class 轨迹错误(Exception):
    '本包异常基类'
    def __init__(自身,消息):
        '说明里去掉绝对路径、用户名和环境变量'
        说明=去掉敏感(消息)
        if 说明=='':
            说明='轨迹错误'
        super().__init__(说明)

def 去掉敏感(文本):
    '去掉绝对路径、用户名和环境变量，留下其余说明'
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

def 页面失败文案(错误):
    '页面上的失败句。去掉绝对路径、用户名和环境变量。'
    if isinstance(错误,BaseException):
        名=type(错误).__name__
        原文=str(错误.args[0]) if len(错误.args)>0 else ''
    else:
        名=''
        原文=str(错误)
    说明=去掉敏感(原文)
    if 说明=='':
        if 名!='':
            return 名
        return '轨迹错误'
    return 说明
