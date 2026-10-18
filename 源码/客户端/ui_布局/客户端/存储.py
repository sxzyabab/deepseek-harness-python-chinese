from ...存储 import 声明存储
from .列宽 import (
    取整,
    夹紧宽度,
    侧栏下限,
    侧栏上限,
    侧栏默认,
    侧栏自动折叠,
    右侧栏下限,
    右侧栏最大比,
    右侧栏默认比,
)

__all__=['创建布局存储']


def 创建布局存储():
    '根上的列宽、主面板和右栏呈现。关侧栏会忘掉拖过的宽度，右栏第一次按帧宽的 45% 记下像素。视口宽由帧在绘制时用那一页的窗口写入'
    def 初态():
        '侧栏默认打开，没有全局面板，右栏还没开过'
        return {
            'panelInfo':{'activePanelId':None},
            'layoutInfo':{
                'sidebar':侧栏默认,
                'viewportWidth':0,
                'narrowExpanded':False,
                'rightbar':None,
                'rightbarShown':False,
                'rightbarTrack':False,
                'rightbarFullscreen':False,
                'rightbarInstant':False,
            },
        }

    def 选择面板(草稿,面板标识):
        '空标识回到对话，不改当前会话'
        草稿['panelInfo']['activePanelId']=面板标识

    def 保留主面板(草稿,面板标识表):
        '活动面板已经不在主槽里就回到对话'
        活动=草稿['panelInfo']['activePanelId']
        if 活动 is not None and 活动 not in 面板标识表:
            草稿['panelInfo']['activePanelId']=None

    def 设侧栏(草稿,像素):
        '拖拽写入夹紧后的侧栏宽'
        信息=草稿['layoutInfo']
        信息['rightbarInstant']=False
        信息['sidebar']=夹紧宽度(像素,侧栏下限,侧栏上限)

    def 切换侧栏(草稿):
        '窄屏只翻是否展开。宽屏在关掉和默认宽之间换，原先的偏好留着'
        信息=草稿['layoutInfo']
        信息['rightbarInstant']=False
        if 信息['viewportWidth']<侧栏自动折叠:
            信息['narrowExpanded']=not 信息['narrowExpanded']
        elif 信息['sidebar']==0:
            信息['sidebar']=侧栏默认
        else:
            信息['sidebar']=0

    def 设视口宽(草稿,宽度):
        '宽度没变就返回。跨过自动折叠断点时清掉窄屏覆盖'
        信息=草稿['layoutInfo']
        if 信息['viewportWidth']==宽度:
            return
        信息['rightbarInstant']=False
        原先窄=信息['viewportWidth']<侧栏自动折叠
        现在窄=宽度<侧栏自动折叠
        if 原先窄!=现在窄:
            信息['narrowExpanded']=False
        信息['viewportWidth']=宽度

    def 设右侧栏(草稿,像素):
        '按当前帧宽夹紧右栏偏好'
        信息=草稿['layoutInfo']
        信息['rightbarInstant']=False
        上限=信息['viewportWidth']*右侧栏最大比
        if 上限<右侧栏下限:
            上限=右侧栏下限
        信息['rightbar']=夹紧宽度(像素,右侧栏下限,上限)

    def 打开右侧栏(草稿,要轨,全屏):
        '记下右栏要不要轨道、是不是全屏。窄屏第一次打开时收起左栏覆盖'
        信息=草稿['layoutInfo']
        if (not 信息['rightbarShown'] or 信息['rightbarTrack']!=要轨
                or 信息['rightbarFullscreen']!=全屏):
            信息['rightbarInstant']=信息['rightbarFullscreen'] and not 全屏
        if not 信息['rightbarShown'] and 信息['viewportWidth']<侧栏自动折叠:
            信息['narrowExpanded']=False
        if 信息['rightbar'] is None:
            信息['rightbar']=max(右侧栏下限,取整(信息['viewportWidth']*右侧栏默认比))
        信息['rightbarShown']=True
        信息['rightbarTrack']=要轨
        信息['rightbarFullscreen']=全屏

    def 关闭右侧栏(草稿):
        '右栏藏起。从全屏藏起时记下瞬切，直到下一次几何动作'
        信息=草稿['layoutInfo']
        if 信息['rightbarShown']:
            信息['rightbarInstant']=信息['rightbarFullscreen']
        信息['rightbarShown']=False
        信息['rightbarTrack']=False
        信息['rightbarFullscreen']=False

    return 声明存储({
        'init':初态,
        'actions':{
            'selectPanel':选择面板,
            'retainMainPanels':保留主面板,
            'setSidebar':设侧栏,
            'toggleSidebar':切换侧栏,
            'setViewportWidth':设视口宽,
            'setRightbar':设右侧栏,
            'openRightbar':打开右侧栏,
            'closeRightbar':关闭右侧栏,
        },
    })
