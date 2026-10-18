from .....工具.值 import 断言永不
from .渲染条目 import 聊天渲染键
from .消息项 import 待插话泡,待提交泡
from .聊天组席 import 聊天组席
from .聊天节点席 import 聊天节点席
from .运行状态 import 运行状态

__all__=['聊天流程']


def 原样(值):
    '整份快照'
    return 值


class 聊天流程:
    '按条目画节点席和组席，后面接本地回显和运行状态'
    def __init__(自身,属性=None):
        '记下流属性'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.席表={}
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '节点和组共用一份席位表，避免每次把子树拆掉'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.setAttribute('data-chat-flow-host','')
        取聊天=属性.get('useChat')

        def 选节点存储(快照):
            '节点存储'
            if isinstance(快照,dict):
                return 快照.get('nodes')
            return None

        节点存储=取聊天(选节点存储) if callable(取聊天) else None
        在跑=False
        if callable(属性.get('useSession')):
            会话=属性['useSession'](原样)
            在跑=isinstance(会话,dict) and 会话.get('running') is True
        最新锚=None
        if callable(取聊天):
            def 选锚(快照):
                '导航最后一项的锚'
                if not isinstance(快照,dict):
                    return None
                导航=快照.get('navigation')
                项=导航.items() if hasattr(导航,'items') else []
                if len(项)==0 or not isinstance(项[-1],dict):
                    return None
                return 项[-1].get('anchorKey')
            最新锚=取聊天(选锚)
        起始=None
        if callable(属性.get('useChatNode')) and 最新锚 is not None:
            def 选起始(节点):
                '开着的回合起点'
                if not isinstance(节点,dict):
                    return None
                位置=节点.get('location')
                if not isinstance(位置,dict) or 位置.get('kind') not in ('turn','step'):
                    return None
                回合=位置.get('turn')
                if isinstance(回合,dict) and 回合.get('status')=='open' and isinstance(回合.get('start'),dict):
                    return 回合['start'].get('time')
                return None
            起始=属性['useChatNode'](最新锚,选起始)
        席属性={
            'window':窗口,
            'nodeStore':节点存储,
            'useChatNode':属性.get('useChatNode'),
            'useChatNodeBottom':属性.get('useChatNodeBottom'),
            'useChatNodeProcess':属性.get('useChatNodeProcess'),
            'usePresentation':属性.get('usePresentation'),
            'useStore':属性.get('useStore'),
            'actions':属性.get('actions'),
            'renderSlot':属性.get('renderSlot'),
            'renderFactorySlot':属性.get('renderFactorySlot'),
            't':属性.get('t'),
            'useGroupAction':属性.get('useGroupAction'),
            'useGroupHeaderAction':属性.get('useGroupHeaderAction'),
            'deferCollapse':属性.get('deferCollapse'),
            'cwd':属性.get('cwd'),
            'openFile':属性.get('openFile'),
            'inspectCall':属性.get('inspectCall'),
            'forkAt':属性.get('forkAt'),
            'loadImage':属性.get('loadImage'),
            'fileMentions':属性.get('fileMentions'),
            'useChat':取聊天,
            'useChatGroup':属性.get('useChatGroup'),
        }
        条目=属性.get('entries') or []
        行=[]
        仍在=set()
        for 项 in 条目:
            if not isinstance(项,dict):
                断言永不(项)
            键=聊天渲染键(项)
            仍在.add(键)
            if 项.get('kind')=='node':
                席项=dict(席属性)
                席项['nodeKey']=项.get('key')
                if 项.get('groupPart') is not None:
                    席项['groupPart']=项.get('groupPart')
                if 键 not in 自身.席表:
                    席项['parent']=自身.根
                    自身.席表[键]=聊天节点席(席项)
                else:
                    自身.席表[键].更新(席项)
                    自身.席表[键].渲染()
                行.append(自身.席表[键])
            elif 项.get('kind')=='group':
                席项=dict(席属性)
                席项['groupKey']=项.get('key')
                if 键 not in 自身.席表:
                    席项['parent']=自身.根
                    自身.席表[键]=聊天组席(席项)
                else:
                    自身.席表[键].更新(席项)
                    自身.席表[键].渲染()
                行.append(自身.席表[键])
            else:
                断言永不(项)
        待定行=[]
        for 待定 in 属性.get('pendingInputs') or []:
            if isinstance(待定,dict) and 'requestId' in 待定:
                泡=待提交泡({
                    'window':窗口,
                    'submission':待定,
                    'loadImage':属性.get('loadImage'),
                    'renderFactorySlot':属性.get('renderFactorySlot'),
                    't':属性.get('t'),
                })
            else:
                泡=待插话泡({
                    'window':窗口,
                    'content':待定.get('content') if isinstance(待定,dict) else None,
                    'loadImage':属性.get('loadImage'),
                    'renderFactorySlot':属性.get('renderFactorySlot'),
                    't':属性.get('t'),
                })
            待定行.append(泡)
        尾=条目[-1] if len(条目)>0 else None
        尾节点=None
        if isinstance(尾,dict) and 尾.get('kind')=='node' and hasattr(节点存储,'get'):
            尾节点=节点存储.get(尾.get('key'))
        if isinstance(尾节点,dict) and 尾节点.get('kind')=='turn-process':
            位置=尾节点.get('location') if isinstance(尾节点.get('location'),dict) else {}
            回合=位置.get('turn') if isinstance(位置.get('turn'),dict) else {}
            if 位置.get('kind')=='turn' and 回合.get('status')=='open' and 回合.get('turn')!=属性.get('lastInputTurn'):
                下标=0
                for 项 in 属性.get('pendingInputs') or []:
                    if isinstance(项,dict) and 'requestId' in 项 and 项.get('placement')=='transcript':
                        if 下标<len(待定行) and len(行)>0:
                            行.insert(len(行)-1,待定行.pop(下标))
                        break
                    下标+=1
        for 旧键 in list(自身.席表):
            if 旧键 not in 仍在:
                旧=自身.席表.pop(旧键)
                if getattr(旧,'根',None) is not None and 旧.根.parentNode is 自身.根:
                    旧.根.remove()
        while 自身.根.firstChild is not None:
            自身.根.removeChild(自身.根.firstChild)
        for 席 in 行:
            if getattr(席,'根',None) is not None:
                自身.根.appendChild(席.根)
        for 泡 in 待定行:
            if getattr(泡,'根',None) is not None:
                自身.根.appendChild(泡.根)
        if 在跑:
            状态=运行状态({'window':窗口,'startTime':起始,'t':属性.get('t')})
            if 状态.根 is not None:
                自身.根.appendChild(状态.根)
        if 属性.get('parent') is not None and 自身.根.parentNode is None:
            属性['parent'].appendChild(自身.根)
        return 自身.根
