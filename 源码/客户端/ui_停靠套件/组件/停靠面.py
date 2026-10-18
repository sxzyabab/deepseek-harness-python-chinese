'停靠表面。手势过程只预览，松手才通过一条意图离开'
import pywebbridge
from ..引擎.约束 import 钳制尺寸,浮动默认尺寸,最小窗格份额
from ..引擎.树 import 取分割,右上窗格标识
from ..引擎.几何 import 含点,分割条尺寸,落点浮动矩形,插入下标,已过阈值,矩形区位
from .测量 import 取可放,量测窗格可放,可放相同,窗格元素,矩形自
from .指针 import 使用手势
from .窗格树 import 窗格树
from .标签布局 import 标签布局
from .渲染 import 清空,注入样式,调意图,始终

__all__=['停靠面','停靠布局']

份额容差=1e-9

def 命中(根,横,纵,能分,可放,投放模式):
    '指针在停靠面里的落点。边带只有这次切开被允许时才给出'
    for 窗格标识,窗格 in 窗格元素(根):
        矩=矩形自(窗格)
        if not 含点(矩,横,纵):
            continue
        条=窗格.querySelector('[data-dockkit-strip]')
        if 条 is not None and 含点(矩形自(条),横,纵):
            芯片矩=[]
            for 芯片 in 条.querySelectorAll('[data-dockkit-tab]'):
                芯片矩.append(矩形自(芯片))
            return {'kind':'strip','paneId':窗格标识,'index':插入下标(芯片矩,横)}
        if 投放模式=='horizontal':
            if 能分 and 取可放(可放,窗格标识)['row']:
                if 横<矩['x']+矩['width']/2:
                    区='left'
                else:
                    区='right'
            else:
                区='center'
        else:
            区=矩形区位(矩,横,纵)
        if 区!='center':
            读数=取可放(可放,窗格标识)
            if 区=='left' or 区=='right':
                够=读数['row']
            else:
                够=读数['column']
            if not 能分 or not 够:
                return None
        return {'kind':'zone','paneId':窗格标识,'zone':区}
    return None

def 拖后份额(拖,横,纵,下限):
    '分割条拖到现在的钳制份额'
    if 拖['axis']=='row':
        移动=横-拖['origin']
    else:
        移动=纵-拖['origin']
    if 拖['extent']>0:
        增量=移动/拖['extent']
    else:
        增量=0
    return 钳制尺寸(分割条尺寸(拖['sizes'],拖['index'],增量),下限)

