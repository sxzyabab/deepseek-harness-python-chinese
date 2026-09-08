"""线性操作历史：在 施加操作 之上记录意图并步进。

对齐上游 `ui-dockkit` 引擎序列。公开面仅中文名。
记录是全量的——含焦点挪动；按意图成条，一步落在用户实际停住的点。
跨焦点条目的连续跑在后退/前进时并作一步。重做再施加已记操作；后退施加捕获的逆。
新记录在后退后会丢掉重做枝。
"""
from ..约定.类型 import 焦点操作种表#约定
from .操作 import 施加操作#操作引擎

__all__=[#仅中文公开名
    '空历史',
    '是否焦点操作',
    '可后退一步',
    '可前进一步',
    '已记操作表',
    '记录',
    '后退一步',
    '前进一步',
    '序列器',
]#公开面结束

空历史={'entries':[],'cursor':0}#空序列


def 是否焦点操作(操作):
    """是否仅挪焦点，从而并入邻条的撤销步。"""
    return 操作['type'] in 焦点操作种表#焦点种


def _是否焦点条目(历史,下标):
    """下标处条目是否仅焦点操作。"""
    if 下标<0 or 下标>=len(历史['entries']):#越界
        return False#否
    条目=历史['entries'][下标]#条目
    for 操作 in 条目['ops']:#逐操作
        if not 是否焦点操作(操作):#含非焦点
            return False#否
    return True#皆焦点


def 可后退一步(历史):
    """是否有已施加条目可退。"""
    return 历史['cursor']>0#可退


def 可前进一步(历史):
    """是否仍有重做枝。"""
    return 历史['cursor']<len(历史['entries'])#可进


def 已记操作表(历史):
    """已记全部操作（含未施加的重做枝），按记录序。"""
    结果=[]#扁平
    for 条目 in 历史['entries']:#逐条
        结果.extend(条目['ops'])#并入
    return 结果#列表


def 记录(历史,状态,操作表):
    """施加一意图的操作并记为一条；先丢掉重做枝。空操作不记。"""
    if 操作表 is None or len(操作表)==0:#空
        return {'history':历史,'state':状态}#原样
    下一=状态#游标
    逆表=[]#逆序堆积
    for 操作 in 操作表:#逐项
        果=施加操作(下一,操作)#施加
        下一=果['state']#进
        逆表=list(果['inverse'])+逆表#逆前插
    if 历史['cursor']==len(历史['entries']):#无重做枝
        保留=list(历史['entries'])#全留
    else:#截断
        保留=list(历史['entries'][:历史['cursor']])#截
    保留.append({'ops':list(操作表),'inverse':逆表})#新条目
    return {'history':{'entries':保留,'cursor':历史['cursor']+1},'state':下一}#步进


def 后退一步(历史,状态):
    """退一意图，或整段连续仅焦点意图；无可退返回 None。"""
    if not 可后退一步(历史):#无可退
        return None#无
    数=1#步数
    if _是否焦点条目(历史,历史['cursor']-1):#焦点跑
        while _是否焦点条目(历史,历史['cursor']-1-数):#连焦点
            数+=1#加
    下一=状态#游标
    for 条目 in reversed(历史['entries'][历史['cursor']-数:历史['cursor']]):#逆施加
        for 操作 in 条目['inverse']:#逆
            下一=施加操作(下一,操作)['state']#进
    return {'history':{'entries':历史['entries'],'cursor':历史['cursor']-数},'state':下一}#结果


def 前进一步(历史,状态):
    """前进对应后退所撤意图；无可进返回 None。"""
    if not 可前进一步(历史):#无可进
        return None#无
    数=1#步数
    if _是否焦点条目(历史,历史['cursor']):#焦点跑
        while _是否焦点条目(历史,历史['cursor']+数):#连
            数+=1#加
    下一=状态#游标
    for 条目 in 历史['entries'][历史['cursor']:历史['cursor']+数]:#正施加
        for 操作 in 条目['ops']:#正
            下一=施加操作(下一,操作)['state']#进
    return {'history':{'entries':历史['entries'],'cursor':历史['cursor']+数},'state':下一}#结果


class 序列器:
    """可变包装：自持状态与历史，委托纯函数 记录/后退一步/前进一步。"""

    def __init__(自身,初态):
        """初态为回放起点；不就地改。"""
        自身._状态=初态#当前
        自身._历史={'entries':[],'cursor':0}#独立空历史

    @property
    def 状态(自身):
        """当前布局状态。"""
        return 自身._状态#态

    @property
    def 历史(自身):
        """已记序列（纯数据）。"""
        return 自身._历史#史

    @property
    def 操作表(自身):
        """全部已记操作，含未施加重做枝。"""
        return 已记操作表(自身._历史)#表

    @property
    def 游标(自身):
        """已施加意图条数。"""
        return 自身._历史['cursor']#游标

    @property
    def 可撤销(自身):
        """是否可后退。"""
        return 可后退一步(自身._历史)#可

    @property
    def 可重做(自身):
        """是否可前进。"""
        return 可前进一步(自身._历史)#可

    def 派发(自身,操作):
        """记并施加单操作。"""
        return 自身.派发全部([操作])#单条

    def 派发全部(自身,操作表):
        """记并施加一意图；空则不动。"""
        步进=记录(自身._历史,自身._状态,操作表)#记
        自身._历史=步进['history']#史
        自身._状态=步进['state']#态
        return 自身._状态#态

    def 撤销(自身):
        """后退一步；无可退返回 False。"""
        步进=后退一步(自身._历史,自身._状态)#退
        if 步进 is None:#无
            return False#否
        自身._历史=步进['history']#史
        自身._状态=步进['state']#态
        return True#成

    def 重做(自身):
        """前进一步；无可进返回 False。"""
        步进=前进一步(自身._历史,自身._状态)#进
        if 步进 is None:#无
            return False#否
        自身._历史=步进['history']#史
        自身._状态=步进['state']#态
        return True#成
