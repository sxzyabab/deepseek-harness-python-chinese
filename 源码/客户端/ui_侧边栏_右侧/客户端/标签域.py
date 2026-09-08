"""标签域：布局记录之外的出现次——导航、寿命信号、自动作。

对齐上游 `ui-sidebar-right/src/client/tab-domain.ts`。公开面仅中文名。
AbortSignal 译为 threading.Event；快照仓就地实现。跨包值为 dict。
"""
import threading#中止旗
from ...ui_停靠套件.引擎 import 查找标签窗格#找窗

__all__=['标签域','快照仓']#仅中文公开名


class 快照仓:#本包自持快照源
    """getSnapshot / subscribe / set；对齐 createSnapshotStore。"""

    def __init__(自身,初值):
        """记下初值。"""
        自身._状态=初值#当前
        自身._监听=set()#订阅

    def getSnapshot(自身):
        """当前快照引用。"""
        return 自身._状态#快照

    def subscribe(自身,监听):
        """返回拆除器。"""
        自身._监听.add(监听)#登记
        def 拆除():
            """退订。"""
            自身._监听.discard(监听)#删
        return 拆除#拆除器

    def set(自身,次值):
        """写入并通知。"""
        自身._状态=次值#写
        for 监听 in list(自身._监听):#扇出
            监听()#回调


class 标签域:#每会话标签出现次
    """对照布局提交同步出现次；导航写入；卸载中止全部。"""

    def __init__(自身,导航器,钉住):
        """导航器为会话定向打开面；钉住为 resources.pin。"""
        自身.导航器=导航器#导航
        自身.钉住=钉住#钉资源
        自身.按会话={}#session → tabId → 持有

    def 同步(自身,会话标识,布局):
        """对照布局调和出现次。"""
        持有=自身._会话(会话标识)#本会话
        for 标签标识 in list(持有.keys()):#已持
            if 标签标识 not in 布局['tabs']:#已消失
                次=持有.pop(标签标识)#取出
                次['controller'].set()#中止（Event）
        for 签 in 布局['tabs'].values():#现有
            次=持有[签['id']] if 签['id'] in 持有 else 自身._持有(会话标识,签['id'],{'address':签['contentId'],'params':None,'revision':0})#出现
            窗=查找标签窗格(布局,签['id'])#窗
            次['paneId']=窗['id'] if 窗['host']=='dock' else None#停靠窗
            if 次['pinned']:#已钉
                continue#跳
            次['pinned']=True#钉
            自身.钉住(次['navigation'].getSnapshot()['address'],次['signal'])#钉资源

    def 出现(自身,会话标识,标签):
        """读已调和出现次 dict；无则抛。"""
        签标识=标签['id'] if isinstance(标签,dict) else 标签#兼容
        次=自身.按会话[会话标识][签标识] if 会话标识 in 自身.按会话 and 签标识 in 自身.按会话[会话标识] else None#次
        if 次 is None:#无
            raise Exception('sidebarRight: tab "'+str(签标识)+'" has no committed occurrence in session "'+str(会话标识)+'"')#拒绝
        return {#对外出现次（只读面）
            'sessionId':次['sessionId'],
            'tabId':次['tabId'],
            'signal':次['signal'],
            'navigation':次['navigation'],
            'tabActions':次['tabActions'],
        }#出现

    def 导航(自身,会话标识,标签标识,目标):
        """记录一次打开落点。"""
        持有=自身._会话(会话标识)#会话
        已有=持有[标签标识] if 标签标识 in 持有 else None#已有
        if 已有 is None:#新建
            自身._持有(会话标识,标签标识,{'address':目标['address'],'params':目标['params'],'revision':1})#持
            return#止
        旧=已有['navigation'].getSnapshot()#旧
        已有['navigation'].set({'address':目标['address'],'params':目标['params'],'revision':旧['revision']+1})#递修订

    def 拆除(自身):
        """卸载：中止全部。"""
        for 持有 in 自身.按会话.values():#会话
            for 次 in 持有.values():#次
                次['controller'].set()#中止
        自身.按会话.clear()#清空

    def _会话(自身,会话标识):
        """取或建会话桶。"""
        if 会话标识 not in 自身.按会话:#无
            自身.按会话[会话标识]={}#建
        return 自身.按会话[会话标识]#桶

    def _持有(自身,会话标识,标签标识,导航):
        """建出现次。"""
        控制器=threading.Event()#中止旗
        导航器=自身.导航器#导航

        def 落点(放置):
            """按出现次窗决定放置。"""
            出={}#放置
            if 放置.get('replaceTab') is True:#替本签
                出['replaceTab']=标签标识#替
            elif 次['paneId'] is not None:#落本窗
                出['paneId']=次['paneId']#窗
            if 'paneId' in 放置 and 放置['paneId'] is not None:#覆盖窗
                出['paneId']=放置['paneId']#窗
            if 'revealIfOpened' in 放置:#揭示
                出['revealIfOpened']=放置['revealIfOpened']#写
            return 出#放置

        def 开资源(地址,选项=None):
            """自本签开资源。"""
            选项=选项 if 选项 is not None else {}#默认
            参=选项['params'] if 'params' in 选项 else None#参
            导航器.在会话打开资源(会话标识,地址,{**落点(选项),'params':参})#开

        def 开标签(种类,选项=None):
            """自本签开页面。"""
            选项=选项 if 选项 is not None else {}#默认
            参=选项['params'] if 'params' in 选项 else None#参
            导航器.在会话打开标签(会话标识,种类,{**落点(选项),'params':参})#开

        def 关闭():
            """关本签。"""
            导航器.在会话关闭(会话标识,标签标识)#关

        次={#持有
            'sessionId':会话标识,
            'tabId':标签标识,
            'controller':控制器,
            'signal':控制器,#Event 即信号
            'navigation':快照仓(导航),
            'paneId':None,
            'pinned':False,
            'tabActions':{'openResource':开资源,'openTab':开标签,'close':关闭},
        }#持有
        自身._会话(会话标识)[标签标识]=次#登记
        return 次#次
