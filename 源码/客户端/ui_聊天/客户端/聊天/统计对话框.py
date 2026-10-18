__all__=['测量样式','统计对话框席']

面板边距=12
面板间隙=8
测量样式={'visibility':'hidden','left':'0','top':'0'}


def 读矩形(元素):
    '没有元素时没有矩形'
    if 元素 is None or not hasattr(元素,'getBoundingClientRect'):
        return None
    return 元素.getBoundingClientRect()


class 统计对话框席:
    '锚在触发器上方，并夹在视口里。点外面或按 Esc 就关'
    def __init__(自身):
        '先关着'
        自身.打开=False
        自身.根=None
        自身.面板=None
        自身.位置=None
        自身.已听=False
        自身.文档=None
        自身.变化=None

    def 设打开(自身,打开):
        '显式开关。外部点击和 Esc 会通知宿主重画'
        下一=打开 is True
        if 下一==自身.打开:
            return
        自身.打开=下一
        if callable(自身.变化):
            自身.变化()

    def 放置(自身):
        '按触发器和面板的真实尺寸夹到视口内'
        if not 自身.打开 or 自身.根 is None or 自身.面板 is None:
            自身.位置=None
            return None
        锚=读矩形(自身.根)
        面=读矩形(自身.面板)
        窗=自身.根.ownerDocument.defaultView if 自身.根.ownerDocument is not None else None
        if 锚 is None or 面 is None or 窗 is None:
            自身.位置=None
            return None
        宽=getattr(窗,'innerWidth',0) or 0
        高=getattr(窗,'innerHeight',0) or 0
        左=锚.left+(锚.width-面.width)/2
        上=锚.top-面板间隙-面.height
        if 左<面板边距:
            左=面板边距
        if 左+面.width>宽-面板边距:
            左=max(面板边距,宽-面板边距-面.width)
        if 上<面板边距:
            上=面板边距
        if 上+面.height>高-面板边距:
            上=max(面板边距,高-面板边距-面.height)
        自身.位置={'left':str(左)+'px','top':str(上)+'px'}
        return 自身.位置

    def 监听(自身,文档):
        '打开期间听 Esc 和捕获阶段的外部点击'
        if 自身.已听 and 自身.文档 is 文档:
            return
        自身.文档=文档
        自身.已听=True

        def 按键(事件):
            'Esc 关闭'
            if getattr(事件,'key',None)=='Escape':
                自身.设打开(False)

        def 点击(事件):
            '触发器和面板以外的点击关闭'
            目标=getattr(事件,'target',None)
            if 目标 is None:
                return
            在根=自身.根 is not None and 自身.根.contains(目标)
            在面=自身.面板 is not None and 自身.面板.contains(目标)
            if not 在根 and not 在面:
                自身.设打开(False)

        文档.addEventListener('keydown',按键)
        文档.addEventListener('click',点击,True)

    def 套样式(自身,面板):
        '还没量到位置时先藏起来量尺寸'
        样式=自身.位置 if 自身.位置 is not None else 测量样式
        面板.style.visibility=样式.get('visibility','')
        面板.style.left=样式.get('left','0')
        面板.style.top=样式.get('top','0')
        面板.style.position='fixed'
