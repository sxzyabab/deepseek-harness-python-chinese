'操作历史。一次意图记成一条，连续的纯焦点意图在撤销和重做时合成一步'
from .操作 import 施加操作

__all__=[
    '空历史','是否焦点操作','可后退一步','可前进一步','已记操作表',
    '记录','后退一步','前进一步','序列器',
]

空历史={'entries':[],'cursor':0}
焦点种类=('focusTab','focusPane','restoreFocus')

def 是否焦点操作(操作):
    '这条操作是不是只移动焦点'
    return 操作['type'] in 焦点种类

def 是否焦点条目(历史,下标):
    '这一条记录是不是全是焦点操作'
    if 下标<0 or 下标>=len(历史['entries']):
        return False
    条目=历史['entries'][下标]
    for 操作 in 条目['ops']:
        if not 是否焦点操作(操作):
            return False
    return True

def 可后退一步(历史):
    '还有没有已经施加、可以撤的记录'
    return 历史['cursor']>0

def 可前进一步(历史):
    '还有没有撤掉之后可以重做的记录'
    return 历史['cursor']<len(历史['entries'])

def 已记操作表(历史):
    '记过的操作，含还没重做的那一支'
    结果=[]
    for 条目 in 历史['entries']:
        结果.extend(条目['ops'])
    return 结果

def 记录(历史,状态,操作表):
    '施加这一意图的操作并记成一条。空操作什么都不记'
    if len(操作表)==0:
        return {'history':历史,'state':状态}
    下一=状态
    逆序=[]
    for 操作 in 操作表:
        结果=施加操作(下一,操作)
        下一=结果['state']
        逆序=[*结果['inverse'],*逆序]
    if 历史['cursor']==len(历史['entries']):
        留下=历史['entries']
    else:
        留下=历史['entries'][:历史['cursor']]
    return {
        'history':{'entries':[*留下,{'ops':操作表,'inverse':逆序}],'cursor':历史['cursor']+1},
        'state':下一,
    }

def 后退一步(历史,状态):
    '撤一条意图。连续的纯焦点意图一次撤完。没有可撤的就返回 None'
    if not 可后退一步(历史):
        return None
    数量=1
    if 是否焦点条目(历史,历史['cursor']-1):
        while 是否焦点条目(历史,历史['cursor']-1-数量):
            数量+=1
    下一=状态
    片段=历史['entries'][历史['cursor']-数量:历史['cursor']]
    for 条目 in reversed(片段):
        for 操作 in 条目['inverse']:
            下一=施加操作(下一,操作)['state']
    return {'history':{'entries':历史['entries'],'cursor':历史['cursor']-数量},'state':下一}

def 前进一步(历史,状态):
    '重做刚才撤掉的那些意图。没有可重做的就返回 None'
    if not 可前进一步(历史):
        return None
    数量=1
    if 是否焦点条目(历史,历史['cursor']):
        while 是否焦点条目(历史,历史['cursor']+数量):
            数量+=1
    下一=状态
    for 条目 in 历史['entries'][历史['cursor']:历史['cursor']+数量]:
        for 操作 in 条目['ops']:
            下一=施加操作(下一,操作)['state']
    return {'history':{'entries':历史['entries'],'cursor':历史['cursor']+数量},'state':下一}

class 序列器:
    '把历史和当前状态放在一起的可变外壳'
    def __init__(自身,初始):
        '从这份初始状态开始记。初始状态本身不改'
        自身._当前=初始
        自身._记录=空历史

    @property
    def 状态(自身):
        '当前布局'
        return 自身._当前

    @property
    def 历史(自身):
        '记下来的序列'
        return 自身._记录

    @property
    def 操作表(自身):
        '全部记过的操作，含未重做的一支'
        return 已记操作表(自身._记录)

    @property
    def 游标(自身):
        '已经施加了多少条记录'
        return 自身._记录['cursor']

    @property
    def 可撤销(自身):
        '还能不能后退'
        return 可后退一步(自身._记录)

    @property
    def 可重做(自身):
        '还能不能前进'
        return 可前进一步(自身._记录)

    def 派发(自身,操作):
        '把一条操作记成独立的一条记录'
        return 自身.派发全部([操作])

    def 派发全部(自身,操作表):
        '把这一意图的操作记成一条。非法操作不会改历史'
        步进=记录(自身._记录,自身._当前,操作表)
        自身._记录=步进['history']
        自身._当前=步进['state']
        return 自身._当前

    def 撤销(自身):
        '后退一条意图，或一整段连续的纯焦点意图'
        步进=后退一步(自身._记录,自身._当前)
        if 步进 is None:
            return False
        自身._记录=步进['history']
        自身._当前=步进['state']
        return True

    def 重做(自身):
        '重做刚才撤销的那些意图'
        步进=前进一步(自身._记录,自身._当前)
        if 步进 is None:
            return False
        自身._记录=步进['history']
        自身._当前=步进['state']
        return True
