"""房间规则的量测侧：由宿主提供窗格像素后调用半格可放。

对齐上游 `ui-dockkit/src/components/measure.ts`。公开面仅中文名。
引擎规划不见像素；本模块比较两次量测是否同结果。
"""
from ..引擎.几何 import 半格可放,分割下限#几何

__all__=['量测窗格可放','取可放','可放相同','未量可放']#仅中文公开名

未量可放={'row':True,'column':True}#未测视为可放


def 量测窗格可放(窗格测量表,下限=None):
    """窗格标识→测量 dict 映射，返回标识→半格可放结果。

    每项测量含 pane / strip / chipsWidth / fillWidth（与几何.半格可放 一致）。
    """
    if 下限 is None:#默认
        下限=分割下限#样式
    结果={}#表
    for 窗格标识,测量 in 窗格测量表.items():#逐窗
        结果[窗格标识]=半格可放(测量,下限)#可放
    return 结果#表


def 取可放(可放表,窗格标识):
    """一窗格最新读数；表中无名则未量可放。"""
    if 窗格标识 not in 可放表:#未量
        return 未量可放#放行
    return 可放表[窗格标识]#读数


def 可放相同(甲,乙):
    """两次量测是否同窗同读，避免无变重渲。"""
    if len(甲)!=len(乙):#大小
        return False#异
    for 窗格标识,可放 in 甲.items():#逐
        if 窗格标识 not in 乙:#缺
            return False#异
        另=乙[窗格标识]#另
        if 另['row']!=可放['row'] or 另['column']!=可放['column']:#异
            return False#异
    return True#同
