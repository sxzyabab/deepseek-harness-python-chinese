"""把固定 Escape 路由接到当前 Conversation 回合的作用域取消。
与停止按钮共用同一套 Session 取消；仅在会话 occurrence 内、非模态、非终端区域生效。
"""
from .停止序列 import 停止序列,停止目标#双击序列

__all__=['安装停止快捷键']#仅中文公开名

def 安装停止快捷键(快捷键,会话面,打开回合,会话界面,取消):
    """把固定输入订到与停止按钮相同的 Session 取消。
    快捷键含 stopSequenceMs 与 observeFixedInput；打开回合(绑定)→回合快照源；取消(会话标识)。
    返回释放输入订阅、挂起观察与过期定时器的拆除器。
    """
    def 空拆():
        """无可拆。"""
        return None#无事
    卸观察=空拆#当前第一下观察拆除
    def 释放观察():
        """卸掉第一下挂住的订阅。"""
        nonlocal 卸观察#写
        卸观察()#卸
        卸观察=空拆#空拆
    序列=停止序列(快捷键.stopSequenceMs,释放观察)#双击序列
    def 重置():
        """清序列与观察。"""
        序列.重置()#重置
    def 处理输入(输入):
        """固定输入扇出：reset 或合格 Escape。输入为 dict。"""
        nonlocal 卸观察#写
        if 输入['type']=='reset':#重置
            重置()#清
            return#止
        手势=输入['gesture']#手势
        上下文=输入['context']#上下文
        #修饰键、重复、合成、模态、终端或无目标：一律清序列
        if (手势['code']!='Escape' or 手势['repeat'] or 手势['composing'] or 手势['defaultPrevented']
            or 手势['control'] or 手势['alt'] or 手势['shift'] or 手势['meta']
            or 上下文['modal'] is not None or 上下文['region']=='terminal'
            or 上下文['target'] is None):#不合格
            重置()#清
            return#止
        目标节点=上下文['target']#事件目标
        出现=目标节点.closest('[data-conversation-session]')#会话 occurrence
        区域=目标节点.closest('[data-conversation-region]')#输入区域
        if (出现 is None or 区域 is None or not 出现.contains(区域)
            or 目标节点.closest('[data-approval-key], iframe, .xterm, [inert]') is not None):#越界
            重置()#清
            return#止
        会话标识=出现.dataset.conversationSession#会话 id
        绑定=会话面.binding(会话标识)#绑定
        if 绑定 is None:#无绑定
            重置()#清
            return#止
        回合源=打开回合(绑定)#当前回合源
        def 当前回合():
            """可取消则返回回合号，否则 None。"""
            会话=绑定.session.getSnapshot()#会话快照
            #未跑、已删、不可续子智能体、或有挂起交互时不可取消
            子代理=会话['subagent']#子代理
            状态=会话界面.sessionStatus.getSnapshot().get(会话标识)#本会话状态
            if (not 会话['running'] or 会话['removed']
                or (子代理 is not None and 子代理['address']['mode']!='continuable')
                or (状态 is not None and 'pendingInteraction' in 状态)):#不可取消
                return None#无回合
            return 回合源.getSnapshot()#活跃回合
        回合=当前回合()#当前
        if 回合 is None:#不可取消
            重置()#清
            return#止
        输入['consume']()#消费按键
        def 执行取消():
            """作用域停止。"""
            取消(会话标识)#取消
        已停=序列.按下(停止目标(会话标识,回合,绑定,区域,执行取消))#压序列
        if 已停:#第二下成对
            return#止
        #第一下未成对：盯绑定与回合变化，变则作废
        def 已变():
            """绑定或回合变则作废。"""
            if 会话面.binding(会话标识) is not 绑定 or 当前回合()!=回合:#变了
                重置()#清
        拆除表=[回合源.subscribe(已变),绑定.session.subscribe(已变),会话界面.sessionStatus.subscribe(已变)]#订阅
        def 卸():
            """卸三路订阅。"""
            for 拆 in 拆除表:#逐个
                拆()#拆
        卸观察=卸#挂住
    退订=快捷键.observeFixedInput(处理输入)#订固定输入
    def 拆除():
        """释放输入订阅与序列。"""
        退订()#退订
        重置()#清序列
    return 拆除#拆除器
