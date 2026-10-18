'把固定的 Escape 送进当前会话回合的取消'
from .停止序列 import 停止序列

__all__=['安装停止快捷键']

def 安装停止快捷键(快捷键,会话面,开着的回合,界面会话,取消):
    '两次独立的 Escape 才取消。中间状态变了就作废'
    拆观察=lambda: None
    def 释放():
        '清掉第一次按键还握着的订阅'
        nonlocal 拆观察
        拆观察()
        拆观察=lambda: None
    序列=停止序列(快捷键.stopSequenceMs,释放)
    def 重置():
        '放弃第一次按键'
        序列.重置()
    def 收到(输入):
        '只接受会话区域里、没有修饰键的 Escape'
        if 输入.get('type')=='reset':
            重置()
            return
        手势=输入['gesture']
        情境=输入['context']
        if 手势['code']!='Escape' or 手势.get('repeat') or 手势.get('composing') or 手势.get('defaultPrevented') or 手势.get('control') or 手势.get('alt') or 手势.get('shift') or 手势.get('meta') or 情境.get('modal') is not None or 情境.get('region')=='terminal' or 情境.get('target') is None:
            重置()
            return
        目标=情境['target']
        出现=目标.closest('[data-conversation-session]')
        区域=目标.closest('[data-conversation-region]')
        if 出现 is None or 区域 is None or not 出现.contains(区域) or 目标.closest('[data-approval-key], iframe, .xterm, [inert]') is not None:
            重置()
            return
        会话标识=出现.dataset.conversationSession
        绑定=会话面.binding(会话标识)
        if 绑定 is None:
            重置()
            return
        回合源=开着的回合(绑定)
        def 当前回合():
            '运行中、可继续、且没有待定交互才算活回合'
            会话=绑定.session.getSnapshot()
            子=会话.get('subagent')
            待定=界面会话.sessionStatus.getSnapshot().get(会话标识)
            if (not 会话.get('running')) or 会话.get('removed') or (isinstance(子,dict) and 子.get('address',{}).get('mode')!='continuable') or (isinstance(待定,dict) and 待定.get('pendingInteraction') is not None):
                return None
            return 回合源.getSnapshot()
        回合=当前回合()
        if 回合 is None:
            重置()
            return
        输入['consume']()
        def 执行取消():
            '取消这个会话'
            取消(会话标识)
        停了=序列.按下({
            'sessionId':会话标识,
            'turn':回合,
            'generation':绑定,
            'region':区域,
            'cancel':执行取消,
        })
        if 停了:
            return
        def 变了():
            '绑定或回合变了就作废第一次'
            if 会话面.binding(会话标识) is not 绑定 or 当前回合()!=回合:
                重置()
        拆除=[回合源.subscribe(变了),绑定.session.subscribe(变了),界面会话.sessionStatus.subscribe(变了)]
        def 拆():
            '拆掉这三份'
            for 项 in 拆除:
                项()
        拆观察=拆
    关掉=快捷键.observeFixedInput(收到)
    def 拆全部():
        '拆输入订阅并重置序列'
        关掉()
        重置()
    return 拆全部
