import os
import pywebbridge
from ...ui_对话.异常 import 叫槽,挂上,清空子,注入模块样式文件,模块节点
from .列宽 import (
    中栏下限,
    侧栏折叠,
    侧栏默认,
    侧栏自动折叠,
    右侧栏下限,
    右侧栏最大比,
    右侧栏默认比,
    夹紧宽度,
    计算列宽,
)
from .文档标题 import 文档标题

__all__=['中列','右列','拖柄','主面板','应用帧','打开页面','本地页面']

样式模块='AppFrame'#样式隔离名
样式路径=os.path.join(os.path.dirname(__file__),'应用帧.module.css')#模块样式文件


def 写标记(节点,名,开):
    '开着写成 true，关着就摘掉。对齐 React 把 false 收成属性缺席'
    if 开 is True:
        节点.setAttribute(名,'true')
    else:
        节点.removeAttribute(名)


def 是页面对象(节点):
    '桥上的页面对象。缺属性会给出 undefined，不能用 hasattr 判断'
    模块=getattr(type(节点),'__module__','')
    return isinstance(模块,str) and 模块.startswith('pywebbridge')


def 取出界面(节点):
    '从槽位返回的树里找出已画出的界面。页面节点不是组件'
    if 节点 is None or 是页面对象(节点):
        return []
    if isinstance(节点,(str,int,float,bool,list,tuple)):
        return []
    if isinstance(节点,dict):
        if 节点.get('type')=='slot-list':
            结果=[]
            for 项 in 节点.get('items') or []:
                结果.extend(取出界面(项))
            return 结果
        for 键 in ('content','body','tree','children'):
            if 键 in 节点 and 节点[键] is not None:
                找到=取出界面(节点[键])
                if len(找到)>0:
                    return 找到
        return []
    try:
        属性=object.__getattribute__(节点,'属性')
        渲染=object.__getattribute__(节点,'渲染')
    except AttributeError:
        return []
    if isinstance(属性,dict) and callable(渲染):
        return [节点]
    return []


def 刷新界面(组件表,份额):
    '拥有方份额变了就写回那份属性，再让界面自己重画'
    for 组件 in 组件表:
        属性=组件.属性
        if isinstance(属性,dict):
            for 名,值 in 份额.items():
                属性[名]=值
        组件.渲染()


class 中列:
    '中列格子。主面板画在里面'
    def __init__(自身,属性):
        '记下窗口并画出格子'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def 渲染(自身):
        '格子只建一次'
        if 自身.根 is None:
            文档=自身.属性['window'].document
            自身.根=模块节点(文档,'div',样式模块,'centerCol')
        return 自身.根


class 右列:
    '右列格子。宽度可以为零，面板仍可以贴着右缘画出来'
    def __init__(自身,属性):
        '记下窗口并画出格子'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def 渲染(自身):
        '格子只建一次，并带上右列标记'
        if 自身.根 is None:
            文档=自身.属性['window'].document
            自身.根=模块节点(文档,'div',样式模块,'rightbarCol')
            自身.根.setAttribute('data-rightbar-col','')
        return 自身.根


