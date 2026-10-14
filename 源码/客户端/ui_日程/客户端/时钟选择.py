'时、分、秒三列'
from nicegui import ui as 界面
from .选择器弹出 import 选择器弹出

__all__=['时钟选择']

def _段(值):
    'HH:MM 或 HH:MM:SS'
    if not isinstance(值,str):
        return ('00','00','00')
    部分=值.split(':')
    时=部分[0] if len(部分)>0 and 部分[0].isdigit() else '00'
    分=部分[1] if len(部分)>1 and 部分[1].isdigit() else '00'
    秒=部分[2] if len(部分)>2 and 部分[2].isdigit() else '00'
    return (时.zfill(2)[:2],分.zfill(2)[:2],秒.zfill(2)[:2])

class 时钟选择:
    '父组件调用渲染。选完交给 onPick'
    def __init__(自身,属性=None):
        '只记 props'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.打开=False

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '按钮打开三列'
        if getattr(自身,'_壳',None) is None:
            自身._壳=界面.column().classes('schedule-clock')
        自身.重画()

    def 重画(自身):
        '时分秒选择'
        壳=自身._壳
        壳.clear()
        属性=自身.属性
        翻译=属性['t'] if 't' in 属性 and callable(属性['t']) else (lambda 键,_参数=None:键)
        要秒='seconds' not in 属性 or 属性['seconds'] is not False
        时,分,秒=_段(属性['value'] if 'value' in 属性 else '')
        def 切换():
            '开合'
            自身.打开=not 自身.打开
            自身.重画()
        def 提交(新时,新分,新秒):
            '拼成时钟文本'
            回调=属性['onPick'] if 'onPick' in 属性 else None
            文=f'{新时}:{新分}'+(f':{新秒}' if 要秒 else '')
            if callable(回调):
                回调(文)
        def 列():
            '三列数字'
            def 改时(事件):
                '改时'
                提交(事件.value,分,秒)
            def 改分(事件):
                '改分'
                提交(时,事件.value,秒)
            def 改秒(事件):
                '改秒'
                提交(时,分,事件.value)
            小时=[f'{n:02d}' for n in range(24)]
            六十分=[f'{n:02d}' for n in range(60)]
            with 界面.row():
                界面.select(小时, value=时, label=翻译('timing.hour'), on_change=改时)
                界面.select(六十分, value=分, label=翻译('timing.minute'), on_change=改分)
                if 要秒:
                    界面.select(六十分, value=秒, label=翻译('timing.second'), on_change=改秒)
        展示=f'{时}:{分}'+(f':{秒}' if 要秒 else '')
        with 壳:
            界面.button(展示, on_click=切换).props('outline')
            选择器弹出({'open':自身.打开,'label':翻译('timing.time'),'children':列,'onClose':切换}).渲染()

    def __call__(自身,属性=None):
        '更新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
