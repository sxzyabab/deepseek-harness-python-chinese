from .覆盖层顶边距 import 覆盖层顶边距

__all__=['锚定位置','使用锚定位置']

def 锚定位置(锚矩形,面板宽,面板高,视口宽,视口高,侧='bottom',对齐='start',间隙=0,边距=0):
    '按锚矩形放置固定层。顶边距读窗框净空，其余边用传入边距'
    左=锚矩形['right']-面板宽 if 对齐=='end' else 锚矩形['left']
    顶=锚矩形['top']-间隙-面板高 if 侧=='top' else 锚矩形['bottom']+间隙
    顶边距=覆盖层顶边距(边距)
    if 面板宽>0:
        上限=视口宽-面板宽-边距
        if 左<边距:
            左=边距
        if 左>上限:
            左=上限
    if 面板高>0:
        上限=视口高-面板高-边距
        if 顶<顶边距:
            顶=顶边距
        if 顶>上限:
            顶=上限
    return {'left':左,'top':顶}

def 使用锚定位置(选项):
    '面板打开时跟着锚。滚动用捕获阶段，并听窗口缩放和面板自身尺寸。返回拆除函数'
    锚=选项['anchor']
    面板=选项['panel']
    窗口=选项['window']
    if 选项.get('open') is not True:
        return lambda: None
    侧=选项['side'] if 'side' in 选项 else 'bottom'
    对齐=选项['align'] if 'align' in 选项 else 'start'
    间隙=选项['gap'] if 'gap' in 选项 else 0
    边距=选项['margin'] if 'margin' in 选项 else 0
    def 放置():
        '量锚和面板，把固定坐标写回面板'
        矩形=锚.getBoundingClientRect()
        宽=面板.offsetWidth if 面板.offsetWidth is not None else 0
        高=面板.offsetHeight if 面板.offsetHeight is not None else 0
        位=锚定位置(
            {'left':矩形.left,'right':矩形.right,'top':矩形.top,'bottom':矩形.bottom},
            宽,高,窗口.innerWidth,窗口.innerHeight,侧,对齐,间隙,边距,
        )
        面板.style.position='fixed'
        面板.style.left=str(位['left'])+'px'
        面板.style.top=str(位['top'])+'px'
    放置()
    窗口.addEventListener('scroll',放置,True)
    窗口.addEventListener('resize',放置)
    观察=None
    构造=getattr(窗口,'ResizeObserver',None)
    if 构造 is not None and 面板 is not None:
        观察=构造(放置)
        观察.observe(面板)
    def 拆除():
        '卸掉滚动、缩放和尺寸观察'
        窗口.removeEventListener('scroll',放置,True)
        窗口.removeEventListener('resize',放置)
        if 观察 is not None:
            观察.disconnect()
    return 拆除
