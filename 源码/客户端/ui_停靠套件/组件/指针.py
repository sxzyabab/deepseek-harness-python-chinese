'停靠面和浮动层共用的指针占用。窗口监听才是手势本身，捕获只是不让路过的滚动容器把指针抢走'
import pywebbridge

__all__=['使用手势']

def 使用手势(窗口,复位):
    '一次只跟一个指针。松开、取消或新的按下都会结束。返回开始和拆除'
    飞行={'当前':None}

    def 拆除():
        '卸掉还在飞的监听，不清预览'
        当前=飞行['当前']
        飞行['当前']=None
        if 当前 is not None:
            当前['停']()

    def 开始(元素,指针标识,跟随):
        '从按下的元素开始跟这个指针'
        上一=飞行['当前']
        if 上一 is not None:
            上一['结束']()
        if callable(getattr(元素,'setPointerCapture',None)):
            元素.setPointerCapture(指针标识)
        控制器=窗口.AbortController()
        信号=控制器.signal
        元素.setAttribute('data-dockkit-pointer',str(指针标识))

        def 中止():
            '手势结束时摘掉指针标记'
            if 元素.getAttribute('data-dockkit-pointer')==str(指针标识):
                元素.removeAttribute('data-dockkit-pointer')

        信号.addEventListener('abort',中止,{'once':True})

        def 落定():
            '清掉飞行记录并让组件收起预览'
            飞行['当前']=None
            复位()

        def 移动(事件):
            '只认这一根指针的移动'
            if 事件.pointerId!=指针标识:
                return
            跟随['move'](事件)

        def 抬起(事件):
            '松开：先结束手势和预览，再交给跟随'
            if 事件.pointerId!=指针标识:
                return
            控制器.abort()
            落定()
            跟随['up'](事件)

        def 取消(事件):
            '指针被取消时只收起，不结算'
            if 事件.pointerId!=指针标识:
                return
            控制器.abort()
            落定()

        def 停():
            '卸掉三个窗口监听'
            控制器.abort()

        def 结束():
            '新的按下挤掉这一笔时，先卸监听再收起预览'
            停()
            落定()

        窗口.addEventListener('pointermove',移动,{'signal':信号})
        窗口.addEventListener('pointerup',抬起,{'signal':信号})
        窗口.addEventListener('pointercancel',取消,{'signal':信号})
        飞行['当前']={'停':停,'结束':结束}

    return {'开始':开始,'拆除':拆除}
