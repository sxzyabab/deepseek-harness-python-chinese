from .助手Markdown import 助手Markdown
from .用披露 import 取钩

__all__=['助手节点视图']


class 助手节点视图:
    '流式、定稿和中断共用一个渲染器'
    def __init__(自身,属性=None):
        '记下助手步'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.文=None
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '收束节点对上这条尾时才解析文件提及'
        属性=自身.属性
        节点=属性.get('node') if isinstance(属性.get('node'),dict) else {}
        数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
        位置=节点.get('location') if isinstance(节点.get('location'),dict) else {}
        回合=位置.get('turn') if 位置.get('kind') in ('turn','step') and isinstance(位置.get('turn'),dict) else None
        取尾=取钩(属性,'useTurnData')
        if 取尾 is None and callable(属性.get('useTurnData')):
            取尾=属性['useTurnData']
        尾=取尾('turn-tail') if callable(取尾) else None
        属主=None
        终=数据.get('finalNode') if isinstance(数据.get('finalNode'),dict) else None
        收束=尾.get('closing') if isinstance(尾,dict) else None
        终尾=收束.get('finalNode') if isinstance(收束,dict) and isinstance(收束.get('finalNode'),dict) else None
        if isinstance(回合,dict) and 回合.get('status')=='closed' and 终 is not None and isinstance(终尾,dict):
            if 终尾.get('seq')==终.get('seq'):
                属主={'turn':回合,'seq':终.get('seq'),'openFile':属性.get('openFile')}
        提及=None
        if 属主 is not None and callable(属性.get('fileMentions')):
            提及=属性['fileMentions'](属主)
        过程=属性.get('turnProcess') if isinstance(属性.get('turnProcess'),dict) else None
        规格=过程.get('spec') if isinstance(过程,dict) and isinstance(过程.get('spec'),dict) else None
        推理隐=False
        if 过程 is not None and 规格 is not None:
            推理隐=过程.get('foldable') is True and 规格.get('answerStep')==数据.get('step') and 规格.get('inlineReasoning') is True and 过程.get('open') is not True

        def 揭开():
            '打开包住这段推理的过程'
            if isinstance(过程,dict) and callable(过程.get('setOpen')):
                过程['setOpen'](True)

        呈现=取钩(属性,'usePresentation')
        if 呈现 is None:
            呈现=属性.get('usePresentation')
        披露=取钩(属性,'useDisclosure')
        if 披露 is None:
            披露=属性.get('useDisclosure')
        组动作=取钩(属性,'useGroupAction')
        if 组动作 is None:
            组动作=属性.get('useGroupAction')
        文属性={
            'window':属性['window'],
            'blocks':数据.get('blocks'),
            'groupPart':属性.get('groupPart'),
            'useDisclosure':披露,
            'streaming':数据.get('status')=='running',
            'interrupted':数据.get('status')=='interrupted',
            'loadImage':属性.get('loadImage'),
            'reasoningHidden':推理隐,
            'useGroupAction':组动作,
            'usePresentation':呈现,
            'renderSlot':属性.get('renderSlot'),
            'revealProcess':揭开,
            'mentions':提及,
            't':属性.get('t'),
            'parent':属性.get('parent'),
        }
        if 自身.文 is None:
            自身.文=助手Markdown(文属性)
        else:
            自身.文.更新(文属性)
            自身.文.渲染()
        自身.根=自身.文.根
        return 自身.根
