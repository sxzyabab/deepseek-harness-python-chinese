__all__=['是可见聊天节点']


def 是可见聊天节点(节点):
    '系统提示、普通上下文、权限命令不进可见行。带工具变更的上下文仍留通知行'
    if 节点.get('visibility')!='visible':
        return False
    种类=节点.get('kind')
    if 种类=='system-prompt':
        return False
    if 种类=='context':
        数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
        内容=数据.get('content') if isinstance(数据.get('content'),list) else []
        有工具变更=False
        for 块 in 内容:
            if isinstance(块,dict) and 块.get('type') in ('tool-addition','tool-removal'):
                有工具变更=True
                break
        if not 有工具变更:
            return False
    if 种类=='command':
        数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
        if 数据.get('name')=='permission':
            return False
    return True
