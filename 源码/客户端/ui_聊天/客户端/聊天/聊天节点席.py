import json
from ....存储 import 创建快照存储
from ....ui_基础界面组件.markdown.json块 import json块
from ....ui_对话.异常 import 标样式模块
from ..存储 import 回合过程是否打开
from ..约定.回合过程 import 回合过程始终打开
from ..约定.组树 import 在该层或更外
from .流程动效 import 正在隐藏或收起
from .用披露 import 注入聊天样式,取钩,真属性,挂节点

__all__=['聊天节点席']

样式模块='chat-view'


def 回合数据自(节点):
    '回合或步骤位置上的回合数据存储'
    if not isinstance(节点,dict):
        return None
    位置=节点.get('location')
    if not isinstance(位置,dict) or 位置.get('kind') not in ('turn','step'):
        return None
    回合=位置.get('turn')
    if isinstance(回合,dict):
        return 回合.get('data')
    return None


def 回合号自(节点):
    '节点落在哪一回合'
    if not isinstance(节点,dict):
        return None
    位置=节点.get('location')
    if not isinstance(位置,dict) or 位置.get('kind') not in ('turn','step'):
        return None
    回合=位置.get('turn')
    if isinstance(回合,dict):
        return 回合.get('turn')
    return None


def 选节点(钩,键,选择=None):
    '钩子直接给节点，或再套一层选择'
    if not callable(钩):
        return None
    if 选择 is None:
        return 钩(键)
    return 钩(键,选择)


