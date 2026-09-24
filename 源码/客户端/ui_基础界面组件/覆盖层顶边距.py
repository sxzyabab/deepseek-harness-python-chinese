__all__=['覆盖层顶边距']

def 覆盖层顶边距(最小,顶净空=None):
    """覆盖层距视口顶的边距；有窗框净空则取较大者。"""
    if 顶净空 is None:
        return 最小
    return 顶净空 if 顶净空>最小 else 最小
