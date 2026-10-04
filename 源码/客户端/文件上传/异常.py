class 文件上传错误(Exception):#本包失败
    '文件上传包内的本地失败'

class 远程错误(文件上传错误):#结构兼容 RemoteError
    '一次远程调用失败：真实异常，携带稳定码与细节。判别按 code，不按类型链'
    def __init__(自身,码,消息,细节=None,选项=None):#构造远程错误
        '写入码、消息、细节与可选因果'
        super().__init__(消息)#人类诊断
        自身.code=码#稳定失败码
        自身.message=消息#跨线路消息
        自身.details={} if 细节 is None else 细节#结构化细节
        自身.isDSHRemoteError=True#结构标记
        自身.name='RemoteError'#错误名
        if 选项 is not None and 'cause' in 选项:#有因果
            自身.__cause__=选项['cause']#挂上原因
