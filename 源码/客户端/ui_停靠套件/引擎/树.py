"""布局状态上的纯树读写。

对齐上游 `ui-dockkit/src/engine/tree.ts`。公开面仅中文名。
每个读者在悬空标识上抛错（操作词汇封闭，未命中是调用方缺陷）；
每个写者返回新状态，未触动的节点保持原身份（同一 dict 引用）。
"""
from ..约定.类型 import 停靠错误,节点种分割,节点种窗格,窗格宿主浮动#约定

__all__=[#仅中文公开名
    '断言穷尽',
    '取节点',
    '取窗格',
    '取分割',
    '取标签',
    '浮动矩形',
    '浮动序号',
    '唯一标签标识',
    '找父分割',
    '查找标签窗格',
    '停靠窗格标识列表',
    '归一尺寸',
    '条目对',
    '键列表',
    '换节点',
    '换标签',
    '插入于',
    '移除于',
    '邻标签标识',
    '窗格换标签条',
    '父槽替换',
    '首停靠窗格标识',
    '右上窗格标识',
]#公开面结束


def 断言穷尽(值,何物):
    """封闭 switch 的未处理判别；抛停靠错误且永不返回。"""
    raise 停靠错误(何物+': unhandled '+repr(值))#未处理


def 取节点(状态,标识):
    """读任意节点。标识不在树中则抛。"""
    节点表=状态['nodes']#节点表
    if 标识 not in 节点表:#悬空
        raise 停靠错误('layout: unknown node '+str(标识))#拒绝
    return 节点表[标识]#节点


def 取窗格(状态,标识):
    """读窗格。缺失或指向分割则抛。"""
    节点=取节点(状态,标识)#节点
    if 节点['kind']!=节点种窗格:#非窗格
        raise 停靠错误('layout: '+str(标识)+' is not a pane')#拒绝
    return 节点#窗格


def 取分割(状态,标识):
    """读分割。缺失或指向窗格则抛。"""
    节点=取节点(状态,标识)#节点
    if 节点['kind']!=节点种分割:#非分割
        raise 停靠错误('layout: '+str(标识)+' is not a split')#拒绝
    return 节点#分割


def 取标签(状态,标识):
    """读标签记录。未打开则抛。"""
    标签表=状态['tabs']#标签表
    if 标识 not in 标签表:#未打开
        raise 停靠错误('layout: unknown tab '+str(标识))#拒绝
    return 标签表[标识]#记录


def 浮动矩形(窗格):
    """浮动窗格的视口矩形。停靠则抛。"""
    if 窗格['host']!=窗格宿主浮动 or 窗格['rect'] is None:#非浮动
        raise 停靠错误('layout: '+str(窗格['id'])+' is not floating')#拒绝
    return 窗格['rect']#矩形


def 浮动序号(状态,标识):
    """浮动窗格在 z 序中的下标（底在前）。未列入则抛。"""
    try:#查找
        return 状态['floats'].index(标识)#下标
    except ValueError:#不在
        raise 停靠错误('layout: floating pane '+str(标识)+' is not in the z order')#拒绝


def 唯一标签标识(窗格):
    """窗格恰有一标签时返回其标识，否则抛。"""
    标签条=窗格['tabs']#标签条
    if len(标签条)!=1:#非恰一
        raise 停靠错误('layout: '+str(窗格['id'])+' does not hold exactly one tab')#拒绝
    return 标签条[0]#唯一


def 找父分割(状态,标识):
    """持有该节点的分割；停靠根与浮动窗格返回 None。"""
    for 节点 in 状态['nodes'].values():#遍历
        if 节点['kind']==节点种分割 and 标识 in 节点['children']:#子含
            return 节点#父
    return None#无父


def 查找标签窗格(状态,标签标识):
    """条带列出该标签的窗格；无则抛。"""
    for 节点 in 状态['nodes'].values():#遍历
        if 节点['kind']==节点种窗格 and 标签标识 in 节点['tabs']:#含标签
            return 节点#窗格
    raise 停靠错误('layout: tab '+str(标签标识)+' has no pane')#拒绝


def 停靠窗格标识列表(状态):
    """视觉序（深度优先）的停靠窗格标识；不含浮动。"""
    结果=[]#输出

    def 行走(标识):
        """递归下探。"""
        节点=取节点(状态,标识)#节点
        if 节点['kind']==节点种窗格:#叶
            结果.append(节点['id'])#记下
            return#止
        for 子 in 节点['children']:#子
            行走(子)#续

    行走(状态['rootId'])#自根
    return 结果#列表


