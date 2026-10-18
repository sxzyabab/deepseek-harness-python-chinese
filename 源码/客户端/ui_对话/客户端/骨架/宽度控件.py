from ....模块.客户端.通告 import 取握手窗口
__all__=['会话宽度控件']

宽度偏好键='dsh.conversation.contentWidth'
内容下限=640
边缘预算=176
滚轮按行=1
滚轮按页=2
回退行高=16

class 宽度手柄:
    '一侧的指针捕获宽度手柄'
    def __init__(自身,属性):
        '记下侧和四个回调，并画出手柄'
        自身.属性=属性
        自身.拖着=False
        自身.基准=0
        自身.起点=0
        自身.最新=0
        自身.帧=None
        自身.根=None
        自身.渲染()

    def 向外宽度(自身):
        '右拖加宽，左拖反向，两侧各算一份'
        差=自身.最新-自身.起点
        向外=差 if 自身.属性['side']=='right' else -差
        return 自身.基准+向外*2

    def 取消帧(自身):
        '丢掉还没画上的一帧'
        if 自身.帧 is not None:
            cancelAnimationFrame(自身.帧)
            自身.帧=None

    def 渲染(自身):
        '画出不占正文的拖动手柄，滚轮转给会话滚动口'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        父=None
        if 自身.根 is not None:
            父=自身.根.parentNode
            自身.根.remove()
        elif 'parent' in 属性:
            父=属性['parent']
        条=文档.createElement('div')
        条.className='widthHandle'
        条.setAttribute('data-dsh-css','conversation-root')
        条.setAttribute('data-side',属性['side'])
        条.setAttribute('data-width-handle',属性['side'])
        def 按下(事件):
            '主键按下后捕获指针'
            if 事件.button!=0:
                return
            事件.preventDefault()
            事件.currentTarget.setPointerCapture(事件.pointerId)
            自身.起点=事件.clientX
            自身.最新=事件.clientX
            自身.基准=属性['onStart']()
            自身.拖着=True
            事件.currentTarget.toggleAttribute('data-dragging',True)
        def 移动(事件):
            '拖动中按指针高度画光标，下一帧提交宽度'
            if not 自身.拖着:
                return
            if not 事件.currentTarget.hasPointerCapture(事件.pointerId):
                return
            盒=事件.currentTarget.getBoundingClientRect()
            事件.currentTarget.style.setProperty('--dsh-width-handle-pointer-y',str(事件.clientY-盒.top)+'px')
            自身.最新=事件.clientX
            if 自身.帧 is None:
                def 帧():
                    '这一帧把向外宽度交给拖动回调'
                    自身.帧=None
                    属性['onDrag'](自身.向外宽度())
                自身.帧=requestAnimationFrame(帧)
        def 抬起(事件):
            '松手时只有真正拖过才写入偏好'
            if not 自身.拖着:
                return
            if not 事件.currentTarget.hasPointerCapture(事件.pointerId):
                return
            自身.拖着=False
            事件.currentTarget.toggleAttribute('data-dragging',False)
            事件.currentTarget.releasePointerCapture(事件.pointerId)
            自身.取消帧()
            自身.最新=事件.clientX
            if 自身.最新!=自身.起点:
                属性['onCommit'](自身.向外宽度())
            属性['onEnd']()
        def 取消(事件):
            '捕获丢失时不写入，交给结束回调恢复'
            if not 自身.拖着:
                return
            自身.拖着=False
            事件.currentTarget.toggleAttribute('data-dragging',False)
            自身.取消帧()
            属性['onEnd']()
        def 滚轮(事件):
            '手柄上的滚轮滚会话滚动口'
            体=事件.currentTarget.parentElement
            if 体 is None:
                return
            滚动口=体.querySelector(':scope > [data-conversation-scroll]')
            if 滚动口 is None:
                return
            if 事件.ctrlKey or 事件.deltaY==0:
                return
            if 事件.deltaMode==滚轮按行:
                行高=float(getComputedStyle(滚动口).lineHeight)
                像素=事件.deltaY*(行高 if 行高==行高 else 回退行高)
            elif 事件.deltaMode==滚轮按页:
                像素=事件.deltaY*滚动口.clientHeight
            else:
                像素=事件.deltaY
            滚动口.scrollBy({'top':像素})
        条.addEventListener('pointerdown',按下)
        条.addEventListener('pointermove',移动)
        条.addEventListener('pointerup',抬起)
        条.addEventListener('pointercancel',取消)
        条.addEventListener('lostpointercapture',取消)
        条.addEventListener('wheel',滚轮)
        自身.根=条
        if 父 is not None:
            父.appendChild(自身.根)
        return 自身.根

