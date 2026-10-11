'实况折叠保持可见锚点，并把未使用的视口空间放在全部数据行之后'

__all__=['行高','检查器表格布局']

行高=30

class 检查器表格布局:
    '视图局部间距；没有前驱时构造会清掉保留的空白'
    def __init__(自身,层级,先前=None,视口=None,锚=None):
        '按当前可见行、上一份布局、滚动几何和可选锚点计算间距'
        if 视口 is None:
            视口={'offset':0,'height':0}
        自身.层级=层级
        自身.行下标={}
        for 行下标,行 in enumerate(层级.行):
            自身.行下标[行['key']]=行下标
        自身.项=[{'key':行['key'],'rowIndex':行下标,'row':行,'size':行高} for 行下标,行 in enumerate(层级.行)]
        自身.保留折叠=False
        if 先前 is not None and len(层级.行)<len(先前.层级.行):
            for 行 in 层级.行:
                if 行.get('disclosure')!='closed':
                    continue
                旧下标=先前.行下标.get(行['key'])
                if 旧下标 is None:
                    旧下标=-1
                旧行=先前.层级.行[旧下标]
                if 旧行.get('disclosure')=='open':
                    自身.保留折叠=True
                    break
        锚下标=None if 锚 is None else 自身.行下标.get(锚['key'])
        if 锚 is not None and 锚下标 is not None:
            自身.滚动偏移=max(0,(锚下标+1)*行高-锚['top'])
        elif 自身.保留折叠 and 先前 is not None:
            自身.滚动偏移=自身._锚偏移(先前,视口['offset'])
        else:
            自身.滚动偏移=None
        自然=(len(自身.项)+1)*行高
        if 自身.滚动偏移 is None:
            最小=0 if 先前 is None else 先前.最小范围
        else:
            先前最小=0 if 先前 is None else 先前.最小范围
            最小=max(自身.滚动偏移+视口['height'],先前最小+自身.滚动偏移-视口['offset'])
        自身.最小范围=最小 if 最小>自然 else 0
        自身.底内边距=max(0,自身.最小范围-自然)

    def 吸顶下标(自身,项下标):
        '保持包围表头出现在首个可见数据行之上'
        return 自身.层级.吸顶下标(项下标)

    def 偏移处吸顶下标(自身,偏移):
        '在表头和已占用吸顶行之下解析每一级'
        下标表=[]
        if len(自身.项)==0:
            return 下标表
        首=max(0,int(偏移/行高))
        while len(下标表)<len(自身.项):
            候选=min(len(自身.项)-1,首+len(下标表))
            祖先=自身.吸顶下标(候选)
            if len(下标表)>=len(祖先):
                break
            下一=祖先[len(下标表)]
            断开=False
            for 级,已有 in enumerate(下标表):
                if 级>=len(祖先) or 祖先[级]!=已有:
                    断开=True
                    break
            if 断开:
                break
            下标表.append(下一)
        return 下标表

    def _锚偏移(自身,先前,偏移):
        '沿前一份可见行或仍在的父级保持屏幕位置'
        首=max(0,min(len(先前.项)-1,int(偏移/行高)))
        下标=min(len(先前.项)-1,首+len(先前.偏移处吸顶下标(偏移)))
        行=先前.项[下标]['row']
        保留=自身.行下标.get(行['key'])
        if 保留 is not None:
            return max(0,偏移+(保留-下标)*行高)
        祖先=先前.吸顶下标(下标)
        级=len(祖先)-1
        while 级>=0:
            父=先前.项[祖先[级]]['row']
            下一=自身.行下标.get(父['key'])
            if 下一 is not None:
                return max(0,(下一-级)*行高)
            级-=1
        return 0
