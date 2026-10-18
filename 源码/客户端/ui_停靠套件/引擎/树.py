'布局树上的纯读取和纯替换。缺标识是调用方的错，按上游抛出'
from ..异常 import 停靠错误

__all__=[
    '盖上','条目表','取节点','取窗格','取分割','取标签',
    '浮动矩形','浮动序号','唯一标签标识','找父分割','查找标签窗格',
    '停靠窗格标识列表','归一份额','换节点','换标签','插入于','移除于',
    '邻标签标识','窗格换标签','父中替换','首停靠窗格标识','右上窗格标识',
]

def 盖上(原,改):
    '浅拷贝一份，再盖上改动的字段。没改到的对象保持原引用'
    出=dict(原)
    出.update(改)
    return 出

def 条目表(记录):
    '标识记录的键值对。键就是当初写进去的标识'
    return list(记录.items())

def 取节点(状态,标识):
    '按标识读分割或窗格'
    if 标识 not in 状态['nodes']:
        raise 停靠错误(f'layout: unknown node {标识}')
    return 状态['nodes'][标识]

def 取窗格(状态,标识):
    '按标识读窗格。分割标识不行'
    节点=取节点(状态,标识)
    if 节点['kind']!='pane':
        raise 停靠错误(f'layout: {标识} is not a pane')
    return 节点

def 取分割(状态,标识):
    '按标识读分割。窗格标识不行'
    节点=取节点(状态,标识)
    if 节点['kind']!='split':
        raise 停靠错误(f'layout: {标识} is not a split')
    return 节点

def 取标签(状态,标识):
    '按标识读标签记录'
    if 标识 not in 状态['tabs']:
        raise 停靠错误(f'layout: unknown tab {标识}')
    return 状态['tabs'][标识]

def 浮动矩形(窗格):
    '浮动窗格的视口矩形。停靠着的不行'
    if 窗格['host']!='float' or 窗格['rect'] is None:
        raise 停靠错误(f'layout: {窗格["id"]} is not floating')
    return 窗格['rect']

def 浮动序号(状态,标识):
    '浮动窗格在叠放里的位置，底下是 0'
    try:
        return 状态['floats'].index(标识)
    except ValueError:
        raise 停靠错误(f'layout: floating pane {标识} is not in the z order')

def 唯一标签标识(窗格):
    '窗格里仅有的那一个标签'
    if len(窗格['tabs'])!=1:
        raise 停靠错误(f'layout: {窗格["id"]} does not hold exactly one tab')
    return 窗格['tabs'][0]

def 找父分割(状态,标识):
    '抱着这个节点的分割。停靠根和浮动窗格没有'
    for 节点 in 状态['nodes'].values():
        if 节点['kind']=='split' and 标识 in 节点['children']:
            return 节点
    return None

def 查找标签窗格(状态,标签标识):
    '条带上列着这个标签的窗格'
    for 节点 in 状态['nodes'].values():
        if 节点['kind']=='pane' and 标签标识 in 节点['tabs']:
            return 节点
    raise 停靠错误(f'layout: tab {标签标识} has no pane')

def 停靠窗格标识列表(状态):
    '停靠窗格标识，按分割树的视觉顺序。浮动的不在里面'
    结果=[]
    def 走(标识):
        '深度优先收集窗格'
        节点=取节点(状态,标识)
        if 节点['kind']=='pane':
            结果.append(节点['id'])
            return
        for 子 in 节点['children']:
            走(子)
    走(状态['rootId'])
    return 结果

def 归一份额(份额表):
    '把份额缩放到和为 1。已经是 1 的原样复制，避免回放漂移'
    合计=0
    for 份额 in 份额表:
        合计+=份额
    if not (合计>0):
        raise 停靠错误('layout: sizes must sum above zero')
    if abs(合计-1)<1e-12:
        return list(份额表)
    出=[]
    for 份额 in 份额表:
        出.append(份额/合计)
    return 出

def 换节点(状态,更新):
    '替换或删除节点。更新里 None 表示删掉这个标识'
    节点表={}
    for 标识,节点 in 条目表(状态['nodes']):
        if 标识 not in 更新:
            节点表[标识]=节点
    for 标识,节点 in 条目表(更新):
        if 节点 is not None:
            节点表[标识]=节点
    return 盖上(状态,{'nodes':节点表})

def 换标签(状态,更新):
    '替换或删除标签记录。更新里 None 表示删掉'
    标签表={}
    for 标识,标签 in 条目表(状态['tabs']):
        if 标识 not in 更新:
            标签表[标识]=标签
    for 标识,标签 in 条目表(更新):
        if 标签 is not None:
            标签表[标识]=标签
    return 盖上(状态,{'tabs':标签表})

def 插入于(表,下标,值):
    '在下标处插入。下标会夹到表的两端之间'
    位于=max(0,min(下标,len(表)))
    return [*表[:位于],值,*表[位于:]]

def 移除于(表,下标):
    '去掉下标上的那一项'
    return [*表[:下标],*表[下标+1:]]

def 邻标签标识(标签表,移除下标):
    '一个标签离开后，窗格改聚焦谁。优先左边，否则右边'
    剩余=移除于(标签表,移除下标)
    if len(剩余)==0:
        return None
    return 剩余[max(0,移除下标-1)]

def 窗格换标签(窗格,标签序,活动标签):
    '复制窗格并换上新的标签序。活动标签由调用方保持一致'
    return 盖上(窗格,{'tabs':标签序,'activeTabId':活动标签})

def 父中替换(状态,目标标识,替换标识):
    '在父分割的槽位上换成另一个节点。没有父节点时它就是停靠根'
    父=找父分割(状态,目标标识)
    if 父 is None:
        if 状态['rootId']!=目标标识:
            raise 停靠错误(f'layout: {目标标识} is neither rooted nor parented')
        return 盖上(状态,{'rootId':替换标识})
    子序=[]
    for 子 in 父['children']:
        if 子==目标标识:
            子序.append(替换标识)
        else:
            子序.append(子)
    return 换节点(状态,{父['id']:盖上(父,{'children':子序})})

def 下行(状态,选择):
    '从停靠根往下走。每个分割由选择函数指定下一子节点'
    节点=取节点(状态,状态['rootId'])
    while 节点['kind']=='split':
        下一=选择(节点)
        if 下一 is None:
            raise 停靠错误(f'layout: split {节点["id"]} has no children')
        节点=取节点(状态,下一)
    return 节点['id']

def 首停靠窗格标识(状态):
    '视觉顺序上的第一块停靠窗格'
    def 选首(分割):
        '每个分割走第一个子节点'
        return 分割['children'][0]
    return 下行(状态,选首)

def 右上窗格标识(状态):
    '右上角那块停靠窗格。行分割走最后一个，列分割走第一个'
    def 选角(分割):
        '行取末子，列取首子'
        if 分割['axis']=='row':
            return 分割['children'][len(分割['children'])-1]
        return 分割['children'][0]
    return 下行(状态,选角)
