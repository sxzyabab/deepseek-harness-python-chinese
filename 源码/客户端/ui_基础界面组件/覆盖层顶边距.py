from ..模块.客户端.通告 import 取握手窗口

__all__=['覆盖层顶边距']

def 读像素(原文):
    '对齐 parseFloat：从开头读数字，读不出就当没有'
    文=str(原文).strip()
    止=0
    if 文.startswith('+') or 文.startswith('-'):
        止=1
    见点=False
    while 止<len(文):
        字=文[止]
        if 字.isdigit():
            止=止+1
            continue
        if 字=='.' and 见点 is False:
            见点=True
            止=止+1
            continue
        break
    数=文[:止]
    if 数 in ('','+','-','.','+.','-.'):
        return None
    return float(数)

def 覆盖层顶边距(最小):
    '覆盖层距视口顶的边距。读窗框 --dsh-frame-top-clearance，全屏只留 20'
    窗口=取握手窗口()
    根=窗口.document.documentElement
    样式=窗口.getComputedStyle(根)
    净空=读像素(样式.getPropertyValue('--dsh-frame-top-clearance'))
    if 净空 is None:
        return 最小
    if 根.hasAttribute('data-fullscreen'):
        加=0
    else:
        加=净空
    合计=加+20
    if 合计>最小:
        return 合计
    return 最小
