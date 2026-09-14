
__all__=['消息反馈注入面','反馈对话框注入面']#仅中文公开名

消息反馈注入面={#助手消息反馈注入业务面模板
    'hooks':{#本条目订阅的宿主可观察面
        'feedback':None,#所属 Session 的共享反馈视图
    },#hooks 结束
    'ensure':None,#首次交互时加载本 Session 反馈
    'current':None,#当前已提交条目
    'retract':None,#匹配才撤回
    'openDialog':None,#打开会话反馈对话框
}#注入面结束

反馈对话框注入面={#对话框注入业务面模板
    'hooks':{#本条目订阅的宿主可观察面
        'dialog':None,#对话框与轻提示状态
    },#hooks 结束
    'edit':None,#替换草稿一部分
    'submit':None,#提交草稿
    'dismiss':None,#关闭对话框
    'dismissFailure':None,#关掉失败提示
    'dismissToast':None,#退役轻提示
}#对话框注入结束
