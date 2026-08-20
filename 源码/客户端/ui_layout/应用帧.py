"""三栏壳帧：登记进内建 root 槽。

对齐上游 `ui-layout/src/client/AppFrame.tsx`。公开面仅中文名。
"""
from .列宽 import 计算列宽,侧栏自动折叠,侧栏默认#列宽求解

__all__=['应用帧','样式表']#仅中文公开名

样式表='''#对齐 AppFrame.module.css
.frame{position:relative;display:grid;grid-template-rows:100%;height:100%;overflow:hidden;background:var(--dsw-alias-bg-base);transition:grid-template-columns var(--ds-transition-duration-slow) var(--ds-ease-in-out)}
.frame[data-dragging]{transition:none}
.sidebarCol{min-width:0;overflow:hidden;background:var(--dsw-specific-sidebar-fill);border-right:1px solid var(--dsw-alias-border-l1)}
.centerCol{min-width:0;display:flex;flex-direction:column;overflow:hidden}
.detailsCol{min-width:0;overflow:hidden;border-left:1px solid var(--dsw-alias-border-l2)}
.frame[data-details-collapsed] .detailsCol{border-left:none}
.handle{position:absolute;top:0;bottom:0;width:8px;margin-left:-4px;cursor:col-resize;z-index:2;touch-action:none;transition:left var(--ds-transition-duration-slow) var(--ds-ease-in-out)}
.frame[data-dragging] .handle{transition:none}
.handle[data-side=details]::after{content:'';position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:12px;height:32px;border-radius:10px;box-sizing:border-box;background:var(--dsw-alias-button-floating-fill);border:1px solid var(--dsw-alias-border-l2-darkmode-thin);opacity:0}
.overlayLayer{position:absolute;inset:0;z-index:20;pointer-events:none}
.overlayLayer>*{pointer-events:auto}
'''#样式表结束

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 应用帧:#三栏壳帧组件
    """侧栏|中栏|详情；拖拽柄与让步链。"""
    def __init__(自身,属性):#按合成 props 构造
        """记下 props 与拖拽基线。"""
        自身.属性=属性#合成 props
        自身.视口=1024#帧宽
        自身.拖拽中=False#是否拖拽
        自身.侧栏基线=0#拖拽起点侧栏宽
        自身.详情基线=0#拖拽起点详情宽
        自身.上次详情会话=None#上次详情会话

    def 更新(自身,属性):#props 变更
        """刷新合成 props。"""
        自身.属性=属性#最新

    def 读面板(自身):#读布局 store 快照
        """经 useStore 选择器。"""
        用仓=取字段(自身.属性,'useStore')#选择器
        if 用仓 is None:#无
            return {'sidebar':侧栏默认,'details':0,'narrow':False,'narrowExpanded':False}#默认
        return 用仓(lambda 快照:快照) or {}#快照

    def 读详情会话(自身):#当前可开详情的会话
        """非 blank 的 current。"""
        用会话=取字段(自身.属性,'useSessions')#选择器
        if 用会话 is None:#无
            return None#无
        def 选(状态):#选详情会话
            """有非 blank 当前会话则返回 id。"""
            当前=取字段(状态,'current')#当前
            if 当前 is None:#无
                return None#无
            表=取字段(状态,'byId') or {}#表
            项=表.get(当前) if isinstance(表,dict) else 取字段(表,当前)#项
            if 取字段(项,'blank') is False:#非 blank
                return 当前#会话 id
            return None#无
        return 用会话(选)#选

    def 同步窄视口(自身,面板,动作):#窄视口断点
        """视口低于断点则 setNarrow。"""
        窄=自身.视口<侧栏自动折叠#断点
        设窄=取字段(动作,'setNarrow')#动作
        if 设窄 is not None:#有
            设窄(窄)#同步
        return 窄#是否窄

    def 侧栏拖开始(自身,列):#侧栏拖开始
        """冻结基线并标拖拽。"""
        自身.侧栏基线=列['sidebar']#基线
        自身.拖拽中=True#拖

    def 详情拖开始(自身,列):#详情拖开始
        """冻结基线并标拖拽。"""
        自身.详情基线=列['details']#基线
        自身.拖拽中=True#拖

    def 侧栏拖(自身,动作,位移):#侧栏拖动
        """基线+位移写入偏好。"""
        设=取字段(动作,'setSidebar')#动作
        if 设 is not None:#有
            设(自身.侧栏基线+位移)#写

    def 详情拖(自身,动作,位移):#详情拖动
        """基线-位移写入偏好。"""
        设=取字段(动作,'setDetails')#动作
        if 设 is not None:#有
            设(自身.详情基线-位移)#写

    def 拖结束(自身):#拖结束
        """清拖拽标志。"""
        自身.拖拽中=False#结束

    def 渲染(自身):#结构化视图
        """产出与上游 JSX 同构的结构化视图。"""
        动作=取字段(自身.属性,'actions') or {}#面板动作
        渲染槽=取字段(自身.属性,'renderSlot')#子槽渲染
        面板=自身.读面板()#面板
        详情会话=自身.读详情会话()#详情会话
        if 详情会话 is not None and 自身.上次详情会话 is not None and 自身.上次详情会话!=详情会话:#会话切换
            关=取字段(动作,'closeDetails')#关详情
            if 关 is not None:#有
                关()#关闭
        if 详情会话 is not None:#有会话
            自身.上次详情会话=详情会话#记下
        窄=自身.同步窄视口(面板,动作)#窄视口
        侧栏折叠= (not 取字段(面板,'narrowExpanded')) if 窄 else (取字段(面板,'sidebar')==0)#折叠判定
        侧栏偏好=0 if 侧栏折叠 else (侧栏默认 if 取字段(面板,'sidebar')==0 else 取字段(面板,'sidebar'))#偏好
        详情偏好=0 if 详情会话 is None else 取字段(面板,'details')#详情偏好
        列=计算列宽(自身.视口,侧栏偏好,详情偏好)#求解
        侧栏面=None#侧栏
        会话面=None#中栏
        详情面=None#详情
        叠层面=None#叠层
        if 渲染槽 is not None:#有渲染
            侧栏面=渲染槽('sidebar',{'collapsed':侧栏折叠,'width':列['sidebar']})#侧栏
            会话面=渲染槽('conversation',{})#会话
            详情面=渲染槽('details',{})#详情
            叠层面=渲染槽('shell.overlay',{})#叠层
        return {#结构化视图
            'type':'app-frame',#类型
            'gridTemplateColumns':f"{列['sidebar']}px minmax(0, 1fr) {列['details']}px",#栅格
            'sidebarCollapsed':侧栏折叠,#侧栏折叠
            'detailsCollapsed':列['details']==0,#详情折叠
            'dragging':自身.拖拽中,#拖拽中
            'sidebar':侧栏面,#侧栏子树
            'conversation':会话面,#中栏
            'details':详情面,#详情
            'overlay':叠层面,#叠层
            'sidebarHandle':None if 侧栏折叠 else {#侧栏柄
                'left':列['sidebar'],#左
                'onStart':lambda:自身.侧栏拖开始(列),#开始
                'onDrag':lambda 位移:自身.侧栏拖(动作,位移),#拖
                'onEnd':自身.拖结束,#结束
            },#柄结束
            'detailsHandle':None if 列['details']<=0 else {#详情柄
                'left':自身.视口-列['details'],#左
                'onStart':lambda:自身.详情拖开始(列),#开始
                'onDrag':lambda 位移:自身.详情拖(动作,位移),#拖
                'onEnd':自身.拖结束,#结束
            },#柄结束
            'css':样式表,#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
