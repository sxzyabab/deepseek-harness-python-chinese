'每个会话一份与目标无关的装配'
from .....依赖.cordis.服务 import 服务
from ....存储 import 创建快照存储
from .....工具.值 import 带值弱映射
from .事件注册表 import 会话事件注册表
from .视图注册表 import 会话视图注册表
from .组注册表 import 会话组注册表
from .用户文本注册表 import 用户文本注册表
from .组装器 import 会话节点组装器
from .既往图像 import 既往图像缓存
from ...异常 import 对话错误
from ..约定.快照 import 空会话快照

__all__=['界面会话']

class 绑定会话:
    '一份会话的快照、开着的回合和按目标的源'
    def __init__(自身,源,组装器):
        '先换成当前窗，再订阅后续变化'
        自身.组装器=组装器
        自身.视图存储=组装器
        自身.快照仓=创建快照存储(自身.当前快照())
        自身.回合仓=创建快照存储(组装器.openTurn())
        自身.目标源={}
        自身.修订=-1
        自身.帧=None
        自身.替换(源.getSnapshot())
        def 接受():
            '事件窗变了就收'
            自身.收下(源.getSnapshot())
        自身.拆源=源.subscribe(接受)

    @property
    def snapshot(自身):
        '可观察的会话快照'
        return 自身.快照仓

    @property
    def openTurn(自身):
        '开着的回合号'
        return 自身.回合仓

    def target(自身,目标):
        '第一次订阅时激活目标'
        已有=自身.目标源.get(目标)
        if 已有 is not None:
            return 已有
        def 取():
            '读这个目标的快照'
            return 自身.视图存储.get(目标)
        def 订(监听):
            '订阅整份快照，并激活目标'
            退=自身.快照仓.subscribe(监听)
            自身.activate(目标)
            return 退
        源={'getSnapshot':取,'subscribe':订}
        自身.目标源[目标]=源
        return 源

    def activate(自身,目标):
        '激活后发布快照和回合'
        if 自身.组装器.activateTarget(目标):
            自身.快照仓.set(自身.当前快照())
        自身.回合仓.set(自身.组装器.openTurn())

    def rebuild(自身):
        '注册表变了就重建'
        自身.发布(自身.组装器.rebuildRegistry())

    def dispose(自身):
        '拆掉帧和事件订阅'
        自身.取消帧()
        if 自身.拆源 is not None:
            自身.拆源()

    def 替换(自身,窗):
        '整窗替换'
        自身.修订=窗['revision']
        自身.发布(自身.组装器.replaceWindow(窗['entries'],窗['hasMore']))

    def 收下(自身,窗):
        '按变更种类追加、前置或结算'
        if 窗['revision']==自身.修订:
            return
        变更=窗['change']
        if 窗['revision']!=自身.修订+1 or 变更['kind']=='replace':
            自身.替换(窗)
            return
        自身.修订=窗['revision']
        种类=变更['kind']
        if 种类=='prepend':
            自身.发布(自身.组装器.prepend(变更['entries'],窗['hasMore']))
        elif 种类=='append':
            发布='none'
            for 事件 in 变更['entries']:
                下一=自身.组装器.append(事件)
                if 下一=='immediate' or 发布=='none':
                    发布=下一
            自身.发布(发布)
        elif 种类=='settle-assistant':
            自身.发布(自身.组装器.settleAssistant(变更['attemptId'],变更.get('entry')))

    def 发布(自身,节奏):
        '立即发布，或隔三帧再刷高频流'
        if 节奏=='none':
            return
        if 节奏=='animation-frame':
            try:
                请求=requestAnimationFrame
            except NameError:
                请求=None
            if callable(请求):
                if 自身.帧 is not None:
                    return
                def 第三():
                    '第三帧刷出'
                    自身.帧=None
                    自身.刷出()
                def 第二():
                    '第二帧'
                    自身.帧=请求(第三)
                def 第一():
                    '第一帧'
                    自身.帧=请求(第二)
                自身.帧=请求(第一)
                return
        自身.取消帧()
        自身.刷出()

    def 取消帧(自身):
        '丢掉还没到的帧'
        if 自身.帧 is not None:
            try:
                cancelAnimationFrame(自身.帧)
            except NameError:
                pass
        自身.帧=None

    def 刷出(自身):
        '组装器说有变化才换快照'
        if 自身.组装器.flush():
            自身.快照仓.set(自身.当前快照())
        自身.回合仓.set(自身.组装器.openTurn())

    def 当前快照(自身):
        '视图存储和活动目标'
        return {
            'views':自身.视图存储,
            'activeTargets':自身.组装器.activityTargets(),
        }

