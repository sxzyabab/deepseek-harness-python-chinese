"""与编译器无关的 Typert 协议类型面。

对齐上游 `typert/protocol/src/types.ts`。公开面仅中文名；运行时以字典形状承载。
"""

__all__=[#仅中文公开名
    '远程失败','远程结果','调用参数描述符','调用源码位置','调用描述符',
    '远程贡献','Typert编解码','Typert模式','查找提供方','查找线路声明',
    '宿主上下文提供方','客户端上下文绑定器','注册表变更','注册表约定',
]#公开面结束

远程失败=dict#code/message/details
远程结果=dict#ok + value|error
调用参数描述符=dict#name/wire/source/lookup?/codec/acceptsUndefined?
调用源码位置=dict#file/line/column
调用描述符=dict#id/service/namespace/method/implementation?/invocation/scope?/parameters/cancellation?/result/sourceLocation?
远程贡献=dict#package/descriptors
Typert编解码=dict#mode strict|src-json；strict 时带 typeSymbol/schema
Typert模式=dict#带 parse(value) 的边界模式
查找提供方=dict#parameter/wire/hostTypeSymbol/wireTypeSymbol/resolve
查找线路声明=dict#key/parameter/wire/hostTypeSymbol/wireTypeSymbol
宿主上下文提供方=dict#wire/wireTypeSymbol/resolve
客户端上下文绑定器=dict#identity(ctx)
注册表变更=dict#kind/key
注册表约定=dict#local/remotes/lookups/contexts
