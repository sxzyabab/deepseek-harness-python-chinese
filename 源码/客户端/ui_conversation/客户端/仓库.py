"""会话与详情注册共享的每会话聊天仓库。

对齐上游 `ui-conversation/src/client/stores.ts`。公开面仅中文名。
插件在 apply 时创建句柄，使身份跟随 fiber。
"""
from .约定.视图 import 初始聊天状态#初值

__all__=['快照仓库','创建聊天仓库']#仅中文公开名

持久化键='dsh.conversation.chat'#持久化键

class 快照仓库:#简易引擎仓库句柄
    """状态 + 动作 + 订阅；对齐 defineStore。"""
    def __init__(自身,初值,动作,持久化=None):#播种
        """记下初值、动作面与可选持久化键。"""
        自身.状态=dict(初值)#状态副本
        自身.动作=动作#写入面
        自身.persist=持久化#持久化键
        自身.监听者=set()#订阅者

    def getSnapshot(自身):#读快照
        """返回当前状态引用。"""
        return 自身.状态#状态

    def subscribe(自身,回调):#订阅
        """登记变更回调。"""
        自身.监听者.add(回调)#加入
        def 退订():#退订
            """取消。"""
            自身.监听者.discard(回调)#删除
        return 退订#退订器

    def 通知(自身):#扇出
        """通知全部监听者。"""
        for 回调 in list(自身.监听者):#每个
            回调()#触发

    def select(自身,目标):#选定目标；None 清空
        """写入 selection。"""
        自身.动作['select'](自身.状态,目标)#动作
        自身.通知()#通知

    def setDraft(自身,文本):#写入草稿文本
        """写入 draft。"""
        自身.动作['setDraft'](自身.状态,文本)#动作
        自身.通知()#通知

    def setView(自身,视图):#切换视图名
        """写入 view。"""
        自身.动作['setView'](自身.状态,视图)#动作
        自身.通知()#通知

    def setInspect(自身,目标):#检视工具调用；None 关闭
        """写入 inspect。"""
        自身.动作['setInspect'](自身.状态,目标)#动作
        自身.通知()#通知

def 创建聊天仓库():#装配每会话聊天仓库
    """返回仓库句柄。"""
    def 选定(草稿,目标):#选定
        """写入 selection。"""
        草稿['selection']=目标#选定
    def 写草稿(草稿,文本):#草稿
        """写入 draft。"""
        草稿['draft']=文本#草稿
    def 写视图(草稿,视图):#视图
        """写入 view。"""
        草稿['view']=视图#视图
    def 写检视(草稿,目标):#检视
        """写入 inspect。"""
        草稿['inspect']=目标#检视
    return 快照仓库(初始聊天状态(),{#动作面
        'select':选定,'setDraft':写草稿,'setView':写视图,'setInspect':写检视,
    },持久化键)#仓库
