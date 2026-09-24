import builtins
from .用滚动跟随 import 滚动度量,用滚动跟随

__all__=['用过程滚动','过程滚动席位']

静止边={'canScrollUp':False,'canScrollDown':False}
滚动键=frozenset(['ArrowUp','ArrowDown','PageUp','PageDown','Home','End',' '])

class 过程滚动席位:
    """一组正文的封顶滚动与淡出，共用跟随控制器。"""
    def __init__(自身,正文引用,内容引用,打开,分组):
        """记下引用与开合。引用为 {'current':元素}。"""
        自身.正文引用=正文引用
        自身.内容引用=内容引用
        自身.打开=打开
        自身.分组=分组
        自身.跟随=用滚动跟随(False,1)
        自身.初始位置=None
        自身.边=静止边
        自身.解绑=None
        自身.观察=None

    def 初始化(自身,位置):
        """手动打开时一次性定位。"""
        自身.初始位置=位置

    def 同步(自身,原因):
        """按滚动/尺寸/滚动结束对齐边与跟随。"""
        正文=自身.正文引用['current']
        下一=静止边
        if 正文 is not None and 正文.closest('[hidden], [data-group-expanded-mode]') is None:
            度量=滚动度量(正文)
            初始=自身.初始位置 if 原因=='resize' else None
            if 初始 is not None:
                度量=自身.跟随.跳转(正文,度量,度量['floor'] if 初始=='bottom' else 0)
                if 初始=='top':
                    自身.跟随.设跟随(False)
                自身.初始位置=None
            else:
                曾动画=自身.跟随.animating
                if 原因=='scrollend':
                    自身.跟随.结算(度量)
                else:
                    自身.跟随.采样(度量)
                if 自身.跟随.active and (原因=='resize' or (原因=='scrollend' and 曾动画)):
                    度量=自身.跟随.到底(正文,度量,'smooth')
            下一={'canScrollUp':度量['top']>1,'canScrollDown':度量['top']<度量['floor']-1}
        else:
            自身.跟随.重置()
        if 自身.边['canScrollUp']!=下一['canScrollUp'] or 自身.边['canScrollDown']!=下一['canScrollDown']:
            自身.边=下一

    def 打断(自身):
        """打断进行中的原生动画。"""
        正文=自身.正文引用['current']
        if 正文 is not None and 自身.跟随.animating:
            自身.跟随.打断(正文,滚动度量(正文))

    def 滚动(自身,_事件=None):
        """滚动事件。"""
        自身.同步('scroll')

    def 滚轮(自身,_事件=None):
        """滚轮打断。"""
        自身.打断()

    def 触摸开始(自身,_事件=None):
        """触摸打断。"""
        自身.打断()

    def 指针按下(自身,_事件=None):
        """指针打断。"""
        自身.打断()

    def 键按下(自身,事件):
        """未默认阻止的滚动键打断。"""
        if (not 事件.defaultPrevented) and 事件.key in 滚动键:
            自身.打断()

    def 开合变更(自身,打开,分组):
        """开合或分组模式变化时重置。"""
        自身.打开=打开
        自身.分组=分组
        自身.打断()
        自身.跟随.重置()
        if not 分组 or not 打开:
            自身.初始位置=None

    def 武装观察(自身):
        """打开时观察正文与内容尺寸。"""
        自身.拆除观察()
        正文=自身.正文引用['current']
        if 正文 is None or not 自身.打开:
            return
        观察类=getattr(builtins,'ResizeObserver',None)
        if 观察类 is None:
            return
        自身.解绑=自身.跟随.绑定(正文)
        def 尺寸():
            """尺寸变化。"""
            自身.同步('resize')
        自身.观察=观察类(尺寸)
        自身.观察.observe(正文)
        内容=自身.内容引用['current']
        if 内容 is not None:
            自身.观察.observe(内容)
        def 滚动结束(事件):
            """仅本正文的 scrollend。"""
            if 事件.target is 正文:
                自身.同步('scrollend')
        自身.滚动结束=滚动结束
        正文.addEventListener('scrollend',滚动结束)

    def 拆除观察(自身):
        """断开观察。"""
        if 自身.解绑 is not None:
            自身.解绑()
            自身.解绑=None
        if 自身.观察 is not None:
            自身.观察.disconnect()
            自身.观察=None
        正文=自身.正文引用['current']
        if 正文 is not None and hasattr(自身,'滚动结束'):
            正文.removeEventListener('scrollend',自身.滚动结束)

def 用过程滚动(正文引用,内容引用,打开,分组):
    """铸造过程滚动席位并武装观察。"""
    席=过程滚动席位(正文引用,内容引用,打开,分组)
    席.武装观察()
    return {
        'edges':席.边,
        'events':{
            'onScroll':席.滚动,
            'onWheel':席.滚轮,
            'onTouchStart':席.触摸开始,
            'onPointerDown':席.指针按下,
            'onKeyDown':席.键按下,
        },
        'initialize':席.初始化,
        'seat':席,
    }
