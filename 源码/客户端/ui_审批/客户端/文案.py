'审批命名空间的中英文案表。页面上的字直接写中文，不从英文表取'

__all__=['命名空间','中文','英文']

命名空间='approval'#本地化命名空间

中文={#简体中文词典，键集合的真源
    'waiting':'等待审批',#等待条
    'detail.aria':'审批详情',#详情区无障碍名
    'escalation':'工具 {toolName} 请求越权执行',#没有理由时的标题
    'reject':'拒绝',#拒绝按钮
    'allowOnce':'允许一次',#允许一次按钮
}

英文={#英文词典，只随登记留下。显示不读这里
    'waiting':'Waiting for approval',
    'detail.aria':'Approval details',
    'escalation':'Tool {toolName} requests privileged execution',
    'reject':'Reject',
    'allowOnce':'Allow once',
}
