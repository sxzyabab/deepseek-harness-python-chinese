import re#sRGB 通道解析
__all__=['观察终端光标']#仅中文公开名

通道模式=re.compile(r'[0-9.]+')#sRGB 数字

def 颜色通道(颜色):#拆 r,g,b[,a]
    """井号六位或 rgb() 通道。"""
    if 颜色.startswith('#'):#井号
        return [int(颜色[1:3],16),int(颜色[3:5],16),int(颜色[5:7],16)]#三通道
    return [float(项) for 项 in 通道模式.findall(颜色)]#rgb 数字

def 亮度(颜色):#相对亮度
    """sRGB 相对亮度。"""
    通道=颜色通道(颜色)#原始
    线性=[]#线性通道
    for 项 in 通道[:3]:#仅 rgb
        值=项/255#归一
        if 值<=0.04045:#低段
            线性.append(值/12.92)#线性
        else:#高段
            线性.append(((值+0.055)/1.055)**2.4)#线性
    return 0.2126*线性[0]+0.7152*线性[1]+0.0722*线性[2]#加权

def 不透明色(颜色,背景):#去掉 alpha
    """有 alpha 时与背景合成。"""
    通道=颜色通道(颜色)#含可能的 alpha
    透明=通道[3] if len(通道)>3 else 1#默认不透明
    if 透明==1:#已不透明
        return 颜色#原样
    底=颜色通道(背景())#表面
    红=round(通道[0]*透明+底[0]*(1-透明))#合成
    绿=round(通道[1]*透明+底[1]*(1-透明))#合成
    蓝=round(通道[2]*透明+底[2]*(1-透明))#合成
    return 'rgb('+str(红)+', '+str(绿)+', '+str(蓝)+')'#合成色

def 观察终端光标(终端,节点,优先光标):#对比度光标
    """按单元格背景保持光标可见。"""
    def 渲染后():#onRender
        """测量单元格色并写 CSS 变量。"""
        光标=节点.querySelector('.xterm-cursor')#光标节点
        if 光标 is None:#尚未绘制
            return#跳过
        光标.classList.remove('xterm-cursor')#露出单元格
        try:#读计算样式
            样式=节点.ownerDocument.defaultView.getComputedStyle(光标)#计算样式
            前景=样式.color#字色
            def 滚动底():#视口底
                """取滚动层背景。"""
                滚动=节点.querySelector('.xterm-scrollable-element')#滚动层
                return 节点.ownerDocument.defaultView.getComputedStyle(滚动).backgroundColor#底色
            背景=不透明色(样式.backgroundColor,滚动底)#不透明底
        finally:#恢复标记
            光标.classList.add('xterm-cursor')#加回
        def 取底():#回落底
            """优先光标合成用底。"""
            return 背景#单元格底
        优先=不透明色(优先光标(),取底)#优先色
        底亮=亮度(背景)#底亮度
        优先亮=亮度(优先)#优先亮度
        对比=(max(底亮,优先亮)+0.05)/(min(底亮,优先亮)+0.05)#对比
        if 对比>=3:#够对比
            填充=优先#用优先
        elif 底亮>0.179:#浅底
            填充='#000000'#黑
        else:#深底
            填充='#ffffff'#白
        节点.style.setProperty('--terminal-cursor',填充)#光标
        if 亮度(填充)>0.179:#浅填充
            衬='#000000'#黑字
        else:#深填充
            衬='#ffffff'#白字
        节点.style.setProperty('--terminal-cursor-accent',衬)#衬色
        节点.style.setProperty('--terminal-cursor-cell-background',背景)#单元格底
        节点.style.setProperty('--terminal-cursor-cell-foreground',前景)#单元格字
    return 终端.onRender(渲染后)#订阅
