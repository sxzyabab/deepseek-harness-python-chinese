'远程智能体查找失败'
import os

__all__=['远程查找错误基类','远程会话未找到','远程子智能体会话所有权','去掉敏感文案','失败说明']#仅中文公开名

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

class 远程查找错误基类(Exception):
    '远程智能体查找包的异常基类'

class 远程会话未找到(远程查找错误基类):
    '持久会话库中没有的冷身份'

class 远程子智能体会话所有权(远程查找错误基类):
    '生命周期属于子智能体路由的会话身份'
    def __init__(自身,会话标识):
        '记下被围栏的会话身份'
        super().__init__('session "'+str(会话标识)+'" is a subagent session; use subagent delivery')#诊断应走子智能体投递
        自身.会话标识=会话标识#会话身份
