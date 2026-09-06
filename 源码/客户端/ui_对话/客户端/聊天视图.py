"""默认会话视图：稳定键列表、分页、待定 steering、贴底跟随。

对齐上游 `ui-conversation/src/client/chat/ChatView.tsx`。公开面仅中文名。
属性、快照、项为 dict。
"""
from .聊天节点席 import 聊天节点席#节点席
from .消息项 import 待插话泡#pending steering
from .消息铬 import 格式化运行时长#回合时钟
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
    最新=None#最新
    for 回合 in 回合表.values():#扫 dict 值
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
    return {#视图
        'type':'turn-status',#类型
        'label':'Deep diving...',#标签
        'showClock':满,#时钟
        'clock':格式化运行时长(经过,翻译) if 满 is True else None,#时长
        'cssModule':'聊天视图.module.css',#样式
    }#结束

def 取聊天序(快照):
    """chat.order。快照为 dict。"""
    聊天=快照['chat'] if 'chat' in 快照 else None#聊天
    序=聊天['order'] if 聊天 is not None and 'order' in 聊天 else None#序
    return 序 if 序 is not None else []#空则空表

def 取节点表(快照):
    """chat.nodes。"""
    聊天=快照['chat'] if 'chat' in 快照 else None#聊天
    return 聊天['nodes'] if 聊天 is not None and 'nodes' in 聊天 else None#表

def 取时间线(快照):
    """chat.timeline。"""
    聊天=快照['chat'] if 'chat' in 快照 else None#聊天
    return 聊天['timeline'] if 聊天 is not None and 'timeline' in 聊天 else None#线

def 取队列(快照):
    """queue。"""
    列=快照['queue'] if 'queue' in 快照 else None#队列
    return 列 if 列 is not None else []#空则空表

def 取运行(快照):
    """running。"""
    return 快照['running'] if 'running' in 快照 else False#运行

def 取打开态(快照):
    """openState。"""
    return 快照['openState'] if 'openState' in 快照 else 'cold'#打开

def 取打开错(快照):
    """openError。"""
    return 快照['openError'] if 'openError' in 快照 else None#错

def 取还有更早(快照):
    """hasMore。"""
    return 快照['hasMore'] if 'hasMore' in 快照 else False#更早

def 取加载更早中(快照):
    """loadingOlder。"""
    return 快照['loadingOlder'] if 'loadingOlder' in 快照 else False#加载中

def 取选中调用(态):
    """selection.callId。态为 dict。"""
    选=态['selection'] if 'selection' in 态 else None#选
    return 选['callId'] if 选 is not None and 'callId' in 选 else None#callId

