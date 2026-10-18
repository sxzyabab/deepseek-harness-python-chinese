'拖拽用的纯几何。组件量完矩形再叫进来'
from .约束 import 停靠边带份额,区位

__all__=[
    '含点','矩形区位','插入下标','分割下限','半格可放',
    '拖拽阈值','已过阈值','分割条尺寸','平移矩形','缩放矩形','落点浮动矩形',
]

分割下限={'divider':0,'chip':100,'body':48}
拖拽阈值=4
抓取左=60
抓取上=14

def 含点(矩形,横,纵):
    '点是否在矩形内，边上也算'
    return 横>=矩形['x'] and 横<=矩形['x']+矩形['width'] and 纵>=矩形['y'] and 纵<=矩形['y']+矩形['height']

def 矩形区位(矩形,横,纵,边带=None):
    '点相对这块窗格矩形落在哪个停靠区位'
    if 边带 is None:
        边带=停靠边带份额
    if not (矩形['width']>0) or not (矩形['height']>0):
        return 'center'
    return 区位((横-矩形['x'])/矩形['width'],(纵-矩形['y'])/矩形['height'],边带)

def 插入下标(标签矩形表,横):
    '指针相对每个标签中点，落在条带的哪个插入槽。范围是 0 到标签数'
    下标=0
    for 矩形 in 标签矩形表:
        if 横<矩形['x']+矩形['width']/2:
            break
        下标+=1
    return 下标

def 半格可放(测量,下限=None):
    '对半切开后，两半是否都还放得下不能再缩的部分。没量到正数就当放得下'
    if 下限 is None:
        下限=分割下限
    窗格=测量['pane']
    条带=测量['strip']
    if not (窗格['width']>0) or not (窗格['height']>0) or not (条带['width']>0):
        return {'row':True,'column':True}
    边框=max(0,窗格['width']-条带['width'])
    控件宽=测量['splitControlWidth'] if 'splitControlWidth' in 测量 and 测量['splitControlWidth'] is not None else 0
    固定=max(0,条带['width']-测量['chipsWidth']-测量['fillWidth']-控件宽)
    半宽=(窗格['width']-下限['divider'])/2-边框
    半高=(窗格['height']-下限['divider'])/2-边框
    return {
        'row':半宽>=固定+下限['chip'],
        'column':半高>=条带['height']+下限['body'],
    }

def 已过阈值(起横,起纵,横,纵):
    '按下之后有没有走出拖拽阈值'
    return abs(横-起横)>=拖拽阈值 or abs(纵-起纵)>=拖拽阈值

def 分割条尺寸(份额表,下标,增量):
    '拖分割条之后的份额。变化全由相邻两格吸收'
    if 下标<0 or 下标+1>=len(份额表):
        return list(份额表)
    下一=list(份额表)
    下一[下标]=份额表[下标]+增量
    下一[下标+1]=份额表[下标+1]-增量
    return 下一

def 平移矩形(矩形,横移,纵移):
    '浮动面板拖动后的矩形，尺寸不变'
    出=dict(矩形)
    出['x']=矩形['x']+横移
    出['y']=矩形['y']+纵移
    return 出

def 缩放矩形(矩形,横移,纵移,最小):
    '从右下角缩放后的矩形，原点不变'
    出=dict(矩形)
    出['width']=max(最小['width'],矩形['width']+横移)
    出['height']=max(最小['height'],矩形['height']+纵移)
    return 出

def 落点浮动矩形(横,纵,尺寸):
    '标签丢到停靠区外面时，面板该出现在哪。页眉挨在落点下方偏左'
    return {
        'x':max(0,横-抓取左),
        'y':max(0,纵-抓取上),
        'width':尺寸['width'],
        'height':尺寸['height'],
    }