class 表面:
    '分割树或标签布局外面的那一层，拥有拖拽和房间测量'
    def __init__(自身,属性,绘制):
        '挂上表面并画出里面'
        自身.属性=属性
        自身.绘制=绘制
        自身.根=None
        自身.子=None
        自身.手势=None
        自身.观察=None
        自身.可放={}
        自身.预览={'draggingTabId':None,'dropTarget':None,'sizes':None}
        自身.渲染()

    def 清预览(自身):
        '手势结束，预览回到没有'
        自身.预览={'draggingTabId':None,'dropTarget':None,'sizes':None}
        自身.套预览()

    def 能加(自身):
        '嵌入方没给时，每格都能加'
        给=自身.属性.get('canAddTab')
        if 给 is None:
            return 始终
        return 给

    def 能关(自身):
        '嵌入方没给时，每张都能关'
        给=自身.属性.get('canCloseTab')
        if 给 is None:
            return 始终
        return 给

    def 投放模式(自身):
        '没写时按四边'
        if 'dropZones' in 自身.属性 and 自身.属性['dropZones'] is not None:
            return 自身.属性['dropZones']
        return 'edges'

    def 下限(自身):
        '没写时用套件自己的窗格份额'
        if 'minPaneFraction' in 自身.属性 and 自身.属性['minPaneFraction'] is not None:
            return 自身.属性['minPaneFraction']
        return 最小窗格份额

    def 分割阻断(自身,窗格标识):
        '先看窗格额度，再看这一格自己的宽度'
        if not 自身.属性['canSplit']:
            return 'budget'
        if 取可放(自身.可放,窗格标识)['row']:
            return None
        return 'width'

    def 组回调(自身):
        '交给里面的树和条带'
        意图=自身.属性['intents']
        状态=自身.属性['state']
        def 聚焦标签(标识):
            '聚焦这张标签'
            调意图(意图,'focusTab',标识)
        def 聚焦窗格(标识):
            '聚焦这块窗格'
            调意图(意图,'focusPane',标识)
        def 切开(标识):
            '切开这块窗格'
            调意图(意图,'splitPane',标识)
        def 加一张(标识):
            '在条带末尾加标签'
            调意图(意图,'addTab',标识)
        def 关掉(标识):
            '关掉这张标签'
            调意图(意图,'closeTab',标识)
        return {
            'onFocusTab':聚焦标签,
            'onFocusPane':聚焦窗格,
            'onSplitPane':切开,
            'onAddTab':加一张,
            'onCloseTab':关掉,
            'onTabPressed':自身.按标签,
            'onDividerPressed':自身.按分割条,
            'splitBlock':自身.分割阻断,
            'hideSplitWhenBlocked':自身.属性.get('hideSplitWhenBlocked') is True,
            'canAddTab':自身.能加(),
            'canCloseTab':自身.能关(),
            'dropTarget':自身.预览['dropTarget'],
            'horizontalDrops':自身.投放模式()=='horizontal',
            'draggingTabId':自身.预览['draggingTabId'],
            'labels':自身.属性['labels'],
            'renderTab':自身.属性['renderTab'],
            'renderTabTitle':自身.属性.get('renderTabTitle'),
            'renderTabMenuItems':自身.属性.get('renderTabMenuItems'),
            'chromePaneId':右上窗格标识(状态),
            'chrome':自身.属性.get('chrome'),
        }

    def 按标签(自身,标签标识,事件):
        '按下还不是拖。走过阈值才抬起芯片并跟落点'
        if 自身.根 is None:
            return
        根=自身.根
        起横=事件.clientX
        起纵=事件.clientY
        拖着={'值':False}
        能分=自身.属性['canSplit']
        模式=自身.投放模式()

        def 移动(挪到):
            '过了阈值才算在拖'
            if not 拖着['值']:
                if not 已过阈值(起横,起纵,挪到.clientX,挪到.clientY):
                    return
                拖着['值']=True
            自身.预览={
                'draggingTabId':标签标识,
                'dropTarget':命中(根,挪到.clientX,挪到.clientY,能分,自身.可放,模式),
                'sizes':None,
            }
            自身.套预览()

        def 松开(放开):
            '没拖就什么都不报。拖出表面才浮出，落在空白上不算移动'
            if not 拖着['值']:
                return
            目标=命中(根,放开.clientX,放开.clientY,能分,自身.可放,模式)
            if 目标 is None:
                if 含点(矩形自(根),放开.clientX,放开.clientY):
                    return
                调意图(
                    自身.属性['intents'],
                    'floatTab',
                    标签标识,
                    落点浮动矩形(放开.clientX,放开.clientY,浮动默认尺寸),
                )
                return
            if 目标['kind']=='strip':
                调意图(自身.属性['intents'],'placeTab',标签标识,目标['paneId'],目标['index'])
            else:
                调意图(自身.属性['intents'],'dropTab',标签标识,目标['paneId'],目标['zone'])

        自身.手势['开始'](事件.currentTarget,事件.pointerId,{'move':移动,'up':松开})

    def 按分割条(自身,分割标识,下标,事件):
        '分割条按下。松手时份额没变就不记'
        容器=事件.currentTarget.parentElement
        if 容器 is None:
            return
        分割=取分割(自身.属性['state'],分割标识)
        盒=矩形自(容器)
        if 分割['axis']=='row':
            起点=事件.clientX
            跨度=盒['width']
        else:
            起点=事件.clientY
            跨度=盒['height']
        拖={
            'splitId':分割标识,
            'index':下标,
            'axis':分割['axis'],
            'origin':起点,
            'extent':跨度,
            'sizes':分割['sizes'],
        }
        下限=自身.下限()

        def 移动(挪到):
            '预览这份份额'
            自身.预览={
                'draggingTabId':None,
                'dropTarget':None,
                'sizes':{'splitId':分割标识,'sizes':拖后份额(拖,挪到.clientX,挪到.clientY,下限)},
            }
            自身.套预览()

        def 松开(放开):
            '和按下时一样就不是缩放'
            份额=拖后份额(拖,放开.clientX,放开.clientY,下限)
            原来=拖['sizes']
            if len(份额)==len(原来):
                相同=True
                for 序号,大小 in enumerate(份额):
                    另=原来[序号]
                    if abs(大小-另)>=份额容差:
                        相同=False
                if 相同:
                    return
            调意图(自身.属性['intents'],'resizeSplit',分割标识,份额)

        自身.手势['开始'](事件.currentTarget,事件.pointerId,{'move':移动,'up':松开})

    def 画子(自身):
        '用现在的回调和预览画里面'
        清空(自身.根)
        if 自身.子 is not None and hasattr(自身.子,'拆除'):
            自身.子.拆除()
        自身.子=自身.绘制(自身.组回调(),自身.预览['sizes'])
        if 自身.子 is not None and 自身.子.根 is not None and 自身.子.根.parentNode is None:
            自身.根.appendChild(自身.子.根)

    def 套预览(自身):
        '预览不重建表面'
        if 自身.子 is None:
            return
        回调=自身.组回调()
        if hasattr(自身.子,'套预览'):
            自身.子.套预览(回调,自身.预览['sizes'])

    def 重测(自身):
        '读像素。读数没变就不通知'
        if 自身.根 is None:
            return
        下一=量测窗格可放(自身.根,自身.属性.get('hideSplitWhenBlocked') is True)
        if 可放相同(自身.可放,下一):
            return
        自身.可放=下一
        if 'onRoom' in 自身.属性 and 自身.属性['onRoom'] is not None:
            自身.属性['onRoom'](自身.可放)

    def 渲染(自身):
        '确保表面在，重画里面，再量房间'
        窗口=自身.属性['window']
        文档=窗口.document
        注入样式(文档)
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.className='surface'
            自身.根.setAttribute('data-dockkit-surface','')
            自身.手势=使用手势(窗口,自身.清预览)
            if hasattr(窗口,'ResizeObserver'):
                def 变了():
                    '表面自己变宽变窄时重测'
                    自身.重测()
                自身.观察=窗口.ResizeObserver(变了)
                自身.观察.observe(自身.根)
            if 'parent' in 自身.属性 and 自身.属性['parent'] is not None:
                自身.属性['parent'].appendChild(自身.根)
        自身.根.setAttribute('data-dockkit-drop-zones',自身.投放模式())
        之前=自身.可放
        自身.画子()
        自身.重测()
        if 自身.可放 is not 之前:
            自身.画子()
        return 自身.根

    def 更新(自身,属性):
        '外面的布局变了就重画'
        自身.属性=属性
        return 自身.渲染()

    def 拆除(自身):
        '卸掉手势、观察和里面'
        if 自身.手势 is not None:
            自身.手势['拆除']()
        if 自身.观察 is not None:
            自身.观察.disconnect()
            自身.观察=None
        if 自身.子 is not None and hasattr(自身.子,'拆除'):
            自身.子.拆除()

