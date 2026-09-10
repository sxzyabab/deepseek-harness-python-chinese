"""会话级反馈的公开词汇。

对齐上游 `command-feedback/src/types.ts`。公开面仅中文名。
类别 id 与事件名是线协议，原样英文。
"""

__all__=[#仅中文公开名
    '反馈类别表',
]#公开面结束

# 类别取值是耐久日志词汇，保持英文元组供运行时与类型注释共用。
反馈类别表=(#反馈类别
    'task-result',
    'instruction-following',
    'product-interaction',
    'service-stability',
    'resource-cost',
    'security-privacy-permission',
    'other',
)#类别结束
