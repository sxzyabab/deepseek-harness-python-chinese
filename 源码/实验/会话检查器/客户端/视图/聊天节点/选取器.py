'一次检查器选取：在主 Chat 上盖一层真正接住点击的蒙层'

from .选取匹配 import 匹配聊天元素
from .文档对象 import 已显示,在聊天内
from .高亮 import 放置聊天高亮

__all__=['检查器聊天选取器']

指针动作=('pointerdown','pointerup','mousedown','mouseup','auxclick','dblclick','contextmenu')

class 检查器聊天选取器:
    '拥有一次选取手势的蒙层、预览和几何观察'
    def __init__(自身,取根,所有者,已选取,已取消,已释放):
        '所有者是检查器按钮；藏起或卸掉它会取消选取'
        自身._取根=取根
        自身._所有者=所有者
        自身._已选取=已选取
        自身._已取消=已取消
        自身._已释放=已释放
        自身._蒙层=None
        自身._覆盖=None
        自身._根=None
        自身._观察=None
        自身._尺寸=None
        自身._移动=自身._处理移动
        自身._离开=自身._隐藏
        自身._点击=自身._处理点击
        自身._滚轮=自身._处理滚轮
        自身._按下键=自身._处理按下键
        自身._压制=自身._处理压制
        自身._定位=自身._处理定位
        自身._核对=自身._处理核对
        自身.取消=自身._处理取消

    def 开始(自身):
        '在可见的主 Chat 上开始选取'
        根=自身._取根()
        if 根 is None or not 已显示(根) or not 已显示(自身._所有者):
            return False
        蒙层=document.createElement('div')
        if not 放置聊天高亮(蒙层,根):
            return False
        蒙层.className='chatPickMask'
        蒙层.dataset.sessionInspectorPicker=''
        蒙层.setAttribute('aria-hidden','true')
        自身._根=根
        自身._蒙层=蒙层
        蒙层.addEventListener('pointermove',自身._移动)
        蒙层.addEventListener('pointerleave',自身._离开)
        蒙层.addEventListener('click',自身._点击)
        蒙层.addEventListener('wheel',自身._滚轮,{'passive':False})
        for 种类 in 指针动作:
            蒙层.addEventListener(种类,自身._压制)
        document.body.append(蒙层)
        window.addEventListener('keydown',自身._按下键,True)
        window.addEventListener('blur',自身.取消)
        window.addEventListener('scroll',自身._定位,True)
        window.addEventListener('resize',自身._定位)
        自身._观察=MutationObserver(自身._核对)
        for 起点 in (自身._所有者,根):
            元素=起点
            while 元素 is not None:
                自身._观察.observe(元素,{'attributes':True,'attributeFilter':['hidden','style','class'],'childList':True})
                元素=元素.parentElement
        try:
            观察器类=ResizeObserver
        except NameError:
            观察器类=None
        if 观察器类 is not None:
            自身._尺寸=观察器类(自身._定位)
            自身._尺寸.observe(根)
        return True

    def 拆除(自身):
        '卸掉蒙层和观察者；卸载期间不调用面板回调'
        蒙层=自身._蒙层
        if 蒙层 is not None:
            蒙层.removeEventListener('pointermove',自身._移动)
            蒙层.removeEventListener('pointerleave',自身._离开)
            蒙层.removeEventListener('click',自身._点击)
            蒙层.removeEventListener('wheel',自身._滚轮)
            for 种类 in 指针动作:
                蒙层.removeEventListener(种类,自身._压制)
            蒙层.remove()
        自身._蒙层=None
        自身._根=None
        window.removeEventListener('keydown',自身._按下键,True)
        window.removeEventListener('blur',自身.取消)
        window.removeEventListener('scroll',自身._定位,True)
        window.removeEventListener('resize',自身._定位)
        if 自身._观察 is not None:
            自身._观察.disconnect()
        自身._观察=None
        if 自身._尺寸 is not None:
            自身._尺寸.disconnect()
        自身._尺寸=None
        自身._隐藏()
        自身._已释放()

    def _当前根(自身):
        '根和按钮都还是这一次、且仍然显示'
        根=自身._根
        if 根 is not None and 自身._取根() is 根 and 已显示(根) and 已显示(自身._所有者):
            return 根
        return None

    def _处理定位(自身,事件=None):
        '滚动或尺寸变化后先藏预览再核对蒙层'
        自身._隐藏()
        自身._核对()

    def _处理核对(自身,记录=None):
        '蒙层对不齐当前 Chat 时取消'
        if 自身._蒙层 is None:
            return
        根=自身._当前根()
        if 根 is None or not 放置聊天高亮(自身._蒙层,根):
            自身.取消()

    def _命中(自身,事件):
        '蒙层和预览下面的、仍在 Chat 内的元素'
        if 自身._蒙层 is None:
            return None
        根=自身._当前根()
        if 根 is None:
            自身.取消()
            return None
        元素=None
        for 候选 in document.elementsFromPoint(事件.clientX,事件.clientY):
            if 候选 is not 自身._蒙层 and 候选 is not 自身._覆盖:
                元素=候选
                break
        if 元素 is not None and 在聊天内(元素,根):
            return {'element':元素,'root':根}
        return None

    def _隐藏(自身):
        '去掉预览覆盖层'
        if 自身._覆盖 is not None:
            自身._覆盖.remove()
        自身._覆盖=None

    def _处理取消(自身,事件=None):
        '停止手势并清掉面板的选取状态'
        if 自身._蒙层 is None:
            return
        自身.拆除()
        自身._已取消()

    def _处理移动(自身,事件):
        '悬停时预览最具体的盒子'
        命中=自身._命中(事件)
        匹配=None if 命中 is None else 匹配聊天元素(命中['element'],命中['root'])
        if 匹配 is None:
            自身._隐藏()
            return
        覆盖=自身._覆盖 if 自身._覆盖 is not None else document.createElement('div')
        覆盖.className='chatPick'
        覆盖.dataset.sessionInspectorHighlight='pick'
        覆盖.setAttribute('aria-hidden','true')
        if not 放置聊天高亮(覆盖,匹配['element']):
            自身._隐藏()
            return
        if 自身._覆盖 is None:
            document.body.append(覆盖)
            自身._覆盖=覆盖

    def _处理压制(自身,事件):
        '蒙层吃掉指针，不让底下的 Chat 控件激活'
        事件.preventDefault()
        事件.stopImmediatePropagation()

    def _处理点击(自身,事件):
        '主键点击选中；选取函数返回真才卸掉蒙层'
        自身._处理压制(事件)
        if 事件.button!=0:
            return
        命中=自身._命中(事件)
        匹配=None if 命中 is None else 匹配聊天元素(命中['element'],命中['root'])
        if 匹配 is not None and 自身._已选取(匹配['target']):
            自身.拆除()

    def _处理滚轮(自身,事件):
        '把滚轮转发给下方可滚动的 Chat 区域'
        自身._处理压制(事件)
        命中=自身._命中(事件)
        元素=None if 命中 is None else 命中['element']
        while 元素 is not None:
            if isinstance(元素,HTMLElement) and 元素.matches('[data-conversation-scroll], [data-step-process-body]'):
                垂直=元素.scrollTop>0 if 事件.deltaY<0 else 元素.scrollTop+元素.clientHeight<元素.scrollHeight
                水平=元素.scrollLeft>0 if 事件.deltaX<0 else 元素.scrollLeft+元素.clientWidth<元素.scrollWidth
                if (事件.deltaY!=0 and 垂直) or (事件.deltaX!=0 and 水平):
                    样式=getComputedStyle(元素)
                    if 事件.deltaMode==WheelEvent.DOM_DELTA_PAGE:
                        比例=元素.clientHeight
                    elif 事件.deltaMode==WheelEvent.DOM_DELTA_LINE:
                        try:
                            比例=float(样式.lineHeight)
                        except (TypeError,ValueError):
                            比例=0
                        if not 比例:
                            try:
                                比例=float(样式.fontSize)
                            except (TypeError,ValueError):
                                比例=1
                            if not 比例:
                                比例=1
                    else:
                        比例=1
                    元素.scrollBy({'top':事件.deltaY*比例,'left':事件.deltaX*比例,'behavior':'instant'})
                    break
            元素=元素.parentElement

    def _处理按下键(自身,事件):
        'Esc 取消选取'
        if 事件.key!='Escape':
            return
        自身._处理压制(事件)
        自身.取消()
