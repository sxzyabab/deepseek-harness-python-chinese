'房间规则的文档一侧：提交之后读每块停靠窗格的矩形，再问半格还够不够'
from ..引擎.几何 import 半格可放,分割下限

__all__=['窗格元素','量测窗格可放','取可放','可放相同','矩形自']

无矩形={'x':0,'y':0,'width':0,'height':0}
未测可放={'row':True,'column':True}

def 矩形自(元素):
    '元素的视口矩形。没有元素时是空矩形'
    if 元素 is None:
        return {'x':无矩形['x'],'y':无矩形['y'],'width':无矩形['width'],'height':无矩形['height']}
    盒=元素.getBoundingClientRect()
    return {'x':盒.x,'y':盒.y,'width':盒.width,'height':盒.height}

def 像素(值):
    '取计算样式开头的数字。读不出就是 0'
    文=str(值).strip()
    缓冲=''
    for 字 in 文:
        if 字.isdigit() or 字=='.' or (字=='-' and 缓冲==''):
            缓冲+=字
            continue
        break
    if 缓冲=='' or 缓冲=='-' or 缓冲=='.' or 缓冲=='-.':
        return 0
    return float(缓冲)

def 窗格元素(根):
    '根下每块停靠窗格和它的标识，按文档顺序'
    结果=[]
    for 窗格 in 根.querySelectorAll('[data-dockkit-pane]'):
        标识=窗格.getAttribute('data-dockkit-pane')
        if 标识 is None:
            continue
        结果.append((标识,窗格))
    return 结果

def 量测窗格可放(根,挡住时隐藏分割=False):
    '量每块停靠窗格对半切开后还够不够用'
    视图=根.ownerDocument.defaultView
    分割条=根.querySelector('[data-dockkit-divider]')
    if 分割条 is None:
        条厚=分割下限['divider']
    else:
        盒=分割条.getBoundingClientRect()
        厚=min(盒.width,盒.height)
        if 厚>0:
            条厚=厚
        else:
            条厚=分割下限['divider']
    芯片=根.querySelector('[data-dockkit-tab]')
    if 芯片 is None:
        芯片下限=分割下限['chip']
    else:
        样式=视图.getComputedStyle(芯片)
        最小=像素(样式.minWidth)
        if 最小<=0:
            芯片下限=分割下限['chip']
        elif 样式.boxSizing=='border-box':
            芯片下限=最小
        else:
            芯片下限=(
                最小
                +像素(样式.paddingLeft)
                +像素(样式.paddingRight)
                +像素(样式.borderLeftWidth)
                +像素(样式.borderRightWidth)
            )
    下限={'divider':条厚,'chip':芯片下限,'body':分割下限['body']}
    可放={}
    for 标识,窗格 in 窗格元素(根):
        分割宽=0
        if 挡住时隐藏分割:
            控件=窗格.querySelector('[data-dockkit-split-button]')
            if 控件 is not None:
                宽=控件.getBoundingClientRect().width
                if 宽>0:
                    条=窗格.querySelector('[data-dockkit-strip]')
                    if 条 is None:
                        间隙=0
                    else:
                        间隙=像素(视图.getComputedStyle(条).columnGap)
                    分割宽=宽+间隙
        可放[标识]=半格可放({
            'pane':矩形自(窗格),
            'strip':矩形自(窗格.querySelector('[data-dockkit-strip]')),
            'chipsWidth':矩形自(窗格.querySelector('[data-dockkit-strip-tabs]')).width,
            'fillWidth':矩形自(窗格.querySelector('[data-dockkit-strip-fill]')).width,
            'splitControlWidth':分割宽,
        },下限)
    return 可放

def 取可放(可放,窗格标识):
    '这一格最近一次的读数。没量过就当放得下'
    if 窗格标识 in 可放:
        return 可放[窗格标识]
    return {'row':未测可放['row'],'column':未测可放['column']}

def 可放相同(甲,乙):
    '两次测量是不是同一批窗格、同一组读数'
    if len(甲)!=len(乙):
        return False
    for 标识,读数 in 甲.items():
        if 标识 not in 乙:
            return False
        另=乙[标识]
        if 另['row']!=读数['row'] or 另['column']!=读数['column']:
            return False
    return True
