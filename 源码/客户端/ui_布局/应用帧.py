import os#产品标题环境变量

from .列宽 import (#列宽求解
    计算列宽,右侧栏默认比,侧栏自动折叠,侧栏默认,
)#列宽
from .文档标题 import 文档标题#浏览器标题

__all__=['应用帧','主面板','样式表']#仅中文公开名

样式表='''#对齐 AppFrame.module.css（远程 rightbar 模型）
.frame{position:relative;display:grid;grid-template-rows:100%;height:100%;overflow:hidden;background:var(--dsw-alias-bg-base);transition:grid-template-columns var(--ds-transition-duration-slow) var(--ds-ease-in-out)}
.frame[data-dragging]{transition:none}
.sidebarCol{min-width:0;overflow:hidden;background:var(--dsw-specific-sidebar-fill);border-right:0.5px solid var(--dsw-alias-border-l3)}
.centerCol{min-width:0;display:flex;flex-direction:column;overflow:hidden}
.handle{position:absolute;top:0;bottom:0;width:8px;margin-left:-4px;cursor:col-resize;z-index:11;touch-action:none;transition:left var(--ds-transition-duration-slow) var(--ds-ease-in-out)}
.frame[data-dragging] .handle{transition:none}
.frame[data-rightbar-fullscreen],.frame[data-rightbar-fullscreen] .handle,.frame[data-rightbar-instant],.frame[data-rightbar-instant] .handle{transition:none}
.rightbarCol{position:relative;min-width:0;overflow:visible}
.overlayLayer{position:absolute;inset:0;z-index:20;pointer-events:none}
.overlayLayer>*{pointer-events:auto}
'''#样式表结束

def 取布局信息(快照):
    """选择 layoutInfo。"""
    return 快照['layoutInfo'] if 'layoutInfo' in 快照 else {}#列几何


class 主面板:#中列主槽投影
    """订阅活动面板键而不让列帧订阅每个面板 id。"""

    def __init__(自身,用面板信息,渲染槽):
        """记下钩与渲染。"""
        自身.用面板信息=用面板信息#usePanelInfo
        自身.渲染槽=渲染槽#renderSlot

    def 渲染(自身):
        """按活动面板键渲染 main；缺省 conversation。"""
        面板标识=None#活动面板
        if 自身.用面板信息 is not None:#有钩
            面板标识=自身.用面板信息(lambda 信息:信息['activePanelId'] if 'activePanelId' in 信息 else None)#活动
        键=面板标识 if 面板标识 is not None else 'conversation'#缺省 Conversation
        if 自身.渲染槽 is None:#无渲染
            return None#空
        return 自身.渲染槽('main',{},{'entryKey':键})#keyed 主槽