class 拖柄:
    '一条拖柄。按下后捕获指针，位移合并到下一帧'
    def __init__(自身,属性):
        '记下哪一侧和回调，并画出柄'
        自身.属性=属性
        自身.拖拽中=False
        自身.起点=0
        自身.最近=0
        自身.帧号=None
        自身.捕获=None
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '刷新位置和回调'
        自身.属性=属性

    def 结束拖拽(自身):
        '放开捕获，清掉还没报出的帧，再通知结束'
        活动=自身.捕获
        if 活动 is None:
            return
        自身.捕获=None
        窗口=自身.属性['window']
        if 自身.帧号 is not None:
            窗口.cancelAnimationFrame(自身.帧号)
            自身.帧号=None
        元素=活动['element']
        if 元素.hasPointerCapture(活动['id']):
            元素.releasePointerCapture(活动['id'])
        自身.拖拽中=False
        自身.属性['onEnd']()

    def 指针按下(自身,事件):
        '主键才开始拖。已经抓着就不再抓'
        if 事件.button!=0 or 自身.捕获 is not None:
            return
        事件.preventDefault()
        元素=自身.根
        元素.setPointerCapture(事件.pointerId)
        自身.捕获={'element':元素,'id':事件.pointerId}
        自身.起点=事件.clientX
        自身.最近=事件.clientX
        自身.属性['onStart']()
        自身.拖拽中=True
        自身.渲染()

    def 到点(自身,时间=None):
        '这一帧把相对起点的位移交出去'
        自身.帧号=None
        自身.属性['onDrag'](自身.最近-自身.起点)

    def 指针移动(自身,事件):
        '只认当前这支指针，并把移动合并到下一帧'
        if 自身.捕获 is None or 自身.捕获['id']!=事件.pointerId:
            return
        自身.最近=事件.clientX
        if 自身.帧号 is None:
            自身.帧号=自身.属性['window'].requestAnimationFrame(自身.到点)

    def 指针抬起(自身,事件):
        '抬起时先交最后一点位移，再结束'
        if 自身.捕获 is None or 自身.捕获['id']!=事件.pointerId:
            return
        自身.属性['onDrag'](事件.clientX-自身.起点)
        自身.结束拖拽()

    def 指针取消(自身,事件):
        '取消或丢掉捕获时结束'
        if 自身.捕获 is not None and 自身.捕获['id']==事件.pointerId:
            自身.结束拖拽()

    def 渲染(自身):
        '柄只建一次。之后改水平位置和是否正在拖'
        属性=自身.属性
        文档=属性['window'].document
        if 自身.根 is None:
            自身.根=模块节点(文档,'div',样式模块,'handle')
            自身.根.addEventListener('pointerdown',自身.指针按下)
            自身.根.addEventListener('pointermove',自身.指针移动)
            自身.根.addEventListener('pointerup',自身.指针抬起)
            自身.根.addEventListener('pointercancel',自身.指针取消)
            自身.根.addEventListener('lostpointercapture',自身.指针取消)
        自身.根.setAttribute('data-side',属性['side'])
        自身.根.style.setProperty('left',str(属性['left'])+'px')
        写标记(自身.根,'data-dragging',自身.拖拽中 is True)
        return 自身.根

    def 拆除(自身):
        '先结束拖拽，再从帧上拿掉'
        自身.结束拖拽()
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None


class 主面板:
    '按活动面板键画 main。没有活动面板时用 conversation'
    def __init__(自身,属性):
        '记下钩子和中列，并画出当前那一格'
        自身.属性=属性
        自身.上次键=None
        自身.已订=False
        自身.渲染()

    def 渲染(自身):
        '键变了才换掉中列里的内容'
        属性=自身.属性
        def 取标识(信息):
            '当前主面板标识'
            return 信息['activePanelId']
        标识=属性['usePanelInfo'](取标识)
        if 标识 is None:
            键='conversation'
        else:
            键=标识
        if 自身.上次键!=键:
            清空子(属性['parent'])
            树=叫槽(属性['renderSlot'],'main',{},属性['window'],{'entryKey':键})
            挂上(属性['parent'],树)
            自身.上次键=键
        if 自身.已订 is not True:
            def 重画():
                '活动面板变了就换主区'
                自身.渲染()
            属性['usePanelInfo']._subscribe(重画)
            自身.已订=True
        return 属性['parent']


