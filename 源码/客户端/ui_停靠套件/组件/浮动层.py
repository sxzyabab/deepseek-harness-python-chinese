'浮动层。每块浮动窗格正好一张标签。按在正文上会抬到顶；拖页眉或右下角松手才记移动或缩放'
import pywebbridge
from ...ui_基础界面组件.icons import 图标
from ...ui_基础界面组件.提示泡 import 提示泡
from ..引擎.约束 import 浮动最小尺寸
from ..引擎.几何 import 平移矩形,缩放矩形
from ..引擎.树 import 浮动矩形,取窗格,取标签,唯一标签标识
from .指针 import 使用手势
from .标签标题 import 标签标题
from .渲染 import 类名,标有无,挂上,注入样式,调意图

__all__=['使用浮动手势','浮动头','浮动层']

def 拖到矩形(拖,横,纵):
    '这一笔从起点挪到现在的矩形'
    横移=横-拖['originX']
    纵移=纵-拖['originY']
    if 拖['mode']=='move':
        return 平移矩形(拖['rect'],横移,纵移)
    return 缩放矩形(拖['rect'],横移,纵移,浮动最小尺寸)

def 使用浮动手势(状态,意图,窗口,预览变了):
    '移动和缩放共用。布局模式怎么变都不拥有正文节点'
    预览={'值':None}
    def 清预览():
        '手势结束时收起预览'
        预览['值']=None
        预览变了()
    手势=使用手势(窗口,清预览)

    def 已抬起(窗格标识):
        '已经聚焦并且在最上面'
        return 状态['activePaneId']==窗格标识 and len(状态['floats'])>0 and 状态['floats'][len(状态['floats'])-1]==窗格标识

    def 抬起(窗格标识):
        '按下或点击时聚焦并抬到顶。已经在上面就什么都不报'
        if 已抬起(窗格标识):
            return
        调意图(意图,'focusPane',窗格标识)

    def 拖(模式,窗格标识,事件):
        '页眉或角上的按下。没移动的松开仍是点击'
        事件.stopPropagation()
        根=窗口.document.documentElement
        视窗=根.hasAttribute('data-windows-titlebar')
        if 视窗 and not 根.hasAttribute('data-fullscreen'):
            文=根.style.getPropertyValue('--dsh-windows-titlebar-height')
            缓冲=''
            for 字 in str(文).strip():
                if 字.isdigit() or 字=='.' or (字=='-' and 缓冲==''):
                    缓冲+=字
                    continue
                break
            if 缓冲=='' or 缓冲=='-' or 缓冲=='.' or 缓冲=='-.':
                标题高=0
            else:
                标题高=float(缓冲)
        else:
            标题高=0
        记下=浮动矩形(取窗格(状态,窗格标识))
        矩形=dict(记下)
        if 视窗:
            矩形['y']=max(记下['y'],标题高+20)
        else:
            矩形['y']=max(记下['y'],0)
        起点={'mode':模式,'originX':事件.clientX,'originY':事件.clientY,'rect':矩形}

        def 移动(挪到):
            '预览跟着手指'
            预览['值']={'paneId':窗格标识,'rect':拖到矩形(起点,挪到.clientX,挪到.clientY)}
            预览变了()

        def 松开(放开):
            '没动就是点击抬起，动了才记移动或缩放'
            到=拖到矩形(起点,放开.clientX,放开.clientY)
            起=起点['rect']
            if 到['x']==起['x'] and 到['y']==起['y'] and 到['width']==起['width'] and 到['height']==起['height']:
                抬起(窗格标识)
            elif 模式=='move':
                调意图(意图,'moveFloat',窗格标识,到['x'],到['y'])
            else:
                调意图(意图,'resizeFloat',窗格标识,到)

        手势['开始'](事件.currentTarget,事件.pointerId,{
            'move':移动,
            'up':松开,
        })

    return {'预览':预览,'抬起':抬起,'拖':拖,'拆除':手势['拆除']}

