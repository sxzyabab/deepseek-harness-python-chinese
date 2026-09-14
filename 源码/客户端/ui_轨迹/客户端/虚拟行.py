from urllib.parse import quote as 编码URI组件#DOM 安全身份编码
from .轨迹记录 import 轨迹记录身份#稳定记录身份

__all__=['内容行高度','折叠摘要高度','末端边界高度','轨迹虚拟记录键','编组轨迹虚拟行']#仅中文公开名

内容行高度=30#普通内容行高度
折叠摘要高度=20#折叠摘要行高度
末端边界高度=9#末端边界行高度

def 轨迹虚拟记录键(记录):#推导虚拟行记录键
    """推导 React、虚拟化器与浏览器滚动约定共用的 DOM 安全行身份。"""
    单元格=记录['cell'] if 'cell' in 记录 else 记录#优先 cell
    折叠=记录['collapsedSummaryKind'] if 'collapsedSummaryKind' in 记录 else None#折叠摘要种类
    身份=编码URI组件(轨迹记录身份(单元格),safe='')#编码后的稳定记录身份
    if 折叠 is None:#不是折叠摘要
        return 身份#直接用编码身份
    return f'{身份}\u0000summary\u0000{折叠}'#追加摘要后缀与种类

def 编组轨迹虚拟行(记录列表):#把记录编成可测量虚拟行
    """把仅分隔符记录挂到下一内容行，使虚拟化器永不拥有零高度条目。"""
    行列表=[]#已编成的虚拟行
    待挂=[]#尚未挂到内容行的分隔条目
    for 逻辑下标,记录 in enumerate(记录列表):#按账本顺序逐条
        条目={'logicalIndex':逻辑下标,'record':记录}#带逻辑下标的条目
        单元格=记录['cell'] if 'cell' in 记录 else 记录#单元格
        if 'requestOnly' in 单元格 and 单元格['requestOnly'] is True:#仅请求分隔锚点
            待挂.append(条目)#挂到下一内容行
            continue#等内容行再成组
        本行条目=待挂+[条目]#分隔条目加上本条内容
        待挂=[]#清空待挂队列
        折叠=记录['collapsedSummaryKind'] if 'collapsedSummaryKind' in 记录 else None#折叠种类
        行列表.append({#压入一条可测量内容行
            'entries':本行条目,#本行全部逻辑条目
            'height':内容行高度 if 折叠 is None else 折叠摘要高度,#行高度
            'key':轨迹虚拟记录键(记录),#以内容记录身份为键
        })#内容行结束
    if len(待挂)>0:#账本末尾仍有未挂分隔符
        行列表.append({#末端分隔符自成一行
            'entries':待挂,#剩余仅分隔条目
            'height':末端边界高度,#CSS 下标记留白高度
            'key':'|'.join(轨迹虚拟记录键(项['record']) for 项 in 待挂),#各分隔身份用竖线拼接
        })#末端边界行结束
    return 行列表#全部可测量虚拟行