def 归一尺寸(尺寸表):
    """使份额和为 1。已和为 1 则原样拷贝，避免回放漂移。"""
    总和=0.0#累计
    for 份额 in 尺寸表:#累加
        总和+=份额#加
    if not (总和>0):#非法
        raise 停靠错误('layout: sizes must sum above zero')#拒绝
    if abs(总和-1)<1e-12:#已归一
        return list(尺寸表)#拷贝
    return [份额/总和 for 份额 in 尺寸表]#缩放


def 条目对(记录):
    """id 键记录的条目对列表。"""
    return list(记录.items())#条目


def 键列表(记录):
    """id 键记录的键列表。"""
    return list(记录.keys())#键


def 换节点(状态,更新):
    """替换或删除节点。更新中值为 None 表示删除；未触动节点保持原引用。"""
    节点表={}#新表
    for 标识,节点 in 条目对(状态['nodes']):#旧
        if 标识 not in 更新:#未更新
            节点表[标识]=节点#保留
    for 标识,节点 in 条目对(更新):#新
        if 节点 is not None:#非删
            节点表[标识]=节点#写入
    下一=dict(状态)#浅拷
    下一['nodes']=节点表#换
    return 下一#状态


def 换标签(状态,更新):
    """替换或删除标签记录。更新中值为 None 表示删除。"""
    标签表={}#新表
    for 标识,记录 in 条目对(状态['tabs']):#旧
        if 标识 not in 更新:#未更新
            标签表[标识]=标签#保留
    for 标识,标签 in 条目对(更新):#新
        if 标签 is not None:#非删
            标签表[标识]=标签#写入
    下一=dict(状态)#浅拷
    下一['tabs']=标签表#换
    return 下一#状态


def 插入于(项表,下标,值):
    """在夹紧后的槽位插入，返回新列表。"""
    处=max(0,min(下标,len(项表)))#夹紧
    return list(项表[:处])+[值]+list(项表[处:])#新表


def 移除于(项表,下标):
    """去掉一处，返回新列表。"""
    return list(项表[:下标])+list(项表[下标+1:])#新表


def 邻标签标识(标签条,移除下标):
    """移除后焦点邻：有前取前，否则取后，空则 None。"""
    剩余=移除于(标签条,移除下标)#剩余
    if len(剩余)==0:#空
        return None#无
    return 剩余[max(0,移除下标-1)]#邻


def 窗格换标签条(窗格,标签条,活动标签标识):
    """拷贝窗格并换标签条与活动标签。"""
    下一=dict(窗格)#浅拷
    下一['tabs']=list(标签条)#条
    下一['activeTabId']=活动标签标识#活动
    return 下一#窗格


def 父槽替换(状态,目标标识,替换标识):
    """在父分割槽或停靠根上把目标换成替换者。"""
    父=找父分割(状态,目标标识)#父
    if 父 is None:#无父
        if 状态['rootId']!=目标标识:#非根
            raise 停靠错误('layout: '+str(目标标识)+' is neither rooted nor parented')#拒绝
        下一=dict(状态)#浅拷
        下一['rootId']=替换标识#换根
        return 下一#状态
    子表=[替换标识 if 子==目标标识 else 子 for 子 in 父['children']]#换槽
    新父=dict(父)#浅拷
    新父['children']=子表#子
    return 换节点(状态,{父['id']:新父})#写回


def _下探(状态,选取):
    """自停靠根下探；每层分割由选取指名子。"""
    节点=取节点(状态,状态['rootId'])#当前
    while 节点['kind']==节点种分割:#分割
        下一标识=选取(节点)#选子
        if 下一标识 is None:#无子
            raise 停靠错误('layout: split '+str(节点['id'])+' has no children')#拒绝
        节点=取节点(状态,下一标识)#下
    return 节点['id']#窗格


def 首停靠窗格标识(状态):
    """视觉序第一个停靠窗格：根或其下首叶。"""
    return _下探(状态,lambda 分割:分割['children'][0] if len(分割['children'])>0 else None)#首子


def 右上窗格标识(状态):
    """右上角停靠窗格：行取末子、列取首子。"""

    def 选取(分割):
        """按轴取角。"""
        子=分割['children']#子
        if len(子)==0:#空
            return None#无
        return 子[-1] if 分割['axis']=='row' else 子[0]#角

    return _下探(状态,选取)#角窗格
