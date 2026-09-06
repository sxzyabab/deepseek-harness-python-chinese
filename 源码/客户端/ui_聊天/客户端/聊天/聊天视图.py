"""Chat 视图：稳定键列表、分页、待定 steering、贴底与回合轨。

对齐上游 `ui-chat/src/client/chat/ChatView.tsx`。公开面仅中文名。
属性、快照、项为 dict。
"""
from .聊天节点席 import 聊天节点席#节点席
from .消息项 import 待插话泡#pending steering
from .消息铬 import 格式化运行时长#回合时钟
from .回合导航器 import 回合导航器#轨
from .回合轨条目 import 合并回合轨条目#合并
import time as 时间模块#墙钟

__all__=['聊天视图','跟随阈值','运行回合起始','回合状态']#仅中文公开名

跟随阈值=24#贴底阈值像素

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

def 空渲染槽(*位置参数,**关键字参数):
    """未注入槽渲染时不画。"""
    return None#不画

def 运行回合起始(时间线):
    """开着的回合 start.time。多开回合取最新。时间线为 dict。"""
    if 时间线 is None:#无
        return None#无
    回合表=时间线['turns'] if 'turns' in 时间线 else None#表
    if 回合表 is None:#无
        return None#无
    迭代=回合表.values()#dict 值
    最新=None#最新
    for 回合 in 迭代:#扫
        态=回合['status'] if 'status' in 回合 else None#态
        起=回合['start'] if 'start' in 回合 else None#起
        if 态=='open' and 起 is not None:#开
            最新=起['time'] if 'time' in 起 else None#时
    return 最新#最新

def 回合状态(起始时,翻译,现在=None):
    """满 15s 显示时钟。"""
    if 现在 is None:#缺省
        现在=int(时间模块.time()*1000)#毫秒
    锚=起始时 if 起始时 is not None else 现在#锚
    经过=max(0,现在-锚)#毫秒
    满=经过>=15000#满
    return {'type':'turn-status','label':翻译('chat.deepDiving'),'showClock':满,'clock':格式化运行时长(经过,翻译) if 满 is True else None,'cssModule':'聊天视图.module.css'}#态

def 取序(快照):
    """快照 order。"""
    序=快照['order'] if 'order' in 快照 else None#序
    return 序 if 序 is not None else []#空则空表

def 取时间线(快照):
    """快照 timeline。"""
    return 快照['timeline'] if 'timeline' in 快照 else None#线

def 取导航(快照):
    """已加载轨。"""
    项=快照['turnNavigation'] if 'turnNavigation' in 快照 else None#项
    return 项 if 项 is not None else []#空则空表

def 取运行(快照):
    """快照 running。"""
    return 快照['running'] if 'running' in 快照 else None#运行

def 取打开态(快照):
    """快照 openState。"""
    return 快照['openState'] if 'openState' in 快照 else None#打开

def 取打开错(快照):
    """快照 openError。"""
    return 快照['openError'] if 'openError' in 快照 else None#错

def 取还有更早(快照):
    """快照 hasMore。"""
    return 快照['hasMore'] if 'hasMore' in 快照 else None#更早

def 取加载更早中(快照):
    """快照 loadingOlder。"""
    return 快照['loadingOlder'] if 'loadingOlder' in 快照 else None#加载中

def 取选中调用(态):
    """selection.callId。态为 dict。"""
    选=态['selection'] if 'selection' in 态 else None#选
    return 选['callId'] if 选 is not None and 'callId' in 选 else None#callId

