'请求头相对上一份提示和当前系统提示的解释'

__all__=['检视请求提示']

def 检视请求提示(先前,事件,系统):
    '抽出这次请求头里的提示快照。和上一份不同就记一条变更'
    数据=事件.get('data') if isinstance(事件,dict) and isinstance(事件.get('data'),dict) else {}
    提示=数据.get('prompt')
    快照={
        'prompt':提示,
        'system':None if 系统 is None else 系统,
        'seq':None if not isinstance(事件,dict) else 事件.get('seq'),
    }
    变更=None
    先前提示=None if not isinstance(先前,dict) else 先前.get('prompt')
    if 提示!=先前提示:
        变更={'previous':先前提示,'next':提示}
    return {'snapshot':快照,'change':变更}
