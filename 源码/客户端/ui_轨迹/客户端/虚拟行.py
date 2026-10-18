from urllib.parse import quote
from .轨迹记录 import 轨迹记录身份#稳定身份

__all__=['轨迹虚拟记录键','编组轨迹虚拟行']

内容行高度=30#普通账本行
折叠摘要高度=20#收起摘要
末端边界高度=9#末尾分隔符的下沿空隙

def 轨迹虚拟记录键(记录):
    '推导虚拟化器与浏览器滚动共用的行身份'
    身份=quote(轨迹记录身份(记录['cell']),safe='')#DOM 安全
    种类=记录.get('collapsedSummaryKind')
    if 种类 is None:
        return 身份#普通行
    return 身份+'\u0000summary\u0000'+种类#折叠摘要后缀

def 编组轨迹虚拟行(记录列表):
    '把仅分隔符记录挂到下一内容行，使虚拟化器永不拥有零高度条目'
    行列表=[]#可测行
    待挂=[]#还没遇到内容行的分隔符
    for 逻辑下标,记录 in enumerate(记录列表):
        条目={'logicalIndex':逻辑下标,'record':记录}#原位置
        if 记录['cell'].get('requestOnly') is True:
            待挂.append(条目)#零高度，挂到后面
            continue
        条目组=待挂+[条目]#分隔符跟着这条内容
        待挂=[]
        if 记录.get('collapsedSummaryKind') is None:
            高度=内容行高度
        else:
            高度=折叠摘要高度
        行列表.append({
            'entries':条目组,
            'height':高度,
            'key':轨迹虚拟记录键(记录),
        })
    if len(待挂)>0:
        行列表.append({
            'entries':待挂,#末尾分隔符单独成行
            'height':末端边界高度,
            'key':'|'.join(轨迹虚拟记录键(候选['record']) for 候选 in 待挂),
        })
    return 行列表
