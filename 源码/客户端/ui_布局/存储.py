"""根入口瞬时布局存储：面板几何是裸像素宽度。

对齐上游 `ui-layout/src/client/stores.ts`。公开面仅中文名。
右侧栏展开态由占用方报告；本存储只记轨与全屏呈现供帧摆放。
"""
from .列宽 import (#列宽约定
    夹紧宽度,详情默认,详情上限,详情下限,
    侧栏默认,侧栏上限,侧栏下限,侧栏自动折叠,
)#列宽

__all__=['创建布局存储','初始布局状态','右侧栏默认比','右侧栏最大比','右侧栏下限']#仅中文公开名

右侧栏默认比=0.45#首次打开占帧宽比
右侧栏最大比=0.6#拖宽上限相对视口
右侧栏下限=280#右侧栏拖拽下限


def 初始布局状态():#冷启动快照
    """默认侧栏开、详情关；右侧栏未开。"""
    return {#初态
        'sidebar':侧栏默认,#左栏
        'details':0,#详情
        'viewportWidth':1280,#视口（无 window 时默认）
        'narrow':False,#窄视口
        'narrowExpanded':False,#窄覆盖
        'rightbar':None,#右侧偏好宽
        'rightbarShown':False,#是否画出
        'rightbarTrack':False,#是否占轨
        'rightbarFullscreen':False,#是否全屏
        'rightbarInstant':False,#瞬切
    }#初态结束


def 创建布局存储():#创建布局面板存储句柄
    """返回状态与动作表；动作写草稿映射。"""
    状态=初始布局状态()#可变状态
    订阅列表=[]#监听表

    def 通知():#广播变更
        """通知全部订阅者。"""
        for 监听器 in list(订阅列表):#快照
            监听器()#回调

    def 设侧栏(像素):#写入侧栏宽度
        """拖拽写入侧栏，夹进约定区间。"""
        状态['rightbarInstant']=False#清瞬切
        状态['sidebar']=夹紧宽度(像素,侧栏下限,侧栏上限)#夹紧
        通知()#广播

    def 设详情(像素):#写入详情栏宽度
        """拖拽写入详情栏，夹进约定区间。"""
        状态['details']=夹紧宽度(像素,详情下限,详情上限)#夹紧
        通知()#广播

    def 切换侧栏():#按窄/宽视口选语义
        """窄视口翻覆盖；宽视口 0 与默认互切。"""
        状态['rightbarInstant']=False#清瞬切
        if 状态['viewportWidth']<侧栏自动折叠:#窄
            状态['narrowExpanded']=not 状态['narrowExpanded']#翻覆盖
        else:#宽
            状态['sidebar']=侧栏默认 if 状态['sidebar']==0 else 0#互切
        通知()#广播

    def 设视口宽(宽):#同步视口读数
        """越过断点丢掉窄覆盖。"""
        if 状态['viewportWidth']==宽:#未变
            return#短路
        状态['rightbarInstant']=False#清
        旧窄=状态['viewportWidth']<侧栏自动折叠#旧
        新窄=宽<侧栏自动折叠#新
        if 旧窄!=新窄:#越断点
            状态['narrowExpanded']=False#清覆盖
        状态['viewportWidth']=宽#写
        状态['narrow']=新窄#旗
        通知()#广播

    def 设窄视口(窄):#兼容旧面
        """越过断点丢掉手动覆盖。"""
        设视口宽(侧栏自动折叠-1 if 窄 else 侧栏自动折叠)#派生

    def 开详情():#打开详情栏
        """已关才写回约定默认。"""
        if 状态['details']==0:#已关
            状态['details']=详情默认#默认
            通知()#广播

    def 关详情():#关闭详情栏
        """忘掉拖拽宽度。"""
        状态['details']=0#关闭
        通知()#广播

    def 设右侧栏(像素):#拖宽右侧栏
        """夹进当前视口允许区间。"""
        状态['rightbarInstant']=False#清
        上限=max(右侧栏下限,状态['viewportWidth']*右侧栏最大比)#上限
        状态['rightbar']=夹紧宽度(像素,右侧栏下限,上限)#夹
        通知()#广播

    def 开右侧栏(要轨,全屏):#报告呈现
        """占用方报告：画出、轨、全屏。"""
        if (not 状态['rightbarShown']) or 状态['rightbarTrack']!=要轨 or 状态['rightbarFullscreen']!=全屏:#变
            状态['rightbarInstant']=状态['rightbarFullscreen'] and not 全屏#瞬切
        if (not 状态['rightbarShown']) and 状态['viewportWidth']<侧栏自动折叠:#开时清窄覆盖
            状态['narrowExpanded']=False#清
        if 状态['rightbar'] is None:#首次
            状态['rightbar']=max(右侧栏下限,round(状态['viewportWidth']*右侧栏默认比))#默认宽
        状态['rightbarShown']=True#画
        状态['rightbarTrack']=要轨#轨
        状态['rightbarFullscreen']=全屏#全屏
        通知()#广播

    def 关右侧栏():#报告隐藏
        """无轨、无柄。"""
        if 状态['rightbarShown']:#曾开
            状态['rightbarInstant']=状态['rightbarFullscreen']#瞬
        状态['rightbarShown']=False#隐
        状态['rightbarTrack']=False#无轨
        状态['rightbarFullscreen']=False#非全
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
        return dict(状态)#拷贝

    return {#存储句柄
        'getSnapshot':取快照,#快照
        'subscribe':订阅,#订阅
        'actions':{#绑定动作（线协议键）
            'setSidebar':设侧栏,#侧栏
            'setDetails':设详情,#详情
            'toggleSidebar':切换侧栏,#切换侧栏
            'setViewportWidth':设视口宽,#视口
            'setNarrow':设窄视口,#窄视口
            'openDetails':开详情,#开详情
            'closeDetails':关详情,#关详情
            'setRightbar':设右侧栏,#右栏宽
            'openRightbar':开右侧栏,#开右栏
            'closeRightbar':关右侧栏,#关右栏
        },#动作结束
    }#句柄结束
