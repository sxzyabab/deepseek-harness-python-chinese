'工作区控制器远程失败、创建失败与文档目录失败'
__all__=['远程错误','工作区创建错误','文档目录错误']#仅中文公开名

class 远程错误(Exception):
    '远程错误。附加信息做成属性'
    def __init__(自身,码,消息,详情=None,原因=None):
        '记下 code/message/details'
        super().__init__(消息)#消息
        自身.code=码#错误码
        自身.message=消息#消息
        自身.details={} if 详情 is None else 详情#详情
        if 原因 is not None:#原因链
            自身.__cause__=原因#链接

class 工作区创建错误(Exception):
    '区分 Host 业务错误的结构化创建失败'

    def __init__(自身,远程失败):
        '记下 Host 业务或折叠后的载体失败'
        码=远程失败['code'] if isinstance(远程失败,dict) else getattr(远程失败,'code',None)#码
        消息=远程失败['message'] if isinstance(远程失败,dict) else getattr(远程失败,'message',None)#消息
        super().__init__('workspace create failed: '+str(码)+': '+str(消息))#文案
        自身.name='WorkspaceCreateError'#错误名
        自身.rpcError=远程失败#远程失败

class 文档目录错误(Exception):
    '文档目录解析失败'
