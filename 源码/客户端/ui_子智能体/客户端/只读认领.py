__all__=['选择只读子智能体']#仅中文公开名

def 选择只读子智能体(属主):
    """一次性历史、未知模式或续跑属主不可用时认领编写器。"""
    会话=属主['session'] if 'session' in 属主 else None
    if 会话 is None:
        return None
    子=会话['subagent'] if 'subagent' in 会话 else None
    if 子 is None:
        return None
    地址=子['address'] if 'address' in 子 else None
    if 地址 is None:
        return None
    if 地址['mode']=='unknown':
        return {'reason':'unknown'}
    if 地址['mode']=='one-shot':
        return {'reason':'one-shot'}
    if ('parentAvailable' not in 子) or (子['parentAvailable'] is not False):
        return None
    if ('running' in 会话) and 会话['running'] is True:
        return None
    return {'reason':'parent-unavailable'}
