"""Chat 视图：稳定键列表、分页、待定 steering、贴底与回合轨。

对齐上游 `ui-chat/src/client/chat/ChatView.tsx`。公开面仅中文名。
"""
from .聊天节点席 import 聊天节点席#节点席
from .消息项 import 待插话泡#pending steering
from .消息铬 import 格式化运行时长#回合时钟
from .回合导航器 import 回合导航器#轨
from .回合轨条目 import 合并回合轨条目#合并
import time as 时间模块#墙钟

__all__=['聊天视图','跟随阈值','运行回合起始','回合状态']#仅中文公开名

跟随阈值=24#贴底阈值像素

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 运行回合起始(时间线):#开着的回合 start.time
    """多开回合取最新。"""
    if 时间线 is None:#无
        return None#无
    回合们=取字段(时间线,'turns')#表
    if 回合们 is None:#无
        return None#无
    值们=getattr(回合们,'values',None)#values
    迭代=值们() if callable(值们) else (回合们.values() if isinstance(回合们,dict) else [])#遍历
    最新=None#最新
    for 回合 in 迭代:#扫
        if 取字段(回合,'status')=='open' and 取字段(回合,'start') is not None:#开
            最新=取字段(取字段(回合,'start'),'time')#时
    return 最新#最新

def 回合状态(起始时,翻译,现在=None):#Deep diving 行
    """满 15s 显示时钟。"""
    if 现在 is None:#缺省
        现在=int(时间模块.time()*1000)#毫秒
    锚=起始时 if 起始时 is not None else 现在#锚
    经过=max(0,现在-锚)#毫秒
    return {'type':'turn-status','label':翻译('chat.deepDiving'),'showClock':经过>=15000,'clock':格式化运行时长(经过,翻译) if 经过>=15000 else None,'cssModule':'聊天视图.module.css'}#态

class 聊天视图:#conversation.view chat 条目
    """有序 Node 列表 + 滚动语义面 + 回合轨。"""

    def __init__(自身,属性=None):#构造
        """记下 props 与滚动态。"""
        自身.属性=属性 or {}#合成
        自身.贴底=True#跟随
        自身.活动回合=None#活动
        自身.忙回合=None#忙跳转
        自身.导航=回合导航器()#轨

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 滚到底(自身):#强制贴底
        """清锚并标记贴底。"""
        自身.贴底=True#贴
        存=取字段(取字段(自身.属性,'chatScroll'),'save')#存
        if callable(存):#有
            存(None)#清记忆

    def 加载更早(自身):#分页
        """调 loadOlder。"""
        加载=取字段(自身.属性,'loadOlder')#加载
        if callable(加载):#有
            加载()#派发

    def 渲染(自身):#结构树
        """列表行 + 轨 + 状态 + steering。"""
        属性=自身.属性#props
        用聊天=取字段(属性,'useChat')#聊天快照
        用过程=取字段(属性,'useChatNodeProcess')#过程
        用节点=取字段(属性,'useChatNode')#节点
        if 用节点 is None and callable(用聊天):#缺席则自建
            def 用节点(键):#按键读
                """chat.nodes.get。"""
                return 用聊天(lambda s:(取字段(取字段(s,'nodes'),'get')(键) if callable(取字段(取字段(s,'nodes'),'get')) else (取字段(s,'nodes') or {}).get(键)))#节点
        用仓=取字段(属性,'useStore')#仓
        渲染槽=取字段(属性,'renderSlot',lambda *_a,**_k:None)#槽
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        def 读(选,缺省=None):#安全读
            """钩缺席则缺省。"""
            if not callable(用聊天):#无
                return 缺省#缺
            return 用聊天(选)#投影
        序=读(lambda s:取字段(s,'order') or [],[])#序
        时间线=读(lambda s:取字段(s,'timeline'))#时间线
        导航项=读(lambda s:取字段(s,'turnNavigation') or [],[])#已加载轨
        大纲=取字段(属性,'turnOutline')#大纲投影
        收件=读(lambda s:取字段(s,'queue') or 取字段(属性,'pendingSteering') or [],[])#队列
        运行中=读(lambda s:取字段(s,'running'),False)#运行
        打开态=读(lambda s:取字段(s,'openState'),'cold')#打开
        打开错=读(lambda s:取字段(s,'openError'))#打开错
        还有更早=读(lambda s:取字段(s,'hasMore'),False)#更早
        加载更早中=读(lambda s:取字段(s,'loadingOlder'),False)#加载中
        历史不全=bool(取字段(属性,'historyIncomplete'))#历史
        紧凑=bool(取字段(属性,'compactTranscript'))#紧凑
        选中调用=用仓(lambda s:取字段(取字段(s,'selection'),'callId')) if callable(用仓) else None#选中
        轨项=合并回合轨条目(导航项,大纲)#合并轨
        席们=[]#行
        for 节点键 in 序:#逐键
            席=聊天节点席({'nodeKey':节点键,'useChatNode':用节点,'useChatNodeProcess':用过程,'historyIncomplete':历史不全,'compactTranscript':紧凑,'useStore':用仓,'actions':取字段(属性,'actions'),'selectedCallId':选中调用,'cwd':取字段(属性,'cwd'),'openFile':取字段(属性,'openFile'),'inspectCall':取字段(属性,'inspectCall'),'forkAt':取字段(属性,'forkAt'),'loadImage':取字段(属性,'loadImage'),'renderMessageImages':取字段(属性,'renderMessageImages'),'fileMentions':取字段(属性,'fileMentions'),'renderSlot':渲染槽,'t':翻译})()#渲
            if 席 is not None:#有
                席们.append(席)#入
        转向行=[]#steering
        for 项 in 收件:#扫
            if 取字段(项,'placement')=='steering' or 取字段(项,'kind')=='steering':#插话
                转向行.append({'id':取字段(项,'id'),'view':待插话泡({'content':取字段(项,'content') or [],'loadImage':取字段(属性,'loadImage'),'t':翻译})()})#行
        运行起始=运行回合起始(时间线)#起始
        def 导航到(项):#轨跳转
            """已加载滚锚，未加载翻页。"""
            跳=取字段(属性,'onNavigateTurn')#跳
            if callable(跳):#有
                跳(项)#派
        return {'type':'chat-view','openState':打开态,'loadingHint':翻译('chat.loadingHistory') if 打开态=='loading' else None,'openError':None if 打开态!='error' or 打开错 is None else 翻译('chat.loadError',{'message':取字段(打开错,'message'),'code':取字段(打开错,'code')}),'hasMore':还有更早,'loadingOlder':加载更早中,'loadOlderLabel':翻译('chat.loadOlder'),'onLoadOlder':自身.加载更早,'seats':席们,'navigator':自身.导航({'items':轨项,'activeTurn':自身.活动回合,'busyTurn':自身.忙回合,'onNavigate':导航到,'t':翻译}),'turnStatus':回合状态(运行起始,翻译) if 运行中 else None,'pendingSteering':转向行,'atBottom':自身.贴底,'toBottomLabel':翻译('chat.toBottom'),'onToBottom':自身.滚到底,'cssModule':'聊天视图.module.css'}#视图

    def __call__(自身,属性=None):#调用形
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