class 应用帧:#三栏壳帧组件
    """侧栏|中栏|右侧栏；拖拽柄与让步链。"""

    def __init__(自身,属性):
        """记下 props 与拖拽基线。"""
        自身.属性=属性 if 属性 is not None else {}#合成 props
        自身.拖拽中=False#是否拖拽
        自身.侧栏基线=0#拖拽起点侧栏宽
        自身.右侧栏基线=0#拖拽起点右栏宽
        自身._列=None#当前列宽（轨道）
        自身._正常右栏=0#正常几何右栏宽
        自身._动作=None#当前动作

    def 更新(自身,属性):
        """刷新合成 props。"""
        自身.属性=属性 if 属性 is not None else {}#最新

    def 读布局信息(自身):
        """经 useStore 取 layoutInfo。快照为 dict。"""
        用存储=自身.属性['useStore'] if 'useStore' in 自身.属性 else None#选择器
        if 用存储 is None:#无
            return {#默认列几何
                'sidebar':侧栏默认,
                'viewportWidth':1280,
                'narrowExpanded':False,
                'rightbar':None,
                'rightbarShown':False,
                'rightbarTrack':False,
                'rightbarFullscreen':False,
                'rightbarInstant':False,
            }#默认结束
        照=用存储(取布局信息)#快照
        return 照 if 照 is not None else {}#空则空表

    def 侧栏拖开始(自身):
        """冻结基线并标拖拽。"""
        列=自身._列#列
        自身.侧栏基线=列['sidebar'] if 列 is not None else 0#基线
        自身.拖拽中=True#拖

    def 右侧栏拖开始(自身):
        """冻结基线并标拖拽。"""
        自身.右侧栏基线=自身._正常右栏#基线取正常几何宽
        自身.拖拽中=True#拖

    def 侧栏拖(自身,位移):
        """基线+位移写入偏好。"""
        动作=自身._动作#动作
        设=动作['setSidebar'] if 动作 is not None and 'setSidebar' in 动作 else None#动作
        if 设 is not None:#有
            设(自身.侧栏基线+位移)#写

    def 右侧栏拖(自身,位移):
        """基线-位移写入偏好（反向）。"""
        动作=自身._动作#动作
        设=动作['setRightbar'] if 动作 is not None and 'setRightbar' in 动作 else None#动作
        if 设 is not None:#有
            设(自身.右侧栏基线-位移)#写

    def 拖结束(自身):
        """清拖拽标志。"""
        自身.拖拽中=False#结束

    def 渲染(自身):
        """产出与上游 JSX 同构的结构化视图。"""
        动作列=自身.属性['actions'] if 'actions' in 自身.属性 else None#面板动作
        动作=动作列 if 动作列 is not None else {}#空则空表
        自身._动作=动作#供拖回调
        渲染槽=自身.属性['renderSlot'] if 'renderSlot' in 自身.属性 else None#子槽渲染
        用面板=自身.属性['usePanelInfo'] if 'usePanelInfo' in 自身.属性 else None#面板钩
        用会话=自身.属性['useSessions'] if 'useSessions' in 自身.属性 else None#会话钩
        翻译=自身.属性['t'] if 't' in 自身.属性 else None#文案
        布局=自身.读布局信息()#列几何
        视口=布局['viewportWidth'] if 'viewportWidth' in 布局 else 1280#视口宽
        窄=视口<侧栏自动折叠#窄视口
        窄展=布局['narrowExpanded'] if 'narrowExpanded' in 布局 else False#窄覆盖
        侧栏宽=布局['sidebar'] if 'sidebar' in 布局 else 侧栏默认#侧栏偏好
        侧栏折叠=(窄展 is not True) if 窄 is True else (侧栏宽==0)#折叠判定
        侧栏偏好=0 if 侧栏折叠 is True else (侧栏默认 if 侧栏宽==0 else 侧栏宽)#偏好
        右栏存=布局['rightbar'] if 'rightbar' in 布局 else None#右栏偏好
        右栏偏好=视口*右侧栏默认比 if 右栏存 is None else 右栏存#默认比
        右栏已画=布局['rightbarShown'] is True if 'rightbarShown' in 布局 else False#是否画出
        右栏要轨=布局['rightbarTrack'] is True if 'rightbarTrack' in 布局 else False#是否占轨
        右栏全屏=布局['rightbarFullscreen'] is True if 'rightbarFullscreen' in 布局 else False#全屏
        右栏瞬切=布局['rightbarInstant'] is True if 'rightbarInstant' in 布局 else False#瞬切
        # 窄帧打开会折叠左栏：资格须在占用方首次 shown 报告前含那块空间
        正常侧栏=0 if (not 右栏已画) and 窄 else 侧栏偏好#正常几何侧栏
        正常=计算列宽(视口,正常侧栏,右栏偏好)#正常几何
        列=计算列宽(视口,侧栏偏好,右栏偏好 if 右栏要轨 else 0)#实际轨道
        自身._列=列#供拖回调
        自身._正常右栏=正常['rightbar']#右栏拖基线
        环境标题=os.environ['DSH_CLIENT_TITLE'] if 'DSH_CLIENT_TITLE' in os.environ else None#构建标题
        if 环境标题 is not None:#有构建
            产品标题=环境标题#用环境
        elif 翻译 is not None:#有文案
            产品标题=翻译('brand.localBuild')#本地构建
        else:#兜底
            产品标题=''#空
        侧栏面=None#侧栏
        主面=None#中栏
        右栏面=None#右侧栏
        叠层面=None#叠层
        标题面=文档标题({#文档标题
            'productTitle':产品标题,
            'useSessions':用会话,
            'usePanelInfo':用面板,
        })()#投影
        if 渲染槽 is not None:#有渲染
            侧栏面=渲染槽('sidebar',{'collapsed':侧栏折叠,'width':列['sidebar']})#侧栏
            主面=主面板(用面板,渲染槽).渲染()#keyed main
            右栏面=渲染槽('rightbar',{#右栏属主份额
                'width':正常['rightbar'],
                'viewportWidth':视口,
                'canShow':正常['rightbar']>0,
            })#右栏
            叠层面=渲染槽('shell.overlay',{})#叠层
        右栏柄=None#右栏柄
        if 右栏已画 and (not 右栏全屏) and 正常['rightbar']>0:#可拖
            右栏柄={#右栏柄
                'left':视口-正常['rightbar'],#左
                'onStart':自身.右侧栏拖开始,#开始
                'onDrag':自身.右侧栏拖,#拖
                'onEnd':自身.拖结束,#结束
            }#柄结束
        return {#结构化视图
            'type':'app-frame',#类型
            'gridTemplateColumns':str(列['sidebar'])+'px minmax(0, 1fr) '+str(列['rightbar'])+'px',#栅格
            'sidebarCollapsed':侧栏折叠,#侧栏折叠
            'rightbarCollapsed':列['rightbar']==0,#右栏折叠
            'rightbarFullscreen':右栏全屏,#全屏
            'rightbarInstant':右栏瞬切,#瞬切
            'dragging':自身.拖拽中,#拖拽中
            'documentTitle':标题面,#文档标题
            'sidebar':侧栏面,#侧栏子树
            'main':主面,#中栏 keyed
            'rightbar':右栏面,#右侧栏
            'overlay':叠层面,#叠层
            'sidebarHandle':None if 侧栏折叠 is True else {#侧栏柄
                'left':列['sidebar'],#左
                'onStart':自身.侧栏拖开始,#开始
                'onDrag':自身.侧栏拖,#拖
                'onEnd':自身.拖结束,#结束
            },#柄结束
            'rightbarHandle':右栏柄,#右栏柄
            'css':样式表,#样式
        }#视图结束

    def __call__(自身,属性=None):
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
