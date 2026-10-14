'目录加载中和读取失败'
from nicegui import ui as 界面
from ...ui_基础界面组件.状态点 import 状态点

__all__=['目录反馈']

class 目录反馈:
    '父组件调用渲染。空面板居中，已有内容时只在失败旁放重试'
    def __init__(自身,属性=None):
        '只记 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        'loading 转圈；error 说明加重试'
        属性=自身.属性
        状态=属性['status'] if 'status' in 属性 else 'ready'
        有内容='populated' in 属性 and 属性['populated'] is True
        翻译=属性['t'] if 't' in 属性 and callable(属性['t']) else (lambda 键,_参数=None:键)
        重试=属性['onRetry'] if 'onRetry' in 属性 and callable(属性['onRetry']) else (lambda *_参数:None)
        if 状态=='loading' and 有内容 is False:
            with 界面.row().classes('schedule-empty'):
                状态点({'state':'ongoing'}).渲染()
                界面.label(翻译('list.loading'))
            return
        if 状态!='error':
            return
        if 有内容:
            with 界面.row().classes('schedule-notice'):
                界面.label(翻译('list.error'))
                界面.button(翻译('list.retry'), on_click=lambda:重试()).props('outline')
            return
        with 界面.column().classes('schedule-empty'):
            界面.icon('warning', size='24px')
            界面.label(翻译('list.error'))
            界面.button(翻译('list.retry'), on_click=lambda:重试()).props('outline')

    def __call__(自身,属性=None):
        '更新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
