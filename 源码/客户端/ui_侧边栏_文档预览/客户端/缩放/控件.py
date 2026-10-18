from ....模块.客户端.通告 import 取握手窗口
import os
import math
from ....ui_对话.异常 import 注入模块样式文件,模块节点
from ....ui_基础界面组件.icons import 图标下chevron14,图标加号16
from ....ui_基础界面组件.提示泡 import 提示泡
from ....ui_基础界面组件.按钮 import 按钮
from ....ui_基础界面组件.菜单 import 菜单
from .类型 import 最大固定缩放,最小固定缩放,缩放步长,缩放选项

__all__=['缩放控件','步进缩放']

样式模块='zoom-controls'

def 步进缩放(缩放,方向):
    '按固定步长加减，并夹在最小和最大之间'
    if 方向==-1:
        步=math.ceil(缩放/缩放步长)-1
    else:
        步=math.floor(缩放/缩放步长)+1
    值=步*缩放步长
    if 值>最大固定缩放:
        值=最大固定缩放
    if 值<最小固定缩放:
        值=最小固定缩放
    return 值

class 缩放控件:
    '适应宽度、固定档位和加减。百分比可以单独更新'
    def __init__(自身,属性=None):
        '记下缩放、文案和回调'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.开=False
        自身.悬停=False
        自身.聚焦=False
        缩放=自身.属性.get('zoom',1)
        自身.显示值=缩放
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换成新的 props，并跟上新的比例'
        自身.属性=属性 if isinstance(属性,dict) else {}
        if 'zoom' in 自身.属性:
            自身.显示值=自身.属性['zoom']

    def 显示缩放(自身,缩放):
        '手势过程中只改百分比，不重画整棵文档'
        自身.显示值=缩放
        if 自身.根 is not None:
            百分比=自身.根.querySelector('[data-document-zoom-percent]')
            if 百分比 is not None:
                标签=自身.属性['labels']
                百分比.textContent=标签['value'](round(缩放*100))

    def 通知活动(自身):
        '菜单、悬停或焦点有一个在，控件就算活动'
        回调=自身.属性.get('onActiveChange')
        if 回调 is not None:
            回调(自身.开 or 自身.悬停 or 自身.聚焦)

    def 渲染(自身):
        '画出缩小、百分比菜单和放大'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '缩放控件样式',
            os.path.join(os.path.dirname(__file__),'控件.module.css'),
            样式模块,
        )
        标签=属性['labels']
        可见=属性.get('visible') is True
        根=模块节点(文档,'div',样式模块,'panel visible' if 可见 else 'panel')
        根.setAttribute('role','toolbar')
        根.setAttribute('aria-label',标签['controls'])
        根.setAttribute('data-document-zoom-controls','')
        if 可见:
            根.setAttribute('data-document-zoom-visible','')
        def 进入(事件):
            '指针进来'
            自身.悬停=True
            自身.通知活动()
        def 离开(事件):
            '指针离开'
            自身.悬停=False
            自身.通知活动()
        def 聚焦(事件):
            '焦点进来'
            自身.聚焦=True
            自身.通知活动()
        def 失焦(事件):
            '焦点离开'
            自身.聚焦=False
            自身.通知活动()
        根.addEventListener('pointerenter',进入)
        根.addEventListener('pointerleave',离开)
        根.addEventListener('focus',聚焦,True)
        根.addEventListener('blur',失焦,True)
        缩小=按钮({
            'window':窗口,
            'size':'sm',
            'className':'zoomButton',
            'disabled':自身.显示值<=最小固定缩放,
            'children':文档.createElement('span'),
        }).渲染()
        缩小.setAttribute('aria-label',标签['out'])
        缩小.setAttribute('data-dsh-css',样式模块)
        缩小.classList.add('zoomButton')
        减=文档.createElement('span')
        减.innerHTML='<svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true"><path d="M2 8h12" fill="none" stroke="currentColor" stroke-width="1.5"></path></svg>'
        缩小.appendChild(减)
        def 点缩小(事件):
            '缩小一档'
            属性['onZoom'](步进缩放(自身.显示值,-1))
        def 按下不抢焦点(事件):
            '按下时不把焦点从文档上拿走'
            事件.preventDefault()
        缩小.addEventListener('mousedown',按下不抢焦点)
        缩小.addEventListener('click',点缩小)
        根.appendChild(提示泡({'window':窗口,'label':标签['out'],'side':'top','children':缩小}).渲染())
        百分比钮=按钮({
            'window':窗口,
            'size':'sm',
            'className':'percent',
            'children':标签['value'](round(自身.显示值*100)),
        }).渲染()
        百分比钮.setAttribute('aria-label',标签['menu'])
        百分比钮.setAttribute('aria-expanded','true' if 自身.开 else 'false')
        百分比钮.setAttribute('data-dsh-css',样式模块)
        字=百分比钮.querySelector('span')
        if 字 is not None:
            字.setAttribute('data-document-zoom-percent','')
        百分比钮.appendChild(图标下chevron14({'window':窗口,'size':12}))
        def 点菜单(事件):
            '打开或关上比例菜单'
            自身.开=not 自身.开
            自身.通知活动()
            自身.渲染()
        百分比钮.addEventListener('click',点菜单)
        条目=[{'id':'fit-width','label':标签['fitWidth']},{'type':'separator','id':'fit-scale'}]
        for 值 in 缩放选项:
            条目.append({'id':str(值),'label':标签['value'](值*100)})
        选中='fit-width' if 属性.get('fitWidth') is True else None
        if 选中 is None and 自身.显示值 in 缩放选项:
            选中=str(自身.显示值)
        def 选了(标识):
            '适应宽度，或设成这一档'
            自身.开=False
            自身.通知活动()
            if 标识=='fit-width':
                属性['onFitWidth']()
            else:
                属性['onZoom'](float(标识))
        def 关上():
            '菜单关上'
            自身.开=False
            自身.通知活动()
        根.appendChild(菜单({
            'window':窗口,
            'open':自身.开,
            'side':'top',
            'align':'start',
            'portal':True,
            'anchor':百分比钮,
            'items':条目,
            'selectedId':选中,
            'onClose':关上,
            'onSelect':选了,
            'listClassName':'zoomMenu',
        }).渲染())
        放大=按钮({
            'window':窗口,
            'size':'sm',
            'className':'zoomButton',
            'disabled':自身.显示值>=最大固定缩放,
            'children':图标加号16({'window':窗口,'size':14}),
        }).渲染()
        放大.setAttribute('aria-label',标签['into'])
        放大.setAttribute('data-dsh-css',样式模块)
        def 点放大(事件):
            '放大一档'
            属性['onZoom'](步进缩放(自身.显示值,1))
        放大.addEventListener('click',点放大)
        根.appendChild(提示泡({'window':窗口,'label':标签['into'],'side':'top','children':放大}).渲染())
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        return 自身.根

    def __call__(自身,属性=None):
        '再次调用时先换 props 再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
