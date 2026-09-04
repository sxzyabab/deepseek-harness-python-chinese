"""`approval` 命名空间词典。

对齐上游 `ui-approval/src/client/locales.ts`。公开面仅中文名。
"""
__all__=['命名空间','中文','英文','NS','zh','en']#仅中文公开名

命名空间='approval'#本地化命名空间
NS=命名空间#上游名

中文={#简体中文词典（键集合真源）
    'waiting':'等待审批',#等待态条带
    'detail.aria':'审批详情',#详情区无障碍标签
    'escalation':'工具 {toolName} 请求越权执行',#无 reason 时的标题模板
    'reject':'拒绝',#拒绝按钮
    'allowOnce':'允许一次',#仅本次允许按钮
}#中文结束

英文={#英文词典，按中文键集合校验
    'waiting':'Waiting for approval',#等待态条带
    'detail.aria':'Approval details',#详情区无障碍标签
    'escalation':'Tool {toolName} requests privileged execution',#无 reason 时的标题模板
    'reject':'Reject',#拒绝按钮
    'allowOnce':'Allow once',#仅本次允许按钮
}#英文结束

zh=中文#上游名
en=英文#上游名