class 停靠面:
    '递归的停靠布局。浮动内容由浮动层另外画'
    def __init__(自身,属性):
        '画出表面和分割树'
        自身.属性=属性
        自身.表面=表面(属性,自身.绘制)
        自身.根=自身.表面.根

    def 绘制(自身,回调,预览):
        '树从根画起'
        return 窗格树({
            'window':自身.属性['window'],
            'state':自身.属性['state'],
            'nodeId':自身.属性['state']['rootId'],
            'callbacks':回调,
            'preview':预览,
        })

    def 更新(自身,属性):
        '换 props'
        自身.属性=属性
        return 自身.表面.更新(属性)

    def 渲染(自身):
        '再画一次'
        return 自身.更新(自身.属性)

    def 拆除(自身):
        '卸掉表面'
        自身.表面.拆除()

class 停靠布局:
    '一块或左右两块，浮动标签留在同一棵内容树里'
    def __init__(自身,属性):
        '画出表面和标签布局'
        自身.属性=属性
        自身.焦点={'当前':None}
        自身.表面=表面(属性,自身.绘制)
        自身.根=自身.表面.根

    def 绘制(自身,回调,预览):
        '把表面的回调交进标签布局。焦点盒留在这一层，重画格子时还在'
        材料=dict(自身.属性)
        材料['callbacks']=回调
        材料['preview']=预览
        材料['focusRequest']=自身.焦点
        return 标签布局(材料)

    def 更新(自身,属性):
        '换 props'
        自身.属性=属性
        return 自身.表面.更新(属性)

    def 渲染(自身):
        '再画一次'
        return 自身.更新(自身.属性)

    def 拆除(自身):
        '卸掉表面'
        自身.表面.拆除()
