"""与载体无关的 Typert Gateway 请求、服务与错误约定。

对齐上游 `api/gateway/src/types.ts`。公开面仅中文名。
"""

__all__=[#仅中文公开名
    '调用远程请求','网关错误码','Typert网关',
]#公开面结束

# InvokeRemoteRequest：namespace/method/args/signal?
调用远程请求=dict#一次远程调用请求形状

# 稳定基础设施与边界失败码（字面量联合）
网关错误码=(#错误码
    'ambiguous-endpoint','arguments-invalid','binding-invalid','context-failed',
    'context-not-found','context-unavailable','definition-unavailable','input-invalid',
    'invocation-unavailable','lookup-failed','lookup-not-found','lookup-unavailable',
    'method-unavailable','provider-mismatch','result-invalid','service-unavailable',
    'signature-invalid',
)#联合

Typert网关=dict#invoke(request) 分发面
