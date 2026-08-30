"""反馈条目的注入面。

对齐上游 `ui-message-feedback/src/client/slots.ts`。公开面仅中文名。
目标槽位 `conversation.chat.assistant-actions` 由 ui-conversation 声明并定类型；本包只贡献条目，因此这里没有 SlotMap 合并。逐条消息的实时状态经 `feedback` hook 到达；inject 携带变更动词外加惰性加载器。
"""

__all__=['消息反馈注入面']#仅中文公开名

#一条助手消息反馈条目的注入业务面（字段名对齐上游 inject）
消息反馈注入面={#注入业务面模板
    'hooks':{#本条目订阅的宿主可观察面
        'feedback':None,#所属 Session 的共享反馈视图
    },#hooks 结束
    'ensure':None,#首次交互时加载本 Session 反馈
    'rate':None,#创建或替换本条消息的反馈
    'toggle':None,#相同则撤回否则写入
    'clearNote':None,#丢掉说明，保留评分
    'clear':None,#删除本条消息的反馈
}#注入面结束
