'回合尾部的创建任务卡列表'
from nicegui import ui as 界面
from ..异常 import 页面失败文案
from .日程创建卡 import 日程创建卡
from .日程创建模型 import 创建工具名,日程创建卡模型
from .日程回合 import 选取日程任务

__all__=['日程回合卡']

class 日程回合卡:
    '槽位只调用构造。这一轮没有创建任务则不画'
    def __init__(自身,属性=None):
        '记下 props。槽位只调用构造，键齐了就画。'
        自身.属性=属性 if isinstance(属性,dict) else {}
        if 'turn' in 自身.属性 and 'useCatalog' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '每条已结算创建一张卡'
        匹配=选取日程任务(自身.属性)
        if 匹配 is None:
            return
        属性=自身.属性
        翻译=属性['t'] if 't' in 属性 and callable(属性['t']) else (lambda 键,_参数=None:键)
        目录=None
        用=属性['useCatalog'] if 'useCatalog' in 属性 else None
        if callable(用):
            try:
                目录=用(lambda 当前:当前)
            except Exception:
                目录=None
        重试=属性['onRetry'] if 'onRetry' in 属性 and callable(属性['onRetry']) else None
        基准=目录['readRequest'] if isinstance(目录,dict) and 'readRequest' in 目录 else 0
        if 重试 is not None:
            重试(基准)
        已答=isinstance(目录,dict) and 目录.get('settled') is True and 目录.get('readSettled',0)>基准
        记录=目录['records'] if 已答 and isinstance(目录,dict) and isinstance(目录.get('records'),list) else None
        with 界面.column().classes('schedule-turn-cards'):
            for 块 in 匹配['created']:
                模型=日程创建卡模型(块,创建工具名)
                任务=模型['task']
                当前缺席=True
                当前=None
                if 任务 is not None and 记录 is not None:
                    当前缺席=False
                    当前=next((项 for 项 in 记录 if isinstance(项,dict) and 项.get('id')==任务.get('id')),None)
                传入={'block':块,'toolName':创建工具名,'openTaskDetail':属性['openTaskDetail'] if 'openTaskDetail' in 属性 else None,'t':翻译}
                if 当前缺席 is False:
                    传入['currentTask']=当前
                日程创建卡(传入).渲染()

    def __call__(自身,属性=None):
        '更新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