def 读宽度偏好(窗口):
    '读出合法的像素偏好。没有或坏了就是 None'
    存储=窗口.localStorage
    读取=存储.getItem
    if not callable(读取):
        return None
    原始=读取(宽度偏好键)
    if 原始 is None:
        return None
    try:
        值=float(原始)
    except ValueError:
        return None
    if 值!=值 or 值<=0:
        return None
    return 值

def 解析内容宽度(列宽,偏好):
    '列宽夹住偏好。没有偏好时用列宽的 64%，落在 680 到 920'
    上限=max(内容下限,列宽-边缘预算)
    if 偏好 is not None:
        return min(max(偏好,内容下限),上限)
    return max(680,min(列宽*0.64,920))

class 会话宽度控件:
    '主会话的宽度轴和左右拖动手柄。活动阶段以外不画'
    def __init__(自身,属性):
        '记下容器和阶段'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.观察=None
        自身.渲染()

    def 发布宽度(自身,容器):
        '把列宽和用户偏好写到滚动体的变量上'
        目标=容器.parentElement if 容器.parentElement is not None else 容器
        列宽=容器.offsetWidth
        目标.style.setProperty('--dsh-conversation-column-width',str(列宽)+'px')
        窗口=自身.属性['window'] if 'window' in 自身.属性 else 取握手窗口()
        偏好=读宽度偏好(窗口)
        if 偏好 is None:
            目标.style.removeProperty('--dsh-chat-user-width')
        else:
            目标.style.setProperty('--dsh-chat-user-width',str(解析内容宽度(列宽,偏好))+'px')

    def 渲染(自身):
        '活动阶段画出左右手柄，并观察容器尺寸'
        属性=自身.属性
        容器=属性.get('container')
        阶段=属性.get('phase')
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        if 自身.观察 is not None:
            自身.观察.disconnect()
            自身.观察=None
        父=None
        if 自身.根 is not None:
            父=自身.根.parentNode
            自身.根.remove()
            自身.根=None
        elif 'parent' in 属性:
            父=属性['parent']
        if 容器 is not None:
            自身.发布宽度(容器)
        if 容器 is None or 阶段!='active':
            return 自身.根
        壳=文档.createElement('div')
        壳.style.display='contents'
        def 开始():
            '拖动起点用当前显示宽度'
            return 解析内容宽度(容器.offsetWidth,读宽度偏好(窗口))
        def 拖动(宽度):
            '拖动中只改变量，不写存储'
            目标=容器.parentElement if 容器.parentElement is not None else 容器
            目标.style.setProperty('--dsh-chat-user-width',str(解析内容宽度(容器.offsetWidth,宽度))+'px')
        def 提交(宽度):
            '松手后把夹住的宽度写入 localStorage'
            窗口.localStorage.setItem(宽度偏好键,str(解析内容宽度(容器.offsetWidth,宽度)))
        def 结束():
            '结束时按存储里的偏好重发'
            自身.发布宽度(容器)
        for 侧 in ('left','right'):
            手柄=宽度手柄({
                'side':侧,
                'onStart':开始,
                'onDrag':拖动,
                'onCommit':提交,
                'onEnd':结束,
                'window':窗口,
            })
            if 手柄.根 is not None:
                壳.appendChild(手柄.根)
        自身.根=壳
        if 父 is not None:
            父.appendChild(自身.根)
        return 自身.根
