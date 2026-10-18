from ....模块.客户端.通告 import 取握手窗口
import os
import math
from ....ui_对话.异常 import 注入模块样式文件,模块节点
from .类型 import 适应宽度,最大固定缩放,最小固定缩放
from .控件 import 缩放控件

__all__=['缩放视口','缩放表面类名']

样式模块='zoom-viewport'
缩放表面类名='surface'
捏合落定毫秒=120
控件隐藏毫秒=420
控件露出高度=72

class 缩放视口:
    '缩放控件和触控板手势。文档树不跟着每一次捏合重画'
    def __init__(自身,属性=None):
        '记下偏好、固有宽度和回调'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.滚动口=None
        自身.控件=None
        自身.视口宽=0
        自身.控件可见=False
        自身.指针在露出区=False
        自身.控件活动=False
        自身.捏合计时=None
        自身.隐藏计时=None
        偏好=自身.属性.get('preference') or 适应宽度
        自身.模式=偏好.get('kind','fit-width')
        自身.当前缩放=1
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 适应缩放(自身):
        '只把比视口宽的内容缩小到适应宽度'
        固有=自身.属性.get('intrinsicWidth')
        if 固有 is None or 固有<=0:
            return 1
        内边=自身.属性.get('horizontalInset') or 0
        可用=自身.视口宽-内边
        if 可用<1:
            可用=1
        return min(1,可用/固有)

    def 清隐藏(自身):
        '取消即将隐藏'
        窗口=自身.属性.get('window')
        if 自身.隐藏计时 is not None and 窗口 is not None and hasattr(窗口,'clearTimeout'):
            窗口.clearTimeout(自身.隐藏计时)
        自身.隐藏计时=None

    def 显示控件(自身):
        '马上露出控件'
        自身.清隐藏()
        if 自身.控件可见:
            return
        自身.控件可见=True
        if 自身.控件 is not None:
            自身.控件.更新({**自身.控件.属性,'visible':True})
            自身.控件.渲染()

    def 安排隐藏(自身):
        '指针不在露出区、控件不活动、也没有捏合时，过一会隐藏'
        自身.清隐藏()
        if 自身.指针在露出区 or 自身.控件活动 or 自身.捏合计时 is not None:
            return
        窗口=自身.属性.get('window')
        if 窗口 is None or not hasattr(窗口,'setTimeout'):
            自身.控件可见=False
            return
        def 隐藏():
            '到点隐藏'
            自身.隐藏计时=None
            自身.控件可见=False
            if 自身.控件 is not None:
                自身.控件.更新({**自身.控件.属性,'visible':False})
                自身.控件.渲染()
        自身.隐藏计时=窗口.setTimeout(隐藏,控件隐藏毫秒)

    def 控件活动变了(自身,活动):
        '菜单或悬停打开时保持露出'
        自身.控件活动=活动
        if 活动:
            自身.显示控件()
        else:
            自身.安排隐藏()

    def 显示这一缩放(自身,下个,客户横=None,客户纵=None):
        '改比例并尽量保住指针下的那一点'
        节点=自身.滚动口
        先前=自身.当前缩放
        if 下个>最大固定缩放:
            下个=最大固定缩放
        if 下个<最小固定缩放:
            下个=最小固定缩放
        if 下个==先前 or 节点 is None:
            return 先前
        界=节点.getBoundingClientRect()
        横=节点.clientWidth/2 if 客户横 is None else 客户横-界.left
        纵=节点.clientHeight/2 if 客户纵 is None else 客户纵-界.top
        锚=自身.指针锚(界.left+横,界.top+纵)
        旧左=节点.scrollLeft
        旧顶=节点.scrollTop
        比=下个/先前 if 先前 else 1
        自身.当前缩放=下个
        自身.模式='fixed'
        if 自身.根 is not None:
            自身.根.setAttribute('data-document-zoom-mode','fixed')
            自身.根.style.setProperty('--document-zoom',str(下个))
        if 自身.控件 is not None:
            自身.控件.显示缩放(下个)
        if 锚 is None:
            节点.scrollLeft=(旧左+横)*比-横
            节点.scrollTop=(旧顶+纵)*比-纵
        else:
            新界=锚['surface'].getBoundingClientRect()
            节点.scrollLeft=节点.scrollLeft+新界.left+锚['x']*比-锚['clientX']
            节点.scrollTop=节点.scrollTop+新界.top+锚['y']*比-锚['clientY']
        return 下个

    def 指针锚(自身,客户横,客户纵):
        '指针下的缩放表面，以及表面内的偏移'
        文档=自身.属性['window'].document
        查找=getattr(文档,'elementFromPoint',None)
        if not callable(查找):
            return None
        命中=查找(客户横,客户纵)
        if 命中 is None or not hasattr(命中,'closest'):
            return None
        表面=命中.closest('[data-document-zoom-surface]')
        if 表面 is None:
            return None
        界=表面.getBoundingClientRect()
        return {'surface':表面,'x':客户横-界.left,'y':客户纵-界.top,'clientX':客户横,'clientY':客户纵}

    def 设缩放(自身,下个):
        '落成固定比例'
        自身.清捏合()
        值=自身.显示这一缩放(下个)
        自身.属性['onPreference']({'kind':'fixed','scale':值})

    def 适应宽(自身):
        '改回适应宽度'
        自身.清捏合()
        适应=自身.适应缩放()
        自身.当前缩放=适应
        自身.模式='fit-width'
        if 自身.根 is not None:
            自身.根.setAttribute('data-document-zoom-mode','fit-width')
            自身.根.style.setProperty('--document-zoom',str(适应))
        if 自身.控件 is not None:
            自身.控件.显示缩放(适应)
        自身.属性['onPreference'](适应宽度)

    def 清捏合(自身):
        '取消还没落定的捏合'
        窗口=自身.属性.get('window')
        if 自身.捏合计时 is not None and 窗口 is not None and hasattr(窗口,'clearTimeout'):
            窗口.clearTimeout(自身.捏合计时)
        自身.捏合计时=None
        自身.清隐藏()

    def 渲染(自身):
        '滚动口、露出区和浮动控件'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        自身.属性=属性
        自身.属性['window']=窗口
        文档=窗口.document
        注入模块样式文件(
            文档,
            '缩放视口样式',
            os.path.join(os.path.dirname(__file__),'视口.module.css'),
            样式模块,
        )
        偏好=属性.get('preference') or 适应宽度
        适应=自身.适应缩放()
        缩放=适应 if 偏好.get('kind')=='fit-width' else 偏好.get('scale',1)
        if 自身.捏合计时 is None:
            自身.当前缩放=缩放
            自身.模式=偏好.get('kind','fit-width')
        根=模块节点(文档,'section',样式模块,'frame')
        根.setAttribute('data-document-zoom-frame','')
        根.setAttribute('data-document-zoom-mode',自身.模式)
        根.style.setProperty('--document-zoom',str(自身.当前缩放))
        根.style.setProperty('--document-zoom-reveal-height',str(控件露出高度)+'px')
        def 移动(事件):
            '鼠标靠近底边时露出控件'
            底=事件.currentTarget.getBoundingClientRect().bottom
            在区=getattr(事件,'pointerType','mouse')=='mouse' and 事件.clientY>=底-控件露出高度
            自身.指针在露出区=在区
            if 在区:
                自身.显示控件()
            else:
                自身.安排隐藏()
        def 移出(事件):
            '离开视口后准备隐藏'
            自身.指针在露出区=False
            自身.安排隐藏()
        根.addEventListener('pointermove',移动)
        根.addEventListener('pointerleave',移出)
        口=模块节点(文档,'div',样式模块,'scrollport')
        口.setAttribute('data-document-zoom-scrollport','')
        子=属性.get('children')
        if getattr(子,'nodeType',None) is not None:
            口.appendChild(子)
        elif isinstance(子,(list,tuple)):
            for 项 in 子:
                if getattr(项,'nodeType',None) is not None:
                    口.appendChild(项)
        根.appendChild(口)
        自身.滚动口=口
        自身.视口宽=口.clientWidth
        回卷=属性.get('scrollportRef')
        if 回卷 is not None:
            回卷(口)
        区=模块节点(文档,'div',样式模块,'revealZone')
        区.setAttribute('data-document-zoom-reveal-zone','')
        区.setAttribute('aria-hidden','true')
        根.appendChild(区)
        if 属性.get('intrinsicWidth') is not None:
            标签=属性['labels']
            自身.控件=缩放控件({
                'window':窗口,
                'zoom':自身.当前缩放,
                'fitWidth':自身.模式=='fit-width',
                'labels':标签,
                'visible':自身.控件可见,
                'onZoom':自身.设缩放,
                'onFitWidth':自身.适应宽,
                'onActiveChange':自身.控件活动变了,
            })
            根.appendChild(自身.控件.渲染())
        def 滚轮(事件):
            '按住 ctrl 的滚轮是捏合'
            信号=属性.get('signal')
            if not getattr(事件,'ctrlKey',False) or (信号 is not None and getattr(信号,'aborted',False)):
                return
            事件.preventDefault()
            自身.显示控件()
            模式值=getattr(事件,'deltaMode',0)
            单位=16 if 模式值==1 else 口.clientHeight if 模式值==2 else 1
            增量=事件.deltaY*单位
            if 增量>40:
                增量=40
            if 增量<-40:
                增量=-40
            自身.显示这一缩放(自身.当前缩放*math.exp(-增量*0.01),事件.clientX,事件.clientY)
            if hasattr(窗口,'clearTimeout') and 自身.捏合计时 is not None:
                窗口.clearTimeout(自身.捏合计时)
            def 落定():
                '捏合停了再写成固定比例'
                自身.捏合计时=None
                属性['onPreference']({'kind':'fixed','scale':自身.当前缩放})
                自身.安排隐藏()
            if hasattr(窗口,'setTimeout'):
                自身.捏合计时=窗口.setTimeout(落定,捏合落定毫秒)
        口.addEventListener('wheel',滚轮,{'passive':False})
        信号=属性.get('signal')
        if 信号 is not None and hasattr(信号,'addEventListener'):
            def 中止时():
                '标签结束时清掉计时'
                自身.清捏合()
            信号.addEventListener('abort',中止时,{'once':True})
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        回调=属性.get('onRenderZoom')
        if 回调 is not None and 自身.捏合计时 is None:
            回调(自身.当前缩放)
        return 自身.根

    def __call__(自身,属性=None):
        '再次调用时先换 props 再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
