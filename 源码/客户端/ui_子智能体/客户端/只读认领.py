__all__=['选择只读子智能体']#仅中文公开名

def 选择只读子智能体(属主):#是否改用只读编写器
    """一次性历史或续跑属主不可用时认领编写器。"""
    会话=属主['session']#会话
    子=会话['subagent'] if 'subagent' in 会话 else None#本会话的子智能体元数据
    if 子 is None:#不是子智能体会话
        return None#不认领
    地址=子['address']#地址
    if 地址['mode']=='one-shot':#一次性
        return {'reason':'one-shot'}#只读历史
    if 子['parentAvailable']:#父会话在
        return None#继续用默认编写器
    if 会话['running'] is True:#运行中不抢
        return None#保留默认编写器
    return {'reason':'parent-unavailable'}#父不可用接管
