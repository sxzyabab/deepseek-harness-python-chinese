'草稿附件轨。滚动条藏起，左右箭头按溢出翻页'
from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块
from ..ui_基础界面组件.icons import 描边图标

__all__=['附件轨']

样式模块='attachment-rail'

class 附件轨:
    '水平排列草稿附件。新加的滚到末尾，首次挂上已有草稿时留在开头'
    def __init__(自身,属性):
        '记下条目、文案和绘制回调'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.轨=None
        自身.窗口=None
        自身.左钮=None
        自身.右钮=None
        自身.左缘=False
        自身.右缘=False
        自身.上次条数=None
        自身.卸观察=None
        自身.已拆=False
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 更新(自身,属性):
        '换上新的条目和文案'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 拆除(自身):
        '卸掉尺寸观察和滚轮监听'
        自身.已拆=True
        if callable(自身.卸观察):
            自身.卸观察()
            自身.卸观察=None
        if 自身.轨 is not None:
            自身.轨.removeEventListener('scroll',自身.滚动了)
            自身.轨.removeEventListener('wheel',自身.滚轮)

    def 接观察(自身):
        '轨宽跟着撰写栏变。浏览器有 ResizeObserver 才订阅'
        构造=getattr(自身.窗口,'ResizeObserver',None)
        if not callable(构造):
            return
        观察=构造(自身.尺寸变了)
        观察.observe(自身.轨)

        def 卸下():
            '停止观察这一条轨'
            观察.disconnect()

        自身.卸观察=卸下

    def 布局(自身):
        '条数变多时把末尾露出来，再按几何重算左右缘'
        if 自身.已拆:
            return
        轨=自身.轨
        if 轨 is None:
            return
        if getattr(轨,'isConnected',None) is not True:
            return
        条数=len(自身.属性.get('items') or [])
        变多=自身.上次条数 is not None and 条数>自身.上次条数
        自身.上次条数=条数
        if 变多:
            轨.scrollLeft=轨.scrollWidth-轨.clientWidth
        自身.刷新边缘()

    def 刷新边缘(自身):
        '左右各留 1 像素，避免分数滚动把边缘判错'
        轨=自身.轨
        if 轨 is None:
            return
        左=轨.scrollLeft>1
        右=轨.scrollLeft<轨.scrollWidth-轨.clientWidth-1
        if 自身.左缘==左 and 自身.右缘==右:
            return
        自身.左缘=左
        自身.右缘=右
        自身.同步箭头()

    def 滚动了(自身,事件=None):
        '滚动之后重算箭头'
        自身.刷新边缘()

    def 尺寸变了(自身,记录=None,观察者=None):
        '宽度变了就重算箭头'
        自身.刷新边缘()

    def 滚轮(自身,事件):
        '有垂直分量就改成横向滚动，并拦住后面的对话滚动'
        if 事件.deltaY==0:
            return
        轨=自身.轨
        if 轨 is None:
            return
        模式=事件.deltaMode
        滚轮事件=自身.窗口.WheelEvent
        if 模式==滚轮事件.DOM_DELTA_LINE:
            比例=16
        elif 模式==滚轮事件.DOM_DELTA_PAGE:
            比例=轨.clientWidth
        else:
            比例=1
        事件.preventDefault()
        if 事件.deltaX!=0:
            左移=事件.deltaX*比例
        else:
            距离=abs(事件.deltaY)*比例
            if 距离>60:
                距离=60
            if 事件.deltaY<0:
                左移=-距离
            else:
                左移=距离
        轨.scrollBy({'left':左移,'behavior':'auto'})

    def 翻页(自身,方向):
        '一步大约一个视口再留一张卡。用户要求减少动效时不平滑'
        轨=自身.轨
        if 轨 is None:
            return
        行为='smooth'
        匹配=getattr(自身.窗口,'matchMedia',None)
        if callable(匹配):
            查询=匹配('(prefers-reduced-motion: reduce)')
            if 查询 is not None and 查询.matches is True:
                行为='auto'
        距离=轨.clientWidth-64
        if 距离<200:
            距离=200
        轨.scrollBy({'left':方向*距离,'behavior':行为})

    def 向左(自身,事件=None):
        '向左翻一页'
        自身.翻页(-1)

    def 向右(自身,事件=None):
        '向右翻一页'
        自身.翻页(1)

    def 造箭头(自身,文档,类名,文案,点下,路径):
        '一颗贴边的翻页箭头'
        钮=文档.createElement('button')
        钮.type='button'
        钮.className=类名
        标样式模块(钮,样式模块)
        钮.setAttribute('aria-label',文案)
        钮.addEventListener('click',点下)
        图=描边图标({'window':自身.窗口,'size':14},'0 0 16 16',[路径])
        if 图 is not None:
            钮.appendChild(图)
        return 钮

    def 同步箭头(自身):
        '有溢出才放对应方向的箭头'
        if 自身.根 is None or 自身.窗口 is None:
            return
        文档=自身.窗口.document
        文案=自身.属性.get('labels') if isinstance(自身.属性.get('labels'),dict) else {}
        if 自身.左缘:
            左文='' if 文案.get('scrollLeft') is None else str(文案['scrollLeft'])
            if 自身.左钮 is None:
                自身.左钮=自身.造箭头(
                    文档,
                    'arrow arrowLeft',
                    左文,
                    自身.向左,
                    'M10 4L6.70711 7.29289C6.31658 7.68342 6.31658 8.31658 6.70711 8.70711L10 12',
                )
                自身.根.insertBefore(自身.左钮,自身.轨)
            else:
                自身.左钮.setAttribute('aria-label',左文)
        elif 自身.左钮 is not None:
            自身.左钮.remove()
            自身.左钮=None
        if 自身.右缘:
            右文='' if 文案.get('scrollRight') is None else str(文案['scrollRight'])
            if 自身.右钮 is None:
                自身.右钮=自身.造箭头(
                    文档,
                    'arrow arrowRight',
                    右文,
                    自身.向右,
                    'M6 12L9.29289 8.70711C9.68342 8.31658 9.68342 7.68342 9.29289 7.29289L6 4',
                )
                自身.根.appendChild(自身.右钮)
            else:
                自身.右钮.setAttribute('aria-label',右文)
        elif 自身.右钮 is not None:
            自身.右钮.remove()
            自身.右钮=None

    def 渲染(自身):
        '保住同一条滚动元素，按草稿顺序重放条目'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        画完=False
        try:
            属性=自身.属性
            窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
            自身.窗口=窗口
            文档=窗口.document
            注入模块样式文件(
                文档,
                'dsh-attachment-rail',
                os.path.join(os.path.dirname(__file__),'附件轨.module.css'),
                样式模块,
            )
            文案=属性.get('labels') if isinstance(属性.get('labels'),dict) else {}
            if 自身.根 is None:
                根=文档.createElement('div')
                根.className='root'
                标样式模块(根,样式模块)
                轨=文档.createElement('div')
                轨.className='rail'
                标样式模块(轨,样式模块)
                轨.setAttribute('role','group')
                轨.addEventListener('scroll',自身.滚动了)
                轨.addEventListener('wheel',自身.滚轮,{'passive':False})
                根.appendChild(轨)
                自身.根=根
                自身.轨=轨
                自身.接观察()
            组名='' if 文案.get('group') is None else str(文案['group'])
            自身.轨.setAttribute('aria-label',组名)
            while 自身.轨.firstChild is not None:
                自身.轨.removeChild(自身.轨.firstChild)
            画一项=属性.get('renderItem')
            for 项 in 属性.get('items') or []:
                盒=文档.createElement('div')
                盒.className='item'
                标样式模块(盒,样式模块)
                子=画一项(项) if 画一项 is not None else None
                节点=子
                if 子 is not None and not isinstance(子,(str,int,float,bool,dict,list,tuple)):
                    根=getattr(子,'根',None)
                    if 根 is not None:
                        节点=根
                if 节点 is not None:
                    盒.appendChild(节点)
                自身.轨.appendChild(盒)
            自身.同步箭头()
            自身.布局()
            排帧=getattr(窗口,'requestAnimationFrame',None)
            if callable(排帧):
                def 稍后(时刻=None):
                    '进页面并完成布局后再读滚动位置'
                    自身.布局()
                排帧(稍后)
            画完=True
        finally:
            自身.绘制中=False
        if 画完 and 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根
