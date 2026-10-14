import re

__all__=['观察终端光标']

通道模式=re.compile(r'[0-9.]+')

def 颜色通道(颜色):
    '井号六位或 rgb() 通道'
    if 颜色.startswith('#'):
        return [int(颜色[1:3],16),int(颜色[3:5],16),int(颜色[5:7],16)]
    return [float(项) for 项 in 通道模式.findall(颜色)]

def 亮度(颜色):
    'sRGB 相对亮度。0.04045 以下走线性段，以上走伽马段'
    通道=颜色通道(颜色)
    线性=[]
    for 项 in 通道[:3]:
        值=项/255
        if 值<=0.04045:
            线性.append(值/12.92)
        else:
            线性.append(((值+0.055)/1.055)**2.4)
    return 0.2126*线性[0]+0.7152*线性[1]+0.0722*线性[2]

def 不透明色(颜色,背景):
    '有 alpha 时与背景合成'
    通道=颜色通道(颜色)
    透明=通道[3] if len(通道)>3 else 1
    if 透明==1:
        return 颜色
    底=颜色通道(背景())
    红=round(通道[0]*透明+底[0]*(1-透明))
    绿=round(通道[1]*透明+底[1]*(1-透明))
    蓝=round(通道[2]*透明+底[2]*(1-透明))
    return 'rgb('+str(红)+', '+str(绿)+', '+str(蓝)+')'

def 观察终端光标(终端,节点,优先光标):
    '按单元格背景保持光标可见。对比不足 3 时，浅底用黑、深底用白'
    def 渲染后():
        '测量单元格色并写 CSS 变量'
        光标=节点.querySelector('.xterm-cursor')
        if 光标 is None:
            return
        光标.classList.remove('xterm-cursor')
        try:
            样式=节点.ownerDocument.defaultView.getComputedStyle(光标)
            前景=样式.color
            def 滚动底():
                '取滚动层背景'
                滚动=节点.querySelector('.xterm-scrollable-element')
                return 节点.ownerDocument.defaultView.getComputedStyle(滚动).backgroundColor
            背景=不透明色(样式.backgroundColor,滚动底)
        finally:
            光标.classList.add('xterm-cursor')
        def 取底():
            '优先光标合成用底'
            return 背景
        优先=不透明色(优先光标(),取底)
        底亮=亮度(背景)
        优先亮=亮度(优先)
        对比=(max(底亮,优先亮)+0.05)/(min(底亮,优先亮)+0.05)
        if 对比>=3:
            填充=优先
        elif 底亮>0.179:
            填充='#000000'
        else:
            填充='#ffffff'
        节点.style.setProperty('--terminal-cursor',填充)
        if 亮度(填充)>0.179:
            衬='#000000'
        else:
            衬='#ffffff'
        节点.style.setProperty('--terminal-cursor-accent',衬)
        节点.style.setProperty('--terminal-cursor-cell-background',背景)
        节点.style.setProperty('--terminal-cursor-cell-foreground',前景)
    return 终端.onRender(渲染后)
