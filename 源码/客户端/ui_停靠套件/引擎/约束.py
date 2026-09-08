"""交互限额与停靠边带几何。

对齐上游 `ui-dockkit/src/engine/constraints.ts`。公开面仅中文名。
模型本身无界；这些是交互层派发前强制的 V1 规则。
"""
from .树 import 断言穷尽,停靠窗格标识列表#树

__all__=[#仅中文公开名
    '最大停靠窗格数',
    '最小窗格份额',
    '浮动默认尺寸',
    '浮动最小尺寸',
    '停靠边带份额',
    '停靠区位表',
    '停靠窗格数',
    '可分割',
    '区位',
    '区位分割',
    '钳制尺寸',
]#公开面结束

最大停靠窗格数=4#V1 停靠网格上限；浮动不计
最小窗格份额=0.12#分割条拖拽最小份额
浮动默认尺寸={'width':380,'height':300}#首浮尺寸（CSS 像素）
浮动最小尺寸={'width':220,'height':140}#浮动可缩下限
停靠边带份额=0.25#边带占宽高份额
停靠区位表=['center','top','right','bottom','left']#五区位


def 停靠窗格数(状态):
    """停靠树窗格数；浮动不计。"""
    return len(停靠窗格标识列表(状态))#计数


def 可分割(状态):
    """停靠树是否仍低于最大停靠窗格数。"""
    return 停靠窗格数(状态)<最大停靠窗格数#可


def 区位(横份额,纵份额,边带=停靠边带份额):
    """指针落在窗格内的停靠边带区位；不在边带则中心。"""
    区='left'#初
    距=横份额#距左
    if 1-横份额<距:#更近右
        区='right'#右
        距=1-横份额#距
    if 纵份额<距:#更近上
        区='top'#上
        距=纵份额#距
    if 1-纵份额<距:#更近下
        区='bottom'#下
        距=1-纵份额#距
    return 区 if 距<边带 else 'center'#边或中


def 区位分割(区):
    """区位对应的分割轴与方向；中心返回 None（迁入窗格）。"""
    if 区=='center':#中
        return None#迁入
    if 区=='left':#左
        return {'axis':'row','direction':'before'}#行前
    if 区=='right':#右
        return {'axis':'row','direction':'after'}#行后
    if 区=='top':#上
        return {'axis':'column','direction':'before'}#列前
    if 区=='bottom':#下
        return {'axis':'column','direction':'after'}#列后
    return 断言穷尽(区,'layout: dock zone')#穷尽


def 钳制尺寸(尺寸表,下限=最小窗格份额):
    """钳制分割份额使无一低于下限，且和为 1。"""
    if len(尺寸表)==0:#空
        return []#空
    地板=min(下限,1/len(尺寸表))#可达成地板
    正=[份额 if 份额>0 else 0 for 份额 in 尺寸表]#非负
    总和=0.0#累
    for 份额 in 正:#加
        总和+=份额#累
    if 总和>0:#可归一
        份额表=[份额/总和 for 份额 in 正]#归一
    else:#全零
        份额表=[1/len(尺寸表) for _ in 尺寸表]#均分
    钉住=set()#已钉下标
    while True:#迭代钉地板
        不足=[]#本轮
        for 甲,份额 in enumerate(份额表):#扫
            if 甲 not in 钉住 and 份额<地板:#不足
                不足.append(甲)#记
        if len(不足)==0:#齐
            return 份额表#成
        for 甲 in 不足:#钉
            钉住.add(甲)#入
        余=1-len(钉住)*地板#自由余量
        自由和=0.0#自由份额和
        for 甲,份额 in enumerate(份额表):#加
            if 甲 not in 钉住:#自由
                自由和+=份额#累
        下一=[]#新表
        for 甲,份额 in enumerate(份额表):#重分配
            if 甲 in 钉住:#钉
                下一.append(地板)#地板
            else:#自由
                下一.append((份额/自由和)*余)#比例
        份额表=下一#换
