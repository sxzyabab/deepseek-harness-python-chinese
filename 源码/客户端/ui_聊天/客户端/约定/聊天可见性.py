__all__=['是可见聊天节点']

def 是可见聊天节点(节点):
    """排除系统提示、普通上下文与权限命令；持久事件与轨迹检视不受影响。节点为 dict。"""
    if 节点['visibility']!='visible':
        return False
    种=节点['kind'] if 'kind' in 节点 else None
    if 种=='system-prompt' or 种=='context':
        return False
    if 种=='command':
        数据=节点['data'] if 'data' in 节点 else {}
        return 数据['name']!='permission'
    return True