class 浮动头:
    '浮动面板的页眉：标题、收回和关闭'
    def __init__(自身,属性):
        '画出页眉'
        自身.属性=属性
        自身.根=None
        自身.标题=None
        自身.渲染()

    def 渲染(自身):
        '整条页眉都是移动把手'
        窗口=自身.属性['window']
        文档=窗口.document
        注入样式(文档)
        窗格标识=自身.属性['paneId']
        标签=自身.属性['tab']
        文案=自身.属性['labels']
        意图=自身.属性['intents']
        根=文档.createElement('header')
        根.className=类名('tabStrip','floatHeader')
        根.setAttribute('data-dockkit-float-grip',窗格标识)

        def 按下(事件):
            '页眉按下开始移动'
            自身.属性['drag']('move',窗格标识,事件)

        根.addEventListener('pointerdown',按下)
        标题盒=文档.createElement('div')
        标题盒.className=类名('tab','floatTitle')
        标题盒.setAttribute('data-dockkit-float-title','')
        内容=标签['title']
        if 自身.属性.get('renderTabTitle') is not None:
            绘=自身.属性['renderTabTitle'](标签)
            if 绘 is not None:
                内容=绘
        自身.标题=标签标题({'window':窗口,'children':内容})
        标题盒.appendChild(自身.标题.根)
        根.appendChild(标题盒)
        填=文档.createElement('div')
        填.className='stripFill'
        根.appendChild(填)
        收回=文档.createElement('button')
        收回.setAttribute('type','button')
        收回.className='iconButton'
        收回.setAttribute('aria-label',文案['dockFloat'])
        收回.setAttribute('data-dockkit-float-dock',窗格标识)
        图标('panel-left-16',{'window':窗口,'parent':收回,'className':'dockGlyph'})

        def 按收回(事件):
            '收回钮不开始拖'
            事件.stopPropagation()

        def 点收回(事件):
            '送回停靠树'
            调意图(意图,'unfloatPane',窗格标识)

        收回.addEventListener('pointerdown',按收回)
        收回.addEventListener('click',点收回)
        根.appendChild(提示泡({
            'window':窗口,
            'label':文案['dockFloat'],
            'side':'bottom',
            'delayMs':500,
            'children':收回,
        }).渲染())
        可关=自身.属性.get('canCloseTab')
        if 可关 is None or 可关(标签['id']):
            关=文档.createElement('button')
            关.setAttribute('type','button')
            关.className='iconButton'
            关.setAttribute('aria-label',文案['closeTab'])
            关.setAttribute('data-dockkit-float-close',窗格标识)
            图标('close-16',{'window':窗口,'parent':关})

            def 按关(事件):
                '关闭钮不开始拖'
                事件.stopPropagation()

            def 点关(事件):
                '关掉这张浮动标签'
                调意图(意图,'closeTab',标签['id'])

            关.addEventListener('pointerdown',按关)
            关.addEventListener('click',点关)
            根.appendChild(提示泡({
                'window':窗口,
                'label':文案['closeTab'],
                'side':'bottom',
                'delayMs':500,
                'shortcutKeys':文案.get('closeTabKeys'),
                'children':关,
            }).渲染())
        自身.根=根
        if 'parent' in 自身.属性 and 自身.属性['parent'] is not None:
            自身.属性['parent'].appendChild(根)
        return 根

    def 拆除(自身):
        '卸掉标题观察'
        if 自身.标题 is not None:
            自身.标题.拆除()