class 聊天视图:#conversation.view chat 条目
    """有序 Node 列表 + 滚动语义面。"""
    def __init__(自身,属性=None):
        """记下 props 与滚动态。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.贴底=True#跟随
        自身.已打开=False#首开跳底
        自身.观测顶=0#程序写顶
        自身.分页锚=None#分页锚
        自身.首序号=None#首 seq
        自身.末键=None#末键
        自身.末转向标识=None#末 steering
        自身.跟随签名=None#跟随签名

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 滚到底(自身):
        """清锚并标记贴底。"""
        自身.分页锚=None#清
        自身.贴底=True#贴
        滚=自身.属性['chatScroll'] if 'chatScroll' in 自身.属性 else None#滚
        存=滚['save'] if 滚 is not None and 'save' in 滚 else None#存
        if 存 is not None:#有
            存(None)#清记忆

    def 加载更早锚定(自身):
        """记下当前可见锚后调 loadOlder。"""
        加载=自身.属性['loadOlder'] if 'loadOlder' in 自身.属性 else None#加载
        if 加载 is not None:#有
            加载()#派发

    def 渲染(自身):
        """列表行 + 状态 + steering + 回底钮。"""
        属性=自身.属性#props
        用会话=属性['useSession'] if 'useSession' in 属性 else None#会话
        取会话列表=属性['useSessions'] if 'useSessions' in 属性 else None#列表
        用存储=属性['useStore'] if 'useStore' in 属性 else None#仓
        渲染槽=属性['renderSlot'] if 'renderSlot' in 属性 else 空渲染槽#槽
        会话标识=属性['sessionId'] if 'sessionId' in 属性 else None#会话
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        序=用会话(取聊天序) if 用会话 is not None else []#序
        时间线=用会话(取时间线) if 用会话 is not None else None#时间线
        收件=用会话(取队列) if 用会话 is not None else []#队列
        运行中=用会话(取运行) if 用会话 is not None else False#运行
        打开态=用会话(取打开态) if 用会话 is not None else 'cold'#打开
        打开错=用会话(取打开错) if 用会话 is not None else None#打开错
        还有更早=用会话(取还有更早) if 用会话 is not None else False#更早
        加载更早中=用会话(取加载更早中) if 用会话 is not None else False#加载中
        工作目录=None#cwd
        if 取会话列表 is not None:#有列表
            def 取cwd(表):
                """byId[sessionId].cwd。表为 dict。"""
                册=表['byId'] if 'byId' in 表 else None#byId
                摘要=册[会话标识] if 册 is not None and 会话标识 in 册 else None#摘要
                return 摘要['cwd'] if 摘要 is not None and 'cwd' in 摘要 else None#cwd
            工作目录=取会话列表(取cwd)#cwd
        选中调用=用存储(取选中调用) if 用存储 is not None else None#选中
        待定转向=[]#steering
        for 项 in 收件:#扫
            if ('placement' in 项) and 项['placement']=='steering':#steering
                待定转向.append(项)#入
        运行起始=运行回合起始(时间线)#起始
        打开文件=属性['openFile'] if 'openFile' in 属性 else None#打开
        检视调用=属性['inspectCall'] if 'inspectCall' in 属性 else None#检视
        分叉=属性['forkAt'] if 'forkAt' in 属性 else None#分叉
        载图=属性['loadImage'] if 'loadImage' in 属性 else None#载图
        提及=属性['fileMentions'] if 'fileMentions' in 属性 else None#提及
        席列表=[]#行
        for 节点键 in 序:#逐键
            席=聊天节点席({#席 props
                'nodeKey':节点键,#键
                'useSession':用会话,#会话
                'selectedCallId':选中调用,#选中
                'cwd':工作目录,#cwd
                'openFile':打开文件,#打开
                'inspectCall':检视调用,#检视
                'forkAt':分叉,#分叉
                'loadImage':载图,#载图
                'fileMentions':提及,#提及
                'renderSlot':渲染槽,#槽
                't':翻译,#文案
            })()#渲
            if 席 is not None:#有
                席列表.append(席)#入
        转向行=[]#steering 行
        for 项 in 待定转向:#扫
            内容=项['content'] if 'content' in 项 and 项['content'] is not None else []#内容
            转向行.append({'id':项['id'] if 'id' in 项 else None,'view':待插话泡({'content':内容,'loadImage':载图,'t':翻译})()})#行
        打开错文=None#打开错
        if 打开态=='error' and 打开错 is not None:#有错
            打开错文=翻译('chat.loadError',{'message':打开错['message'] if 'message' in 打开错 else None,'code':打开错['code'] if 'code' in 打开错 else None})#文
        return {#视图
            'type':'chat-view',#类型
            'openState':打开态,#打开态
            'loadingHint':翻译('chat.loadingHistory') if 打开态=='loading' else None,#加载
            'openError':打开错文,#打开错
            'hasMore':还有更早,#更早
            'loadingOlder':加载更早中,#加载中
            'loadOlderLabel':翻译('loading') if 加载更早中 is True else 翻译('chat.loadOlder'),#分页标
            'onLoadOlder':自身.加载更早锚定,#分页
            'seats':席列表,#节点席
            'turnStatus':回合状态(运行起始,翻译) if 运行中 is True else None,#回合态
            'pendingSteering':转向行,#steering
            'atBottom':自身.贴底,#贴底
            'toBottomLabel':翻译('chat.toBottom'),#回底
            'onToBottom':自身.滚到底,#回底
            'cssModule':'聊天视图.module.css',#样式
        }#结束

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
