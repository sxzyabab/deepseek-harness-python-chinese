'一轮里创建出的任务卡'
from nicegui import ui as 界面
from .日历图标 import 日历图标
from .日程创建模型 import 创建工具名,日程创建卡模型
from .日程格式 import 格式化日程频率,任务名

__all__=['日程创建卡']

class 日程创建卡:
    '父组件调用渲染。能打开时给出打开按钮'
    def __init__(自身,属性=None):
        '只记 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '标题、频率、打开'
        属性=自身.属性
        翻译=属性['t'] if 't' in 属性 and callable(属性['t']) else (lambda 键,_参数=None:键)
        工具=属性['toolName'] if 'toolName' in 属性 else 创建工具名
        模型=日程创建卡模型(属性['block'] if 'block' in 属性 else {},工具)
        当前='currentTask' in 属性
        任务=属性['currentTask'] if 当前 else 模型['task']
        已删=当前 and 属性['currentTask'] is None
        if 当前 and 属性['currentTask'] is not None:
            标题=任务名(属性['currentTask'])
        else:
            标题=模型['title']
        能开=isinstance(任务,dict) and 已删 is False
        def 打开():
            '打开右侧详情'
            回调=属性['openTaskDetail'] if 'openTaskDetail' in 属性 else None
            if callable(回调) and isinstance(任务,dict):
                回调(任务['id'])
        with 界面.row().classes('schedule-create-card'):
            日历图标({'size':18}).渲染()
            with 界面.column():
                界面.label(标题)
                if isinstance(任务,dict):
                    界面.label(翻译('card.deleted') if 已删 else 格式化日程频率(任务,翻译))
            if 能开:
                界面.button(翻译('card.open'), on_click=打开).props('outline aria-label="'+翻译('card.openLabel',{'title':标题})+'"')
            elif 模型['output'] is not None and 模型['task'] is None:
                界面.label(模型['output'])

    def __call__(自身,属性=None):
        '更新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
