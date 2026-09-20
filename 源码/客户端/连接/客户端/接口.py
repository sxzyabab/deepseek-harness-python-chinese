from ..rpc import Rpc标识,传输错误#关联 id 与传输失败结果

__all__=[#仅中文公开名
    '结果槽',
    'Rpc标识',
    '传输错误',
]

def 结果槽(响应):#取出 result
    """取出一元响应：RpcResponse → RpcResult（业务代码只关心 result 槽）。"""
    return 响应['result']#业务结果槽
