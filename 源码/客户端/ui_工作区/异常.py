class 工作区错误(Exception):
    '本包工作区浏览器失败'

class 目录浏览错误(Exception):
    '目录浏览业务失败'
    def __init__(自身,rpc错误):
        'rpc错误为 RemoteFailure dict'
        自身.rpcError=rpc错误
        码=rpc错误['code'] if isinstance(rpc错误,dict) and 'code' in rpc错误 else ''
        文=rpc错误['message'] if isinstance(rpc错误,dict) and 'message' in rpc错误 else str(rpc错误)
        super().__init__('目录浏览失败: '+str(码)+': '+str(文))
        自身.name='DirectoryBrowseError'
