'会话和聊天状态面上的上下文占用'

__all__=['上下文占用']

def 上下文占用(压力):
    '分子和容量都已知时才给出占用，否则为 None'
    if not isinstance(压力,dict):
        return None
    已用=压力['projectedTokens'] if 'projectedTokens' in 压力 and 压力['projectedTokens'] is not None else 压力.get('pressureTokens')
    if 已用 is None or 压力.get('contextWindow') is None:
        return None
    窗口=压力['contextWindow']
    return {
        'percent':min(100,round(已用/窗口*100)),
        'usedTokens':已用,
        'contextWindow':窗口,
    }