class 聊天节点席:
    '订阅一个稳定键，套上回合过程显隐，再交给对应渲染器'
    def __init__(自身,属性=None):
        '记下节点键'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.隐藏席=None
        自身.披露重置=创建快照存储(0)
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '过程成员收起时用可搜索隐藏，不卸子树'
        属性=自身.属性
        if 'window' not in 属性:
            return 自身.根
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'聊天视图.module.css')
        键=属性.get('nodeKey')
        节点=选节点(属性.get('useChatNode'),键)
        if not isinstance(节点,dict):
            if 自身.根 is not None:
                自身.根.remove()
                自身.根=None
            return None
        组分=属性.get('groupPart')
        回合=回合号自(节点)
        呈现=选节点(属性.get('useChatNodeProcess'),键)
        规格=呈现.get('spec') if isinstance(呈现,dict) else None
        贴底=属性.get('useChatNodeBottom')
        在底=贴底(键) is True if callable(贴底) else False
        推迟=在底 and 属性.get('deferCollapse') is True
        存储钩=属性.get('useStore')
        已存开=False
        if callable(存储钩) and isinstance(规格,dict):
            def 选开(状态):
                '读者对这一过程的开合'
                return 回合过程是否打开(状态,规格,推迟)
            已存开=存储钩(选开) is True
        进行中=isinstance(呈现,dict) and 呈现.get('turnClosed') is not True
        交错=isinstance(呈现,dict) and 呈现.get('hasInterleavedInput') is True
        总开=进行中 or 交错 or 回合过程始终打开(节点)
        过程开=总开 or 已存开

        def 设开(打开):
            '写回这一回答代的开合'
            if isinstance(规格,dict) and not 总开 and callable(属性.get('actions',{}).get('setTurnProcessOpen') if isinstance(属性.get('actions'),dict) else None):
                属性['actions']['setTurnProcessOpen'](规格.get('turn'),规格.get('answerStep') or 0,打开)

        策略=取钩(属性,'usePresentation')
        if 策略 is None:
            策略=属性.get('usePresentation')
        折完成=False
        if callable(策略):
            def 选折(政策):
                '完成回合要不要折叠'
                return isinstance(政策,dict) and 政策.get('foldCompletedTurns') is True
            折完成=策略(选折) is True
        窗口就绪=isinstance(规格,dict) and isinstance(呈现,dict) and 折完成 and 呈现.get('turn')==规格.get('turn') and (呈现.get('turnStarted') is True or 呈现.get('turnClosed') is True)
        成员=窗口就绪 and not 在该层或更外(节点,'turn') and 节点.get('anchorSeq') is not None and 规格.get('processStartSeq') is not None and 节点['anchorSeq']>=规格['processStartSeq'] and (进行中 or 规格.get('answerAnchorSeq') is None or 节点['anchorSeq']<规格['answerAnchorSeq'] or (组分=='reasoning' and 节点.get('kind')=='assistant-step' and isinstance(节点.get('data'),dict) and 节点['data'].get('step')==规格.get('answerStep')))
        答案=窗口就绪 and not 进行中 and 组分!='reasoning' and 节点.get('kind')=='assistant-step' and isinstance(节点.get('data'),dict) and 节点['data'].get('step')==规格.get('answerStep')
        持披露=节点.get('kind')=='turn-process' or 答案
        可折=窗口就绪 and (进行中 or 成员 or 持披露)
        有内容=isinstance(规格,dict) and not 交错 and (isinstance(呈现,dict) and (呈现.get('hasExternalProcess') is True or 规格.get('inlineReasoning') is True))
        过程面=None
        if isinstance(规格,dict):
            过程面={'spec':规格,'foldable':可折,'hasContent':有内容,'open':过程开,'setOpen':设开}
        控件失活=节点.get('kind')=='turn-process' and 折完成 and not 可折
        紧凑答=答案 and 可折 and isinstance(呈现,dict) and 呈现.get('compactAnswer') is True and not 过程开
        过程隐=控件失活 or (可折 and 成员 and not 过程开)

        def 揭开():
            '成员被找到时打开过程'
            if 成员:
                设开(True)

        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.className='flowItem'
            标样式模块(自身.根,样式模块)
        流键=节点.get('key') if 组分 is None or 组分=='response' else json.dumps([节点.get('key'),组分],ensure_ascii=False)
        自身.根.setAttribute('data-chat-anchor-key','' if 流键 is None else str(流键))
        自身.根.setAttribute('data-chat-flow-key','' if 流键 is None else str(流键))
        真属性(自身.根,'data-chat-paging-anchor',节点.get('kind')!='turn-process')
        自身.根.setAttribute('data-chat-node-key','' if 节点.get('key') is None else str(节点.get('key')))
        if 组分 is None:
            自身.根.removeAttribute('data-chat-group-part')
        else:
            自身.根.setAttribute('data-chat-group-part',str(组分))
        自身.根.setAttribute('data-chat-flow-kind',str(节点.get('kind')))
        if 回合 is None:
            自身.根.removeAttribute('data-chat-turn')
        else:
            自身.根.setAttribute('data-chat-turn',str(回合))
        真属性(自身.根,'data-turn-process-member',成员)
        真属性(自身.根,'data-turn-process-hidden',过程隐)
        真属性(自身.根,'data-turn-process-answer',紧凑答)
        组动作=取钩(属性,'useGroupAction')
        if 组动作 is None:
            组动作=属性.get('useGroupAction')
        if callable(组动作):
            if 自身.隐藏席 is None:
                自身.隐藏席=组动作(过程隐,揭开)
            elif hasattr(自身.隐藏席,'准备'):
                自身.隐藏席.准备(过程隐,揭开)
            if hasattr(自身.隐藏席,'绑'):
                自身.隐藏席.绑(自身.根)
        if 成员 and 过程隐 and 自身.根 is not None and 正在隐藏或收起(自身.根):
            if hasattr(自身.披露重置,'set') and hasattr(自身.披露重置,'getSnapshot'):
                自身.披露重置.set(自身.披露重置.getSnapshot()+1)
        while 自身.根.firstChild is not None:
            自身.根.removeChild(自身.根.firstChild)
        属主={
            'window':窗口,
            'node':节点,
            'cwd':属性.get('cwd'),
            'openFile':属性.get('openFile'),
            'inspectCall':属性.get('inspectCall'),
            'forkAt':属性.get('forkAt'),
            'loadImage':属性.get('loadImage'),
            'fileMentions':属性.get('fileMentions'),
            'turnProcess':过程面,
            't':属性.get('t'),
            'renderSlot':属性.get('renderSlot'),
            'renderFactorySlot':属性.get('renderFactorySlot'),
            'useChat':属性.get('useChat'),
            'useStore':属性.get('useStore'),
            'actions':属性.get('actions'),
            'usePresentation':策略,
        }
        if 组分 is not None:
            属主['groupPart']=组分
        钩上下文={'turnData':回合数据自(节点),'disclosureReset':自身.披露重置,'useGroupAction':组动作}

        def 截断(总):
            '截断脚'
            译=属性.get('t')
            if callable(译):
                return 译('json.truncated',{'total':总})
            return str(总)

        回退=json块({
            'window':窗口,
            'label':属性['t']('message.unknownSurface',{'type':节点.get('kind')}) if callable(属性.get('t')) else str(节点.get('kind')),
            'payload':节点.get('data'),
            'truncatedLabel':截断,
        })
        槽=属性.get('renderSlot')
        画出=None
        if callable(槽):
            画出=槽('conversation.chat.node',属主,{
                'entryKey':节点.get('kind'),
                'hookContext':钩上下文,
                'fallback':回退,
                'window':窗口,
            })
        if 画出 is None or 画出 is 回退:
            画出=回退.渲染()
        挂节点(自身.根,画出)
        if 属性.get('parent') is not None and 自身.根.parentNode is None:
            属性['parent'].appendChild(自身.根)
        return 自身.根
