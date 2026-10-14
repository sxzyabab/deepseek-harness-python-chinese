'右侧标签芯片：时钟加任务标题'
from nicegui import ui as 界面
from ..异常 import 页面失败文案
from .日历图标 import 日历图标
from .任务标签目标 import 解析任务标签目标
from .日程格式 import 任务名

__all__=['日程任务标签标题']

def 取(对象,键):
    '字典或对象'
    if isinstance(对象,dict):
        return 对象[键] if 键 in 对象 else None
    return getattr(对象,键,None)

class 日程任务标签标题:
    '槽位只调用构造'
    def __init__(自身,属性=None):
        '记下 props。槽位只调用构造，键齐了就画。'
        自身.属性=属性 if isinstance(属性,dict) else {}
        if 'useTabInfo' in 自身.属性 and 'useCatalog' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '有目录行用标题，否则用详情名'
        属性=自身.属性
        翻译=属性['t'] if 't' in 属性 and callable(属性['t']) else (lambda 键,_参数=None:键)
        标签={}
        用=属性['useTabInfo'] if 'useTabInfo' in 属性 else None
        if callable(用):
            try:
                标签=取(用(lambda 当前:当前),'tab') or {}
            except Exception:
                标签={}
        解析=解析任务标签目标(属性.get('sessionId'),标签,属性['taskBindings'] if 'taskBindings' in 属性 else None)
        参数=解析['params']
        记录=None
        用目录=属性['useCatalog'] if 'useCatalog' in 属性 else None
        if callable(用目录) and isinstance(参数,dict):
            try:
                快照=用目录(lambda 当前:当前)
            except Exception:
                快照={}
            表=快照['records'] if isinstance(快照,dict) and 'records' in 快照 and isinstance(快照['records'],list) else []
            记录=next((项 for 项 in 表 if isinstance(项,dict) and 项.get('id')==参数.get('id')),None)
        with 界面.row().classes('schedule-tab-title').style('align-items:center;gap:6px'):
            日历图标({'size':16}).渲染()
            界面.label(翻译('detail.label') if 记录 is None else 任务名(记录))

    def __call__(自身,属性=None):
        '更新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
