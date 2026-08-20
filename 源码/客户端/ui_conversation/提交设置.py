"""宿主用户设置文档里存储的忙碌时 Enter 偏好。

对齐上游 `ui-conversation/src/submission-settings.ts`。公开面仅中文名。配置键英文字面量保持上游。
"""
from schemastery import 模式#配置模式

__all__=[#仅中文公开名
    '会话设置命名空间',
    '忙碌回车字段',
    '忙碌回车行为表',
    '默认忙碌回车行为',
    '会话设置模式',
]#公开面结束

会话设置命名空间='ui-conversation'#会话插件设置命名空间
忙碌回车字段='busyEnter'#忙碌时 Enter 字段名
忙碌回车行为表=('queue','steer')#忙碌时 Enter 合法行为：排队或介入
默认忙碌回车行为='queue'#默认忙碌时 Enter 为排队

会话设置模式=模式.对象({#持久会话设置 schema
    忙碌回车字段:模式.联合(list(忙碌回车行为表)).默认(默认忙碌回车行为),#busyEnter：排队或介入，默认排队
})#模式结束
