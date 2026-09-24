"""与载体无关的 Typert Gateway 请求、服务与错误约定。"""

__all__=[#仅中文公开名
    '调用远程请求','网关错误码','Typert网关',
]#公开面结束

# InvokeRemoteRequest：namespace/method/args/signal?
调用远程请求=dict#一次远程调用请求形状

# 稳定基础设施与边界失败码（字面量联合）
网关错误码=(#错误码
    'gateway/ambiguous-endpoint','gateway/arguments-invalid','gateway/binding-invalid',
    'gateway/context-failed','gateway/context-not-found','gateway/context-unavailable',
    'gateway/definition-unavailable','gateway/input-invalid','gateway/invocation-unavailable',
    'gateway/lookup-failed','gateway/lookup-not-found','gateway/lookup-unavailable',
    'gateway/method-unavailable','gateway/protocol','gateway/provider-mismatch',
    'gateway/result-invalid','gateway/service-unavailable','gateway/signature-invalid',
    'gateway/uplink-overflow',
)#联合

Typert网关=dict#invoke(request) 分发面
