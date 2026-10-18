from ..约定.聊天可见性 import 是可见聊天节点

__all__=['回合导航项相同','回合导航项']

提示预览上限=50
回答预览上限=120


def 预览(片段表,上限):
    '拼可见文本，压空白，超过上限就截断并加省略号'
    文=''
    未读完=False
    for 片段 in 片段表:
        if len(文)>=上限*2:
            未读完=True
            break
        被截=len(片段)>上限*2
        块=片段[:上限*2] if 被截 else 片段
        文=块 if 文=='' else 文+' '+块
        if 被截:
            未读完=True
            break
    规范=' '.join(文.split())
    if len(规范)>上限-1:
        return 规范[:上限-1].rstrip()+'…'
    if 未读完:
        return 规范+'…'
    return 规范


def 提示文本(节点):
    '用户消息里的文本预览'
    if not isinstance(节点,dict) or 节点.get('kind')!='user':
        return ''
    数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
    内容=数据.get('content') if isinstance(数据.get('content'),list) else []
    片段=[]
    for 块 in 内容:
        if isinstance(块,dict) and 块.get('type')=='text' and isinstance(块.get('text'),str):
            片段.append(块['text'])
    return 预览(片段,提示预览上限)


def 回答文本(节点):
    '助手步骤里的文本预览'
    if not isinstance(节点,dict) or 节点.get('kind')!='assistant-step':
        return ''
    数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
    块表=数据.get('blocks') if isinstance(数据.get('blocks'),list) else []
    片段=[]
    for 块 in 块表:
        if isinstance(块,dict) and 块.get('kind')=='text' and isinstance(块.get('text'),str):
            片段.append(块['text'])
    return 预览(片段,回答预览上限)


def 回合导航项相同(左,右):
    '两边描述的是不是同一枚轨道标记'
    if not isinstance(左,dict) or not isinstance(右,dict):
        return 左 is 右
    return (
        左.get('turn')==右.get('turn')
        and 左.get('anchorKey')==右.get('anchorKey')
        and 左.get('prompt')==右.get('prompt')
        and 左.get('response')==右.get('response')
    )


def 回合导航项(回合,位置索引,节点存储):
    '一个已加载回合的轨道项。没有可见节点就没有'
    已加载=[]
    for 键 in 位置索引.getTurn(回合):
        节点=节点存储.get(键)
        if isinstance(节点,dict) and 是可见聊天节点(节点):
            已加载.append(节点)
    用户=None
    for 节点 in 已加载:
        if 节点.get('kind')=='user':
            用户=节点
            break
    锚=用户 if 用户 is not None else (已加载[0] if len(已加载)>0 else None)
    if 锚 is None:
        return None
    回答=None
    for 节点 in reversed(已加载):
        if 回答文本(节点)!='':
            回答=节点
            break
    return {
        'turn':回合,
        'anchorKey':锚.get('key'),
        'prompt':'' if 用户 is None else 提示文本(用户),
        'response':'' if 回答 is None else 回答文本(回答),
    }
