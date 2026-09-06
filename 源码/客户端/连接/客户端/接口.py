"""约定再导出中心：web-runtime 内每一条约定导入都走本文件。

对齐上游 `connection/src/client/api.ts`。公开面仅中文名。
类型与运行时协议辅助来自 apiproxy 的 api 层（零 Node 依赖，浏览器安全）；
抽象接口客户端是客户端边界。绝不要导入包根：那会把 bootHost/cordis 拖进浏览器打包。
"""
from ....host.apiproxy.接口 import (#网关 api 层再导出
    Rpc标识,#品牌化 RPC id
    会话搜索结果上限,#会话搜索结果上限
    传输错误,#传输错误工厂
)#结束网关导入
from ....host.apiproxy.客户端 import (#客户端边界
    抽象接口客户端,#抽象 API 客户端
    接口客户端协议,#客户端接口
)#结束客户端导入

__all__=[#仅中文公开名
    '结果槽',
    '抽象接口客户端',
    '接口客户端协议',
    'Rpc标识',
    '会话搜索结果上限',
    '传输错误',
]#公开面结束

def 结果槽(响应):#取出 result
    """解开一元响应：RpcResponse → RpcResult（业务代码只关心 result 槽）。"""
    return 响应['result']#业务结果槽