class 应用帧:
    '三列帧。侧栏、右栏和底栏都是槽位，不直接画别的包里的壳'

    def __init__(自身,属性):
        '记下 props。帧节点只留在这一份实例上，跟这一页的窗口走'
        自身.属性=属性
        自身.状态={
            '根':None,
            '侧栏列':None,
            '中列':None,
            '右列':None,
            '底行':None,
            '罩层':None,
            '前导':None,
            '左柄':None,
            '右柄':None,
            '标题':None,
            '主面板':None,
            '槽':{},
            '拖拽中':False,
            '侧栏基线':0,
            '右栏基线':0,
            '列':None,
            '正常右栏':0,
            '动画代':0,
            '上次开关':None,
            '上次视口':None,
            '落定计时':None,
            '过渡监听':None,
            '已观察':False,
            '已订':False,
            '观察帧':None,
            '已拆':False,
            '绘制中':False,
            '待重画':False,
        }
        自身.渲染()

    def 更新(自身,属性):
        '换一份 props'
        自身.属性=属性

    def 取窗口(自身):
        '只用调用方交给这一帧的窗口'
        return 自身.属性['window']

    def 侧栏拖开始(自身):
        '冻结当时画出的侧栏宽，避免跳回偏好值'
        自身.状态['侧栏基线']=自身.状态['列']['sidebar']
        自身.状态['拖拽中']=True
        自身.渲染()

    def 右栏拖开始(自身):
        '冻结当时算出的正常右栏宽'
        自身.状态['右栏基线']=自身.状态['正常右栏']
        自身.状态['拖拽中']=True
        自身.渲染()

    def 侧栏拖(自身,位移):
        '基线加上指针位移，写回侧栏偏好'
        自身.属性['actions']['setSidebar'](自身.状态['侧栏基线']+位移)

    def 右栏拖(自身,位移):
        '右缘反向，基线减去指针位移'
        自身.属性['actions']['setRightbar'](自身.状态['右栏基线']-位移)

    def 拖结束(自身):
        '这一笔拖完，列宽过渡可以恢复'
        自身.状态['拖拽中']=False
        自身.渲染()

    def 安排落定(自身):
        '列宽过渡结束，或 600 毫秒后，拿掉动画标记'
        状态=自身.状态
        代=状态['动画代']
        帧=状态['根']
        窗口=自身.取窗口()
        if 状态['落定计时'] is not None:
            窗口.clearTimeout(状态['落定计时'])
            状态['落定计时']=None
        if 状态['过渡监听'] is not None:
            帧.removeEventListener('transitionend',状态['过渡监听'])
            状态['过渡监听']=None

        def 落定():
            '只认这一代动画'
            if 状态['动画代']!=代:
                return
            状态['动画代']=0
            if 状态['落定计时'] is not None:
                窗口.clearTimeout(状态['落定计时'])
                状态['落定计时']=None
            if 状态['过渡监听'] is not None:
                帧.removeEventListener('transitionend',状态['过渡监听'])
                状态['过渡监听']=None
            自身.渲染()

        def 过渡结束(事件):
            '只认帧自己的列模板过渡'
            if 事件.target is 帧 and 事件.propertyName=='grid-template-columns':
                落定()

        状态['过渡监听']=过渡结束
        帧.addEventListener('transitionend',过渡结束)
        状态['落定计时']=窗口.setTimeout(落定,600)

    def 装观察(自身):
        '监听帧自己的盒子宽度，不用窗口宽度'
        状态=自身.状态
        if 状态['已观察'] is True:
            return
        状态['已观察']=True
        元素=状态['根']
        窗口=自身.取窗口()

        def 测量():
            '宽度大于零才写入'
            if 元素 is None:
                return
            宽=元素.getBoundingClientRect()['width']
            if isinstance(宽,(int,float)):#亚像素来回取整会再触发观察
                宽=int(宽+0.5)
            if 宽>0:
                自身.属性['actions']['setViewportWidth'](宽)

        def 冲刷(时间=None):
            '下一帧再量'
            状态['观察帧']=None
            if 状态['已拆'] is True:
                return
            测量()

        def 排队(*位置参数):
            '同一帧里的多次尺寸变化只量一次'
            if 状态['已拆'] is True or 状态['观察帧'] is not None:
                return
            状态['观察帧']=窗口.requestAnimationFrame(冲刷)

        测量()
        观察者=pywebbridge.new(窗口.ResizeObserver,排队)
        观察者.observe(元素)
        状态['观察者']=观察者

    def 确保槽(自身,键,父,份额,要刷新):
        '第一次画出槽位。份额会变的槽位之后写回已挂上的界面'
        记录=自身.状态['槽'].get(键)
        if 记录 is None:
            树=叫槽(自身.属性['renderSlot'],键,份额,自身.取窗口())
            挂上(父,树)
            自身.状态['槽'][键]={'组件':取出界面(树)}
            return
        if 要刷新 is True and len(记录['组件'])>0:
            刷新界面(记录['组件'],份额)

    def 同步柄(自身,键,要,属性):
        '需要时建柄，不需要时拆掉。还在就只改位置'
        状态=自身.状态
        柄=状态[键]
        if 要 is not True:
            if 柄 is not None:
                柄.拆除()
                状态[键]=None
            return
        if 柄 is None:
            柄=拖柄(属性)
            状态['根'].appendChild(柄.根)
            状态[键]=柄
            return
        柄.更新(属性)
        柄.渲染()

    def 渲染(自身):
        '按存储里的列几何画三列、底栏、罩层和拖柄'
        状态=自身.状态
        if 状态['绘制中'] is True:
            状态['待重画']=True
            return 状态['根']
        状态['绘制中']=True
        try:
            属性=自身.属性
            窗口=自身.取窗口()
            文档=窗口.document
            注入模块样式文件(文档,'应用帧样式',样式路径,样式模块)
            def 取布局信息(快照):
                '只要列几何'
                return 快照['layoutInfo']
            布局信息=属性['useStore'](取布局信息)
            if 布局信息['viewportWidth']<=0:#还没有量过，先用窗口宽度画第一帧
                属性['actions']['setViewportWidth'](窗口.innerWidth)
                布局信息=属性['useStore'](取布局信息)
            视口=布局信息['viewportWidth']
            窄=视口<侧栏自动折叠
            if 窄 is True:
                侧栏收起=not 布局信息['narrowExpanded']
            else:
                侧栏收起=布局信息['sidebar']==0
            if 侧栏收起 is True:
                侧栏偏好=0
            elif 布局信息['sidebar']==0:
                侧栏偏好=侧栏默认
            else:
                侧栏偏好=布局信息['sidebar']
            if 布局信息['rightbar'] is None:
                右偏好=视口*右侧栏默认比
            else:
                右偏好=布局信息['rightbar']
            根元素=文档.documentElement
            达尔文=根元素.getAttribute('data-platform')=='darwin'
            窗标题=根元素.hasAttribute('data-windows-titlebar')
            if 达尔文 is True or 窗标题 is True:
                折叠宽=0
            else:
                折叠宽=侧栏折叠
            if 布局信息['rightbarShown'] is not True and 窄 is True:
                左给正常=0
            else:
                左给正常=侧栏偏好
            正常=计算列宽(视口,左给正常,右偏好,折叠宽)
            if 布局信息['rightbarTrack'] is True:
                右给列=右偏好
            else:
                右给列=0
            列=计算列宽(视口,侧栏偏好,右给列,折叠宽)
            状态['列']=列
            状态['正常右栏']=正常['rightbar']
            if 列['rightbar']==0:
                右最大=0
                中最小=0
            else:
                右最大=夹紧宽度(右偏好,右侧栏下限,视口*右侧栏最大比)
                中最小=中栏下限
            根=状态['根']
            if 根 is None:
                根=模块节点(文档,'div',样式模块,'frame')
                状态['根']=根
                自身.根=根#渲染器按这个节点挂进槽位
            父=属性['parent'] if 'parent' in 属性 else None
            if 父 is not None and 根.parentNode is not 父:
                父.appendChild(根)
            模板=(
                str(列['sidebar'])+'px minmax('+str(中最小)+'px, 1fr) minmax(0px, '
                +str(右最大)+'px)'
            )
            根.style.setProperty('grid-template-columns',模板)
            if 窗标题 is True:
                根.style.setProperty('--dsh-windows-sidebar-width',str(列['sidebar'])+'px')
            else:
                根.style.removeProperty('--dsh-windows-sidebar-width')
            开关=str(侧栏收起 is True)+':'+str(布局信息['rightbarTrack'] is True)
            if 状态['上次开关'] is None:
                状态['上次开关']=开关
                状态['上次视口']=视口
            else:
                视口变了=状态['上次视口']!=视口
                状态['上次视口']=视口
                if 状态['上次开关']!=开关:
                    状态['上次开关']=开关
                    if 视口变了 is not True:
                        状态['动画代']=状态['动画代']+1
                        自身.安排落定()
            写标记(根,'data-sidebar-collapsed',侧栏收起 is True)
            写标记(根,'data-rightbar-collapsed',列['rightbar']==0)
            写标记(根,'data-rightbar-fullscreen',布局信息['rightbarFullscreen'] is True)
            写标记(根,'data-rightbar-instant',布局信息['rightbarInstant'] is True)
            写标记(根,'data-dragging',状态['拖拽中'] is True)
            写标记(根,'data-animating',状态['动画代']>0)
            if 状态['侧栏列'] is None:
                状态['侧栏列']=模块节点(文档,'div',样式模块,'sidebarCol')
                根.appendChild(状态['侧栏列'])
            if 状态['中列'] is None:
                状态['中列']=中列({'window':窗口})
                根.appendChild(状态['中列'].根)
            if 状态['右列'] is None:
                状态['右列']=右列({'window':窗口})
                根.appendChild(状态['右列'].根)
            if 状态['底行'] is None:
                状态['底行']=模块节点(文档,'div',样式模块,'bottomRow')
                状态['底行'].setAttribute('data-shell-bottom','')
                根.appendChild(状态['底行'])
            if 状态['罩层'] is None:
                状态['罩层']=模块节点(文档,'div',样式模块,'overlayLayer')
                状态['罩层'].setAttribute('data-shell-overlay','')
                根.appendChild(状态['罩层'])
            自身.确保槽('sidebar',状态['侧栏列'],{
                'collapsed':侧栏收起 is True,
                'width':列['sidebar'],
            },True)
            if 状态['主面板'] is None:
                状态['主面板']=主面板({
                    'window':窗口,
                    'parent':状态['中列'].根,
                    'usePanelInfo':属性['usePanelInfo'],
                    'renderSlot':属性['renderSlot'],
                })
            自身.确保槽('rightbar',状态['右列'].根,{
                'width':正常['rightbar'],
                'viewportWidth':视口,
                'canShow':正常['rightbar']>0,
            },True)
            自身.确保槽('shell.bottom',状态['底行'],{},False)
            自身.确保槽('shell.overlay',状态['罩层'],{},False)
            前导挂载=达尔文 is True and 侧栏收起 is True
            if 前导挂载 is True:
                if 状态['前导'] is None:
                    状态['前导']=模块节点(文档,'div',样式模块,'leadingSeat')
                    状态['前导'].setAttribute('data-shell-leading','')
                    根.appendChild(状态['前导'])
                自身.确保槽('shell.leading',状态['前导'],{},False)
            elif 状态['前导'] is not None:
                清空子(状态['前导'])
                状态['前导'].remove()
                状态['前导']=None
                状态['槽'].pop('shell.leading',None)
            自身.同步柄('左柄',侧栏收起 is not True,{
                'window':窗口,
                'side':'sidebar',
                'left':列['sidebar'],
                'onStart':自身.侧栏拖开始,
                'onDrag':自身.侧栏拖,
                'onEnd':自身.拖结束,
            })
            要右柄=(
                布局信息['rightbarShown'] is True
                and 布局信息['rightbarFullscreen'] is not True
                and 正常['rightbar']>0
            )
            自身.同步柄('右柄',要右柄,{
                'window':窗口,
                'side':'rightbar',
                'left':视口-正常['rightbar'],
                'onStart':自身.右栏拖开始,
                'onDrag':自身.右栏拖,
                'onEnd':自身.拖结束,
            })
            配置标题=os.environ.get('DSH_CLIENT_TITLE')
            if 配置标题 is None:
                产品='DSH 本地构建'
            else:
                产品=配置标题
            if 状态['标题'] is None:
                状态['标题']=文档标题({
                    'window':窗口,
                    'productTitle':产品,
                    'useSessions':属性['useSessions'],
                    'usePanelInfo':属性['usePanelInfo'],
                })
            else:
                状态['标题'].属性['productTitle']=产品
                状态['标题'].渲染()
            if 状态['已订'] is not True:
                def 重画():
                    '列几何变了就重画这一帧'
                    自身.渲染()
                属性['useStore']._subscribe(重画)
                状态['已订']=True
            自身.装观察()
            父=属性['parent'] if 'parent' in 属性 else None
            if 父 is not None and 根.parentNode is not 父:
                父.appendChild(根)
        finally:
            状态['绘制中']=False
        if 状态['待重画'] is True:
            状态['待重画']=False
            return 自身.渲染()
        return 状态['根']

    def __call__(自身,属性=None):
        '槽位再次调用时刷新'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()


def 本地页面():
    '本机网页要挂的帧类'
    return 应用帧


def 打开页面(窗口,页面):
    '把帧挂进这个窗口的文档。页面是本地页面给出的帧类'
    from .存储 import 创建布局存储
    from .服务 import 面板信息源
    from ...ui_渲染器.客户端.绑定选择器 import 绑定快照选择器
    句柄=创建布局存储()
    实例=句柄.create()

    class 空会话:
        '标题钩子要的会话表。这条入口还没有会话'
        def getSnapshot(自身):
            '没有会话'
            return {'byId':{}}

        def subscribe(自身,回调):
            '这份表不会变'
            def 退订():
                '没有订阅可退'
                return None
            return 退订

    def 空槽(名,属主,选项=None):
        '这条入口不经过槽位登记，子槽先留空'
        return None

    帧=页面({
        'window':窗口,
        'parent':窗口.document.body,
        'useStore':绑定快照选择器(实例),
        'actions':实例.actions,
        'usePanelInfo':绑定快照选择器(面板信息源(实例)),
        'useSessions':绑定快照选择器(空会话()),
        'renderSlot':空槽,
    })
    return 帧
