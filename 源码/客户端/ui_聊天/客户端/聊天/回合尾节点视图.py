from ....ui_对话.异常 import 标样式模块
from ..约定.助手内容 import 有助手回复内容
from .回合助手 import 助手文本
from .回合用量面板 import 回合用量面板
from .消息图标动作 import 消息图标动作
from .用披露 import 取钩,注入聊天样式,挂节点

__all__=['回合尾节点视图']

样式模块='turn-tail'


def 末内容(快照,回合,跳过警告):
    '从后往前找这条回合里最后一块真正的内容'
    if not isinstance(快照,dict):
        return None
    位置=快照.get('locations')
    键表=[]
    if hasattr(位置,'getTurn'):
        键表=位置.getTurn(回合) or []
    elif isinstance(位置,dict) and callable(位置.get('getTurn')):
        键表=位置['getTurn'](回合) or []
    节点表=快照.get('nodes')
    下标=len(键表)-1
    while 下标>=0:
        键=键表[下标]
        节点=None
        if hasattr(节点表,'get'):
            节点=节点表.get(键)
        if isinstance(节点,dict):
            种=节点.get('kind')
            if 种 not in ('turn-tail','turn-process') and not (跳过警告 and 种=='turn-max-tokens'):
                return 节点
        下标-=1
    return None


class 回合尾节点视图:
    '回合本地动作和功能尾。助手放在哪不影响这里'
    def __init__(自身,属性=None):
        '记下尾节点'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '还没收束时只留功能尾。收束后加复制、分叉和用量'
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'回合尾节点视图.module.css')
        翻译=属性.get('t')
        节点=属性.get('node') if isinstance(属性.get('node'),dict) else {}
        位置=节点.get('location') if isinstance(节点.get('location'),dict) else {}
        回合位=位置.get('turn') if 位置.get('kind') in ('turn','step') and isinstance(位置.get('turn'),dict) else None
        if 回合位 is None:
            return None
        数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
        用量钩=取钩(属性,'usePerformanceUsage')
        if 用量钩 is None and callable(属性.get('usePerformanceUsage')):
            用量钩=属性['usePerformanceUsage']
        详细=False
        if callable(用量钩):
            def 选模式(模式):
                '详细模式才显示用量'
                return 模式
            详细=用量钩(选模式)=='detailed'
        访问=取钩(属性,'useAccess')
        if 访问 is None and callable(属性.get('useAccess')):
            访问=属性['useAccess']
        允许分叉=False
        if callable(访问):
            允许分叉=访问('session/fork') is True
        聊天=属性.get('useChat')
        更晚=False
        以回复结束=False
        if callable(聊天):
            def 选更晚(快照):
                '后面还有聊天节点就不能从这里分叉'
                收束=数据.get('closing') if isinstance(数据.get('closing'),dict) else None
                终=收束.get('finalNode') if isinstance(收束,dict) and isinstance(收束.get('finalNode'),dict) else {}
                锚=末内容(快照,数据.get('turn'),True)
                锚序=锚.get('anchorSeq') if isinstance(锚,dict) else -1
                if 锚序 is None:
                    锚序=-1
                return 锚序>(终.get('seq') if 终.get('seq') is not None else 数据.get('seq'))

            def 选回复(快照):
                '最后一回合的最后一块是面对用户的回复'
                if not isinstance(快照,dict):
                    return False
                时间线=快照.get('timeline') if isinstance(快照.get('timeline'),dict) else {}
                序=时间线.get('turnOrder') if isinstance(时间线.get('turnOrder'),list) else []
                if len(序)==0 or 序[-1]!=数据.get('turn'):
                    return False
                最后=末内容(快照,数据.get('turn'),False)
                if not isinstance(最后,dict) or 最后.get('kind')!='assistant-step':
                    return False
                步数据=最后.get('data') if isinstance(最后.get('data'),dict) else {}
                块表=步数据.get('blocks') if isinstance(步数据.get('blocks'),list) else []
                块=None
                下标=len(块表)-1
                while 下标>=0:
                    候选=块表[下标]
                    if isinstance(候选,dict):
                        种=候选.get('kind')
                        文=候选.get('text') if isinstance(候选.get('text'),str) else ''
                        if 种 not in ('text','reasoning') or 文.strip()!='':
                            块=候选
                            break
                    下标-=1
                return 块 is not None and 有助手回复内容([块])

            更晚=聊天(选更晚) is True
            以回复结束=聊天(选回复) is True
        收束=数据.get('closing')
        属主={'turn':回合位,'seq':数据.get('seq'),'openFile':属性.get('openFile'),'window':窗口}
        if isinstance(收束,dict) and isinstance(收束.get('finalNode'),dict) and 收束['finalNode'].get('seq') is not None:
            属主['seq']=收束['finalNode']['seq']
        槽=属性.get('renderSlot')
        尾=槽('conversation.chat.turnTail',属主) if callable(槽) else None
        根=文档.createElement('div')
        根.className='root'
        标样式模块(根,样式模块)
        根.setAttribute('data-turn-tail',str(数据.get('turn')))
        if 收束 is None:
            if 尾 is None:
                return None
            挂节点(根,尾)
            自身.根=根
            if 属性.get('parent') is not None:
                属性['parent'].appendChild(根)
            return 根
        根.setAttribute('data-actions-reveal','always' if 以回复结束 else 'hover')
        挂节点(根,尾)
        消息号=None
        终节点=收束.get('finalNode') if isinstance(收束.get('finalNode'),dict) else {}
        if 终节点.get('messageId') is not None:
            消息号=终节点['messageId']
        助手动作=None
        if 消息号 is not None and callable(槽):
            助手动作=槽('conversation.chat.assistant-actions',{'messageId':消息号,'window':窗口})
        用量=None
        if 详细 and isinstance(数据.get('tokenUsage'),dict):
            用量=回合用量面板({'window':窗口,'usage':数据['tokenUsage'],'t':翻译})
        分叉=None
        if 允许分叉:
            def 去分叉():
                '用尾节点自己的序号切开'
                切=属性.get('forkAt')
                if callable(切):
                    切(数据.get('seq'))
            分叉=去分叉
        动作=消息图标动作({
            'window':窗口,
            'text':助手文本(收束.get('blocks')),
            'time':收束.get('time'),
            'clock':'end',
            'onBranch':分叉,
            'branchUnavailable':数据.get('branchUnavailable') is True or 更晚 is True,
            'className':'actions',
            'extraActions':助手动作,
            'usageAction':用量,
            't':翻译,
        })
        挂节点(根,动作.根)
        自身.根=根
        if 属性.get('parent') is not None:
            属性['parent'].appendChild(根)
        return 根