class 界面会话(服务):
    '根服务。登记表和每份会话的绑定都在这里'
    提供服务名='uiConversation'
    def __init__(自身,上下文,会话面):
        '建注册表、用户文本和图像缓存'
        super().__init__(上下文,'uiConversation')
        自身.sessions=会话面
        自身.events=会话事件注册表(上下文)
        自身.views=会话视图注册表(上下文)
        自身.groups=会话组注册表(上下文,自身.views)
        自身.userText=用户文本注册表(上下文)
        自身.图像=既往图像缓存(上下文,会话面)
        自身.绑定=带值弱映射()
        已排队=False
        def 重建():
            '每份绑定重建一次'
            for 记录 in 自身.绑定.values:
                记录['binding'].rebuild()
        def 安排():
            '合并到一个微任务'
            nonlocal 已排队
            if 已排队:
                return
            已排队=True
            def 跑():
                '微任务里重建'
                nonlocal 已排队
                已排队=False
                重建()
            try:
                queueMicrotask(跑)
            except NameError:
                跑()
        def 挂上():
            '三份注册表一起拆'
            拆事件=自身.events.subscribe(安排)
            拆视图=自身.views.subscribe(安排)
            拆组=自身.groups.subscribe(安排)
            def 拆():
                '拆订阅并丢掉绑定'
                拆组()
                拆视图()
                拆事件()
                for 记录 in list(自身.绑定.values):
                    自身.丢掉(记录,True)
            return 拆
        上下文.effect(挂上,'ui-conversation assembly')

    def binding(自身,源):
        '按绑定或会话标识取稳定的会话绑定'
        if isinstance(源,str):
            会话标识=源
            主人=自身.sessions.binding(源)
        else:
            会话标识=源.sessionId
            主人=源
        if 主人 is None:
            raise 对话错误('uiConversation.binding: unknown session "'+str(会话标识)+'"')
        if 自身.sessions.binding(会话标识) is not 主人:
            raise 对话错误('uiConversation.binding: inactive session "'+str(会话标识)+'"')
        当前=自身.绑定.get(主人)
        if 当前 is not None:
            return 当前['binding']
        绑定=绑定会话(主人.eventSource,会话节点组装器(自身.events,自身.views,自身.groups))
        记录={'source':主人,'binding':绑定,'disposeScope':lambda: None}
        自身.绑定.set(主人,记录)
        def 挂范围():
            '作用域结束时丢掉，但不重复拆作用域'
            def 拆():
                '丢掉这份记录'
                自身.丢掉(记录,False)
            return 拆
        拆除=主人.ctx.effect(挂范围,'ui-conversation binding')
        def 拆范围():
            '幂等'
            if callable(拆除):
                拆除()
        记录['disposeScope']=拆范围
        return 绑定

    def imageUrl(自身,会话标识,附件):
        '解析并缓存一张会话图片的地址'
        return 自身.图像.解析(会话标识,附件)

    def peekImageUrl(自身,会话标识,附件):
        '已经能显示的地址。不发起读取'
        return 自身.图像.窥视(会话标识,附件)

    def seedImageUrl(自身,会话标识,附件,地址):
        '先用现成预览，再去读耐久字节'
        return 自身.图像.播种(会话标识,附件,地址)

    def inspectSystemPrompt(自身,先前,事件):
        '系统消息或表面替换'
        from ..约定.系统提示 import 检视系统提示
        return 检视系统提示(先前,事件)

    def inspectRequestPrompt(自身,先前,事件,系统):
        '对照上一份提示和当前系统提示解释请求头'
        from ..约定.请求检视 import 检视请求提示
        return 检视请求提示(先前,事件,系统)

    def 丢掉(自身,记录,释放范围):
        '拆绑定。需要时再拆作用域 effect'
        if 自身.绑定.get(记录['source']) is not 记录:
            return
        自身.绑定.delete(记录['source']) if hasattr(自身.绑定,'delete') else 自身._删(记录)
        记录['binding'].dispose()
        if 释放范围:
            记录['disposeScope']()

    def _删(自身,记录):
        '弱映射没有 delete 时用内部表'
        if hasattr(自身.绑定,'delete'):
            自身.绑定.delete(记录['source'])
            return
        键表=自身.绑定._键表
        if 记录['source'] in 键表:
            旧=键表[记录['source']]
            del 键表[记录['source']]
            if 旧 in 自身.绑定._值集:
                自身.绑定._值集.remove(旧)
