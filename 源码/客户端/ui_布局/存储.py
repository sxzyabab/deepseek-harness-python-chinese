from .列宽 import (#列宽约定
    夹紧宽度,侧栏默认,侧栏上限,侧栏下限,侧栏自动折叠,
    右侧栏默认比,右侧栏最大比,右侧栏下限,
)#列宽

__all__=['创建布局存储','初始布局状态','右侧栏默认比','右侧栏最大比','右侧栏下限']#仅中文公开名


def 初始布局状态():#冷启动快照
    """默认侧栏开；无全局面板；右侧栏未开。"""
    return {#初态
        'panelInfo':{'activePanelId':None},#无全局面板
        'layoutInfo':{#列几何
            'sidebar':侧栏默认,#左栏
            'viewportWidth':1280,#视口（无 window 时默认）
            'narrowExpanded':False,#窄覆盖
            'rightbar':None,#右侧偏好宽
            'rightbarShown':False,#是否画出
            'rightbarTrack':False,#是否占轨
            'rightbarFullscreen':False,#是否全屏
            'rightbarInstant':False,#瞬切
        },#列几何结束
    }#初态结束


def 创建布局存储():#创建布局面板存储句柄
    """返回状态与动作表；动作写草稿映射。"""
    状态=初始布局状态()#可变状态
    订阅列表=[]#监听表

    def 通知():#广播变更
        """通知全部订阅者。"""
        for 监听器 in list(订阅列表):#快照
            监听器()#回调

    def 选择面板(面板标识):#写入活动主面板
        """Null 回 Conversation。"""
        状态['panelInfo']['activePanelId']=面板标识#写
        通知()#广播

    def 保留主面板(面板标识列表):#主槽撤登记时清理
        """活动面板已不在登记表则回 Conversation。"""
        活动=状态['panelInfo']['activePanelId']#当前
        if 活动 is not None and 活动 not in 面板标识列表:#已撤
            状态['panelInfo']['activePanelId']=None#回 Conversation
            通知()#广播

    def 设侧栏(像素):#写入侧栏宽度
        """拖拽写入侧栏，夹进约定区间。"""
        几何=状态['layoutInfo']#列几何
        几何['rightbarInstant']=False#清瞬切
        几何['sidebar']=夹紧宽度(像素,侧栏下限,侧栏上限)#夹紧
        通知()#广播

    def 切换侧栏():#按窄/宽视口选语义
        """窄视口翻覆盖；宽视口 0 与默认互切。"""
        几何=状态['layoutInfo']#列几何
        几何['rightbarInstant']=False#清瞬切
        if 几何['viewportWidth']<侧栏自动折叠:#窄
            几何['narrowExpanded']=not 几何['narrowExpanded']#翻覆盖
        else:#宽
            几何['sidebar']=侧栏默认 if 几何['sidebar']==0 else 0#互切
        通知()#广播

    def 设视口宽(宽):#同步视口读数
        """越过断点丢掉窄覆盖。"""
        几何=状态['layoutInfo']#列几何
        if 几何['viewportWidth']==宽:#未变
            return#短路
        几何['rightbarInstant']=False#清
        旧窄=几何['viewportWidth']<侧栏自动折叠#旧
        新窄=宽<侧栏自动折叠#新
        if 旧窄!=新窄:#越断点
            几何['narrowExpanded']=False#清覆盖
        几何['viewportWidth']=宽#写
        通知()#广播

    def 设右侧栏(像素):#拖宽右侧栏
        """夹进当前视口允许区间。"""
        几何=状态['layoutInfo']#列几何
        几何['rightbarInstant']=False#清
        上限=max(右侧栏下限,几何['viewportWidth']*右侧栏最大比)#上限
        几何['rightbar']=夹紧宽度(像素,右侧栏下限,上限)#夹
        通知()#广播

    def 开右侧栏(要轨,全屏):#报告呈现
        """占用方报告：画出、轨、全屏。"""
        几何=状态['layoutInfo']#列几何
        if (not 几何['rightbarShown']) or 几何['rightbarTrack']!=要轨 or 几何['rightbarFullscreen']!=全屏:#变
            几何['rightbarInstant']=几何['rightbarFullscreen'] and not 全屏#瞬切
        if (not 几何['rightbarShown']) and 几何['viewportWidth']<侧栏自动折叠:#开时清窄覆盖
            几何['narrowExpanded']=False#清
        if 几何['rightbar'] is None:#首次
            几何['rightbar']=max(右侧栏下限,round(几何['viewportWidth']*右侧栏默认比))#默认宽
        几何['rightbarShown']=True#画
        几何['rightbarTrack']=要轨#轨
        几何['rightbarFullscreen']=全屏#全屏
        通知()#广播

    def 关右侧栏():#报告隐藏
        """无轨、无柄。"""
        几何=状态['layoutInfo']#列几何
        if 几何['rightbarShown']:#曾开
            几何['rightbarInstant']=几何['rightbarFullscreen']#瞬
        几何['rightbarShown']=False#隐
        几何['rightbarTrack']=False#无轨
        几何['rightbarFullscreen']=False#非全
        通知()#广播

    def 订阅(监听器):#订阅变更
        """返回拆除函数。"""
        订阅列表.append(监听器)#登记
        def 拆除订阅():#拆除
            """去掉监听。"""
            if 监听器 in 订阅列表:#仍在
                订阅列表.remove(监听器)#删
        return 拆除订阅#拆除器

    def 取快照():#读当前状态
        """返回状态浅拷贝。"""
        return {#拷贝
            'panelInfo':dict(状态['panelInfo']),#面板信息
            'layoutInfo':dict(状态['layoutInfo']),#列几何
        }#拷贝结束

    return {#存储句柄
        'getSnapshot':取快照,#快照
        'subscribe':订阅,#订阅
        'create':lambda: None,#由应用层换成共享实例
        'actions':{#绑定动作（线协议键）
            'selectPanel':选择面板,#主面板
            'retainMainPanels':保留主面板,#保留
            'setSidebar':设侧栏,#侧栏
            'toggleSidebar':切换侧栏,#切换侧栏
            'setViewportWidth':设视口宽,#视口
            'setRightbar':设右侧栏,#右栏宽
            'openRightbar':开右侧栏,#开右栏
            'closeRightbar':关右侧栏,#关右栏
        },#动作结束
    }#句柄结束
