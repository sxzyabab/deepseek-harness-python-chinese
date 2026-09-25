__all__=[#仅中文公开名
    '远程失败','远程结果','远程流','远程流句柄','对等标识','对等作用域','远程调用','调用参数描述符','调用源码位置','调用描述符',
    '远程贡献','Typert编解码','Typert模式','查找提供方','查找线路声明',
    '宿主上下文提供方','客户端上下文绑定器','注册表变更','注册表约定',
]#公开面结束

远程失败=dict#code/message/details
远程结果=dict#ok + value|error
远程流=dict#下行项；可选上行类型标记
远程流句柄=dict#send/end/dispose
对等标识=str#PeerId
对等作用域=dict#id/ctx/dispose
远程调用=dict#request/service/peer/signal/uplink
调用参数描述符=dict#name/wire/source/lookup?/codec/acceptsUndefined?
调用源码位置=dict#file/line/column
调用描述符=dict#id/service/namespace/method/implementation?/mode?/invocation/scope?/parameters/uplink?/cancellation?/result/sourceLocation?
远程贡献=dict#package/descriptors
Typert编解码=dict#mode strict|src-json；strict 时带 typeSymbol/schema
Typert模式=dict#带 parse(value) 的边界模式
查找提供方=dict#parameter/wire/hostTypeSymbol/wireTypeSymbol/resolve
查找线路声明=dict#key/parameter/wire/hostTypeSymbol/wireTypeSymbol
宿主上下文提供方=dict#wire/wireTypeSymbol/resolve→Context|协议拥有值|None
客户端上下文绑定器=dict#identity(ctx)；resolve→Context|协议拥有值|None
注册表变更=dict#kind/key
注册表约定=dict#local/remotes/lookups/contexts
