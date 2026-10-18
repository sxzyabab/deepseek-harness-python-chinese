from .用滚动跟随 import 滚动度量,用滚动跟随

__all__=['过程滚动']

静止={'canScrollUp':False,'canScrollDown':False}
滚动键={'ArrowUp','ArrowDown','PageUp','PageDown','Home','End',' '}


class 过程滚动:
    '过程组自己的贴底，不连到外层转录'
    def __init__(自身):
        '先不跟'
        自身.跟随=用滚动跟随(False,1)
        自身.初始=None
        自身.边=dict(静止)
        自身.体=None
        自身.内容=None
        自身.打开=False
        自身.成组=False
        自身.观察=None
        自身.松开=None

    def 初始化(自身,位置):
        '手动打开时一次定位到顶或底'
        自身.初始=位置

    def 同步(自身,原因):
        '按当前滚动位置更新上下渐隐'
        体=自身.体
        下一=dict(静止)
        if 体 is not None and 体.closest('[hidden], [data-group-expanded-mode]') is None:
            度量=滚动度量(体)
            初始=自身.初始 if 原因=='resize' else None
            if 初始 is not None:
                度量=自身.跟随.跳到(体,度量,度量['floor'] if 初始=='bottom' else 0)
                if 初始=='top':
                    自身.跟随.设跟随(False)
                自身.初始=None
            else:
                曾动画=自身.跟随.动画中()
                if 原因=='scrollend':
                    自身.跟随.结算(度量)
                else:
                    自身.跟随.采样(度量)
                if 自身.跟随.活动() and (原因=='resize' or (原因=='scrollend' and 曾动画)):
                    度量=自身.跟随.到底(体,度量,'smooth')
            下一={'canScrollUp':度量['top']>1,'canScrollDown':度量['top']<度量['floor']-1}
        else:
            自身.跟随.重置()
        if 下一['canScrollUp']!=自身.边['canScrollUp'] or 下一['canScrollDown']!=自身.边['canScrollDown']:
            自身.边=下一
        return 自身.边

    def 打断(自身):
        '滚轮、触摸和滚动键打断动画'
        if 自身.体 is not None and 自身.跟随.动画中():
            自身.跟随.打断(自身.体,滚动度量(自身.体))

    def 挂(自身,体,内容,打开,成组):
        '打开且成组时观察尺寸'
        自身.体=体
        自身.内容=内容
        if not 成组 or not 打开:
            自身.初始=None
        自身.打断()
        自身.跟随.重置()
        if 自身.松开 is not None:
            自身.松开()
            自身.松开=None
        if 自身.观察 is not None:
            自身.观察.disconnect()
            自身.观察=None
        if 体 is None or not 打开:
            return
        自身.松开=自身.跟随.绑定(体)
        窗=体.ownerDocument.defaultView if 体.ownerDocument is not None else None
        if 窗 is None or not hasattr(窗,'ResizeObserver'):
            return
        def 尺寸(条目=None):
            '尺寸变了重新对齐'
            自身.同步('resize')
        自身.观察=窗.ResizeObserver(尺寸)
        自身.观察.observe(体)
        if 内容 is not None:
            自身.观察.observe(内容)

        def 滚动结束(事件):
            '只处理这一层滚动口'
            if getattr(事件,'target',None) is 体:
                自身.同步('scrollend')

        体.addEventListener('scrollend',滚动结束)

    def 滚动(自身,事件=None):
        '滚动中采样'
        自身.同步('scroll')

    def 滚轮(自身,事件=None):
        '滚轮打断跟随动画'
        自身.打断()

    def 按下(自身,事件=None):
        '指针和触摸打断跟随动画'
        自身.打断()

    def 按键(自身,事件):
        '没被拦住的滚动键打断动画'
        if getattr(事件,'defaultPrevented',False):
            return
        if getattr(事件,'key',None) in 滚动键:
            自身.打断()
