from .消息铬 import 格式化消息时钟,格式化运行时长#时间标签
from .用日历日 import 用日历日#日席位
from .消息项 import 打开列

__all__=['消息图标动作']#仅中文公开名

from nicegui import ui as 界面

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

class 消息图标动作:
    '时钟 + 可选分叉'
    def __init__(自身,属性=None):
        '记下合成 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.根=None#列

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '动作行'
        属性=自身.属性#props
        节点=属性['node'] if 'node' in 属性 and 属性['node'] is not None else {}#节点
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        时间=属性['time'] if 'time' in 属性 else None#直接时刻
        if 时间 is None:
            时间=节点['time'] if 'time' in 节点 else None#时间
        if 时间 is None and 'finalNode' in 节点 and 节点['finalNode'] is not None:#定稿时间
            终=节点['finalNode']#定稿
            时间=终['time'] if 'time' in 终 else None#时间
        用日历日()#日席位（稳定时钟）
        时钟=格式化消息时钟(时间,翻译) if 时间 is not None else None#时钟
        分叉=属性['forkAt'] if 'forkAt' in 属性 else None#分叉
        属不可=属性['branchUnavailable'] if 'branchUnavailable' in 属性 else None#属不可
        节不可=节点['branchUnavailable'] if 'branchUnavailable' in 节点 else None#节不可
        不可用=属不可 is True or 节不可 is True#不可用
        时长=属性['durationMs'] if 'durationMs' in 属性 else None#时长
        运行=翻译('message.ranFor',{'duration':格式化运行时长(时长 if 时长 is not None else 0,翻译)}) if 时长 is not None else None#运行
        序号=节点['seq'] if 'seq' in 节点 else None#序号
        if 序号 is None and 'finalNode' in 节点 and 节点['finalNode'] is not None:
            终节=节点['finalNode']
            序号=终节['seq'] if 'seq' in 终节 else None
        已有回调=属性['onBranch'] if 'onBranch' in 属性 else None
        def 点分叉():
            '分叉到该序号'
            if 已有回调 is not None:
                已有回调()
                return
            if 分叉 is not None:
                分叉(序号)#分叉
        可分=(已有回调 is not None or 分叉 is not None) and 不可用 is False#可分
        with 打开列(自身,'消息图标动作'):
            with 界面.row().classes('动作行'):
                if 时钟 is not None and 时钟=='':
                    界面.label('')
                elif 时钟 is not None:
                    界面.label(时钟)
                if 运行 is not None:
                    界面.label(运行)
                if 可分 is True:
                    界面.button(翻译('message.branch'),on_click=点分叉)
                elif 不可用 is True:
                    界面.label(翻译('message.branchUnavailable'))

    def __call__(自身,属性=None):
        '对齐'
        if 属性 is not None:
            自身.更新(属性)#刷
        自身.渲染()#画
