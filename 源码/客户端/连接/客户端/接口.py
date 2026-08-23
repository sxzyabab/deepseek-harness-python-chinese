"""约定再导出中心：web-runtime 内每一条约定导入都走本文件。

对齐上游 `connection/src/client/api.ts`。公开面仅中文名。
类型与运行时协议辅助来自 apiproxy 的 api 层（零 Node 依赖，浏览器安全）；
抽象接口客户端是客户端边界。绝不要导入包根：那会把 bootHost/cordis 拖进浏览器打包。
"""
from ....host.apiproxy.接口 import (#网关 api 层再导出
    Rpc标识 as RpcId,#品牌化 RPC id
    会话搜索结果上限 as SESSION_SEARCH_RESULT_LIMIT,#会话搜索结果上限
    传输错误 as transportError,#传输错误工厂
)#结束网关导入
from ....host.apiproxy.客户端 import (#客户端边界
    抽象接口客户端 as AbstractApiClient,#抽象 API 客户端
    接口客户端协议 as IApiClient,#客户端接口
)#结束客户端导入

__all__=[#仅中文公开名与上游别名
    '结果槽',
    '抽象接口客户端',
    '接口客户端协议',
    'Rpc标识',
    '会话搜索结果上限',
    '传输错误',
    'AbstractApiClient',
    'IApiClient',
    'RpcId',
    'SESSION_SEARCH_RESULT_LIMIT',
    'transportError',
    'resultOf',
]#公开面结束

抽象接口客户端=AbstractApiClient#中文名
接口客户端协议=IApiClient#中文名
Rpc标识=RpcId#中文名
会话搜索结果上限=SESSION_SEARCH_RESULT_LIMIT#中文名
传输错误=transportError#中文名

def 结果槽(响应):#取出 result
    """解开一元响应：RpcResponse → RpcResult（业务代码只关心 result 槽）。"""
    if isinstance(响应,dict):#映射形
        return 响应['result']#业务结果槽
    return 响应.result#属性形

resultOf=结果槽#上游名
