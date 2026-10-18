'系统提示在某个事件上的解释。字段用上游英文键'

__all__=['检视系统提示']

def 检视系统提示(先前,事件):
    '系统消息或表面替换之后的提示状态。没有新事实时沿用先前'
    if not isinstance(事件,dict):
        return 先前
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    if 事件.get('type')=='system/message':
        return {
            'text':数据.get('text') if 数据.get('text') is not None else (None if 先前 is None else 先前.get('text')),
            'seq':事件.get('seq'),
        }
    if 先前 is None:
        return None
    return 先前
