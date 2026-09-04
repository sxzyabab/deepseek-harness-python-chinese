"""Agent Teams Web 词典。

对齐上游 `client-ui-agent-team/src/client/locales.ts`。公开面仅中文名。
"""
__all__=['命名空间','中文','英文','NS','zh','en']#仅中文公开名

命名空间='agent-team'#locale 命名空间
NS=命名空间#英文别名

中文={#简体中文词典
    'trigger':'Agent Team',#触发按钮
    'refresh':'刷新 Team',#刷新
    'close':'关闭',#关闭
    'loading':'正在加载 Team…',#加载中
    'empty':'还没有共享任务',#空任务
    'roster':'成员',#成员区
    'tasks':'共享任务',#任务区
    'model':'模型',#模型标签
    'open':'打开 teammate 会话',#打开子会话
    'create':'新建任务',#新建
    'subject':'任务标题',#标题
    'description':'任务描述',#描述
    'blockers':'依赖任务 id（逗号分隔）',#依赖
    'scopes':'写入范围（逗号分隔）',#写范围
    'save':'保存',#保存
    'cancel':'取消',#取消
    'edit':'编辑',#编辑
    'complete':'完成',#完成
    'reopen':'重开',#重开
    'delete':'删除',#删除
    'owner':'Owner',#owner 标签
    'unowned':'未分配',#无主
    'blockedBy':'依赖',#依赖标签
    'writeScopes':'写入范围',#写范围标签
    'ready':'可开始',#就绪
    'blocked':'被依赖阻塞',#阻塞
    'conflict':'任务状态已变化，已重新加载；请检查后重试。',#冲突
    'memberStatus.running':'运行中',#成员运行中
    'memberStatus.idle':'空闲',#成员空闲
    'memberStatus.inactive':'未运行',#成员未运行
    'memberStatus.provisioning':'准备中',#成员准备中
    'memberStatus.failed':'失败',#成员失败
    'status.pending':'待处理',#任务待处理
    'status.in_progress':'进行中',#任务进行中
    'status.completed':'已完成',#任务已完成
}#中文结束
zh=中文#英文别名

英文={#英文词典
    'trigger':'Agent Team',#触发按钮
    'refresh':'Refresh Team',#刷新
    'close':'Close',#关闭
    'loading':'Loading Team…',#加载中
    'empty':'No shared tasks yet',#空任务
    'roster':'Members',#成员区
    'tasks':'Shared tasks',#任务区
    'model':'Model',#模型标签
    'open':'Open teammate conversation',#打开子会话
    'create':'New task',#新建
    'subject':'Task subject',#标题
    'description':'Task description',#描述
    'blockers':'Blocking task ids (comma separated)',#依赖
    'scopes':'Write scopes (comma separated)',#写范围
    'save':'Save',#保存
    'cancel':'Cancel',#取消
    'edit':'Edit',#编辑
    'complete':'Complete',#完成
    'reopen':'Reopen',#重开
    'delete':'Delete',#删除
    'owner':'Owner',#owner 标签
    'unowned':'Unowned',#无主
    'blockedBy':'Blocked by',#依赖标签
    'writeScopes':'Write scopes',#写范围标签
    'ready':'Ready',#就绪
    'blocked':'Blocked by dependencies',#阻塞
    'conflict':'Task state changed and was reloaded. Review it before retrying.',#冲突
    'memberStatus.running':'Running',#成员运行中
    'memberStatus.idle':'Idle',#成员空闲
    'memberStatus.inactive':'Inactive',#成员未运行
    'memberStatus.provisioning':'Provisioning',#成员准备中
    'memberStatus.failed':'Failed',#成员失败
    'status.pending':'Pending',#任务待处理
    'status.in_progress':'In progress',#任务进行中
    'status.completed':'Completed',#任务已完成
}#英文结束
en=英文#英文别名