class 聊天视图:
    """有序 Node 列表 + 滚动语义面 + 回合轨。"""
    def __init__(自身,属性=None):
        """记下 props 与滚动态。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.贴底=True#跟随
        自身.活动回合=None#活动
        自身.忙回合=None#忙跳转
        自身.导航=回合导航器()#轨

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 滚到底(自身):
        """清锚并标记贴底。"""
        自身.贴底=True#贴
        滚=自身.属性['chatScroll'] if 'chatScroll' in 自身.属性 else None#滚
        存=滚['save'] if 滚 is not None and 'save' in 滚 else None#存
        if 存 is not None:#有
            存(None)#清记忆

    def 加载更早(自身):
        """调 loadOlder。"""
        加载=自身.属性['loadOlder'] if 'loadOlder' in 自身.属性 else None#加载
        if 加载 is not None:#有
            加载()#派发

    def 渲染(自身):
        """列表行 + 轨 + 状态 + steering。"""
        属性=自身.属性#props
        用聊天=属性['useChat'] if 'useChat' in 属性 else None#聊天快照
        用过程=属性['useChatNodeProcess'] if 'useChatNodeProcess' in 属性 else None#过程
        用节点=属性['useChatNode'] if 'useChatNode' in 属性 else None#节点
        if 用节点 is None and 用聊天 is not None:#钩缺席则自建
            def 按键读节点(键):
                """chat.nodes.get。仓库为契约 dict。"""
                def 取节点(快照):
                    """仓库 get。"""
                    仓=快照['nodes']#仓
                    return 仓['get'](键)#节点
                return 用聊天(取节点)#节点
            用节点=按键读节点#自建
        用存储=属性['useStore'] if 'useStore' in 属性 else None#仓
        渲染槽=属性['renderSlot'] if 'renderSlot' in 属性 else 空渲染槽#槽
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        待插=属性['pendingSteering'] if 'pendingSteering' in 属性 else None#待插
        def 取收件(快照):
            """queue，缺则 pendingSteering。空列表保留。"""
            if 'queue' in 快照 and 快照['queue'] is not None:#有队列
                return 快照['queue']#队列
            return 待插 if 待插 is not None else []#待插
        序=用聊天(取序) if 用聊天 is not None else []#序
        时间线=用聊天(取时间线) if 用聊天 is not None else None#时间线
        导航项=用聊天(取导航) if 用聊天 is not None else []#已加载轨
        大纲=属性['turnOutline'] if 'turnOutline' in 属性 else None#大纲投影
        收件=用聊天(取收件) if 用聊天 is not None else []#队列
        运行中=用聊天(取运行) if 用聊天 is not None else False#运行
        打开态=用聊天(取打开态) if 用聊天 is not None else 'cold'#打开
        打开错=用聊天(取打开错) if 用聊天 is not None else None#打开错
        还有更早=用聊天(取还有更早) if 用聊天 is not None else False#更早
        加载更早中=用聊天(取加载更早中) if 用聊天 is not None else False#加载中
        历史不全=属性['historyIncomplete'] is True if 'historyIncomplete' in 属性 else False#历史
        紧凑=属性['compactTranscript'] is True if 'compactTranscript' in 属性 else False#紧凑
        选中调用=用存储(取选中调用) if 用存储 is not None else None#选中
        轨项=合并回合轨条目(导航项,大纲)#合并轨
        席列表=[]#行
        动作=属性['actions'] if 'actions' in 属性 else None#动作
        工作目录=属性['cwd'] if 'cwd' in 属性 else None#cwd
        打开文件=属性['openFile'] if 'openFile' in 属性 else None#打开
        察调用=属性['inspectCall'] if 'inspectCall' in 属性 else None#察
        分叉=属性['forkAt'] if 'forkAt' in 属性 else None#分叉
        加载图=属性['loadImage'] if 'loadImage' in 属性 else None#图
        渲图=属性['renderMessageImages'] if 'renderMessageImages' in 属性 else None#渲图
        提及=属性['fileMentions'] if 'fileMentions' in 属性 else None#提及
        for 节点键 in 序:#逐键
            席=聊天节点席({'nodeKey':节点键,'useChatNode':用节点,'useChatNodeProcess':用过程,'historyIncomplete':历史不全,'compactTranscript':紧凑,'useStore':用存储,'actions':动作,'selectedCallId':选中调用,'cwd':工作目录,'openFile':打开文件,'inspectCall':察调用,'forkAt':分叉,'loadImage':加载图,'renderMessageImages':渲图,'fileMentions':提及,'renderSlot':渲染槽,'t':翻译})()#渲
            if 席 is not None:#席非空
                席列表.append(席)#入
        转向行=[]#steering
        for 项 in 收件:#扫
            位=项['placement'] if 'placement' in 项 else None#位
            种类=项['kind'] if 'kind' in 项 else None#种类
            if 位=='steering' or 种类=='steering':#插话
                内容=项['content'] if 'content' in 项 and 项['content'] is not None else []#内容
                标识=项['id'] if 'id' in 项 else None#id
                转向行.append({'id':标识,'view':待插话泡({'content':内容,'loadImage':加载图,'t':翻译})()})#行
        运行起始=运行回合起始(时间线)#起始
        def 导航到(项):
            """已加载滚锚，未加载翻页。"""
            跳=属性['onNavigateTurn'] if 'onNavigateTurn' in 属性 else None#跳
            if 跳 is not None:#有
                跳(项)#派
        错文=None#错文
        if 打开态=='error' and 打开错 is not None:#有错
            错消息=打开错['message'] if 'message' in 打开错 else None#消息
            错码=打开错['code'] if 'code' in 打开错 else None#码
            错文=翻译('chat.loadError',{'message':错消息,'code':错码})#错
        加载提示=翻译('chat.loadingHistory') if 打开态=='loading' else None#加载提示
        回合态=回合状态(运行起始,翻译) if 运行中 is True else None#回合态
        return {'type':'chat-view','openState':打开态,'loadingHint':加载提示,'openError':错文,'hasMore':还有更早,'loadingOlder':加载更早中,'loadOlderLabel':翻译('chat.loadOlder'),'onLoadOlder':自身.加载更早,'seats':席列表,'navigator':自身.导航({'items':轨项,'activeTurn':自身.活动回合,'busyTurn':自身.忙回合,'onNavigate':导航到,'t':翻译}),'turnStatus':回合态,'pendingSteering':转向行,'atBottom':自身.贴底,'toBottomLabel':翻译('chat.toBottom'),'onToBottom':自身.滚到底,'cssModule':'聊天视图.module.css'}#视图

    def __call__(自身,属性=None):
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
