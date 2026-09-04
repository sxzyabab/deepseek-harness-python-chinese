"""公开的 Agent Teams 身份、持久记录与服务请求值。

对齐上游 `agent-team/src/types.ts`。公开面仅中文名。
"""
__all__=[#仅中文公开名
    '团队标识','团队任务标识','团队消息标识',
    '团队成员阶段','团队任务状态','团队任务动作',
]#公开面结束

def 团队标识(标识):#根 Session→TeamId
    """把根 Session 身份烙成隐式 Team 身份。"""
    return 标识#同串烙印

def 团队任务标识(标识):#字符串→TeamTaskId
    """烙印已校验的任务 id。"""
    return 标识#同串烙印

def 团队消息标识(标识):#字符串→TeamMessageId
    """烙印已生成的 peer 消息 id。"""
    return 标识#同串烙印

团队成员阶段=('provisioning','active','failed')#成员阶段联合
团队任务状态=('pending','in_progress','completed','deleted')#任务状态联合
团队任务动作=(#任务动作联合
    'claim','release','edit','set_dependencies',#认领释放编辑依赖
    'complete','reopen','reassign','delete',#完成重开改派删除
)#动作结束
