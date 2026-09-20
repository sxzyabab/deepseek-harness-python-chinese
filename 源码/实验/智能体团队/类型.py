__all__=[
    '团队标识','团队任务标识','团队消息标识',
    '团队成员阶段','团队任务状态','团队任务动作',
]

def 团队标识(标识):
    """把根 Session 身份烙成隐式 Team 身份。"""
    return 标识

def 团队任务标识(标识):
    """烙印已校验的任务 id。"""
    return 标识

def 团队消息标识(标识):
    """烙印已生成的 peer 消息 id。"""
    return 标识

团队成员阶段=('provisioning','active','failed')
团队任务状态=('pending','in_progress','completed','deleted')
团队任务动作=(
    'claim','release','edit','set_dependencies',
    'complete','reopen','reassign','delete',
)
