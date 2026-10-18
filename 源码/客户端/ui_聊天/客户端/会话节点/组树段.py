from ..约定.组树 import 在该层或更外
from .节点工厂 import 位置坐标

__all__=['组树段']

无回合=()


class 组树段:
    '已加载回合按某个组树位置上的节点切成连续段。最新段从最后一个这样的回合开始'
    def __init__(自身,位置):
        '记下哪一层节点会切开一段'
        自身.位置=位置
        自身.开口={}
        自身.最新开口=None
        自身.最新起点=None

    def 跟踪(自身,先前,其后):
        '记一笔节点变化。同一回合的开口数加减，归零就重新找最新开口'
        之前=自身.开口回合(先前)
        之后=自身.开口回合(其后)
        if 之前==之后:
            return
        if 之前 is not None and 自身.调整(之前,-1)==0 and 之前==自身.最新开口:
            自身.最新开口=自身.最后开口回合()
        if 之后 is not None:
            自身.调整(之后,1)
            if 自身.最新开口 is None or 之后>自身.最新开口:
                自身.最新开口=之后

    def 在最新段(自身,回合):
        '按上一次结算，这个回合是不是在最新段里'
        return 回合 is not None and 自身.最新起点 is not None and 回合>=自身.最新起点

    def 结算(自身,回合序):
        '按当前已加载回合移动最新段起点，返回进出最新段的回合'
        先前=自身.最新起点
        起点=自身.最新开口 if 自身.最新开口 is not None else (回合序[0] if len(回合序)>0 else None)
        if 起点==先前:
            return 无回合
        自身.最新起点=起点
        有界=先前 is not None and 起点 is not None
        if 有界:
            下界=先前 if 先前<起点 else 起点
            上界=先前 if 先前>起点 else 起点
        else:
            下界=None
            上界=None
        变化=[]
        开始=0
        if 下界 is not None:
            下标=-1
            序号=0
            for 回合 in 回合序:
                if 回合<下界:
                    下标=序号
                序号+=1
            开始=下标+1
        for 回合 in list(回合序)[开始:]:
            if 上界 is not None and 回合>=上界:
                break
            变化.append(回合)
        return 变化

    def 开口回合(自身,节点):
        '这个节点如果站在这一层或更外，返回它的回合'
        if 节点 is None or not isinstance(节点,dict) or not 在该层或更外(节点,自身.位置):
            return None
        return 位置坐标(节点.get('location')).get('turn')

    def 最后开口回合(自身):
        '开口表里最大的回合'
        最后=None
        for 回合 in 自身.开口:
            if 最后 is None or 回合>最后:
                最后=回合
        return 最后

    def 调整(自身,回合,增量):
        '加减这一回合的开口数。归零就从表里拿掉'
        下一=自身.开口.get(回合,0)+增量
        if 下一>0:
            自身.开口[回合]=下一
        elif 回合 in 自身.开口:
            del 自身.开口[回合]
        return 下一
