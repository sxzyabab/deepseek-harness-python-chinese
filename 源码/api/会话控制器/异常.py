'会话控制器远程失败、创建分叉失败与线事件验收失败'
__all__=[#仅中文公开名
    '远程错误','会话未找到','子智能体会话所有权','cwd冲突','预设冲突',
    '会话创建错误','会话分叉错误','会话线事件错误',
]#公开面结束

class 远程错误(Exception):
    '远程错误。附加信息做成属性'
    def __init__(自身,码,消息,详情=None,原因=None):
        '记下 code/message/details'
        super().__init__(消息)#消息
        自身.code=码#错误码
        自身.message=消息#消息
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
