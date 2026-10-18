'交互上限和停靠区位。模型本身不设限，这些是交互层在派发前用的规则'
from ..异常 import 未处理
from .树 import 停靠窗格标识列表

__all__=[
    '最大停靠窗格数','最小窗格份额','浮动默认尺寸','浮动最小尺寸',
    '停靠边带份额','停靠窗格数','可分割','停靠区位表','区位','区位分割','钳制尺寸',
]

最大停靠窗格数=4
最小窗格份额=0.12
浮动默认尺寸={'width':380,'height':300}
浮动最小尺寸={'width':220,'height':140}
停靠边带份额=0.25
停靠区位表=('center','top','right','bottom','left')

def 停靠窗格数(状态):
    '停靠树里有几块窗格。浮动的不算'
    return len(停靠窗格标识列表(状态))

def 可分割(状态):
    '还能不能再开一块停靠窗格'
    return 停靠窗格数(状态)<最大停靠窗格数

def 区位(横,纵,边带=None):
    '指针在窗格宽高份额上的停靠区位。靠哪条边最近，且进了边带，否则是 center'
    if 边带 is None:
        边带=停靠边带份额
    区='left'
    距离=横
    if 1-横<距离:
        区='right'
        距离=1-横
    if 纵<距离:
        区='top'
        距离=纵
    if 1-纵<距离:
        区='bottom'
        距离=1-纵
    if 距离<边带:
        return 区
    return 'center'

def 区位分割(区):
    '这个区位会怎么切开窗格。center 不切，只是把标签移进去'
    if 区=='center':
        return None
    if 区=='left':
        return {'axis':'row','direction':'before'}
    if 区=='right':
        return {'axis':'row','direction':'after'}
    if 区=='top':
        return {'axis':'column','direction':'before'}
    if 区=='bottom':
        return {'axis':'column','direction':'after'}
    未处理(区,'layout: dock zone')

def 钳制尺寸(份额表,下限=None):
    '把分割份额钳到不低于下限，总和仍为 1'
    if 下限 is None:
        下限=最小窗格份额
    if len(份额表)==0:
        return []
    地板=min(下限,1/len(份额表))
    正向=[]
    for 份额 in 份额表:
        if 份额>0:
            正向.append(份额)
        else:
            正向.append(0)
    合计=0
    for 份额 in 正向:
        合计+=份额
    if 合计>0:
        份额列=[]
        for 份额 in 正向:
            份额列.append(份额/合计)
    else:
        份额列=[]
        for 份额 in 正向:
            份额列.append(1/len(份额表))
    钉住=set()
    while True:
        不足=[]
        for 序号,份额 in enumerate(份额列):
            if 序号 not in 钉住 and 份额<地板:
                不足.append(序号)
        if len(不足)==0:
            return 份额列
        for 序号 in 不足:
            钉住.add(序号)
        剩余=1-len(钉住)*地板
        自由合计=0
        for 序号,份额 in enumerate(份额列):
            if 序号 not in 钉住:
                自由合计+=份额
        下一=[]
        for 序号,份额 in enumerate(份额列):
            if 序号 in 钉住:
                下一.append(地板)
            else:
                下一.append((份额/自由合计)*剩余)
        份额列=下一
