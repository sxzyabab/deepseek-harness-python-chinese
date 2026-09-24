__all__=['智能体预设投影定义']

def 初始化预设投影(头):
    """从会话头取出创建时的预设标识。"""
    if 'agentPreset' in 头:
        return 头['agentPreset']
    return None

def 应用预设投影(状态,事件):
    """选中事件推进当前预设，其余事件保持。"""
    if 事件['type']=='agent-preset/selected':
        return 事件['data']['agentPreset']
    return 状态

def 视图预设投影(状态):
    """主机状态原样作为可见视图。"""
    return 状态

智能体预设投影定义={
    'key':'agentPreset',
    'init':初始化预设投影,
    'apply':应用预设投影,
    'wire':{'view':视图预设投影},
    'stateVersion':1,
}
