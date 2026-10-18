'指针拖拽和方向键把诊断底栏限制在视口高度的 20% 到 80%'
from .....客户端.模块.客户端.通告 import 取握手窗口

__all__=['检查器缩放柄','最小高度','最大高度']

最小高度=20
最大高度=80


class 检查器缩放柄:
    '水平分隔条。高度是视口百分比，由面板记住'
    def __init__(自身,属性):
        '记下高度、回调和面板，并画出分隔条'
        自身.属性=属性
        自身.高度=属性['height']
        自身.拖=None
        自身.根=None
        自身.渲染()

    def 调整(自身,值):
        '夹到允许区间后交给面板，并刷新当前值'
        次值=min(最大高度,max(最小高度,值))
        自身.高度=次值
        自身.属性['onResize'](次值)
        if 自身.根 is not None:
            自身.根.setAttribute('aria-valuenow',str(round(次值)))

    def 渲染(自身):
        '分隔条可指向、可键盘操作'
        文档=取握手窗口().document
        柄=文档.createElement('div')
        柄.className='resize'
        柄.setAttribute('role','separator')
        柄.tabIndex=0
        柄.setAttribute('aria-label',自身.属性['label'])
        柄.setAttribute('aria-orientation','horizontal')
        柄.setAttribute('aria-controls',自身.属性['panelId'])
        柄.setAttribute('aria-valuemin',str(最小高度))
        柄.setAttribute('aria-valuemax',str(最大高度))
        柄.setAttribute('aria-valuenow',str(round(自身.高度)))

        def 移动(事件):
            '按指针位移换算视口百分比'
            起点=自身.拖
            if 起点 is None or 起点['pointerId']!=事件.pointerId:
                return
            内高=取握手窗口().innerHeight or 1
            自身.调整(起点['height']+(起点['y']-事件.clientY)/内高*100)

        def 结束(事件):
            '松开或取消时放掉捕获'
            if 自身.拖 is None or 自身.拖['pointerId']!=事件.pointerId:
                return
            自身.拖=None
            if 事件.currentTarget.hasPointerCapture(事件.pointerId):
                事件.currentTarget.releasePointerCapture(事件.pointerId)

        def 按下(事件):
            '主键按下开始拖。已经在拖则忽略'
            if 事件.button!=0 or 自身.拖 is not None:
                return
            事件.preventDefault()
            事件.currentTarget.setPointerCapture(事件.pointerId)
            自身.拖={'pointerId':事件.pointerId,'y':事件.clientY,'height':自身.高度}

        def 抬起(事件):
            '先按最后位置调整，再结束拖拽'
            移动(事件)
            结束(事件)

        def 按键(事件):
            '上加 5，下减 5，Home 到最小，End 到最大'
            下一步={'ArrowUp':自身.高度+5,'ArrowDown':自身.高度-5,'Home':最小高度,'End':最大高度}
            次值=下一步.get(事件.key)
            if 次值 is None:
                return
            事件.preventDefault()
            自身.调整(次值)

        柄.addEventListener('pointerdown',按下)
        柄.addEventListener('pointermove',移动)
        柄.addEventListener('pointerup',抬起)
        柄.addEventListener('pointercancel',结束)
        柄.addEventListener('lostpointercapture',结束)
        柄.addEventListener('keydown',按键)
        自身.根=柄
        return 柄