class 浮动层:
    '按叠放顺序画出全部浮动面板'
    def __init__(自身,属性):
        '记下布局并画出'
        自身.属性=属性
        自身.根=None
        自身.手势=None
        自身.头=[]
        自身.盒表={}
        自身.渲染()

    def 渲染(自身):
        '每块面板一个固定定位的盒子'
        窗口=自身.属性['window']
        文档=窗口.document
        注入样式(文档)
        状态=自身.属性['state']
        意图=自身.属性['intents']
        if 自身.手势 is not None:
            自身.手势['拆除']()
        for 头 in 自身.头:
            头.拆除()
        自身.头=[]
        自身.盒表={}
        def 预览变了():
            '手势预览只改几何，不换掉正在拖的页眉'
            自身.套几何()
        自身.手势=使用浮动手势(状态,意图,窗口,预览变了)
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            if 'parent' in 自身.属性 and 自身.属性['parent'] is not None:
                自身.属性['parent'].appendChild(自身.根)
        else:
            while 自身.根.firstChild is not None:
                自身.根.firstChild.remove()
        for 深度,窗格标识 in enumerate(状态['floats']):
            窗格=取窗格(状态,窗格标识)
            标签=取标签(状态,唯一标签标识(窗格))
            抬=自身.手势['预览']['值']
            if 抬 is not None and 抬['paneId']==窗格标识:
                活=抬['rect']
                层=len(状态['floats'])+1
            else:
                活=浮动矩形(窗格)
                层=深度+1
            盒=文档.createElement('div')
            盒.className='float'
            盒.setAttribute('data-dockkit-float',窗格标识)
            盒.tabIndex=-1
            标有无(盒,'data-dockkit-float-active',状态['activePaneId']==窗格标识)
            盒.style.left=f'{活["x"]}px'
            盒.style.top=f'max(var(--dsh-dockkit-float-top, 0px), {活["y"]}px)'
            盒.style.width=f'{活["width"]}px'
            盒.style.height=f'{活["height"]}px'
            盒.style.zIndex=str(层)

            def 按下(事件,标识=窗格标识):
                '按在面板上就抬起'
                自身.手势['抬起'](标识)

            盒.addEventListener('pointerdown',按下)
            头=浮动头({
                'window':窗口,
                'paneId':窗格标识,
                'tab':标签,
                'labels':自身.属性['labels'],
                'intents':意图,
                'renderTabTitle':自身.属性.get('renderTabTitle'),
                'canCloseTab':自身.属性.get('canCloseTab'),
                'drag':自身.手势['拖'],
                'parent':盒,
            })
            自身.头.append(头)
            身=文档.createElement('div')
            身.className='floatBody'
            挂上(身,自身.属性['renderTab'](标签))
            盒.appendChild(身)
            角=文档.createElement('div')
            角.className='floatResize'
            角.setAttribute('data-dockkit-float-resize',窗格标识)

            def 按角(事件,标识=窗格标识):
                '右下角按下开始缩放'
                自身.手势['拖']('resize',标识,事件)

            角.addEventListener('pointerdown',按角)
            盒.appendChild(角)
            自身.盒表[窗格标识]=盒
            自身.根.appendChild(盒)
        return 自身.根

    def 套几何(自身):
        '按预览改位置和叠放，不重建面板'
        if 自身.手势 is None:
            return
        状态=自身.属性['state']
        抬=自身.手势['预览']['值']
        for 深度,窗格标识 in enumerate(状态['floats']):
            盒=自身.盒表.get(窗格标识)
            if 盒 is None:
                continue
            if 抬 is not None and 抬['paneId']==窗格标识:
                活=抬['rect']
                层=len(状态['floats'])+1
            else:
                活=浮动矩形(取窗格(状态,窗格标识))
                层=深度+1
            盒.style.left=f'{活["x"]}px'
            盒.style.top=f'max(var(--dsh-dockkit-float-top, 0px), {活["y"]}px)'
            盒.style.width=f'{活["width"]}px'
            盒.style.height=f'{活["height"]}px'
            盒.style.zIndex=str(层)

    def 更新(自身,属性):
        '布局变了就重画浮动层'
        自身.属性=属性
        return 自身.渲染()

    def 拆除(自身):
        '卸掉手势和页眉'
        if 自身.手势 is not None:
            自身.手势['拆除']()
            自身.手势=None
        for 头 in 自身.头:
            头.拆除()
