from ..约定.聊天可见性 import 是可见聊天节点
from ..约定.组树 import 在该层或更外

__all__=['聊天回合过程投影']


def 节点回合(节点):
    '节点落到的回合'
    if not isinstance(节点,dict):
        return None
    位置=节点.get('location')
    if isinstance(位置,dict) and 位置.get('kind') in ('turn','step'):
        回合=位置.get('turn') if isinstance(位置.get('turn'),dict) else {}
        return 回合.get('turn')
    return None


def 呈现相同(左,右):
    '两份过程呈现是不是同一份布局事实'
    if 左 is 右:
        return True
    if not isinstance(左,dict) or not isinstance(右,dict):
        return False
    return (
        左.get('spec') is 右.get('spec')
        and 左.get('turn')==右.get('turn')
        and 左.get('turnStarted')==右.get('turnStarted')
        and 左.get('turnClosed')==右.get('turnClosed')
        and 左.get('hasExternalProcess')==右.get('hasExternalProcess')
        and 左.get('hasInterleavedInput')==右.get('hasInterleavedInput')
        and 左.get('compactAnswer')==右.get('compactAnswer')
    )


def 推导呈现(回合,位置索引,节点存储):
    '从这一回合已加载的节点推出过程布局'
    键表=位置索引.getTurn(回合)
    控制=None
    for 键 in 键表:
        节点=节点存储.get(键)
        if isinstance(节点,dict) and 节点.get('kind')=='turn-process':
            控制=节点
            break
    if not isinstance(控制,dict):
        return None
    规格=控制.get('data') if isinstance(控制.get('data'),dict) else {}
    位置=控制.get('location') if isinstance(控制.get('location'),dict) else {}
    if 位置.get('kind') not in ('turn','step'):
        return None
    回合体=位置.get('turn') if isinstance(位置.get('turn'),dict) else {}
    开头人锚=None
    起点=回合体.get('start') if isinstance(回合体.get('start'),dict) else None
    起序号=起点.get('seq') if isinstance(起点,dict) else None
    for 键 in 键表:
        节点=节点存储.get(键)
        if not isinstance(节点,dict) or not 在该层或更外(节点,'input'):
            continue
        if 规格.get('controlAnchorSeq')==起序号 or 节点.get('anchorSeq')<规格.get('controlAnchorSeq'):
            锚=节点.get('anchorSeq')
            开头人锚=锚 if 开头人锚 is None or 锚>开头人锚 else 开头人锚
    有外部过程=False
    有插入输入=False
    紧凑回答=True
    for 键 in 键表:
        节点=节点存储.get(键)
        if not isinstance(节点,dict) or not 是可见聊天节点(节点) or 节点.get('kind')=='turn-process':
            continue
        if 在该层或更外(节点,'input') and (开头人锚 is None or 节点.get('anchorSeq')>开头人锚):
            有插入输入=True
            if 规格.get('answerAnchorSeq') is None or 节点.get('anchorSeq')<规格.get('answerAnchorSeq'):
                紧凑回答=False
        if 在该层或更外(节点,'turn') or 节点.get('anchorSeq')<规格.get('processStartSeq') or (规格.get('answerAnchorSeq') is not None and 节点.get('anchorSeq')>=规格.get('answerAnchorSeq')):
            continue
        数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
        if 节点.get('kind')!='assistant-step' or 规格.get('answerStep') is None or 数据.get('step')!=规格.get('answerStep'):
            有外部过程=True
    return {
        'turn':回合,
        'spec':规格,
        'turnStarted':回合体.get('start') is not None,
        'turnClosed':回合体.get('status')=='closed',
        'hasExternalProcess':有外部过程,
        'hasInterleavedInput':有插入输入,
        'compactAnswer':紧凑回答,
    }


class 聊天回合过程投影:
    '按回合保留的过程布局。节点变化后只重算受影响的回合'
    def __init__(自身):
        '开始时没有任何回合'
        自身.呈现={}

    def get(自身,节点):
        '读这个节点所属回合的过程呈现'
        回合=节点回合(节点)
        if 回合 is None:
            return None
        return 自身.呈现.get(回合)

    def replace(自身,顺序,位置索引,节点存储):
        '按当前可见顺序整表替换，返回呈现变了的回合'
        回合集=set()
        for 键 in 顺序:
            回合=节点回合(节点存储.get(键))
            if 回合 is not None:
                回合集.add(回合)
        变化=set()
        for 回合 in set(list(自身.呈现.keys())+list(回合集)):
            下一=推导呈现(回合,位置索引,节点存储) if 回合 in 回合集 else None
            if 自身.设置(回合,下一):
                变化.add(回合)
        return 变化

    def update(自身,回合集,位置索引,节点存储):
        '只重算给出的回合'
        变化=set()
        for 回合 in 回合集:
            if 自身.设置(回合,推导呈现(回合,位置索引,节点存储)):
                变化.add(回合)
        return 变化

    def 设置(自身,回合,下一):
        '相同呈现不替换引用'
        当前=自身.呈现.get(回合)
        if 呈现相同(当前,下一):
            return False
        if 下一 is None:
            if 回合 in 自身.呈现:
                del 自身.呈现[回合]
        else:
            自身.呈现[回合]=下一
        return True
