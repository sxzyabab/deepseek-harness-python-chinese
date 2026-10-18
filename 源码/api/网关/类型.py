'与载体无关的网关请求、服务与错误约定。remote-error-codes 的既有映射也是类型，声明合并没有运行时，故障细节写在这里'

调用远程请求字段=('namespace','method','args','uplink','uplinkWindow','peer','signal')#解码后的一次调用
网关错误码=(#分发与边界失败
    'gateway/ambiguous-endpoint',
    'gateway/arguments-invalid',
    'gateway/binding-invalid',
    'gateway/context-failed',
    'gateway/context-not-found',
    'gateway/context-unavailable',
    'gateway/definition-unavailable',
    'gateway/input-invalid',
    'gateway/interactions-forbidden',
    'gateway/invocation-unavailable',
    'gateway/lookup-failed',
    'gateway/lookup-not-found',
    'gateway/lookup-unavailable',
    'gateway/method-unavailable',
    'gateway/peer-disposed',
    'gateway/protocol',
    'gateway/provider-mismatch',
    'gateway/result-invalid',
    'gateway/service-unavailable',
    'gateway/signature-invalid',
    'gateway/uplink-overflow',
)#错误码结束
网关故障细节字段=('endpoint','field')#每条基础设施失败都带端点，字段可选
线路流字段=('open','failure')#载体适配器
远程事件帧字段=('event','args','resources')#转发通知
远程事件上下文字段=('value','subject','agentId')#作用域事件的宿主事实
远程事件结局种类=('result','next')#客户端瀑布结局
远程事件宿主字段=('home',)#就绪帧里的宿主事实

__all__=[#公开名
    '调用远程请求字段','网关错误码','网关故障细节字段','线路流字段',
    '远程事件帧字段','远程事件上下文字段','远程事件结局种类','远程事件宿主字段',
]#公开面结束
