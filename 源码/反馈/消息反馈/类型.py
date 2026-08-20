"""消息反馈公开请求/取值/失败词汇（仅类型约定，运行时以 dict 承载）。

对齐上游 `message-feedback/src/types.ts`。公开面仅中文名；失败码字面量保持上游。
"""

__all__=[#仅中文公开名
    '消息反馈版本','消息反馈评价','消息反馈项',
    '消息反馈列表请求','消息反馈列表取值','消息反馈写入请求','消息反馈删除请求','消息反馈删除取值',
    '消息反馈会话未找到','消息反馈目标未找到','消息反馈版本冲突','消息反馈评注空白','消息反馈评注过大',
    '消息反馈失败','消息反馈成功','消息反馈拒绝',
    '消息反馈列表结果','消息反馈写入结果','消息反馈删除结果',
]#公开面结束

消息反馈版本=str#品牌化版本令牌运行时为 str
消息反馈评价=('positive','negative')#正负评价
消息反馈项=dict#一条反馈
消息反馈列表请求=dict#list 请求
消息反馈列表取值=dict#list 取值
消息反馈写入请求=dict#put 请求
消息反馈删除请求=dict#delete 请求
消息反馈删除取值=dict#delete 取值 absent:true
消息反馈会话未找到=dict#session-not-found
消息反馈目标未找到=dict#target-not-found
消息反馈版本冲突=dict#version-conflict
消息反馈评注空白=dict#note-blank
消息反馈评注过大=dict#note-too-large
消息反馈失败=dict#失败联合
消息反馈成功=dict#ok:true
消息反馈拒绝=dict#ok:false
消息反馈列表结果=dict#list 结果
消息反馈写入结果=dict#put 结果
消息反馈删除结果=dict#delete 结果
