__all__=('JSONRPC传输错误','JSONRPC响应错误')#仅中文公开名

class JSONRPC传输错误(Exception):
    '本包异常基类'

class JSONRPC响应错误(JSONRPC传输错误):
    'JSON-RPC 错误响应，保留线上 code 与可选 data'
    def __init__(自身,码,消息,数据=None):
        '记下线上错误码、消息与可选载荷'
        super().__init__(消息)#用线上消息构造
        自身.code=码#线上错误码；对端未给时为 None
        自身.message=消息#线上错误消息
        自身.data=数据#可选结构化错误载荷
        自身.name='JsonRpcResponseError'#固定错误名
