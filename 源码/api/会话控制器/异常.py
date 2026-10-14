'会话控制器远程失败、创建分叉失败与线事件验收失败'
import os

__all__=[#仅中文公开名
    '远程错误','会话未找到','子智能体会话所有权','cwd冲突','预设冲突',
    '会话创建错误','会话分叉错误','会话线事件错误','去掉敏感文案',
]#公开面结束

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
        if 原因 is not None:#原因
            自身.__cause__=原因#链接

class 会话未找到(Exception):
    '冷会话未找到'

class 子智能体会话所有权(Exception):
    '子智能体所有权围栏'
    def __init__(自身,会话标识):
        '记下会话标识'
        super().__init__('session "'+str(会话标识)+'" is a subagent session; use subagent delivery')#消息
        自身.sessionId=会话标识#id

class cwd冲突(Exception):
    'cwd 冲突'
    def __init__(自身,会话标识,请求cwd,已有cwd):
        '记下冲突 cwd'
        super().__init__('session cwd conflict')#消息
        自身.sessionId=会话标识#id
        自身.requestedCwd=请求cwd#请求
        自身.existingCwd=已有cwd#已有

class 预设冲突(Exception):
    '预设冲突'
    def __init__(自身,会话标识,请求预设,已有预设):
        '记下冲突预设'
        super().__init__('session preset conflict')#消息
        自身.sessionId=会话标识#id
        自身.requestedPreset=请求预设#请求
        自身.existingPreset=已有预设#已有

class 会话创建错误(Exception):
    '结构化 session 创建失败'
    def __init__(自身,远程失败,请求会话标识=None):
        '记下失败'
        码=远程失败.code if hasattr(远程失败,'code') else 远程失败.get('code')#码
        消息=远程失败.message if hasattr(远程失败,'message') else 远程失败.get('message')#消息
        super().__init__('session create failed: '+str(码)+': '+str(消息))#文案
        自身.name='SessionCreateError'#名
        自身.rpcError=远程失败
        自身.requestedSessionId=请求会话标识#请求 id

class 会话分叉错误(Exception):
    '结构化 session 分叉失败'
    def __init__(自身,远程失败,源会话标识):
        '记下失败'
        码=远程失败.code if hasattr(远程失败,'code') else 远程失败.get('code')#码
        消息=远程失败.message if hasattr(远程失败,'message') else 远程失败.get('message')#消息
        super().__init__('session fork failed: '+str(码)+': '+str(消息))#文案
        自身.name='SessionForkError'#名
        自身.rpcError=远程失败
        自身.sourceSessionId=源会话标识#源

class 会话线事件错误(Exception):
    '会话线事件验收失败'
