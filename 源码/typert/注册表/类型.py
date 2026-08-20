"""纯生成制品与运行时注册表类型。

对齐上游 `typert/registry/src/types.ts`。公开面仅中文名；结构为普通字典约定。
"""

__all__=[#仅中文公开名
    'Typert面','Typert文档标签','Typert文档','Typert成员模型','Typert类型模型',
    'Typert服务模型','Typert事件模型','Typert对象模型','Typert包模型','Typert模式',
    'Typert贡献','Typert模式记录','Typert包记录','Typert模式过滤','Typert包过滤',
]#公开面结束

# 面字面量：'host' | 'client'
Typert面=str#宿主面或客户端面

# 以下类型在 Python 侧以字典形状承载，名称仅作文档锚点
Typert文档标签=dict#JSDoc 标签：name/argument?/comment?/text
Typert文档=dict#description?/summary?/tags/jsDoc?
Typert成员模型=dict#kind/name/signature/summary?/jsDoc?
Typert类型模型=dict#name/declaration
Typert服务模型=dict#文档 + key/exportName/members/types
Typert事件模型=dict#文档 + name/mode?/signature
Typert对象模型=dict#文档 + name/exportName/members/types
Typert包模型=dict#services/events/objects
Typert模式=dict#name + schema（带 parse 的模式实例）
Typert贡献=dict#package/face/schemas/model/invocations
Typert模式记录=dict#模式 + package/face/key
Typert包记录=dict#package/face/key/model
Typert模式过滤=dict#package?/face?
Typert包过滤=dict#package?/face?
